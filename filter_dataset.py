"""
Filter dataset to exclude entries with num_turns >= 7
"""

import json
import os
from glob import glob

def filter_single_dataset(input_path: str, max_turns: int = 6) -> tuple:
    """
    Filter a single dataset file
    Returns: (original_count, filtered_count, output_path)
    """
    print(f"Processing {input_path}...")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    original_count = len(data)

    # Filter entries with num_turns < 7
    filtered_data = [
        entry for entry in data
        if entry.get('num_turns', 0) < max_turns
    ]

    filtered_count = len(filtered_data)

    # Save filtered data (overwrite original)
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, indent=2, ensure_ascii=False)

    return original_count, filtered_count, input_path

def filter_all_datasets(directory: str = "multilingual_datasets", max_turns: int = 7):
    """
    Filter all dataset files in directory
    """
    print("="*60)
    print(f"FILTERING DATASETS (Removing entries with {max_turns}+ turns)")
    print("="*60)

    # Find all final dataset files (not part files)
    pattern = os.path.join(directory, "mhj_dataset_*.json")
    files = [f for f in glob(pattern) if '_part' not in f]

    print(f"Found {len(files)} dataset files to filter\n")

    total_original = 0
    total_filtered = 0

    # Process each file
    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        orig, filt, _ = filter_single_dataset(filepath, max_turns)

        removed = orig - filt
        percentage = (removed / orig * 100) if orig > 0 else 0

        print(f"  {filename}: {orig} → {filt} entries (removed {removed}, {percentage:.1f}%)")

        total_original += orig
        total_filtered += filt

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total entries before: {total_original}")
    print(f"Total entries after:  {total_filtered}")
    print(f"Total removed:        {total_original - total_filtered}")
    print(f"Reduction:            {(total_original - total_filtered) / total_original * 100:.1f}%")

def analyze_turn_distribution(directory: str = "multilingual_datasets"):
    """
    Analyze distribution of num_turns before filtering
    """
    print("="*60)
    print("ANALYZING TURN DISTRIBUTION")
    print("="*60)

    # Find all dataset files
    pattern = os.path.join(directory, "mhj_dataset_*.json")
    files = [f for f in glob(pattern) if '_part' not in f]

    turn_counts = {}

    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for entry in data:
            turns = entry.get('num_turns', 0)
            turn_counts[turns] = turn_counts.get(turns, 0) + 1

    print("\nTurn distribution across all datasets:")
    for turns in sorted(turn_counts.keys()):
        count = turn_counts[turns]
        print(f"  {turns} turns: {count} entries")

    # Calculate how many will be removed
    removed_count = sum(count for turns, count in turn_counts.items() if turns >= 7)
    total_count = sum(turn_counts.values())

    print(f"\nEntries with 7+ turns: {removed_count}/{total_count} ({removed_count/total_count*100:.1f}%)")
    print("These will be removed by filtering")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Filter datasets by number of turns')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze turn distribution without filtering')
    parser.add_argument('--max-turns', type=int, default=7,
                       help='Maximum number of turns to keep (default: 7, meaning keep 1-6)')
    parser.add_argument('--directory', default='multilingual_datasets',
                       help='Directory containing datasets')
    parser.add_argument('--original', default='mhj_dataset.json',
                       help='Also filter the original dataset')

    args = parser.parse_args()

    if args.analyze:
        # Just analyze, don't filter
        analyze_turn_distribution(args.directory)
    else:
        # First filter the original if it exists
        if os.path.exists(args.original):
            print(f"\nFiltering original dataset: {args.original}")
            orig, filt, _ = filter_single_dataset(args.original, args.max_turns)
            print(f"  Original: {orig} → {filt} entries\n")

        # Filter all translated datasets
        filter_all_datasets(args.directory, args.max_turns)

        print("\n✓ Filtering complete!")
        print("All datasets now contain only entries with 1-6 turns")

if __name__ == "__main__":
    main()