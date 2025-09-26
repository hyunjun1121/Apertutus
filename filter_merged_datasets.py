import json
from pathlib import Path

def filter_merged_datasets():
    """Filter the newly merged datasets to 382 entries"""

    dataset_dir = Path('multilingual_datasets')
    filtered_dir = Path('multilingual_datasets_filtered')
    filtered_dir.mkdir(exist_ok=True)

    # Languages that were just merged
    merged_languages = [
        'arb.Arab', 'ces.Latn', 'ind.Latn', 'nld.Latn',
        'pol.Latn', 'por.Latn', 'ron.Latn', 'tur.Latn'
    ]

    print("=" * 60)
    print("FILTERING MERGED DATASETS")
    print("=" * 60)

    successful_languages = []

    for lang in merged_languages:
        input_file = dataset_dir / f'mhj_dataset_{lang}.json'
        output_file = filtered_dir / f'mhj_dataset_{lang}.json'

        if input_file.exists():
            print(f"\nProcessing {lang}...")

            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"  Loaded: {len(data)} entries")

            # Since these are already merged from filtered parts, they should be 382
            # But let's verify they don't have 7+ turn entries
            filtered_data = [e for e in data if e.get('num_turns', 0) <= 6]

            print(f"  After filtering: {len(filtered_data)} entries")

            # Save filtered dataset
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)

            if len(filtered_data) == 382:
                print(f"  SUCCESS: Ready for LLM testing")
                successful_languages.append(lang)
            else:
                print(f"  WARNING: Unexpected count ({len(filtered_data)} != 382)")
        else:
            print(f"\n{lang}: File not found")

    # Combine with existing ready languages
    existing_ready_file = Path('ready_for_llm_testing.txt')
    if existing_ready_file.exists():
        with open(existing_ready_file, 'r') as f:
            existing_languages = [line.strip() for line in f if line.strip()]
    else:
        existing_languages = []

    all_ready_languages = list(set(existing_languages + successful_languages))
    all_ready_languages.sort()

    # Save complete list
    with open('ready_for_llm_testing_complete.txt', 'w') as f:
        for lang in all_ready_languages:
            f.write(f"{lang}\n")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Newly processed: {len(successful_languages)} languages")
    print(f"Total ready: {len(all_ready_languages)} languages")
    print("\nAll ready languages:")
    for lang in all_ready_languages:
        print(f"  - {lang}")

    print(f"\nComplete list saved to 'ready_for_llm_testing_complete.txt'")

    return all_ready_languages


if __name__ == "__main__":
    filter_merged_datasets()