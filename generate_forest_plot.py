"""
Forest Plot Generation for EACL Paper
=====================================
Creates publication-quality forest plots showing template effects with 95% CIs.
No new API calls required - uses existing evaluation data.
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set publication-quality style
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 13

# Languages
LANGUAGES = [
    'arb.Arab', 'ces.Latn', 'cmn.Hani', 'deu.Latn', 'fra.Latn',
    'ind.Latn', 'ita.Latn', 'jpn.Jpan', 'kor.Hang', 'nld.Latn',
    'pol.Latn', 'por.Latn', 'ron.Latn', 'rus.Cyrl', 'spa.Latn', 'tur.Latn'
]

LANGUAGE_NAMES = {
    'arb.Arab': 'Arabic',
    'ces.Latn': 'Czech',
    'cmn.Hani': 'Chinese',
    'deu.Latn': 'German',
    'fra.Latn': 'French',
    'ind.Latn': 'Indonesian',
    'ita.Latn': 'Italian',
    'jpn.Jpan': 'Japanese',
    'kor.Hang': 'Korean',
    'nld.Latn': 'Dutch',
    'pol.Latn': 'Polish',
    'por.Latn': 'Portuguese',
    'ron.Latn': 'Romanian',
    'rus.Cyrl': 'Russian',
    'spa.Latn': 'Spanish',
    'tur.Latn': 'Turkish'
}

# Condition paths
CONDITIONS = {
    'Apertus-Eng': ('final_results', 'complete.json', 'evaluation'),
    'Apertus-Trans': ('final_results/apertus_translated_eval', 'apertus_translated_eval.json', 'apertus_translated_evaluation'),
    'GPT-Eng': ('final_results/gpt_english_eval', 'gpt_english_eval.json', 'gpt_english_evaluation'),
    'GPT-Trans': ('final_results/gpt_translated_eval', 'gpt_translated_eval.json', 'gpt_translated_evaluation')
}


def load_effect_sizes():
    """Load template effects (Trans - Eng) with 95% CIs for each language."""
    data = []

    for lang in LANGUAGES:
        # Load Apertus conditions
        apertus_eng_path = Path('final_results') / f'{lang}_complete.json'
        apertus_trans_path = Path('final_results/apertus_translated_eval') / f'{lang}_apertus_translated_eval.json'

        with open(apertus_eng_path, 'r', encoding='utf-8') as f:
            apertus_eng = json.load(f)
        with open(apertus_trans_path, 'r', encoding='utf-8') as f:
            apertus_trans = json.load(f)

        apertus_eng_scores = [e['evaluation']['strongreject_score'] for e in apertus_eng]
        apertus_trans_scores = [e['apertus_translated_evaluation']['strongreject_score'] for e in apertus_trans]

        # Paired differences
        apertus_diffs = np.array(apertus_trans_scores) - np.array(apertus_eng_scores)
        apertus_mean = np.mean(apertus_diffs)
        apertus_se = stats.sem(apertus_diffs)
        apertus_ci = 1.96 * apertus_se  # 95% CI

        # Load GPT conditions
        gpt_eng_path = Path('final_results/gpt_english_eval') / f'{lang}_gpt_english_eval.json'
        gpt_trans_path = Path('final_results/gpt_translated_eval') / f'{lang}_gpt_translated_eval.json'

        with open(gpt_eng_path, 'r', encoding='utf-8') as f:
            gpt_eng = json.load(f)
        with open(gpt_trans_path, 'r', encoding='utf-8') as f:
            gpt_trans = json.load(f)

        gpt_eng_scores = [e['gpt_english_evaluation']['strongreject_score'] for e in gpt_eng]
        gpt_trans_scores = [e['gpt_translated_evaluation']['strongreject_score'] for e in gpt_trans]

        # Paired differences
        gpt_diffs = np.array(gpt_trans_scores) - np.array(gpt_eng_scores)
        gpt_mean = np.mean(gpt_diffs)
        gpt_se = stats.sem(gpt_diffs)
        gpt_ci = 1.96 * gpt_se  # 95% CI

        data.append({
            'language': LANGUAGE_NAMES[lang],
            'lang_code': lang,
            'Apertus_effect': apertus_mean,
            'Apertus_ci_lower': apertus_mean - apertus_ci,
            'Apertus_ci_upper': apertus_mean + apertus_ci,
            'GPT_effect': gpt_mean,
            'GPT_ci_lower': gpt_mean - gpt_ci,
            'GPT_ci_upper': gpt_mean + gpt_ci
        })

    return pd.DataFrame(data)


def create_forest_plot(df, judge='Apertus'):
    """Create forest plot for template effects."""
    # Sort by effect size
    df_sorted = df.sort_values(f'{judge}_effect', ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8, 10))

    # Plot points and error bars
    y_positions = np.arange(len(df_sorted))

    effect_col = f'{judge}_effect'
    ci_lower_col = f'{judge}_ci_lower'
    ci_upper_col = f'{judge}_ci_upper'

    effects = df_sorted[effect_col]
    ci_lower = df_sorted[ci_lower_col]
    ci_upper = df_sorted[ci_upper_col]

    # Color by positive/negative effect
    colors = ['forestgreen' if x > 0 else 'firebrick' for x in effects]

    # Plot error bars
    for i, (low, high) in enumerate(zip(ci_lower, ci_upper)):
        ax.plot([low, high], [i, i], color=colors[i], linewidth=1.5, alpha=0.7)

    # Plot effect points
    ax.scatter(effects, y_positions, s=80, c=colors, alpha=0.9, edgecolors='black', linewidths=0.5, zorder=3)

    # Reference line at 0
    ax.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=1)

    # Labels
    ax.set_yticks(y_positions)
    ax.set_yticklabels(df_sorted['language'])
    ax.set_xlabel('Template Translation Effect (Native - English)', fontweight='bold')
    ax.set_title(f'{judge} Judge: Template Translation Effect by Language', fontweight='bold', pad=15)

    # Grid
    ax.grid(axis='x', alpha=0.3, linestyle=':')
    ax.set_axisbelow(True)

    # Add effect size annotations
    for i, effect in enumerate(effects):
        x_offset = 0.02 if effect > 0 else -0.02
        ha = 'left' if effect > 0 else 'right'
        ax.text(effect + x_offset, i, f'{effect:.3f}',
                va='center', ha=ha, fontsize=8, color=colors[i], fontweight='bold')

    plt.tight_layout()
    return fig


def create_comparison_forest_plot(df):
    """Create side-by-side comparison of Apertus and GPT."""
    # Sort by Apertus effect
    df_sorted = df.sort_values('Apertus_effect', ascending=True).reset_index(drop=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 10), sharey=True)

    y_positions = np.arange(len(df_sorted))

    # Apertus panel
    apertus_effects = df_sorted['Apertus_effect']
    apertus_ci_lower = df_sorted['Apertus_ci_lower']
    apertus_ci_upper = df_sorted['Apertus_ci_upper']

    colors_a = ['forestgreen' if x > 0 else 'firebrick' for x in apertus_effects]

    for i, (low, high) in enumerate(zip(apertus_ci_lower, apertus_ci_upper)):
        ax1.plot([low, high], [i, i], color=colors_a[i], linewidth=1.5, alpha=0.7)

    ax1.scatter(apertus_effects, y_positions, s=80, c=colors_a, alpha=0.9,
                edgecolors='black', linewidths=0.5, zorder=3)
    ax1.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
    ax1.set_xlabel('Template Effect (Native - English)', fontweight='bold')
    ax1.set_title('Apertus-70B (Weak Judge)', fontweight='bold', pad=15)
    ax1.set_yticks(y_positions)
    ax1.set_yticklabels(df_sorted['language'])
    ax1.grid(axis='x', alpha=0.3, linestyle=':')
    ax1.set_axisbelow(True)

    # GPT panel
    gpt_effects = df_sorted['GPT_effect']
    gpt_ci_lower = df_sorted['GPT_ci_lower']
    gpt_ci_upper = df_sorted['GPT_ci_upper']

    colors_g = ['forestgreen' if x > 0 else 'firebrick' for x in gpt_effects]

    for i, (low, high) in enumerate(zip(gpt_ci_lower, gpt_ci_upper)):
        ax2.plot([low, high], [i, i], color=colors_g[i], linewidth=1.5, alpha=0.7)

    ax2.scatter(gpt_effects, y_positions, s=80, c=colors_g, alpha=0.9,
                edgecolors='black', linewidths=0.5, zorder=3)
    ax2.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
    ax2.set_xlabel('Template Effect (Native - English)', fontweight='bold')
    ax2.set_title('GPT-4.1 (Strong Judge)', fontweight='bold', pad=15)
    ax2.grid(axis='x', alpha=0.3, linestyle=':')
    ax2.set_axisbelow(True)

    plt.tight_layout()
    return fig


def main():
    """Generate forest plots."""
    print("=" * 80)
    print("FOREST PLOT GENERATION FOR EACL PAPER")
    print("=" * 80)
    print()

    # Load data
    print("Loading effect sizes with 95% confidence intervals...")
    df = load_effect_sizes()
    print(f"Loaded {len(df)} languages")
    print()

    # Save effect size table
    df.to_csv('template_effects_with_ci.csv', index=False)
    print("✓ Saved effect size table to: template_effects_with_ci.csv")
    print()

    # Generate Apertus forest plot
    print("Generating Apertus forest plot...")
    fig1 = create_forest_plot(df, judge='Apertus')
    fig1.savefig('forest_plot_apertus.pdf', dpi=300, bbox_inches='tight')
    fig1.savefig('forest_plot_apertus.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: forest_plot_apertus.pdf")
    print("✓ Saved: forest_plot_apertus.png")
    print()

    # Generate GPT forest plot
    print("Generating GPT forest plot...")
    fig2 = create_forest_plot(df, judge='GPT')
    fig2.savefig('forest_plot_gpt.pdf', dpi=300, bbox_inches='tight')
    fig2.savefig('forest_plot_gpt.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: forest_plot_gpt.pdf")
    print("✓ Saved: forest_plot_gpt.png")
    print()

    # Generate comparison plot
    print("Generating side-by-side comparison plot...")
    fig3 = create_comparison_forest_plot(df)
    fig3.savefig('forest_plot_comparison.pdf', dpi=300, bbox_inches='tight')
    fig3.savefig('forest_plot_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: forest_plot_comparison.pdf")
    print("✓ Saved: forest_plot_comparison.png")
    print()

    plt.close('all')

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("Generated files:")
    print("  1. template_effects_with_ci.csv - Effect sizes with 95% CIs")
    print("  2. forest_plot_apertus.{pdf,png} - Apertus template effects")
    print("  3. forest_plot_gpt.{pdf,png} - GPT template effects")
    print("  4. forest_plot_comparison.{pdf,png} - Side-by-side comparison")
    print()
    print("All plots show template translation effects (Native - English)")
    print("with 95% confidence intervals. Green = positive effect, Red = negative.")
    print()


if __name__ == '__main__':
    main()
