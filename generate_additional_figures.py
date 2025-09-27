#!/usr/bin/env python3
"""
Generate additional publication-quality figures for conference paper
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-paper')
sns.set_context("paper", font_scale=1.2)

def load_data():
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


def figure2_detailed_language_analysis(all_data, language_data):
    """Figure 2: Detailed language analysis"""
    print("Generating Figure 2: Detailed Language Analysis...")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # 2.1: Box plot of scores by language
    ax = axes[0, 0]
    lang_scores = {}
    for lang, data in language_data.items():
        scores = [e.get('strongreject_score', 0) for e in data]
        lang_scores[lang] = scores

    # Sort by median
    sorted_langs = sorted(lang_scores.keys(),
                         key=lambda x: np.median(lang_scores[x]))

    box_data = [lang_scores[lang] for lang in sorted_langs[:8]]  # Top 8
    bp = ax.boxplot(box_data, patch_artist=True)

    for patch, color in zip(bp['boxes'], sns.color_palette("husl", 8)):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xticklabels([l.split('.')[0].upper() for l in sorted_langs[:8]], rotation=45)
    ax.set_ylabel('StrongReject Score')
    ax.set_title('(a) Score Distribution by Language (Top 8)')
    ax.grid(True, alpha=0.3)

    # 2.2: Refusal rate comparison
    ax = axes[0, 1]
    refusal_rates = []
    for lang in sorted_langs:
        refused = [e.get('evaluation', {}).get('refused', 0) for e in language_data[lang]]
        refusal_rates.append(np.mean(refused) * 100)

    bars = ax.bar(range(len(sorted_langs)), refusal_rates,
                   color=plt.cm.RdYlGn(np.array(refusal_rates)/100))
    ax.set_xticks(range(len(sorted_langs)))
    ax.set_xticklabels([l.split('.')[0].upper() for l in sorted_langs], rotation=90, ha='right')
    ax.set_ylabel('Refusal Rate (%)')
    ax.set_title('(b) Refusal Rates Across Languages')
    ax.axhline(y=95, color='red', linestyle='--', alpha=0.5, label='95% threshold')
    ax.legend()

    # 2.3: Language family comparison
    ax = axes[0, 2]
    language_families = {
        'Germanic': ['deu.Latn', 'nld.Latn'],
        'Romance': ['fra.Latn', 'ita.Latn', 'por.Latn', 'spa.Latn', 'ron.Latn'],
        'Slavic': ['rus.Cyrl', 'pol.Latn', 'ces.Latn'],
        'East Asian': ['cmn.Hani', 'jpn.Jpan', 'kor.Hang'],
        'Other': ['arb.Arab', 'tur.Latn', 'ind.Latn']
    }

    family_scores = {}
    for family, langs in language_families.items():
        scores = []
        for lang in langs:
            if lang in language_data:
                scores.extend([e.get('strongreject_score', 0) for e in language_data[lang]])
        family_scores[family] = scores

    positions = range(len(family_scores))
    bp = ax.violinplot([family_scores[f] for f in family_scores.keys()],
                        positions=positions, widths=0.7, showmeans=True)

    ax.set_xticks(positions)
    ax.set_xticklabels(list(family_scores.keys()), rotation=45, ha='right')
    ax.set_ylabel('StrongReject Score')
    ax.set_title('(c) Score Distribution by Language Family')
    ax.grid(True, alpha=0.3, axis='y')

    # 2.4: Success rate over turns by language
    ax = axes[1, 0]
    for lang in sorted_langs[:5]:  # Top 5 languages
        turn_success = {}
        for entry in language_data[lang]:
            turns = entry.get('num_turns', 1)
            refused = entry.get('evaluation', {}).get('refused', 0)
            if turns not in turn_success:
                turn_success[turns] = []
            turn_success[turns].append(1 - refused)

        x = sorted(turn_success.keys())
        y = [np.mean(turn_success[t]) * 100 for t in x]
        ax.plot(x, y, marker='o', label=lang.split('.')[0].upper())

    ax.set_xlabel('Number of Turns')
    ax.set_ylabel('Attack Success Rate (%)')
    ax.set_title('(d) Multi-turn Success by Language')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)

    # 2.5: Language similarity dendrogram
    ax = axes[1, 1]
    from scipy.cluster.hierarchy import dendrogram, linkage

    # Create feature matrix (mean scores per category per language)
    languages = sorted(language_data.keys())
    categories = list(set(e.get('violation_category', '') for e in all_data if e.get('violation_category')))

    feature_matrix = []
    for lang in languages:
        lang_features = []
        for cat in categories:
            cat_scores = [e.get('strongreject_score', 0) for e in language_data[lang]
                         if e.get('violation_category') == cat]
            lang_features.append(np.mean(cat_scores) if cat_scores else 0)
        feature_matrix.append(lang_features)

    # Hierarchical clustering
    Z = linkage(feature_matrix, 'ward')
    dendrogram(Z, labels=[l.split('.')[0].upper() for l in languages], ax=ax)
    ax.set_title('(e) Language Clustering by Performance')
    ax.set_xlabel('Language')
    ax.set_ylabel('Distance')

    # 2.6: Correlation matrix
    ax = axes[1, 2]

    # Create correlation matrix between languages
    corr_matrix = np.zeros((len(sorted_langs[:8]), len(sorted_langs[:8])))
    for i, lang1 in enumerate(sorted_langs[:8]):
        for j, lang2 in enumerate(sorted_langs[:8]):
            scores1 = [e.get('strongreject_score', 0) for e in language_data[lang1]]
            scores2 = [e.get('strongreject_score', 0) for e in language_data[lang2]]
            if len(scores1) == len(scores2):
                corr_matrix[i, j] = np.corrcoef(scores1, scores2)[0, 1]

    im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
    ax.set_xticks(range(len(sorted_langs[:8])))
    ax.set_xticklabels([l.split('.')[0].upper() for l in sorted_langs[:8]], rotation=45)
    ax.set_yticks(range(len(sorted_langs[:8])))
    ax.set_yticklabels([l.split('.')[0].upper() for l in sorted_langs[:8]])
    ax.set_title('(f) Cross-Language Correlation')
    plt.colorbar(im, ax=ax)

    plt.suptitle('Figure 2: Detailed Language Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('final_figures/figure2_language_analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig('final_figures/figure2_language_analysis.pdf', bbox_inches='tight')
    plt.close()
    print("Saved: figure2_language_analysis.png/pdf")


def figure3_category_deep_dive(all_data):
    """Figure 3: Category-specific analysis"""
    print("Generating Figure 3: Violation Category Deep Dive...")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Get category data
    category_data = {}
    for entry in all_data:
        cat = entry.get('violation_category', 'Unknown')
        if cat not in category_data:
            category_data[cat] = {
                'scores': [],
                'refused': [],
                'turns': [],
                'languages': []
            }
        category_data[cat]['scores'].append(entry.get('strongreject_score', 0))
        category_data[cat]['refused'].append(entry.get('evaluation', {}).get('refused', 0))
        category_data[cat]['turns'].append(entry.get('num_turns', 1))
        category_data[cat]['languages'].append(entry['language'])

    # 3.1: Category difficulty ranking
    ax = axes[0, 0]
    cat_means = [(cat, np.mean(data['scores'])) for cat, data in category_data.items()]
    cat_means.sort(key=lambda x: x[1], reverse=True)

    cats, means = zip(*cat_means)
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(cats)))

    bars = ax.barh(range(len(cats)), means, color=colors)
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels([c[:20] for c in cats], fontsize=9)
    ax.set_xlabel('Mean StrongReject Score')
    ax.set_title('(a) Category Vulnerability Ranking')
    ax.grid(True, alpha=0.3, axis='x')

    # 3.2: Category vs Turns interaction
    ax = axes[0, 1]
    top_cats = [c for c, _ in cat_means[:5]]

    for cat in top_cats:
        turn_scores = {}
        for score, turns in zip(category_data[cat]['scores'], category_data[cat]['turns']):
            if turns not in turn_scores:
                turn_scores[turns] = []
            turn_scores[turns].append(score)

        x = sorted(turn_scores.keys())
        y = [np.mean(turn_scores[t]) for t in x]
        ax.plot(x, y, marker='o', label=cat[:15], linewidth=2)

    ax.set_xlabel('Number of Turns')
    ax.set_ylabel('Mean Score')
    ax.set_title('(b) Category Performance vs Turn Count')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 3.3: Category success rate distribution
    ax = axes[0, 2]
    success_rates = []
    labels = []

    for cat in cats[:10]:  # Top 10
        success_rate = (1 - np.mean(category_data[cat]['refused'])) * 100
        success_rates.append(success_rate)
        labels.append(cat[:15])

    ax.bar(range(len(labels)), success_rates, color=plt.cm.Reds(np.array(success_rates)/20))
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('Attack Success Rate (%)')
    ax.set_title('(c) Attack Success by Category')
    ax.axhline(y=5, color='green', linestyle='--', alpha=0.5, label='5% threshold')
    ax.legend()

    # 3.4: Category distribution pie chart
    ax = axes[1, 0]
    cat_counts = [(cat, len(data['scores'])) for cat, data in category_data.items()]
    cat_counts.sort(key=lambda x: x[1], reverse=True)

    sizes = [c[1] for c in cat_counts[:8]]  # Top 8 + Others
    labels = [c[0][:15] for c in cat_counts[:8]]
    if len(cat_counts) > 8:
        sizes.append(sum(c[1] for c in cat_counts[8:]))
        labels.append('Others')

    colors = sns.color_palette("husl", len(sizes))
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.set_title('(d) Category Distribution in Dataset')

    # 3.5: Box plot for top categories
    ax = axes[1, 1]
    top_5_cats = [c for c, _ in cat_means[:5]]
    box_data = [category_data[cat]['scores'] for cat in top_5_cats]

    bp = ax.boxplot(box_data, patch_artist=True, labels=[c[:10] for c in top_5_cats])
    for patch, color in zip(bp['boxes'], sns.color_palette("Set2", 5)):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel('StrongReject Score')
    ax.set_title('(e) Score Distribution for Top 5 Categories')
    ax.grid(True, alpha=0.3, axis='y')

    # 3.6: Category effectiveness by turn
    ax = axes[1, 2]
    turn_effectiveness = {}

    for turns in range(1, 7):
        turn_cats = {}
        for cat, data in category_data.items():
            cat_turn_scores = [s for s, t in zip(data['scores'], data['turns']) if t == turns]
            if cat_turn_scores:
                turn_cats[cat] = np.mean(cat_turn_scores)

        if turn_cats:
            best_cat = min(turn_cats.items(), key=lambda x: x[1])
            worst_cat = max(turn_cats.items(), key=lambda x: x[1])
            turn_effectiveness[turns] = {
                'best': best_cat,
                'worst': worst_cat,
                'range': worst_cat[1] - best_cat[1]
            }

    turns = list(turn_effectiveness.keys())
    ranges = [turn_effectiveness[t]['range'] for t in turns]

    ax.bar(turns, ranges, color='orange', alpha=0.7)
    ax.set_xlabel('Number of Turns')
    ax.set_ylabel('Score Range (max - min)')
    ax.set_title('(f) Category Variance by Turn Count')
    ax.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Figure 3: Violation Category Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('final_figures/figure3_category_analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig('final_figures/figure3_category_analysis.pdf', bbox_inches='tight')
    plt.close()
    print("Saved: figure3_category_analysis.png/pdf")


def figure4_turn_dynamics(all_data):
    """Figure 4: Multi-turn conversation dynamics"""
    print("Generating Figure 4: Multi-turn Conversation Dynamics...")

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 4.1: Turn distribution
    ax = axes[0, 0]
    turn_counts = {}
    for entry in all_data:
        turns = entry.get('num_turns', 1)
        turn_counts[turns] = turn_counts.get(turns, 0) + 1

    turns = sorted(turn_counts.keys())
    counts = [turn_counts[t] for t in turns]

    bars = ax.bar(turns, counts, color='skyblue', edgecolor='navy')
    ax.set_xlabel('Number of Turns')
    ax.set_ylabel('Count')
    ax.set_title('(a) Distribution of Conversation Lengths')

    # Add percentage labels
    total = sum(counts)
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{count/total*100:.1f}%', ha='center', va='bottom')

    # 4.2: Score progression by turn
    ax = axes[0, 1]
    turn_scores = {}
    turn_refusals = {}

    for entry in all_data:
        turns = entry.get('num_turns', 1)
        score = entry.get('strongreject_score', 0)
        refused = entry.get('evaluation', {}).get('refused', 0)

        if turns not in turn_scores:
            turn_scores[turns] = []
            turn_refusals[turns] = []
        turn_scores[turns].append(score)
        turn_refusals[turns].append(refused)

    x = sorted(turn_scores.keys())
    y_score = [np.mean(turn_scores[t]) for t in x]
    y_refusal = [np.mean(turn_refusals[t]) * 100 for t in x]

    ax2 = ax.twinx()

    line1 = ax.plot(x, y_score, 'b-o', label='Mean Score', linewidth=2, markersize=8)
    line2 = ax2.plot(x, y_refusal, 'r-s', label='Refusal Rate (%)', linewidth=2, markersize=8)

    ax.set_xlabel('Number of Turns')
    ax.set_ylabel('Mean Score', color='b')
    ax2.set_ylabel('Refusal Rate (%)', color='r')
    ax.set_title('(b) Performance Metrics vs Turn Count')
    ax.grid(True, alpha=0.3)

    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc='center right')

    # 4.3: Turn effectiveness heatmap
    ax = axes[1, 0]

    # Create matrix: categories x turns
    categories = list(set(e.get('violation_category', '') for e in all_data))[:8]
    turn_numbers = list(range(1, 7))

    matrix = []
    for cat in categories:
        row = []
        for turn in turn_numbers:
            scores = [e.get('strongreject_score', 0) for e in all_data
                     if e.get('violation_category') == cat and e.get('num_turns') == turn]
            row.append(np.mean(scores) if scores else 0)
        matrix.append(row)

    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(range(len(turn_numbers)))
    ax.set_xticklabels(turn_numbers)
    ax.set_yticks(range(len(categories)))
    ax.set_yticklabels([c[:15] for c in categories], fontsize=9)
    ax.set_xlabel('Number of Turns')
    ax.set_title('(c) Turn × Category Vulnerability Heatmap')

    plt.colorbar(im, ax=ax, label='Mean Score')

    # 4.4: Optimal turn analysis
    ax = axes[1, 1]

    # Find optimal turns for each category
    optimal_turns = {}
    for cat in categories:
        best_turn = 1
        best_score = float('inf')

        for turn in turn_numbers:
            scores = [e.get('strongreject_score', 0) for e in all_data
                     if e.get('violation_category') == cat and e.get('num_turns') == turn]
            if scores:
                mean_score = np.mean(scores)
                if mean_score < best_score:
                    best_score = mean_score
                    best_turn = turn

        optimal_turns[cat] = (best_turn, best_score)

    # Plot optimal turns
    cats = list(optimal_turns.keys())
    opt_turns = [optimal_turns[c][0] for c in cats]
    opt_scores = [optimal_turns[c][1] for c in cats]

    scatter = ax.scatter(opt_turns, opt_scores, c=opt_turns, cmap='viridis',
                        s=100, alpha=0.7, edgecolors='black')

    # Add labels
    for i, cat in enumerate(cats):
        ax.annotate(cat[:10], (opt_turns[i], opt_scores[i]),
                   fontsize=8, xytext=(5, 5), textcoords='offset points')

    ax.set_xlabel('Optimal Number of Turns')
    ax.set_ylabel('Best Achievable Score')
    ax.set_title('(d) Optimal Turn Strategy by Category')
    ax.grid(True, alpha=0.3)

    plt.colorbar(scatter, ax=ax, label='Turn Count')

    plt.suptitle('Figure 4: Multi-turn Conversation Dynamics', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('final_figures/figure4_turn_dynamics.png', dpi=300, bbox_inches='tight')
    plt.savefig('final_figures/figure4_turn_dynamics.pdf', bbox_inches='tight')
    plt.close()
    print("Saved: figure4_turn_dynamics.png/pdf")


def main():
    print("Generating additional conference-quality figures...")

    # Load data
    all_data, language_data = load_data()

    # Generate figures
    figure2_detailed_language_analysis(all_data, language_data)
    figure3_category_deep_dive(all_data)
    figure4_turn_dynamics(all_data)

    print("\nAll figures generated successfully!")
    print("Location: final_figures/")
    print("Files:")
    print("  - figure2_language_analysis.png/pdf")
    print("  - figure3_category_analysis.png/pdf")
    print("  - figure4_turn_dynamics.png/pdf")


if __name__ == "__main__":
    main()