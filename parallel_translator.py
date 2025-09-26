"""
Parallel translation system utilizing 5 API keys efficiently
"""

import json
import asyncio
from typing import List, Dict, Any
from apertus_api import ApertusAPI
import os
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor
import math

class ParallelTranslator:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.languages = self.config['languages']
        self.api_keys = self.config['api_keys']

        # Create separate API instances for each key
        self.api_instances = []
        for api_key in self.api_keys:
            api = ApertusAPI(config_path)
            # Override to use specific key
            api.api_keys = [api_key]
            api.current_key_index = 0
            self.api_instances.append(api)

    async def translate_turn_with_api(self, api: ApertusAPI, turn: Dict[str, Any],
                                     target_language: Dict[str, str]) -> Dict[str, Any]:
        """Translate a single turn using specific API instance"""
        translated_content = await api.atranslate_text(
            turn['content'],
            target_language['code'],
            target_language['name']
        )

        return {
            'turn_number': turn['turn_number'],
            'content': translated_content if translated_content else turn['content'],
            'original_content': turn['content']
        }

    async def translate_entry_with_api(self, api: ApertusAPI, entry: Dict[str, Any],
                                      target_language: Dict[str, str]) -> Dict[str, Any]:
        """Translate entry using specific API instance"""
        # Translate all turns
        tasks = []
        for turn in entry['turns']:
            tasks.append(self.translate_turn_with_api(api, turn, target_language))

        translated_turns = await asyncio.gather(*tasks)

        return {
            'source': entry['source'],
            'base_prompt': entry['base_prompt'],  # Keep English
            'turn_type': entry['turn_type'],
            'num_turns': entry['num_turns'],
            'turns': translated_turns,
            'language_code': target_language['code'],
            'language_name': target_language['name']
        }

    async def translate_language_batch(self, api: ApertusAPI, dataset: List[Dict[str, Any]],
                                      target_language: Dict[str, str],
                                      start_idx: int, end_idx: int) -> List[Dict[str, Any]]:
        """Translate a batch of entries for one language using one API key"""
        results = []
        batch = dataset[start_idx:end_idx]

        for i, entry in enumerate(batch):
            try:
                translated = await self.translate_entry_with_api(api, entry, target_language)
                results.append(translated)

                if (i + 1) % 10 == 0:
                    print(f"  API {self.api_keys.index(api.api_keys[0])+1} - {target_language['name']}: {i+1}/{len(batch)} entries")
            except Exception as e:
                print(f"  Error translating entry {start_idx + i}: {e}")
                results.append(entry)  # Keep original if failed

        return results

    async def translate_single_language_parallel(self, dataset: List[Dict[str, Any]],
                                                target_language: Dict[str, str]) -> List[Dict[str, Any]]:
        """Translate one language using all 5 API keys in parallel"""
        total_entries = len(dataset)
        entries_per_api = math.ceil(total_entries / len(self.api_instances))

        print(f"\nTranslating to {target_language['name']} using {len(self.api_instances)} API keys")
        print(f"Total entries: {total_entries}, ~{entries_per_api} entries per API key")

        tasks = []
        for i, api in enumerate(self.api_instances):
            start_idx = i * entries_per_api
            end_idx = min(start_idx + entries_per_api, total_entries)

            if start_idx < total_entries:
                task = self.translate_language_batch(
                    api, dataset, target_language, start_idx, end_idx
                )
                tasks.append(task)

        # Run all API keys in parallel for this language
        results_batches = await asyncio.gather(*tasks)

        # Combine results
        all_results = []
        for batch in results_batches:
            all_results.extend(batch)

        return all_results

    async def translate_multiple_languages_parallel(self, dataset: List[Dict[str, Any]],
                                                   languages: List[Dict[str, str]] = None) -> Dict[str, str]:
        """Translate to multiple languages, processing them in groups of 5"""
        if languages is None:
            languages = self.languages

        os.makedirs("multilingual_datasets", exist_ok=True)
        output_files = {}

        # Save original English
        english_output = os.path.join("multilingual_datasets", "mhj_dataset_eng.Latn.json")
        eng_dataset = dataset.copy()
        for entry in eng_dataset:
            entry['language_code'] = 'eng.Latn'
            entry['language_name'] = 'English'
        with open(english_output, 'w', encoding='utf-8') as f:
            json.dump(eng_dataset, f, indent=2, ensure_ascii=False)
        output_files['eng.Latn'] = english_output

        # Process languages in groups of 5 (one per API key)
        for i in range(0, len(languages), 5):
            language_batch = languages[i:i+5]
            print(f"\n{'='*60}")
            print(f"Processing language batch {i//5 + 1}/{math.ceil(len(languages)/5)}")
            print(f"Languages: {[lang['name'] for lang in language_batch]}")
            print('='*60)

            # Each API key handles one language
            tasks = []
            for j, language in enumerate(language_batch):
                if j < len(self.api_instances):
                    # Assign one API to translate entire dataset for one language
                    api = self.api_instances[j]
                    task = self.translate_language_batch(
                        api, dataset, language, 0, len(dataset)
                    )
                    tasks.append((language, task))

            # Run translations in parallel
            start_time = time.time()
            results = await asyncio.gather(*[task for _, task in tasks])

            # Save results
            for (language, _), translated_data in zip(tasks, results):
                output_file = os.path.join("multilingual_datasets", f"mhj_dataset_{language['code']}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(translated_data, f, indent=2, ensure_ascii=False)
                output_files[language['code']] = output_file
                print(f"Saved {language['name']} to {output_file}")

            elapsed = time.time() - start_time
            print(f"Batch completed in {elapsed:.2f} seconds")

        return output_files

async def run_parallel_translation(languages_to_translate: List[str] = None):
    """Main function to run parallel translation"""
    # Load dataset
    with open("mhj_dataset.json", 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    translator = ParallelTranslator()

    # Filter languages if specified
    if languages_to_translate:
        translator.languages = [lang for lang in translator.languages
                               if lang['code'] in languages_to_translate]

    print(f"Starting parallel translation for {len(translator.languages)} languages")
    print(f"Using {len(translator.api_instances)} API keys in parallel")

    start_time = time.time()
    output_files = await translator.translate_multiple_languages_parallel(dataset)

    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print("TRANSLATION COMPLETE")
    print(f"Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"Average time per language: {total_time/len(translator.languages):.2f} seconds")
    print(f"Generated {len(output_files)} datasets")
    print('='*60)

if __name__ == "__main__":
    # Example: Translate only specific languages
    # asyncio.run(run_parallel_translation(["kor.Hang", "jpn.Jpan", "cmn.Hani"]))

    # Translate all languages
    asyncio.run(run_parallel_translation())