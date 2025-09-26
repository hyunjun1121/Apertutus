"""
Simple batch translator - Sequential processing with clear batching
"""

import json
import os
from typing import List, Dict, Any
from apertus_api import ApertusAPI
import time
from datetime import datetime

class SimpleBatchTranslator:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.languages = self.config['languages']
        self.api = ApertusAPI(config_path)  # Single API instance using round-robin

    def translate_turn(self, turn: Dict[str, Any], target_language: Dict[str, str]) -> Dict[str, Any]:
        """Translate a single turn synchronously"""
        try:
            translated_content = self.api.translate_text(
                text=turn['content'],
                target_language=target_language['code'],
                language_name=target_language['name']
            )

            return {
                'turn_number': turn['turn_number'],
                'content': translated_content if translated_content else turn['content'],
                'original_content': turn['content']
            }
        except Exception as e:
            print(f"  Error translating turn {turn['turn_number']}: {e}")
            return {
                'turn_number': turn['turn_number'],
                'content': turn['content'],  # Keep original on error
                'original_content': turn['content'],
                'translation_error': str(e)
            }

    def translate_entry(self, entry: Dict[str, Any], target_language: Dict[str, str]) -> Dict[str, Any]:
        """Translate all turns in an entry"""
        translated_turns = []

        for turn in entry['turns']:
            translated_turn = self.translate_turn(turn, target_language)
            translated_turns.append(translated_turn)
            time.sleep(0.1)  # Small delay to respect rate limits

        return {
            'source': entry['source'],
            'base_prompt': entry['base_prompt'],  # Keep English
            'turn_type': entry['turn_type'],
            'num_turns': entry['num_turns'],
            'turns': translated_turns,
            'language_code': target_language['code'],
            'language_name': target_language['name']
        }

    def translate_batch(self, dataset: List[Dict[str, Any]],
                       target_language: Dict[str, str],
                       batch_size: int = 10) -> List[Dict[str, Any]]:
        """Translate a dataset in batches for one language"""
        translated_data = []
        total_entries = len(dataset)

        print(f"\nTranslating to {target_language['name']} ({target_language['code']})")
        print(f"Total entries: {total_entries}, Batch size: {batch_size}")

        for i in range(0, total_entries, batch_size):
            batch_end = min(i + batch_size, total_entries)
            print(f"  Processing batch {i//batch_size + 1}: entries {i+1}-{batch_end}")

            batch_start_time = time.time()

            for j, entry in enumerate(dataset[i:batch_end]):
                translated_entry = self.translate_entry(entry, target_language)
                translated_data.append(translated_entry)

                if (j + 1) % 5 == 0:
                    print(f"    Processed {j+1}/{batch_end-i} entries in current batch")

            batch_time = time.time() - batch_start_time
            print(f"    Batch completed in {batch_time:.1f} seconds")

            # Longer pause between batches
            if batch_end < total_entries:
                print(f"    Pausing before next batch...")
                time.sleep(1)

        return translated_data

    def run_translation(self,
                       input_file: str = "mhj_dataset.json",
                       output_dir: str = "multilingual_datasets",
                       languages_to_translate: List[str] = None,
                       batch_size: int = 10):
        """Main translation function"""
        # Load dataset
        print("Loading dataset...")
        with open(input_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        print(f"Loaded {len(dataset)} entries")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Filter languages if specified
        languages = self.languages
        if languages_to_translate:
            languages = [lang for lang in self.languages
                        if lang['code'] in languages_to_translate]

        print(f"Will translate to {len(languages)} languages")

        # Save original English
        print("\nSaving original English dataset...")
        english_output = os.path.join(output_dir, "mhj_dataset_eng.Latn.json")
        eng_dataset = []
        for entry in dataset:
            eng_entry = entry.copy()
            eng_entry['language_code'] = 'eng.Latn'
            eng_entry['language_name'] = 'English'
            eng_dataset.append(eng_entry)

        with open(english_output, 'w', encoding='utf-8') as f:
            json.dump(eng_dataset, f, indent=2, ensure_ascii=False)

        print(f"✓ English dataset saved to {english_output}")

        # Process each language sequentially
        output_files = {'eng.Latn': english_output}

        for lang_idx, language in enumerate(languages):
            print(f"\n{'='*60}")
            print(f"Language {lang_idx+1}/{len(languages)}")
            print(f"{'='*60}")

            start_time = time.time()

            # Translate this language
            translated_data = self.translate_batch(dataset, language, batch_size)

            # Save translated dataset
            output_file = os.path.join(output_dir, f"mhj_dataset_{language['code']}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(translated_data, f, indent=2, ensure_ascii=False)

            elapsed = time.time() - start_time
            print(f"\n✓ {language['name']} completed in {elapsed:.1f} seconds")
            print(f"✓ Saved to {output_file}")

            output_files[language['code']] = output_file

            # Progress summary
            print(f"\nProgress: {lang_idx+1}/{len(languages)} languages completed")

            # Pause between languages
            if lang_idx < len(languages) - 1:
                print("Pausing before next language...")
                time.sleep(2)

        print(f"\n{'='*60}")
        print("TRANSLATION COMPLETE")
        print(f"{'='*60}")
        print(f"Generated {len(output_files)} datasets")

        return output_files

def main():
    """Run translation with simple batching"""
    translator = SimpleBatchTranslator()

    # You can specify languages to translate, or leave None for all
    # Example: translate only Korean and Japanese
    # languages = ["kor.Hang", "jpn.Jpan"]

    # Translate all languages
    languages = None

    # Or test with just a few languages
    # languages = ["kor.Hang", "jpn.Jpan", "fra.Latn"]

    print("="*60)
    print("SIMPLE BATCH TRANSLATION SYSTEM")
    print("="*60)
    print("This runs sequentially with clear batch processing")
    print("No async, no multiprocessing, just simple batches")
    print()

    start_time = time.time()

    output_files = translator.run_translation(
        input_file="mhj_dataset.json",
        output_dir="multilingual_datasets",
        languages_to_translate=languages,
        batch_size=10  # Process 10 entries at a time
    )

    total_time = time.time() - start_time

    print(f"\nTotal execution time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"Average per language: {total_time/len(output_files):.1f} seconds")

if __name__ == "__main__":
    main()