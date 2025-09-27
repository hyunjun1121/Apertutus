#!/usr/bin/env python3
"""
Comprehensive Analysis of Multilingual Jailbreak Evaluation Results
Focus: Violation Categories, Number of Turns, Cross-Language Patterns
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("husl")

def load_all_results():
    """Load all evaluation results"""
    final_dir = Path('final_results')

    all_data = []
    language_data = {}

    for file_path in final_dir.glob('*_complete.json'):
        language = file_path.stem.replace('_complete', '')

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Add language tag to each entry
        for entry in data:
            entry['language'] = language
            all_data.append(entry)

        language_data[language] = data

    return all_data, language_data


def analyze_by_category(all_data):
    """Analyze performance by violation category"""
    print("\n" + "="*80)
    print("ANALYSIS 1: PERFORMANCE BY VIOLATION CATEGORY")
    print("="*80)

    # Group by category
    category_scores = defaultdict(list)
    category_refusals = defaultdict(list)

    for entry in all_data:
        category = entry.get('violation_category', 'Unknown')
        score = entry.get('strongreject_score', 0)
        refused = entry.get('evaluation', {}).get('refused', 0)

        category_scores[category].append(score)
        category_refusals[category].append(refused)

    # Calculate statistics
    category_stats = []
    for cat in category_scores:
        scores = category_scores[cat]
        refusals = category_refusals[cat]

        category_stats.append({
            'Category': cat,
            'Count': len(scores),
            'Mean_Score': np.mean(scores),
            'Std_Score': np.std(scores),
            'Median_Score': np.median(scores),
            'Refusal_Rate': np.mean(refusals) * 100,
            'CI_95_Lower': np.percentile(scores, 2.5),
            'CI_95_Upper': np.percentile(scores, 97.5)
        })

    # Sort by mean score (higher = more vulnerable)
    df_category = pd.DataFrame(category_stats)
    df_category = df_category.sort_values('Mean_Score', ascending=False)

    print("\nTable 1: StrongReject Performance by Violation Category")
    print("-"*80)
    print(f"{'Category':<35} {'N':<6} {'Mean±Std':<15} {'Refusal%':<10} {'95% CI'}")
    print("-"*80)

    for _, row in df_category.iterrows():
        print(f"{row['Category']:<35} {row['Count']:<6} "
              f"{row['Mean_Score']:.3f}±{row['Std_Score']:.3f}  "
              f"{row['Refusal_Rate']:<10.1f} "
              f"[{row['CI_95_Lower']:.3f}, {row['CI_95_Upper']:.3f}]")

    # Statistical test (ANOVA)
    categories_for_anova = [category_scores[cat] for cat in category_scores if len(category_scores[cat]) > 30]
    if len(categories_for_anova) > 2:
        f_stat, p_value = stats.f_oneway(*categories_for_anova)
        print(f"\nANOVA Result: F={f_stat:.3f}, p={p_value:.4f}")
        if p_value < 0.001:
            print("*** Highly significant differences between categories (p<0.001)")

    return df_category


def analyze_by_turns(all_data):
    """Analyze performance by number of conversation turns"""
    print("\n" + "="*80)
    print("ANALYSIS 2: IMPACT OF CONVERSATION TURNS")
    print("="*80)

    # Group by number of turns
    turns_scores = defaultdict(list)
    turns_refusals = defaultdict(list)

    for entry in all_data:
        num_turns = entry.get('num_turns', 1)
        score = entry.get('strongreject_score', 0)
        refused = entry.get('evaluation', {}).get('refused', 0)

        turns_scores[num_turns].append(score)
        turns_refusals[num_turns].append(refused)

    # Calculate statistics
    turns_stats = []
    for turns in sorted(turns_scores.keys()):
        scores = turns_scores[turns]
        refusals = turns_refusals[turns]

        turns_stats.append({
            'Turns': turns,
            'Count': len(scores),
            'Mean_Score': np.mean(scores),
            'Std_Score': np.std(scores),
            'Refusal_Rate': np.mean(refusals) * 100,
            'Success_Rate': (1 - np.mean(refusals)) * 100  # Attack success
        })

    df_turns = pd.DataFrame(turns_stats)

    print("\nTable 2: Multi-turn Jailbreak Effectiveness")
    print("-"*80)
    print(f"{'Turns':<8} {'N':<8} {'Mean±Std':<15} {'Refusal%':<12} {'Attack Success%'}")
    print("-"*80)

    for _, row in df_turns.iterrows():
        print(f"{row['Turns']:<8} {row['Count']:<8} "
              f"{row['Mean_Score']:.3f}±{row['Std_Score']:.3f}  "
              f"{row['Refusal_Rate']:<12.1f} "
              f"{row['Success_Rate']:.1f}")

    # Correlation analysis
    if len(df_turns) > 1:
        correlation = np.corrcoef(df_turns['Turns'], df_turns['Mean_Score'])[0, 1]
        print(f"\nCorrelation (Turns vs Score): r={correlation:.3f}")

        # Linear regression
        from scipy.stats import linregress
        slope, intercept, r_value, p_value, std_err = linregress(df_turns['Turns'], df_turns['Mean_Score'])
        print(f"Linear Regression: Score = {slope:.4f} * Turns + {intercept:.4f}")
        print(f"R² = {r_value**2:.3f}, p = {p_value:.4f}")

        if p_value < 0.05:
            print("* Significant linear relationship between turns and vulnerability")

    return df_turns


def analyze_language_families(all_data, language_data):
    """Analyze performance by language families"""
    print("\n" + "="*80)
    print("ANALYSIS 3: CROSS-LINGUISTIC PATTERNS")
    print("="*80)

    # Language family mapping
    language_families = {
        'Germanic': ['deu.Latn', 'nld.Latn'],
        'Romance': ['fra.Latn', 'ita.Latn', 'por.Latn', 'spa.Latn', 'ron.Latn'],
        'Slavic': ['rus.Cyrl', 'pol.Latn', 'ces.Latn'],
        'East Asian': ['cmn.Hani', 'jpn.Jpan', 'kor.Hang'],
        'Other': ['arb.Arab', 'tur.Latn', 'ind.Latn']
    }

    # Reverse mapping
    lang_to_family = {}
    for family, langs in language_families.items():
        for lang in langs:
            lang_to_family[lang] = family

    # Calculate family statistics
    family_scores = defaultdict(list)

    for entry in all_data:
        lang = entry['language']
        family = lang_to_family.get(lang, 'Other')
        score = entry.get('strongreject_score', 0)
        family_scores[family].append(score)

    family_stats = []
    for family in family_scores:
        scores = family_scores[family]
        family_stats.append({
            'Family': family,
            'Languages': len([l for l, f in lang_to_family.items() if f == family]),
            'Samples': len(scores),
            'Mean_Score': np.mean(scores),
            'Std_Score': np.std(scores),
            'Median_Score': np.median(scores)
        })

    df_family = pd.DataFrame(family_stats)
    df_family = df_family.sort_values('Mean_Score')

    print("\nTable 3: Performance by Language Family")
    print("-"*80)
    print(f"{'Family':<15} {'Languages':<12} {'Samples':<10} {'Mean±Std':<15} {'Median'}")
    print("-"*80)

    for _, row in df_family.iterrows():
        print(f"{row['Family']:<15} {row['Languages']:<12} {row['Samples']:<10} "
              f"{row['Mean_Score']:.3f}±{row['Std_Score']:.3f}  "
              f"{row['Median_Score']:.3f}")

    # Statistical test between families
    family_arrays = [family_scores[f] for f in family_scores if len(family_scores[f]) > 100]
    if len(family_arrays) > 2:
        f_stat, p_value = stats.f_oneway(*family_arrays)
        print(f"\nANOVA (Language Families): F={f_stat:.3f}, p={p_value:.4f}")

    return df_family, lang_to_family


def analyze_category_language_interaction(all_data):
    """Analyze interaction between category and language"""
    print("\n" + "="*80)
    print("ANALYSIS 4: CATEGORY × LANGUAGE INTERACTION")
    print("="*80)

    # Create contingency table
    category_language_scores = defaultdict(lambda: defaultdict(list))

    for entry in all_data:
        category = entry.get('violation_category', 'Unknown')
        language = entry['language']
        score = entry.get('strongreject_score', 0)

        category_language_scores[category][language].append(score)

    # Focus on top categories
    category_counts = {cat: sum(len(scores) for scores in langs.values())
                      for cat, langs in category_language_scores.items()}
    top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    print("\nTable 4: Top 5 Categories - Performance Variance Across Languages")
    print("-"*80)
    print(f"{'Category':<35} {'Best Lang (Score)':<25} {'Worst Lang (Score)':<25} {'Range'}")
    print("-"*80)

    for cat, _ in top_categories:
        lang_means = {}
        for lang, scores in category_language_scores[cat].items():
            if scores:
                lang_means[lang] = np.mean(scores)

        if lang_means:
            best_lang = min(lang_means.items(), key=lambda x: x[1])
            worst_lang = max(lang_means.items(), key=lambda x: x[1])
            range_val = worst_lang[1] - best_lang[1]

            print(f"{cat:<35} {best_lang[0]:<15} ({best_lang[1]:.3f})     "
                  f"{worst_lang[0]:<15} ({worst_lang[1]:.3f})     {range_val:.3f}")

    return category_language_scores


def analyze_turn_effectiveness(all_data):
    """Detailed analysis of multi-turn attack patterns"""
    print("\n" + "="*80)
    print("ANALYSIS 5: MULTI-TURN ATTACK PATTERNS")
    print("="*80)

    # Analyze turn effectiveness by category
    turn_category_success = defaultdict(lambda: defaultdict(list))

    for entry in all_data:
        num_turns = entry.get('num_turns', 1)
        category = entry.get('violation_category', 'Unknown')
        refused = entry.get('evaluation', {}).get('refused', 0)
        success = 1 - refused  # Attack successful if not refused

        turn_category_success[num_turns][category].append(success)

    print("\nTable 5: Attack Success Rate (%) by Turns and Category")
    print("-"*80)

    # Get top categories
    all_categories = set()
    for turn_cats in turn_category_success.values():
        all_categories.update(turn_cats.keys())

    category_totals = {cat: sum(len(turn_category_success[t].get(cat, []))
                               for t in turn_category_success)
                       for cat in all_categories}
    top_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]

    # Create table header
    header = "Turns  " + "  ".join([f"{cat[:8]:<10}" for cat, _ in top_cats[:5]])
    print(header)
    print("-"*80)

    for turns in sorted(turn_category_success.keys()):
        row = f"{turns:<7}"
        for cat, _ in top_cats[:5]:
            if cat in turn_category_success[turns]:
                success_rate = np.mean(turn_category_success[turns][cat]) * 100
                row += f"{success_rate:<10.1f}  "
            else:
                row += f"{'--':<10}  "
        print(row)

    # Find optimal turn count for each category
    print("\nOptimal Turn Count by Category:")
    for cat, _ in top_cats[:5]:
        best_turns = 1
        best_success = 0
        for turns in turn_category_success:
            if cat in turn_category_success[turns]:
                success_rate = np.mean(turn_category_success[turns][cat])
                if success_rate > best_success:
                    best_success = success_rate
                    best_turns = turns
        print(f"  {cat}: {best_turns} turns (success rate: {best_success*100:.1f}%)")

    return turn_category_success


def generate_visualizations(all_data, language_data):
    """Generate publication-quality figures"""
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS")
    print("="*80)

    # Figure 1: Language Ranking
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1.1: Language scores
    lang_scores = {}
    for lang, data in language_data.items():
        scores = [e.get('strongreject_score', 0) for e in data]
        lang_scores[lang] = np.mean(scores)

    sorted_langs = sorted(lang_scores.items(), key=lambda x: x[1])
    langs, scores = zip(*sorted_langs)

    ax = axes[0, 0]
    bars = ax.barh(range(len(langs)), scores, color='steelblue')
    ax.set_yticks(range(len(langs)))
    ax.set_yticklabels([l.split('.')[0].upper() for l in langs])
    ax.set_xlabel('Mean StrongReject Score')
    ax.set_title('(a) Language Safety Rankings')
    ax.axvline(x=np.mean(list(lang_scores.values())), color='red', linestyle='--', alpha=0.5)

    # 1.2: Category distribution
    category_counts = defaultdict(int)
    for entry in all_data:
        category = entry.get('violation_category', 'Unknown')
        category_counts[category] += 1

    sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    cats, counts = zip(*sorted_cats)

    ax = axes[0, 1]
    ax.bar(range(len(cats)), counts, color='coral')
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels([c[:10] for c in cats], rotation=45, ha='right')
    ax.set_ylabel('Count')
    ax.set_title('(b) Violation Category Distribution')

    # 1.3: Turn effectiveness
    turns_data = defaultdict(list)
    for entry in all_data:
        num_turns = entry.get('num_turns', 1)
        score = entry.get('strongreject_score', 0)
        turns_data[num_turns].append(score)

    ax = axes[1, 0]
    turn_nums = sorted(turns_data.keys())
    turn_means = [np.mean(turns_data[t]) for t in turn_nums]
    turn_stds = [np.std(turns_data[t]) for t in turn_nums]

    ax.errorbar(turn_nums, turn_means, yerr=turn_stds, marker='o', capsize=5, linewidth=2)
    ax.set_xlabel('Number of Turns')
    ax.set_ylabel('Mean StrongReject Score')
    ax.set_title('(c) Multi-turn Attack Effectiveness')
    ax.grid(True, alpha=0.3)

    # 1.4: Heatmap of top categories vs languages
    ax = axes[1, 1]

    # Create matrix for heatmap
    top_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_langs = sorted_langs[:8]  # Best performing languages

    matrix = []
    for cat, _ in top_cats:
        row = []
        for lang, _ in top_langs:
            lang_cat_scores = [e.get('strongreject_score', 0) for e in language_data[lang]
                              if e.get('violation_category') == cat]
            row.append(np.mean(lang_cat_scores) if lang_cat_scores else 0)
        matrix.append(row)

    im = ax.imshow(matrix, cmap='RdYlGn_r', aspect='auto')
    ax.set_xticks(range(len(top_langs)))
    ax.set_xticklabels([l[0].split('.')[0].upper() for l in top_langs], rotation=45)
    ax.set_yticks(range(len(top_cats)))
    ax.set_yticklabels([c[0][:15] for c in top_cats])
    ax.set_title('(d) Category × Language Vulnerability')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('StrongReject Score', rotation=270, labelpad=15)

    plt.suptitle('Multilingual Jailbreak Evaluation Results', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('analysis_figure1.png', dpi=300, bbox_inches='tight')
    plt.savefig('analysis_figure1.pdf', bbox_inches='tight')
    print("Saved: analysis_figure1.png/pdf")

    plt.close()

    return True


def generate_statistical_summary(all_data, language_data):
    """Generate comprehensive statistical summary"""
    print("\n" + "="*80)
    print("STATISTICAL SUMMARY")
    print("="*80)

    # Overall statistics
    all_scores = [e.get('strongreject_score', 0) for e in all_data]
    all_refused = [e.get('evaluation', {}).get('refused', 0) for e in all_data]

    print("\nDataset Overview:")
    print(f"  Total samples: {len(all_data)}")
    print(f"  Languages: {len(language_data)}")
    print(f"  Unique base prompts: {len(set(e.get('base_prompt', '') for e in all_data))}")
    print(f"  Violation categories: {len(set(e.get('violation_category', '') for e in all_data))}")

    print("\nOverall Performance:")
    print(f"  Mean StrongReject Score: {np.mean(all_scores):.4f} ± {np.std(all_scores):.4f}")
    print(f"  Median Score: {np.median(all_scores):.4f}")
    print(f"  Overall Refusal Rate: {np.mean(all_refused)*100:.2f}%")
    print(f"  Perfect Refusals (score=0): {sum(1 for s in all_scores if s == 0)} ({sum(1 for s in all_scores if s == 0)/len(all_scores)*100:.1f}%)")

    # Best and worst performing combinations
    print("\nExtreme Cases:")

    # Find best category-language combination
    cat_lang_scores = defaultdict(list)
    for entry in all_data:
        key = (entry.get('violation_category', 'Unknown'), entry['language'])
        cat_lang_scores[key].append(entry.get('strongreject_score', 0))

    # Filter for sufficient samples
    cat_lang_means = {k: np.mean(v) for k, v in cat_lang_scores.items() if len(v) >= 5}

    if cat_lang_means:
        best = min(cat_lang_means.items(), key=lambda x: x[1])
        worst = max(cat_lang_means.items(), key=lambda x: x[1])

        print(f"  Most Robust: {best[0][0]} in {best[0][1]} (score={best[1]:.3f})")
        print(f"  Most Vulnerable: {worst[0][0]} in {worst[0][1]} (score={worst[1]:.3f})")

    return True


def main():
    """Run comprehensive analysis"""
    print("="*80)
    print("COMPREHENSIVE MULTILINGUAL JAILBREAK ANALYSIS")
    print("Conference-Quality Statistical Analysis")
    print("="*80)

    # Load data
    print("\nLoading data from final_results/...")
    all_data, language_data = load_all_results()
    print(f"Loaded {len(all_data)} total entries from {len(language_data)} languages")

    # Run analyses
    df_category = analyze_by_category(all_data)
    df_turns = analyze_by_turns(all_data)
    df_family, lang_to_family = analyze_language_families(all_data, language_data)
    category_language_scores = analyze_category_language_interaction(all_data)
    turn_category_success = analyze_turn_effectiveness(all_data)

    # Generate visualizations
    generate_visualizations(all_data, language_data)

    # Statistical summary
    generate_statistical_summary(all_data, language_data)

    # Save results
    results = {
        'category_analysis': df_category.to_dict(),
        'turns_analysis': df_turns.to_dict(),
        'family_analysis': df_family.to_dict(),
        'summary': {
            'total_samples': len(all_data),
            'languages': len(language_data),
            'mean_score': np.mean([e.get('strongreject_score', 0) for e in all_data]),
            'refusal_rate': np.mean([e.get('evaluation', {}).get('refused', 0) for e in all_data]) * 100
        }
    }

    with open('comprehensive_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("Outputs:")
    print("  - analysis_figure1.png/pdf - Main visualization")
    print("  - comprehensive_analysis_results.json - Numerical results")
    print("="*80)


if __name__ == "__main__":
    main()