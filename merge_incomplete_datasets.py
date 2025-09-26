import json
from pathlib import Path

def merge_and_fix_datasets():
    """Merge part files for incomplete languages and create complete 382-entry datasets"""

    dataset_dir = Path('multilingual_datasets')

    # Languages that have only 82 entries but should have 382
    incomplete_languages = [
        'arb.Arab', 'ces.Latn', 'ind.Latn', 'nld.Latn',
        'pol.Latn', 'por.Latn', 'ron.Latn', 'tur.Latn'
    ]

    print("=" * 60)
    print("MERGING INCOMPLETE DATASETS")
    print("=" * 60)

    for lang in incomplete_languages:
        print(f"\nProcessing {lang}...")

        # Collect all part files
        part_files = sorted(dataset_dir.glob(f'mhj_dataset_{lang}_part*.json'))

        if not part_files:
            print(f"  WARNING: No part files found for {lang}")
            continue

        print(f"  Found {len(part_files)} part files")

        # Merge all parts
        merged_data = []
        seen_indices = set()

        for part_file in part_files:
            part_name = part_file.stem.split('_')[-1]

            with open(part_file, 'r', encoding='utf-8') as f:
                part_data = json.load(f)

            print(f"    {part_name}: {len(part_data)} entries")

            # Add unique entries
            for entry in part_data:
                idx = entry.get('entry_index', -1)
                if idx not in seen_indices:
                    seen_indices.add(idx)
                    merged_data.append(entry)

        # Sort by entry_index
        merged_data.sort(key=lambda x: x.get('entry_index', 0))

        print(f"  Total unique entries: {len(merged_data)}")

        # Save merged dataset
        output_file = dataset_dir / f'mhj_dataset_{lang}_merged.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)

        print(f"  Saved to: {output_file.name}")

        # Verify it's 382 entries (after filtering)
        filtered = [e for e in merged_data if e.get('num_turns', 0) <= 6]
        print(f"  After filtering (<=6 turns): {len(filtered)} entries")

        if len(filtered) == 382:
            print(f"  SUCCESS: Complete dataset ready!")

            # Overwrite the incomplete file
            main_file = dataset_dir / f'mhj_dataset_{lang}.json'
            with open(main_file, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
            print(f"  Updated main file: {main_file.name}")
        else:
            print(f"  WARNING: Expected 382 entries, got {len(filtered)}")

    print("\n" + "=" * 60)
    print("MERGE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    merge_and_fix_datasets()