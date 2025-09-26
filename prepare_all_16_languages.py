import json
from pathlib import Path

def merge_part_files(language_code: str, dataset_dir: Path) -> list:
    """Merge all part files for a language"""
    merged_data = []
    seen_indices = set()

    # Get all part files for this language
    part_files = sorted(dataset_dir.glob(f'mhj_dataset_{language_code}_part*.json'))

    print(f"  Found {len(part_files)} part files for {language_code}")

    for part_file in part_files:
        with open(part_file, 'r', encoding='utf-8') as f:
            part_data = json.load(f)

        # Add unique entries only
        for entry in part_data:
            idx = entry.get('entry_index', -1)
            if idx not in seen_indices:
                seen_indices.add(idx)
                merged_data.append(entry)

    # Sort by entry_index
    merged_data.sort(key=lambda x: x.get('entry_index', 0))

    return merged_data


def filter_dataset(data: list, max_turns: int = 6) -> list:
    """Filter dataset to only include entries with max_turns or fewer turns"""
    filtered = []
    for entry in data:
        if entry.get('num_turns', 0) <= max_turns:
            filtered.append(entry)
    return filtered


def prepare_all_16_languages():
    """Prepare all 16 completed languages for LLM response generation"""

    dataset_dir = Path('multilingual_datasets')
    filtered_dir = Path('multilingual_datasets_filtered')
    filtered_dir.mkdir(exist_ok=True)

    # Define the 16 completed languages
    languages_537_entries = [
        'cmn.Hani', 'deu.Latn', 'fra.Latn', 'ita.Latn',
        'jpn.Jpan', 'kor.Hang', 'rus.Cyrl', 'spa.Latn'
    ]

    languages_need_merge = [
        'arb.Arab', 'ces.Latn', 'ind.Latn', 'nld.Latn',
        'pol.Latn', 'por.Latn', 'ron.Latn', 'tur.Latn'
    ]

    all_languages = languages_537_entries + languages_need_merge
    successful_languages = []

    print("=" * 60)
    print("PREPARING ALL 16 LANGUAGES")
    print("=" * 60)

    # Process languages with 537 entries (just filter)
    print("\n1. Processing languages with 537 entries (filtering only):")
    print("-" * 40)

    for lang in languages_537_entries:
        input_file = dataset_dir / f'mhj_dataset_{lang}.json'

        if input_file.exists():
            print(f"\nProcessing {lang}...")

            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Filter to max 6 turns
            filtered_data = filter_dataset(data, max_turns=6)

            print(f"  Original: {len(data)} entries")
            print(f"  Filtered: {len(filtered_data)} entries")

            # Save filtered dataset
            output_file = filtered_dir / f'mhj_dataset_{lang}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)

            if len(filtered_data) == 382:
                print(f"  ✓ SUCCESS: Ready for LLM testing")
                successful_languages.append(lang)
            else:
                print(f"  ⚠ WARNING: Unexpected count ({len(filtered_data)} != 382)")
        else:
            print(f"\n{lang}: File not found")

    # Process languages that need merging
    print("\n2. Processing languages that need part file merging:")
    print("-" * 40)

    for lang in languages_need_merge:
        print(f"\nProcessing {lang}...")

        # First check if final file exists
        final_file = dataset_dir / f'mhj_dataset_{lang}.json'

        if final_file.exists():
            # Use the final file
            with open(final_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"  Using final file: {len(data)} entries")
        else:
            # Merge part files
            data = merge_part_files(lang, dataset_dir)
            print(f"  Merged from parts: {len(data)} entries")

        # Filter to max 6 turns
        filtered_data = filter_dataset(data, max_turns=6)
        print(f"  Filtered: {len(filtered_data)} entries")

        # Save filtered dataset
        output_file = filtered_dir / f'mhj_dataset_{lang}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)

        if len(filtered_data) == 382:
            print(f"  ✓ SUCCESS: Ready for LLM testing")
            successful_languages.append(lang)
        elif len(filtered_data) > 0:
            print(f"  ⚠ PARTIAL: {len(filtered_data)} entries available")
            successful_languages.append(lang)  # Include partial datasets
        else:
            print(f"  ✗ FAILED: No data available")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Successfully prepared: {len(successful_languages)}/{len(all_languages)} languages")
    print("\nReady for LLM response generation:")
    for lang in successful_languages:
        output_file = filtered_dir / f'mhj_dataset_{lang}.json'
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"  - {lang}: {len(data)} entries")

    # Save list of ready languages
    with open('ready_languages_16.txt', 'w') as f:
        for lang in successful_languages:
            f.write(f"{lang}\n")

    print(f"\nLanguage list saved to 'ready_languages_16.txt'")

    return successful_languages


if __name__ == "__main__":
    prepare_all_16_languages()