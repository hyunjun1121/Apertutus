"""
Statistical Enhancements for EACL Paper
=======================================
Adds multiple comparison correction, effect sizes, power analysis, and robustness checks.
No new API calls required - uses existing evaluation data.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from scipy.stats import shapiro, wilcoxon, mannwhitneyu
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.power import TTestPower
import warnings
warnings.filterwarnings('ignore')

# Language list
LANGUAGES = [
    'arb.Arab', 'ces.Latn', 'cmn.Hani', 'deu.Latn', 'fra.Latn',
    'ind.Latn', 'ita.Latn', 'jpn.Jpan', 'kor.Hang', 'nld.Latn',
    'pol.Latn', 'por.Latn', 'ron.Latn', 'rus.Cyrl', 'spa.Latn', 'tur.Latn'
]

# Condition paths
CONDITIONS = {
    'Apertus-Eng': ('final_results', 'complete.json', 'evaluation'),
    'Apertus-Trans': ('final_results/apertus_translated_eval', 'apertus_translated_eval.json', 'apertus_translated_evaluation'),
    'GPT-Eng': ('final_results/gpt_english_eval', 'gpt_english_eval.json', 'gpt_english_evaluation'),
    'GPT-Trans': ('final_results/gpt_translated_eval', 'gpt_translated_eval.json', 'gpt_translated_evaluation')
}


def load_language_means():
    """Load mean scores for each language and condition."""
    data = {cond: [] for cond in CONDITIONS.keys()}

    for lang in LANGUAGES:
        for cond_name, (folder, suffix, eval_key) in CONDITIONS.items():
            file_path = Path(folder) / f'{lang}_{suffix}'
            with open(file_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)
            scores = [e[eval_key]['strongreject_score'] for e in entries]
            data[cond_name].append(np.mean(scores))

    return pd.DataFrame(data, index=LANGUAGES)


def cohen_d(x, y):
    """Calculate Cohen's d effect size for paired samples."""
    diff = np.array(x) - np.array(y)
    return np.mean(diff) / np.std(diff, ddof=1)


def eta_squared(group1, group2):
    """Calculate eta-squared effect size for independent samples."""
    all_data = np.concatenate([group1, group2])
    grand_mean = np.mean(all_data)

    ss_between = len(group1) * (np.mean(group1) - grand_mean)**2 + \
                 len(group2) * (np.mean(group2) - grand_mean)**2
    ss_total = np.sum((all_data - grand_mean)**2)

    return ss_between / ss_total


def multiple_comparison_correction(df):
    """Apply Bonferroni and FDR corrections to p-values."""
    results = []

    # Template effect: Apertus-Eng vs Apertus-Trans (paired)
    t_stat, p_val = stats.ttest_rel(df['Apertus-Eng'], df['Apertus-Trans'])
    d = cohen_d(df['Apertus-Eng'], df['Apertus-Trans'])
    results.append({
        'comparison': 'Apertus: Eng vs Trans',
        'test_type': 'paired t-test',
        't_statistic': t_stat,
        'p_value': p_val,
        'cohens_d': d,
        'effect_size_interpretation': interpret_cohens_d(d)
    })

    # Template effect: GPT-Eng vs GPT-Trans (paired)
    t_stat, p_val = stats.ttest_rel(df['GPT-Eng'], df['GPT-Trans'])
    d = cohen_d(df['GPT-Eng'], df['GPT-Trans'])
    results.append({
        'comparison': 'GPT: Eng vs Trans',
        'test_type': 'paired t-test',
        't_statistic': t_stat,
        'p_value': p_val,
        'cohens_d': d,
        'effect_size_interpretation': interpret_cohens_d(d)
    })

    # Judge gap: Apertus-Eng vs GPT-Eng (independent)
    t_stat, p_val = stats.ttest_ind(df['Apertus-Eng'], df['GPT-Eng'])
    eta2 = eta_squared(df['Apertus-Eng'].values, df['GPT-Eng'].values)
    results.append({
        'comparison': 'English template: Apertus vs GPT',
        'test_type': 'independent t-test',
        't_statistic': t_stat,
        'p_value': p_val,
        'eta_squared': eta2,
        'effect_size_interpretation': interpret_eta_squared(eta2)
    })

    # Judge gap: Apertus-Trans vs GPT-Trans (independent)
    t_stat, p_val = stats.ttest_ind(df['Apertus-Trans'], df['GPT-Trans'])
    eta2 = eta_squared(df['Apertus-Trans'].values, df['GPT-Trans'].values)
    results.append({
        'comparison': 'Native template: Apertus vs GPT',
        'test_type': 'independent t-test',
        't_statistic': t_stat,
        'p_value': p_val,
        'eta_squared': eta2,
        'effect_size_interpretation': interpret_eta_squared(eta2)
    })

    # Apply corrections
    p_values = [r['p_value'] for r in results]
    reject_bonf, p_bonf, _, _ = multipletests(p_values, method='bonferroni', alpha=0.05)
    reject_fdr, p_fdr, _, _ = multipletests(p_values, method='fdr_bh', alpha=0.05)

    for i, r in enumerate(results):
        r['p_bonferroni'] = p_bonf[i]
        r['p_fdr'] = p_fdr[i]
        r['significant_bonferroni'] = reject_bonf[i]
        r['significant_fdr'] = reject_fdr[i]

    return pd.DataFrame(results)


def interpret_cohens_d(d):
    """Interpret Cohen's d effect size."""
    abs_d = abs(d)
    if abs_d < 0.2:
        return 'negligible'
    elif abs_d < 0.5:
        return 'small'
    elif abs_d < 0.8:
        return 'medium'
    else:
        return 'large'


def interpret_eta_squared(eta2):
    """Interpret eta-squared effect size."""
    if eta2 < 0.01:
        return 'negligible'
    elif eta2 < 0.06:
        return 'small'
    elif eta2 < 0.14:
        return 'medium'
    else:
        return 'large'


def power_analysis(df):
    """Conduct post-hoc power analysis."""
    power_calc = TTestPower()
    results = []

    # Template effect: Apertus
    d = cohen_d(df['Apertus-Eng'], df['Apertus-Trans'])
    power = power_calc.solve_power(effect_size=abs(d), nobs=len(df), alpha=0.05)
    results.append({
        'analysis': 'Apertus: Eng vs Trans',
        'effect_size': d,
        'sample_size': len(df),
        'alpha': 0.05,
        'power': power,
        'power_interpretation': 'adequate' if power >= 0.8 else 'inadequate'
    })

    # Template effect: GPT
    d = cohen_d(df['GPT-Eng'], df['GPT-Trans'])
    power = power_calc.solve_power(effect_size=abs(d), nobs=len(df), alpha=0.05)
    results.append({
        'analysis': 'GPT: Eng vs Trans',
        'effect_size': d,
        'sample_size': len(df),
        'alpha': 0.05,
        'power': power,
        'power_interpretation': 'adequate' if power >= 0.8 else 'inadequate'
    })

    return pd.DataFrame(results)


def normality_tests(df):
    """Test normality assumptions for t-tests."""
    results = []

    for col in df.columns:
        stat, p_val = shapiro(df[col])
        results.append({
            'condition': col,
            'shapiro_statistic': stat,
            'shapiro_p_value': p_val,
            'is_normal': p_val > 0.05,
            'interpretation': 'Normal' if p_val > 0.05 else 'Non-normal (consider non-parametric tests)'
        })

    return pd.DataFrame(results)


def non_parametric_tests(df):
    """Conduct non-parametric alternatives (robustness check)."""
    results = []

    # Wilcoxon signed-rank test (paired alternative to t-test)
    stat, p_val = wilcoxon(df['Apertus-Eng'], df['Apertus-Trans'])
    results.append({
        'comparison': 'Apertus: Eng vs Trans',
        'test': 'Wilcoxon signed-rank',
        'statistic': stat,
        'p_value': p_val
    })

    stat, p_val = wilcoxon(df['GPT-Eng'], df['GPT-Trans'])
    results.append({
        'comparison': 'GPT: Eng vs Trans',
        'test': 'Wilcoxon signed-rank',
        'statistic': stat,
        'p_value': p_val
    })

    # Mann-Whitney U test (independent alternative to t-test)
    stat, p_val = mannwhitneyu(df['Apertus-Eng'], df['GPT-Eng'], alternative='two-sided')
    results.append({
        'comparison': 'English template: Apertus vs GPT',
        'test': 'Mann-Whitney U',
        'statistic': stat,
        'p_value': p_val
    })

    stat, p_val = mannwhitneyu(df['Apertus-Trans'], df['GPT-Trans'], alternative='two-sided')
    results.append({
        'comparison': 'Native template: Apertus vs GPT',
        'test': 'Mann-Whitney U',
        'statistic': stat,
        'p_value': p_val
    })

    return pd.DataFrame(results)


def main():
    """Run all statistical enhancements."""
    print("=" * 80)
    print("STATISTICAL ENHANCEMENTS FOR EACL PAPER")
    print("=" * 80)
    print()

    # Load data
    print("Loading language-level means...")
    df = load_language_means()
    print(f"Loaded {len(df)} languages × {len(df.columns)} conditions")
    print()

    # 1. Multiple Comparison Correction + Effect Sizes
    print("1. MULTIPLE COMPARISON CORRECTION & EFFECT SIZES")
    print("-" * 80)
    corrections = multiple_comparison_correction(df)
    corrections.to_csv('statistical_corrections.csv', index=False)
    print(corrections.to_string(index=False))
    print()
    print("✓ Saved to: statistical_corrections.csv")
    print()

    # 2. Power Analysis
    print("2. POST-HOC POWER ANALYSIS")
    print("-" * 80)
    power = power_analysis(df)
    power.to_csv('power_analysis.csv', index=False)
    print(power.to_string(index=False))
    print()
    print("✓ Saved to: power_analysis.csv")
    print()

    # 3. Normality Tests
    print("3. NORMALITY TESTS (Shapiro-Wilk)")
    print("-" * 80)
    normality = normality_tests(df)
    normality.to_csv('normality_tests.csv', index=False)
    print(normality.to_string(index=False))
    print()
    print("✓ Saved to: normality_tests.csv")
    print()

    # 4. Non-Parametric Tests (Robustness Check)
    print("4. NON-PARAMETRIC ROBUSTNESS CHECKS")
    print("-" * 80)
    nonparam = non_parametric_tests(df)
    nonparam.to_csv('nonparametric_tests.csv', index=False)
    print(nonparam.to_string(index=False))
    print()
    print("✓ Saved to: nonparametric_tests.csv")
    print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("Generated 4 CSV files:")
    print("  1. statistical_corrections.csv - Effect sizes + multiple comparison corrections")
    print("  2. power_analysis.csv - Post-hoc power analysis")
    print("  3. normality_tests.csv - Shapiro-Wilk normality tests")
    print("  4. nonparametric_tests.csv - Wilcoxon & Mann-Whitney U tests")
    print()
    print("All results use EXISTING DATA only (no new API calls).")
    print()


if __name__ == '__main__':
    main()
