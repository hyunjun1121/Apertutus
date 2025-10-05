"""
Language Family and Script Analysis for EACL Paper
==================================================
Analyzes template translation effects by language family and script system.
No new API calls required - uses existing evaluation data.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from scipy.stats import f_oneway
import warnings
warnings.filterwarnings('ignore')

# Language groupings
LANGUAGE_FAMILIES = {
    'Germanic': ['deu.Latn', 'nld.Latn'],
    'Romance': ['fra.Latn', 'ita.Latn', 'por.Latn', 'ron.Latn', 'spa.Latn'],
    'Slavic': ['ces.Latn', 'pol.Latn', 'rus.Cyrl'],
    'CJK': ['cmn.Hani', 'jpn.Jpan', 'kor.Hang'],
    'Other': ['arb.Arab', 'ind.Latn', 'tur.Latn']
}

SCRIPT_SYSTEMS = {
    'Latin': ['ces.Latn', 'deu.Latn', 'fra.Latn', 'ind.Latn', 'ita.Latn',
              'nld.Latn', 'pol.Latn', 'por.Latn', 'ron.Latn', 'spa.Latn', 'tur.Latn'],
    'Non-Latin': ['arb.Arab', 'cmn.Hani', 'jpn.Jpan', 'kor.Hang', 'rus.Cyrl']
}

# All languages
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


def load_language_data():
    """Load mean scores and deltas for each language."""
    data = []

    for lang in LANGUAGES:
        row = {'language': lang}

        # Load all four conditions
        for cond_name, (folder, suffix, eval_key) in CONDITIONS.items():
            file_path = Path(folder) / f'{lang}_{suffix}'
            with open(file_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)
            scores = [e[eval_key]['strongreject_score'] for e in entries]
            row[cond_name] = np.mean(scores)

        # Calculate template effects (Trans - Eng)
        row['Apertus_delta'] = row['Apertus-Trans'] - row['Apertus-Eng']
        row['GPT_delta'] = row['GPT-Trans'] - row['GPT-Eng']

        # Assign family and script
        for family, langs in LANGUAGE_FAMILIES.items():
            if lang in langs:
                row['family'] = family
                break

        for script, langs in SCRIPT_SYSTEMS.items():
            if lang in langs:
                row['script'] = script
                break

        data.append(row)

    return pd.DataFrame(data)


def family_anova(df):
    """ANOVA: Does template effect vary by language family?"""
    results = []

    # Apertus template effect by family
    groups = [df[df['family'] == fam]['Apertus_delta'].values
              for fam in LANGUAGE_FAMILIES.keys()]
    f_stat, p_val = f_oneway(*groups)

    results.append({
        'analysis': 'Apertus template effect by language family',
        'test': 'One-way ANOVA',
        'F_statistic': f_stat,
        'p_value': p_val,
        'significant': p_val < 0.05,
        'interpretation': 'Template effect differs across families' if p_val < 0.05
                         else 'No significant family difference'
    })

    # GPT template effect by family
    groups = [df[df['family'] == fam]['GPT_delta'].values
              for fam in LANGUAGE_FAMILIES.keys()]
    f_stat, p_val = f_oneway(*groups)

    results.append({
        'analysis': 'GPT template effect by language family',
        'test': 'One-way ANOVA',
        'F_statistic': f_stat,
        'p_value': p_val,
        'significant': p_val < 0.05,
        'interpretation': 'Template effect differs across families' if p_val < 0.05
                         else 'No significant family difference'
    })

    return pd.DataFrame(results)


def script_comparison(df):
    """Compare template effects: Latin vs Non-Latin scripts."""
    results = []

    # Apertus: Latin vs Non-Latin
    latin = df[df['script'] == 'Latin']['Apertus_delta']
    nonlatin = df[df['script'] == 'Non-Latin']['Apertus_delta']
    t_stat, p_val = stats.ttest_ind(latin, nonlatin)

    results.append({
        'analysis': 'Apertus template effect: Latin vs Non-Latin',
        'test': 'Independent t-test',
        't_statistic': t_stat,
        'p_value': p_val,
        'Latin_mean': latin.mean(),
        'NonLatin_mean': nonlatin.mean(),
        'difference': latin.mean() - nonlatin.mean(),
        'interpretation': 'Latin scripts benefit more' if latin.mean() > nonlatin.mean()
                         else 'Non-Latin scripts benefit more'
    })

    # GPT: Latin vs Non-Latin
    latin = df[df['script'] == 'Latin']['GPT_delta']
    nonlatin = df[df['script'] == 'Non-Latin']['GPT_delta']
    t_stat, p_val = stats.ttest_ind(latin, nonlatin)

    results.append({
        'analysis': 'GPT template effect: Latin vs Non-Latin',
        'test': 'Independent t-test',
        't_statistic': t_stat,
        'p_value': p_val,
        'Latin_mean': latin.mean(),
        'NonLatin_mean': nonlatin.mean(),
        'difference': latin.mean() - nonlatin.mean(),
        'interpretation': 'Latin scripts benefit more' if latin.mean() > nonlatin.mean()
                         else 'Non-Latin scripts benefit more'
    })

    return pd.DataFrame(results)


def family_summary(df):
    """Summarize template effects by language family."""
    summary = []

    for family in LANGUAGE_FAMILIES.keys():
        fam_df = df[df['family'] == family]

        summary.append({
            'family': family,
            'n_languages': len(fam_df),
            'Apertus_Eng_mean': fam_df['Apertus-Eng'].mean(),
            'Apertus_Trans_mean': fam_df['Apertus-Trans'].mean(),
            'Apertus_delta_mean': fam_df['Apertus_delta'].mean(),
            'Apertus_delta_std': fam_df['Apertus_delta'].std(),
            'GPT_Eng_mean': fam_df['GPT-Eng'].mean(),
            'GPT_Trans_mean': fam_df['GPT-Trans'].mean(),
            'GPT_delta_mean': fam_df['GPT_delta'].mean(),
            'GPT_delta_std': fam_df['GPT_delta'].std()
        })

    return pd.DataFrame(summary)


def main():
    """Run language family and script analysis."""
    print("=" * 80)
    print("LANGUAGE FAMILY & SCRIPT ANALYSIS FOR EACL PAPER")
    print("=" * 80)
    print()

    # Load data
    print("Loading data...")
    df = load_language_data()
    print(f"Loaded {len(df)} languages")
    print()

    # 1. Family summary statistics
    print("1. TEMPLATE EFFECT BY LANGUAGE FAMILY")
    print("-" * 80)
    family_stats = family_summary(df)
    family_stats.to_csv('family_summary.csv', index=False)
    print(family_stats.to_string(index=False))
    print()
    print("✓ Saved to: family_summary.csv")
    print()

    # 2. ANOVA: Template effect by family
    print("2. ANOVA: DOES TEMPLATE EFFECT VARY BY FAMILY?")
    print("-" * 80)
    anova_results = family_anova(df)
    anova_results.to_csv('family_anova.csv', index=False)
    print(anova_results.to_string(index=False))
    print()
    print("✓ Saved to: family_anova.csv")
    print()

    # 3. Script comparison: Latin vs Non-Latin
    print("3. SCRIPT COMPARISON: LATIN vs NON-LATIN")
    print("-" * 80)
    script_results = script_comparison(df)
    script_results.to_csv('script_comparison.csv', index=False)
    print(script_results.to_string(index=False))
    print()
    print("✓ Saved to: script_comparison.csv")
    print()

    # 4. Per-language details
    print("4. PER-LANGUAGE DETAILS")
    print("-" * 80)
    detail_cols = ['language', 'family', 'script',
                   'Apertus-Eng', 'Apertus-Trans', 'Apertus_delta',
                   'GPT-Eng', 'GPT-Trans', 'GPT_delta']
    details = df[detail_cols].sort_values('family')
    details.to_csv('language_details.csv', index=False)
    print(details.to_string(index=False))
    print()
    print("✓ Saved to: language_details.csv")
    print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("Generated 4 CSV files:")
    print("  1. family_summary.csv - Mean template effects by language family")
    print("  2. family_anova.csv - ANOVA testing family differences")
    print("  3. script_comparison.csv - Latin vs Non-Latin script comparison")
    print("  4. language_details.csv - Per-language breakdown with family/script")
    print()
    print("All results use EXISTING DATA only (no new API calls).")
    print()


if __name__ == '__main__':
    main()
