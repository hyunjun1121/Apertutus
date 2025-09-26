import json
import os
from pathlib import Path

def check_dataset_completion():
    """Check the completion status of all translated datasets"""

    dataset_dir = Path('multilingual_datasets')
    expected_count = 382  # After filtering 7+ turn entries

    results = []

    # Get all JSON files
    json_files = sorted(dataset_dir.glob('mhj_dataset_*.json'))

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = len(data)
                language_code = json_file.stem.replace('mhj_dataset_', '')

                status = "COMPLETE" if count == expected_count else "INCOMPLETE"
                results.append({
                    'language': language_code,
                    'count': count,
                    'status': status,
                    'missing': expected_count - count if count < expected_count else 0
                })

        except Exception as e:
            language_code = json_file.stem.replace('mhj_dataset_', '')
            results.append({
                'language': language_code,
                'count': 0,
                'status': 'ERROR',
                'error': str(e)
            })

    # Print summary
    print(f"Dataset Completion Status (Expected: {expected_count} entries)")
    print("=" * 60)

    complete_datasets = []
    incomplete_datasets = []

    for result in results:
        if result['status'] == 'COMPLETE':
            complete_datasets.append(result['language'])
            print(f"[COMPLETE] {result['language']}: {result['count']} entries")
        elif result['status'] == 'INCOMPLETE':
            incomplete_datasets.append(result['language'])
            print(f"[INCOMPLETE] {result['language']}: {result['count']} entries (missing {result['missing']})")
        else:
            print(f"[ERROR] {result['language']}: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 60)
    print(f"Complete datasets: {len(complete_datasets)}")
    for lang in complete_datasets:
        print(f"  - {lang}")

    if incomplete_datasets:
        print(f"\nIncomplete datasets: {len(incomplete_datasets)}")
        for lang in incomplete_datasets:
            print(f"  - {lang}")

    return complete_datasets

if __name__ == "__main__":
    complete_datasets = check_dataset_completion()

    # Save list of complete datasets
    with open('complete_datasets.txt', 'w') as f:
        for lang in complete_datasets:
            f.write(f"{lang}\n")

    print(f"\nComplete dataset list saved to 'complete_datasets.txt'")