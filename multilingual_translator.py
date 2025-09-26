import json
import asyncio
from typing import List, Dict, Any
from apertus_api import ApertusAPI
import os
from datetime import datetime
import time

class MultilingualTranslator:
    def __init__(self, config_path: str = "config.json"):
        self.api = ApertusAPI(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.languages = self.config['languages']

    async def translate_turn(self, turn: Dict[str, Any], target_language: Dict[str, str]) -> Dict[str, Any]:
        """Translate a single turn to target language"""
        translated_content = await self.api.atranslate_text(
            turn['content'],
            target_language['code'],
            target_language['name']
        )

        return {
            'turn_number': turn['turn_number'],
            'content': translated_content if translated_content else turn['content'],
            'original_content': turn['content']
        }

    async def translate_entry(self, entry: Dict[str, Any], target_language: Dict[str, str]) -> Dict[str, Any]:
        """Translate only turns to target language (keep base_prompt in English)"""
        # Translate all turns in parallel
        tasks = []
        for turn in entry['turns']:
            tasks.append(self.translate_turn(turn, target_language))

        translated_turns = await asyncio.gather(*tasks)

        return {
            'source': entry['source'],
            'base_prompt': entry['base_prompt'],  # Keep original English base_prompt
            'turn_type': entry['turn_type'],
            'num_turns': entry['num_turns'],
            'turns': translated_turns,
            'language_code': target_language['code'],
            'language_name': target_language['name']
        }

    async def translate_dataset_to_language(self, dataset: List[Dict[str, Any]],
                                           target_language: Dict[str, str],
                                           batch_size: int = 10) -> List[Dict[str, Any]]:
        """Translate entire dataset to a single target language with batching"""
        translated_data = []
        total = len(dataset)

        for i in range(0, total, batch_size):
            batch = dataset[i:i+batch_size]
            print(f"Translating to {target_language['name']}: {i+1}-{min(i+batch_size, total)}/{total}")

            tasks = []
            for entry in batch:
                tasks.append(self.translate_entry(entry, target_language))

            batch_results = await asyncio.gather(*tasks)
            translated_data.extend(batch_results)

            # Small delay to respect rate limits
            await asyncio.sleep(0.5)

        return translated_data

    async def translate_to_all_languages(self, input_file: str = "mhj_dataset.json",
                                        output_dir: str = "multilingual_datasets") -> Dict[str, str]:
        """Translate dataset to all configured languages and save separately"""
        # Load original dataset
        with open(input_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        output_files = {}

        # Include original English dataset
        english_output = os.path.join(output_dir, "mhj_dataset_eng.Latn.json")
        with open(english_output, 'w', encoding='utf-8') as f:
            # Add language metadata to original
            for entry in dataset:
                entry['language_code'] = 'eng.Latn'
                entry['language_name'] = 'English'
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        output_files['eng.Latn'] = english_output
        print(f"Saved original English dataset to {english_output}")

        # Translate to each language
        for language in self.languages:
            print(f"\nStarting translation to {language['name']} ({language['code']})")
            start_time = time.time()

            translated = await self.translate_dataset_to_language(dataset, language, batch_size=10)

            # Save translated dataset
            output_file = os.path.join(output_dir, f"mhj_dataset_{language['code']}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(translated, f, indent=2, ensure_ascii=False)

            elapsed = time.time() - start_time
            print(f"Completed {language['name']} in {elapsed:.2f} seconds. Saved to {output_file}")
            output_files[language['code']] = output_file

        return output_files

def run_translation():
    """Main function to run translation"""
    translator = MultilingualTranslator()
    output_files = asyncio.run(translator.translate_to_all_languages())

    print("\n=== Translation Complete ===")
    print(f"Generated {len(output_files)} multilingual datasets:")
    for lang_code, filepath in output_files.items():
        print(f"  - {lang_code}: {filepath}")

if __name__ == "__main__":
    run_translation()