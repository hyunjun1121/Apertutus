import json
from pathlib import Path
import numpy as np

def calculate_average_strongreject(filepath):
    """Calculate average strongreject_score for a single JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scores = []

    if isinstance(data, list):
        for entry in data:
            if 'evaluation' in entry:
                strongreject_score = entry['evaluation'].get('strongreject_score')
                if strongreject_score is not None:
                    scores.append(strongreject_score)

    if scores:
        return {
            'file': filepath.name,
            'language': filepath.name.replace('_complete.json', ''),
            'average_score': np.mean(scores),
            'std_dev': np.std(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'total_entries': len(scores)
        }
    else:
        return {
            'file': filepath.name,
            'language': filepath.name.replace('_complete.json', ''),
            'average_score': None,
            'std_dev': None,
            'min_score': None,
            'max_score': None,
            'total_entries': 0
        }

def main():
    results_dir = Path("E:/Project/Apertutus/final_results")

    # Get all language JSON files
    json_files = [
        f for f in results_dir.glob("*.json")
        if "_complete.json" in f.name and not f.name.startswith("complete_")
    ]

    print("=" * 70)
    print("AVERAGE STRONGREJECT_SCORE BY LANGUAGE")
    print("=" * 70)
    print(f"{'Language':<15} {'Avg Score':<12} {'Std Dev':<10} {'Min':<8} {'Max':<8} {'Count':<8}")
    print("-" * 70)

    all_results = []

    for json_file in sorted(json_files):
        result = calculate_average_strongreject(json_file)
        all_results.append(result)

        if result['average_score'] is not None:
            print(f"{result['language']:<15} {result['average_score']:<12.4f} {result['std_dev']:<10.4f} {result['min_score']:<8.2f} {result['max_score']:<8.2f} {result['total_entries']:<8}")
        else:
            print(f"{result['language']:<15} {'N/A':<12} {'N/A':<10} {'N/A':<8} {'N/A':<8} {result['total_entries']:<8}")

    # Calculate overall average
    all_scores = []
    for result in all_results:
        if result['average_score'] is not None:
            all_scores.append(result['average_score'])

    print("-" * 70)
    if all_scores:
        overall_avg = np.mean(all_scores)
        print(f"{'OVERALL':<15} {overall_avg:<12.4f}")

    # Sort by average score
    print("\n" + "=" * 70)
    print("LANGUAGES RANKED BY AVERAGE STRONGREJECT_SCORE (Lower = Better Rejection)")
    print("=" * 70)

    sorted_results = sorted([r for r in all_results if r['average_score'] is not None],
                           key=lambda x: x['average_score'])

    for i, result in enumerate(sorted_results, 1):
        print(f"{i:2}. {result['language']:<15} {result['average_score']:.4f}")

    # Save summary to file
    summary = {
        'individual_results': all_results,
        'overall_average': overall_avg if all_scores else None,
        'ranking': [r['language'] for r in sorted_results]
    }

    with open(results_dir / 'strongreject_scores_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nSummary saved to: strongreject_scores_summary.json")

if __name__ == "__main__":
    main()