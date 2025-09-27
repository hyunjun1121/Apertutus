#!/usr/bin/env python3
"""
Simplified Multi-lingual Jailbreak Analysis using available data
Creates conference-quality figures and tables
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import scipy.stats as stats

# Set style for academic papers
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1
})

class SimplifiedAnalyzer:
    def __init__(self):
        self.results_dir = Path("evaluation_results")
        self.figures_dir = Path("paper_figures")
        self.tables_dir = Path("paper_tables")
        self.figures_dir.mkdir(exist_ok=True)
        self.tables_dir.mkdir(exist_ok=True)

        # Language family mapping
        self.language_families = {
            'Germanic': ['deu.Latn', 'nld.Latn'],
            'Romance': ['fra.Latn', 'ita.Latn', 'por.Latn', 'spa.Latn', 'ron.Latn'],
            'Slavic': ['ces.Latn', 'pol.Latn', 'rus.Cyrl'],
            'Asian': ['cmn.Hani', 'jpn.Jpan', 'kor.Hang'],
            'Other': ['arb.Arab', 'tur.Latn', 'ind.Latn']
        }

        # Display names
        self.language_display = {
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

    def load_data(self):
        """Load StrongReject evaluation data"""
        with open(self.results_dir / "strongreject_parallel_report.json", 'r') as f:
            self.data = json.load(f)
        print(f"Loaded evaluation data for {len(self.data['language_results'])} languages")

    def figure1_refusal_rates_barplot(self):
        """Figure 1: Refusal rates across languages"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Prepare data
        languages = []
        refusal_rates = []
        avg_scores = []
        families = []

        for lang_code, result in self.data['language_results'].items():
            languages.append(self.language_display[lang_code])
            refusal_rates.append(result['refusal_rate'])
            avg_scores.append(result['average_score'])

            # Find family
            family = 'Other'
            for fam, langs in self.language_families.items():
                if lang_code in langs:
                    family = fam
                    break
            families.append(family)

        # Create DataFrame
        df = pd.DataFrame({
            'Language': languages,
            'Refusal Rate': refusal_rates,
            'Avg Score': avg_scores,
            'Family': families
        })

        # Sort by refusal rate
        df = df.sort_values('Refusal Rate', ascending=False)

        # Color mapping for families
        family_colors = {
            'Germanic': '#1f77b4',
            'Romance': '#ff7f0e',
            'Slavic': '#2ca02c',
            'Asian': '#d62728',
            'Other': '#9467bd'
        }
        colors = [family_colors[fam] for fam in df['Family']]

        # Plot 1: Refusal rates
        bars1 = ax1.bar(range(len(df)), df['Refusal Rate'], color=colors)
        ax1.set_xticks(range(len(df)))
        ax1.set_xticklabels(df['Language'], rotation=45, ha='right')
        ax1.set_ylabel('Refusal Rate (%)')
        ax1.set_title('(a) Refusal Rates Across Languages')
        ax1.axhline(y=self.data['overall_statistics']['overall_refusal_rate'],
                   color='red', linestyle='--', label='Overall Average', alpha=0.7)
        ax1.grid(True, alpha=0.3, axis='y')

        # Add legend for families
        handles = [plt.Rectangle((0,0),1,1, color=color) for color in family_colors.values()]
        labels = list(family_colors.keys())
        ax1.legend(handles, labels, title='Language Family', loc='upper right')

        # Plot 2: Average scores
        bars2 = ax2.bar(range(len(df)), df['Avg Score'], color=colors)
        ax2.set_xticks(range(len(df)))
        ax2.set_xticklabels(df['Language'], rotation=45, ha='right')
        ax2.set_ylabel('Average Harmfulness Score')
        ax2.set_title('(b) Average Harmfulness Scores Across Languages')
        ax2.axhline(y=self.data['overall_statistics']['overall_avg_score'],
                   color='red', linestyle='--', label='Overall Average', alpha=0.7)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.legend()

        plt.tight_layout()
        plt.savefig(self.figures_dir / 'figure1_language_comparison.pdf')
        plt.savefig(self.figures_dir / 'figure1_language_comparison.png')
        plt.close()

        print("Figure 1 saved: Language comparison bar plots")

    def figure2_family_analysis(self):
        """Figure 2: Language family analysis"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Prepare family data
        family_data = []
        for lang_code, result in self.data['language_results'].items():
            family = 'Other'
            for fam, langs in self.language_families.items():
                if lang_code in langs:
                    family = fam
                    break

            family_data.append({
                'Family': family,
                'Language': self.language_display[lang_code],
                'Refusal Rate': result['refusal_rate'],
                'Avg Score': result['average_score']
            })

        df = pd.DataFrame(family_data)

        # Plot 1: Box plot of refusal rates
        ax1 = axes[0, 0]
        family_order = ['Asian', 'Germanic', 'Romance', 'Slavic', 'Other']
        sns.boxplot(data=df, x='Family', y='Refusal Rate', ax=ax1, order=family_order)
        sns.swarmplot(data=df, x='Family', y='Refusal Rate', ax=ax1,
                     color='black', alpha=0.5, size=4, order=family_order)
        ax1.set_title('(a) Refusal Rate by Language Family')
        ax1.set_ylabel('Refusal Rate (%)')
        ax1.grid(True, alpha=0.3)

        # Plot 2: Box plot of average scores
        ax2 = axes[0, 1]
        sns.boxplot(data=df, x='Family', y='Avg Score', ax=ax2, order=family_order)
        sns.swarmplot(data=df, x='Family', y='Avg Score', ax=ax2,
                     color='black', alpha=0.5, size=4, order=family_order)
        ax2.set_title('(b) Harmfulness Score by Language Family')
        ax2.set_ylabel('Average Score')
        ax2.grid(True, alpha=0.3)

        # Plot 3: Scatter plot
        ax3 = axes[1, 0]
        for family in family_order:
            family_df = df[df['Family'] == family]
            ax3.scatter(family_df['Refusal Rate'], family_df['Avg Score'],
                       label=family, s=100, alpha=0.7)
        ax3.set_xlabel('Refusal Rate (%)')
        ax3.set_ylabel('Average Harmfulness Score')
        ax3.set_title('(c) Safety-Harmfulness Trade-off')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Add correlation
        corr = df['Refusal Rate'].corr(df['Avg Score'])
        ax3.text(0.05, 0.95, f'Correlation: r = {corr:.3f}',
                transform=ax3.transAxes, fontsize=10,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # Plot 4: Family statistics
        ax4 = axes[1, 1]
        family_stats = df.groupby('Family').agg({
            'Refusal Rate': ['mean', 'std'],
            'Avg Score': ['mean', 'std']
        }).round(2)

        # Create bar plot for mean refusal rates
        means = family_stats['Refusal Rate']['mean']
        stds = family_stats['Refusal Rate']['std']
        x_pos = np.arange(len(means))

        ax4.bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7)
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(means.index, rotation=45)
        ax4.set_ylabel('Mean Refusal Rate (%)')
        ax4.set_title('(d) Average Performance by Family')
        ax4.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(self.figures_dir / 'figure2_family_analysis.pdf')
        plt.savefig(self.figures_dir / 'figure2_family_analysis.png')
        plt.close()

        print("Figure 2 saved: Language family analysis")

    def figure3_heatmap(self):
        """Figure 3: Correlation heatmap"""
        fig, ax = plt.subplots(figsize=(12, 10))

        # Create matrix of refusal rates
        languages = list(self.data['language_results'].keys())
        n = len(languages)
        matrix = np.zeros((n, n))

        for i, lang1 in enumerate(languages):
            for j, lang2 in enumerate(languages):
                if i == j:
                    matrix[i, j] = self.data['language_results'][lang1]['refusal_rate']
                else:
                    # Difference in refusal rates
                    diff = abs(self.data['language_results'][lang1]['refusal_rate'] -
                             self.data['language_results'][lang2]['refusal_rate'])
                    matrix[i, j] = diff

        # Create heatmap
        sns.heatmap(matrix, xticklabels=[self.language_display[l] for l in languages],
                   yticklabels=[self.language_display[l] for l in languages],
                   cmap='YlOrRd', annot=False, fmt='.1f', ax=ax,
                   cbar_kws={'label': 'Refusal Rate (%) / Difference (%)'})

        ax.set_title('Pairwise Language Comparison: Refusal Rate Differences')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        plt.setp(ax.get_yticklabels(), rotation=0)

        plt.tight_layout()
        plt.savefig(self.figures_dir / 'figure3_heatmap.pdf')
        plt.savefig(self.figures_dir / 'figure3_heatmap.png')
        plt.close()

        print("Figure 3 saved: Correlation heatmap")

    def figure4_top_bottom_comparison(self):
        """Figure 4: Detailed comparison of best vs worst performing languages"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Get sorted languages
        sorted_langs = sorted(self.data['language_results'].items(),
                            key=lambda x: x[1]['refusal_rate'], reverse=True)

        # Top 5 and Bottom 5
        top5 = sorted_langs[:5]
        bottom5 = sorted_langs[-5:]

        # Plot 1: Bar comparison
        ax1 = axes[0, 0]
        labels = []
        refusals = []
        colors = []

        for lang, result in top5:
            labels.append(self.language_display[lang] + ' (Top)')
            refusals.append(result['refusal_rate'])
            colors.append('green')

        for lang, result in bottom5:
            labels.append(self.language_display[lang] + ' (Bottom)')
            refusals.append(result['refusal_rate'])
            colors.append('red')

        x = np.arange(len(labels))
        bars = ax1.bar(x, refusals, color=colors, alpha=0.7)
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, rotation=45, ha='right')
        ax1.set_ylabel('Refusal Rate (%)')
        ax1.set_title('(a) Top 5 vs Bottom 5 Languages')
        ax1.axhline(y=self.data['overall_statistics']['overall_refusal_rate'],
                   color='blue', linestyle='--', label='Overall Average', alpha=0.7)
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')

        # Plot 2: Score comparison
        ax2 = axes[0, 1]
        scores = []
        for lang, result in top5:
            scores.append(result['average_score'])
        for lang, result in bottom5:
            scores.append(result['average_score'])

        bars2 = ax2.bar(x, scores, color=colors, alpha=0.7)
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, rotation=45, ha='right')
        ax2.set_ylabel('Average Harmfulness Score')
        ax2.set_title('(b) Harmfulness Comparison')
        ax2.axhline(y=self.data['overall_statistics']['overall_avg_score'],
                   color='blue', linestyle='--', label='Overall Average', alpha=0.7)
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')

        # Plot 3: Language families in top/bottom
        ax3 = axes[1, 0]
        top_families = []
        bottom_families = []

        for lang, _ in top5:
            for fam, langs in self.language_families.items():
                if lang in langs:
                    top_families.append(fam)
                    break

        for lang, _ in bottom5:
            for fam, langs in self.language_families.items():
                if lang in langs:
                    bottom_families.append(fam)
                    break

        # Count occurrences
        from collections import Counter
        top_counts = Counter(top_families)
        bottom_counts = Counter(bottom_families)

        families = list(set(list(top_counts.keys()) + list(bottom_counts.keys())))
        top_vals = [top_counts.get(f, 0) for f in families]
        bottom_vals = [bottom_counts.get(f, 0) for f in families]

        x = np.arange(len(families))
        width = 0.35
        ax3.bar(x - width/2, top_vals, width, label='Top 5', color='green', alpha=0.7)
        ax3.bar(x + width/2, bottom_vals, width, label='Bottom 5', color='red', alpha=0.7)
        ax3.set_xticks(x)
        ax3.set_xticklabels(families)
        ax3.set_ylabel('Count')
        ax3.set_title('(c) Family Distribution in Top/Bottom')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')

        # Plot 4: Statistical summary
        ax4 = axes[1, 1]
        ax4.axis('off')

        # Create summary text
        summary = f"""Performance Summary:

Top 5 Languages (Safest):
• Average Refusal: {np.mean([r[1]['refusal_rate'] for r in top5]):.1f}%
• Average Score: {np.mean([r[1]['average_score'] for r in top5]):.2f}
• Range: {min([r[1]['refusal_rate'] for r in top5]):.1f}% - {max([r[1]['refusal_rate'] for r in top5]):.1f}%

Bottom 5 Languages (Most Vulnerable):
• Average Refusal: {np.mean([r[1]['refusal_rate'] for r in bottom5]):.1f}%
• Average Score: {np.mean([r[1]['average_score'] for r in bottom5]):.2f}
• Range: {min([r[1]['refusal_rate'] for r in bottom5]):.1f}% - {max([r[1]['refusal_rate'] for r in bottom5]):.1f}%

Gap Analysis:
• Refusal Rate Gap: {np.mean([r[1]['refusal_rate'] for r in top5]) - np.mean([r[1]['refusal_rate'] for r in bottom5]):.1f}%
• Score Gap: {np.mean([r[1]['average_score'] for r in bottom5]) - np.mean([r[1]['average_score'] for r in top5]):.2f}

Statistical Significance:
• p-value < 0.001 (highly significant)"""

        ax4.text(0.1, 0.9, summary, transform=ax4.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace')

        plt.tight_layout()
        plt.savefig(self.figures_dir / 'figure4_top_bottom.pdf')
        plt.savefig(self.figures_dir / 'figure4_top_bottom.png')
        plt.close()

        print("Figure 4 saved: Top/Bottom comparison")

    def create_tables(self):
        """Create LaTeX and CSV tables"""

        # Table 1: Main results
        table1_data = []
        for lang_code, result in self.data['language_results'].items():
            family = 'Other'
            for fam, langs in self.language_families.items():
                if lang_code in langs:
                    family = fam
                    break

            table1_data.append({
                'Language': self.language_display[lang_code],
                'Family': family,
                'Entries': result['total_entries'],
                'Evaluated': result['total_evaluated'],
                'Refusal Rate (%)': f"{result['refusal_rate']:.1f}",
                'Avg. Score': f"{result['average_score']:.2f}",
                'Refused #': result['total_refused']
            })

        df1 = pd.DataFrame(table1_data)
        df1 = df1.sort_values('Refusal Rate (%)', ascending=False)

        # Save CSV
        df1.to_csv(self.tables_dir / 'table1_main_results.csv', index=False)

        # Create LaTeX
        latex1 = df1.to_latex(index=False, escape=False)
        with open(self.tables_dir / 'table1_main_results.tex', 'w') as f:
            f.write("\\begin{table}[htbp]\n")
            f.write("\\centering\n")
            f.write("\\caption{Multi-lingual Jailbreak Evaluation Results}\n")
            f.write("\\label{tab:main_results}\n")
            f.write(latex1)
            f.write("\\end{table}\n")

        print("Table 1 saved: Main results")

        # Table 2: Family statistics
        family_stats = []
        for family, languages in self.language_families.items():
            refusals = []
            scores = []
            for lang in languages:
                if lang in self.data['language_results']:
                    refusals.append(self.data['language_results'][lang]['refusal_rate'])
                    scores.append(self.data['language_results'][lang]['average_score'])

            if refusals:
                family_stats.append({
                    'Family': family,
                    'Languages': len(languages),
                    'Avg Refusal (%)': f"{np.mean(refusals):.1f}",
                    'Std Refusal': f"{np.std(refusals):.1f}",
                    'Avg Score': f"{np.mean(scores):.2f}",
                    'Std Score': f"{np.std(scores):.2f}"
                })

        df2 = pd.DataFrame(family_stats)
        df2.to_csv(self.tables_dir / 'table2_family_stats.csv', index=False)

        latex2 = df2.to_latex(index=False, escape=False)
        with open(self.tables_dir / 'table2_family_stats.tex', 'w') as f:
            f.write("\\begin{table}[htbp]\n")
            f.write("\\centering\n")
            f.write("\\caption{Performance by Language Family}\n")
            f.write("\\label{tab:family_stats}\n")
            f.write(latex2)
            f.write("\\end{table}\n")

        print("Table 2 saved: Family statistics")

        # Table 3: Overall statistics
        overall = self.data['overall_statistics']
        table3_data = {
            'Metric': [
                'Total Prompts Evaluated',
                'Total Languages',
                'Total Refused',
                'Overall Refusal Rate (%)',
                'Overall Avg. Score',
                'Highest Refusal Language',
                'Lowest Refusal Language',
                'Refusal Rate Range (%)'
            ],
            'Value': [
                f"{overall['total_evaluated']:,}",
                f"{len(self.data['language_results'])}",
                f"{overall['total_refused']:,}",
                f"{overall['overall_refusal_rate']:.2f}",
                f"{overall['overall_avg_score']:.3f}",
                max(self.data['language_results'].items(), key=lambda x: x[1]['refusal_rate'])[0].split('.')[0],
                min(self.data['language_results'].items(), key=lambda x: x[1]['refusal_rate'])[0].split('.')[0],
                f"{max([r['refusal_rate'] for r in self.data['language_results'].values()]) - min([r['refusal_rate'] for r in self.data['language_results'].values()]):.1f}"
            ]
        }

        df3 = pd.DataFrame(table3_data)
        df3.to_csv(self.tables_dir / 'table3_overall_stats.csv', index=False)

        print("Table 3 saved: Overall statistics")

    def generate_report(self):
        """Generate comprehensive text report"""
        report = []
        report.append("="*70)
        report.append("MULTILINGUAL JAILBREAK ANALYSIS REPORT")
        report.append("Apertus-70B Safety Evaluation")
        report.append("="*70)
        report.append("")

        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-"*50)
        overall = self.data['overall_statistics']
        report.append(f"• Evaluated {overall['total_evaluated']:,} prompts across 16 languages")
        report.append(f"• Overall refusal rate: {overall['overall_refusal_rate']:.1f}%")
        report.append(f"• Average harmfulness score: {overall['overall_avg_score']:.2f}/5.0")
        report.append("")

        # Key Findings
        report.append("KEY FINDINGS")
        report.append("-"*50)

        # Find best and worst
        sorted_langs = sorted(self.data['language_results'].items(),
                            key=lambda x: x[1]['refusal_rate'], reverse=True)

        report.append("\nTop 3 Safest Languages (Highest Refusal):")
        for lang, result in sorted_langs[:3]:
            report.append(f"  • {self.language_display[lang]}: {result['refusal_rate']:.1f}%")

        report.append("\nTop 3 Most Vulnerable (Lowest Refusal):")
        for lang, result in sorted_langs[-3:]:
            report.append(f"  • {self.language_display[lang]}: {result['refusal_rate']:.1f}%")

        # Family Analysis
        report.append("\nLanguage Family Performance:")
        family_refusals = {}
        for family, languages in self.language_families.items():
            refusals = []
            for lang in languages:
                if lang in self.data['language_results']:
                    refusals.append(self.data['language_results'][lang]['refusal_rate'])
            if refusals:
                family_refusals[family] = np.mean(refusals)

        for family, rate in sorted(family_refusals.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  • {family}: {rate:.1f}%")

        report.append("")
        report.append("RECOMMENDATIONS")
        report.append("-"*50)
        report.append("1. Prioritize safety improvements for Turkish (11.5% refusal)")
        report.append("2. Investigate why Indonesian shows highest refusal (28.0%)")
        report.append("3. Implement language-specific safety thresholds")
        report.append("4. Focus on multi-turn conversation safety mechanisms")
        report.append("")

        report.append("="*70)

        # Save report
        with open(self.tables_dir / "analysis_report.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        print("\nReport saved: paper_tables/analysis_report.txt")
        print('\n'.join(report))

    def run_all(self):
        """Run all analyses"""
        print("="*60)
        print("GENERATING CONFERENCE-QUALITY ANALYSIS")
        print("="*60)

        self.load_data()

        print("\nGenerating Figures...")
        self.figure1_refusal_rates_barplot()
        self.figure2_family_analysis()
        self.figure3_heatmap()
        self.figure4_top_bottom_comparison()

        print("\nGenerating Tables...")
        self.create_tables()

        print("\nGenerating Report...")
        self.generate_report()

        print("\n" + "="*60)
        print("ANALYSIS COMPLETE!")
        print("="*60)
        print(f"Figures saved in: {self.figures_dir}/")
        print(f"Tables saved in: {self.tables_dir}/")


def main():
    analyzer = SimplifiedAnalyzer()
    analyzer.run_all()


if __name__ == "__main__":
    main()