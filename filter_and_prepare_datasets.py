import json
import os
from pathlib import Path

def filter_dataset(data, max_turns=6):
    """Filter dataset to only include entries with max_turns or fewer turns"""
    filtered = []
    for entry in data:
        if entry.get('num_turns', 0) <= max_turns:
            filtered.append(entry)
    return filtered

def process_complete_datasets():
    """Process datasets with 537 entries and filter them to 382 entries"""

    dataset_dir = Path('multilingual_datasets')
    filtered_dir = Path('multilingual_datasets_filtered')
    filtered_dir.mkdir(exist_ok=True)

    # Languages with 537 entries (complete but unfiltered)
    complete_537 = ['cmn.Hani', 'deu.Latn', 'fra.Latn', 'ita.Latn',
                    'jpn.Jpan', 'kor.Hang', 'rus.Cyrl', 'spa.Latn']

    processed_languages = []

    for lang in complete_537:
        input_file = dataset_dir / f'mhj_dataset_{lang}.json'
        output_file = filtered_dir / f'mhj_dataset_{lang}.json'

        if input_file.exists():
            print(f"Processing {lang}...")
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Filter to max 6 turns
            filtered_data = filter_dataset(data, max_turns=6)

            print(f"  Original: {len(data)} entries")
            print(f"  Filtered: {len(filtered_data)} entries")

            # Save filtered dataset
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)

            if len(filtered_data) == 382:
                processed_languages.append(lang)
                print(f"  Status: READY for LLM testing")
            else:
                print(f"  Status: Unexpected count ({len(filtered_data)} != 382)")

    print("\n" + "=" * 60)
    print(f"Successfully prepared {len(processed_languages)} datasets for LLM testing:")
    for lang in processed_languages:
        print(f"  - {lang}")

    return processed_languages

if __name__ == "__main__":
    ready_languages = process_complete_datasets()

    # Save list of ready datasets
    with open('ready_for_llm_testing.txt', 'w') as f:
        for lang in ready_languages:
            f.write(f"{lang}\n")

    print(f"\nReady language list saved to 'ready_for_llm_testing.txt'")