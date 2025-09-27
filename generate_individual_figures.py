#!/usr/bin/env python3
"""
Generate individual high-quality figures for conference paper
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-paper')
sns.set_context("paper", font_scale=1.5)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 11
plt.rcParams['figure.titlesize'] = 16

def load_all_results():
    """Load all evaluation results"""
    final_dir = Path('final_results')
    all_data = []
    language_data = {}

    for file_path in final_dir.glob('*_complete.json'):
        language = file_path.stem.replace('_complete', '')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for entry in data:
            entry['language'] = language
            all_data.append(entry)
        language_data[language] = data

    return all_data, language_data


def figure1_language_ranking(language_data):
    """Figure 1: Language Safety Rankings"""
    print("Generating Figure 1: Language Safety Rankings...")

    # Calculate mean scores for each language
    lang_scores = {}
    lang_refusal = {}
    for lang, data in language_data.items():
        scores = [e.get('strongreject_score', 0) for e in data]
        refusals = [e.get('evaluation', {}).get('refused', 0) for e in data]
        lang_scores[lang] = np.mean(scores)
        lang_refusal[lang] = np.mean(refusals) * 100

    # Sort by score
    sorted_langs = sorted(lang_scores.items(), key=lambda x: x[1])
    langs, scores = zip(*sorted_langs)
    refusal_rates = [lang_refusal[l] for l in langs]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Create bars
    y_pos = np.arange(len(langs))
    bars = ax.barh(y_pos, scores, color='steelblue', alpha=0.8)

    # Color bars by performance
    for i, (bar, score) in enumerate(zip(bars, scores)):
        if score < 0.08:  # Best performers
            bar.set_color('#2ecc71')
        elif score > 0.15:  # Worst performers
            bar.set_color('#e74c3c')
        else:
            bar.set_color('#3498db')

    # Add refusal rate as text
    for i, (score, refusal) in enumerate(zip(scores, refusal_rates)):
        ax.text(score + 0.002, i, f'{refusal:.1f}%',
                va='center', fontsize=10, color='gray')

    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels([l.split('.')[0].upper() for l in langs])
    ax.set_xlabel('Mean StrongReject Score (Lower is Better)', fontweight='bold')
    ax.set_title('Language Safety Rankings with Refusal Rates', fontweight='bold', pad=20)

    # Add mean line
    mean_score = np.mean(list(lang_scores.values()))
    ax.axvline(x=mean_score, color='red', linestyle='--', alpha=0.5, label=f'Mean: {mean_score:.3f}')

    # Add legend
    ax.legend(loc='lower right')

    # Grid
    ax.grid(True, axis='x', alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig('final_figures/figure1_language_ranking.png', dpi=300, bbox_inches='tight')
    plt.savefig('final_figures/figure1_language_ranking.pdf', bbox_inches='tight')
    plt.close()
    print("  Saved: figure1_language_ranking.png/pdf")


def figure2_category_distribution(all_data):
    """Figure 2: Violation Category Distribution and Performance"""
    print("Generating Figure 2: Violation Category Analysis...")

    # Analyze by category
    category_scores = defaultdict(list)
    category_refusals = defaultdict(list)

    for entry in all_data:
        category = entry.get('violation_category', 'Unknown')
        score = entry.get('strongreject_score', 0)
        refused = entry.get('evaluation', {}).get('refused', 0)
        category_scores[category].append(score)
        category_refusals[category].append(refused)

    # Calculate statistics
    cat_stats = []
    for cat in category_scores:
        cat_stats.append({
            'Category': cat,
            'Count': len(category_scores[cat]),
            'Mean_Score': np.mean(category_scores[cat]),
            'Refusal_Rate': np.mean(category_refusals[cat]) * 100
        })

    df = pd.DataFrame(cat_stats)
    df = df.sort_values('Count', ascending=False).head(10)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Left: Distribution
    colors = sns.color_palette("husl", len(df))
    bars = ax1.bar(range(len(df)), df['Count'], color=colors)
    ax1.set_xticks(range(len(df)))
    ax1.set_xticklabels([c[:12] for c in df['Category']], rotation=45, ha='right')
    ax1.set_ylabel('Number of Samples', fontweight='bold')
    ax1.set_title('(a) Category Distribution', fontweight='bold')
    ax1.grid(True, axis='y', alpha=0.3)

    # Add percentage labels
    total = df['Count'].sum()
    for bar, count in zip(bars, df['Count']):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{count/total*100:.1f}%',
                ha='center', va='bottom', fontsize=9)

    # Right: Performance
    ax2.scatter(df['Mean_Score'], df['Refusal_Rate'],
               s=df['Count']/5, alpha=0.6, c=colors)

    # Add labels for each point
    for idx, row in df.iterrows():
        ax2.annotate(row['Category'][:10],
                    (row['Mean_Score'], row['Refusal_Rate']),
                    fontsize=9, alpha=0.7)

    ax2.set_xlabel('Mean StrongReject Score', fontweight='bold')
    ax2.set_ylabel('Refusal Rate (%)', fontweight='bold')
    ax2.set_title('(b) Category Safety Performance', fontweight='bold')
    ax2.grid(True, alpha=0.3)

    plt.suptitle('Violation Category Analysis', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('final_figures/figure2_category_analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig('final_figures/figure2_category_analysis.pdf', bbox_inches='tight')
    plt.close()
    print("  Saved: figure2_category_analysis.png/pdf")


def figure3_turn_effectiveness(all_data):
    """Figure 3: Multi-turn Attack Effectiveness"""
    print("Generating Figure 3: Turn Effectiveness...")

    # Analyze by turns
    turns_data = defaultdict(list)
    turns_refused = defaultdict(list)

    for entry in all_data:
        num_turns = entry.get('num_turns', 1)
        score = entry.get('strongreject_score', 0)
        refused = entry.get('evaluation', {}).get('refused', 0)
        turns_data[num_turns].append(score)
        turns_refused[num_turns].append(refused)

    # Calculate statistics
    turn_nums = sorted(turns_data.keys())
    turn_means = [np.mean(turns_data[t]) for t in turn_nums]
    turn_stds = [np.std(turns_data[t]) for t in turn_nums]
    turn_refusal = [np.mean(turns_refused[t]) * 100 for t in turn_nums]
    turn_counts = [len(turns_data[t]) for t in turn_nums]

    # Create figure
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot score with error bars
    color1 = '#e74c3c'
    ax1.errorbar(turn_nums, turn_means, yerr=turn_stds,
                marker='o', capsize=5, linewidth=2.5,
                markersize=8, color=color1, label='StrongReject Score')
    ax1.set_xlabel('Number of Conversation Turns', fontweight='bold')
    ax1.set_ylabel('Mean StrongReject Score', color=color1, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)

    # Create second y-axis for refusal rate
    ax2 = ax1.twinx()
    color2 = '#27ae60'
    ax2.plot(turn_nums, turn_refusal, marker='s',
            linewidth=2.5, markersize=8, color=color2,
            label='Refusal Rate', linestyle='--')
    ax2.set_ylabel('Refusal Rate (%)', color=color2, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=color2)

    # Add sample counts as text
    for x, y, n in zip(turn_nums, turn_means, turn_counts):
        ax1.text(x, y - 0.02, f'n={n}', fontsize=9,
                ha='center', color='gray', alpha=0.7)

    # Title and legend
    ax1.set_title('Multi-turn Conversation Attack Effectiveness',
                 fontweight='bold', pad=20)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    plt.tight_layout()
    plt.savefig('final_figures/figure3_turn_effectiveness.png', dpi=300, bbox_inches='tight')
    plt.savefig('final_figures/figure3_turn_effectiveness.pdf', bbox_inches='tight')
    plt.close()
    print("  Saved: figure3_turn_effectiveness.png/pdf")


def figure4_heatmap(all_data, language_data):
    """Figure 4: Category × Language Heatmap"""
    print("Generating Figure 4: Category × Language Heatmap...")

    # Create interaction matrix
    category_language_scores = defaultdict(lambda: defaultdict(list))

    for entry in all_data:
        category = entry.get('violation_category', 'Unknown')
        language = entry['language']
        score = entry.get('strongreject_score', 0)
        category_language_scores[category][language].append(score)

    # Get top categories by count
    category_counts = {cat: sum(len(scores) for scores in langs.values())
                      for cat, langs in category_language_scores.items()}
    top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:8]

    # Get languages sorted by overall performance
    lang_means = {}
    for lang, data in language_data.items():
        scores = [e.get('strongreject_score', 0) for e in data]
        lang_means[lang] = np.mean(scores)
    sorted_langs = sorted(lang_means.items(), key=lambda x: x[1])[:10]

    # Create matrix
    matrix = []
    cat_labels = []
    for cat, _ in top_categories:
        row = []
        for lang, _ in sorted_langs:
            lang_cat_scores = category_language_scores[cat].get(lang, [])
            if lang_cat_scores:
                row.append(np.mean(lang_cat_scores))
            else:
                row.append(np.nan)
        matrix.append(row)
        cat_labels.append(cat[:20])

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create heatmap
    im = ax.imshow(matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=0.3)

    # Set ticks
    ax.set_xticks(range(len(sorted_langs)))
    ax.set_xticklabels([l[0].split('.')[0].upper() for l in sorted_langs], rotation=45)
    ax.set_yticks(range(len(top_categories)))
    ax.set_yticklabels(cat_labels)

    # Add text annotations
    for i in range(len(cat_labels)):
        for j in range(len(sorted_langs)):
            if not np.isnan(matrix[i][j]):
                text = ax.text(j, i, f'{matrix[i][j]:.2f}',
                             ha="center", va="center", color="white" if matrix[i][j] > 0.15 else "black",
                             fontsize=9)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Mean StrongReject Score', rotation=270, labelpad=20, fontweight='bold')

    # Title and labels
    ax.set_title('Vulnerability Heatmap: Category × Language', fontweight='bold', pad=20)
    ax.set_xlabel('Language', fontweight='bold')
    ax.set_ylabel('Violation Category', fontweight='bold')

    plt.tight_layout()
    plt.savefig('final_figures/figure4_heatmap.png', dpi=300, bbox_inches='tight')
    plt.savefig('final_figures/figure4_heatmap.pdf', bbox_inches='tight')
    plt.close()
    print("  Saved: figure4_heatmap.png/pdf")


def main():
    """Generate all individual figures"""
    print("="*60)
    print("GENERATING INDIVIDUAL CONFERENCE FIGURES")
    print("="*60)

    # Load data
    print("\nLoading data...")
    all_data, language_data = load_all_results()
    print(f"Loaded {len(all_data)} entries from {len(language_data)} languages")

    # Generate each figure
    figure1_language_ranking(language_data)
    figure2_category_distribution(all_data)
    figure3_turn_effectiveness(all_data)
    figure4_heatmap(all_data, language_data)

    print("\n" + "="*60)
    print("ALL FIGURES GENERATED SUCCESSFULLY!")
    print("Location: final_figures/")
    print("="*60)


if __name__ == "__main__":
    main()