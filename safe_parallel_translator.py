"""
Safe parallel translation system with duplicate prevention
"""

import json
import asyncio
from typing import List, Dict, Any, Set, Tuple
from apertus_api import ApertusAPI
import os
from datetime import datetime
import time
import hashlib
from dataclasses import dataclass, asdict
import threading

@dataclass
class TranslationTask:
    """Unique task identifier"""
    entry_index: int
    language_code: str
    turn_number: int

    def get_id(self) -> str:
        """Generate unique ID for this task"""
        return f"{self.entry_index}_{self.language_code}_{self.turn_number}"

class TranslationTracker:
    """Thread-safe tracker to prevent duplicate processing"""
    def __init__(self):
        self.lock = threading.Lock()
        self.processed: Set[str] = set()
        self.in_progress: Set[str] = set()
        self.failed: Dict[str, str] = {}
        self.results: Dict[str, Any] = {}

    def can_process(self, task_id: str) -> bool:
        """Check if task can be processed"""
        with self.lock:
            if task_id in self.processed or task_id in self.in_progress:
                return False
            self.in_progress.add(task_id)
            return True

    def mark_completed(self, task_id: str, result: Any = None):
        """Mark task as completed"""
        with self.lock:
            self.in_progress.discard(task_id)
            self.processed.add(task_id)
            if result is not None:
                self.results[task_id] = result

    def mark_failed(self, task_id: str, error: str):
        """Mark task as failed"""
        with self.lock:
            self.in_progress.discard(task_id)
            self.failed[task_id] = error

    def get_status(self) -> Dict[str, int]:
        """Get current status"""
        with self.lock:
            return {
                'processed': len(self.processed),
                'in_progress': len(self.in_progress),
                'failed': len(self.failed)
            }

class SafeParallelTranslator:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.languages = self.config['languages']
        self.api_keys = self.config['api_keys']
        self.tracker = TranslationTracker()

        # Create API instances with specific keys
        self.api_instances = []
        for i, api_key in enumerate(self.api_keys):
            api = ApertusAPI(config_path)
            api.api_keys = [api_key]
            api.current_key_index = 0
            api.instance_id = i  # Add unique ID to each instance
            self.api_instances.append(api)

    def generate_task_id(self, entry_idx: int, lang_code: str, turn_num: int = -1) -> str:
        """Generate unique task ID"""
        if turn_num >= 0:
            return f"entry{entry_idx}_lang{lang_code}_turn{turn_num}"
        return f"entry{entry_idx}_lang{lang_code}"

    async def translate_turn_safe(self, api: ApertusAPI, turn: Dict[str, Any],
                                 target_language: Dict[str, str],
                                 entry_idx: int) -> Dict[str, Any]:
        """Safely translate a single turn"""
        task_id = self.generate_task_id(entry_idx, target_language['code'], turn['turn_number'])

        # Check if already processed
        if not self.tracker.can_process(task_id):
            # Return cached result if exists
            if task_id in self.tracker.results:
                return self.tracker.results[task_id]
            # Wait and retry if in progress
            await asyncio.sleep(0.1)
            return await self.translate_turn_safe(api, turn, target_language, entry_idx)

        try:
            translated_content = await api.atranslate_text(
                turn['content'],
                target_language['code'],
                target_language['name']
            )

            result = {
                'turn_number': turn['turn_number'],
                'content': translated_content if translated_content else turn['content'],
                'original_content': turn['content']
            }

            self.tracker.mark_completed(task_id, result)
            return result

        except Exception as e:
            self.tracker.mark_failed(task_id, str(e))
            raise

    async def translate_entry_safe(self, api: ApertusAPI, entry: Dict[str, Any],
                                 target_language: Dict[str, str],
                                 entry_idx: int) -> Dict[str, Any]:
        """Safely translate an entry"""
        entry_task_id = self.generate_task_id(entry_idx, target_language['code'])

        # Check if entire entry was already processed
        if entry_task_id in self.tracker.processed:
            if entry_task_id in self.tracker.results:
                return self.tracker.results[entry_task_id]

        # Translate turns
        translated_turns = []
        for turn in entry['turns']:
            translated_turn = await self.translate_turn_safe(
                api, turn, target_language, entry_idx
            )
            translated_turns.append(translated_turn)

        result = {
            'source': entry['source'],
            'base_prompt': entry['base_prompt'],
            'turn_type': entry['turn_type'],
            'num_turns': entry['num_turns'],
            'turns': translated_turns,
            'language_code': target_language['code'],
            'language_name': target_language['name'],
            'entry_index': entry_idx  # Add for verification
        }

        self.tracker.mark_completed(entry_task_id, result)
        return result

    async def process_language_segment(self, api_idx: int, dataset: List[Dict[str, Any]],
                                      language: Dict[str, str],
                                      start_idx: int, end_idx: int) -> Tuple[str, List[Dict[str, Any]]]:
        """Process a specific segment for one language"""
        api = self.api_instances[api_idx]
        results = []

        print(f"API {api_idx+1} processing {language['name']}: entries {start_idx}-{end_idx}")

        for i in range(start_idx, end_idx):
            if i >= len(dataset):
                break

            try:
                translated = await self.translate_entry_safe(
                    api, dataset[i], language, i
                )
                results.append(translated)

                if (i - start_idx + 1) % 10 == 0:
                    status = self.tracker.get_status()
                    print(f"  API {api_idx+1} - {language['name']}: {i-start_idx+1}/{end_idx-start_idx} "
                          f"(Total: {status['processed']} done, {status['in_progress']} in progress)")

            except Exception as e:
                print(f"  Error at entry {i}: {e}")
                # Add original with error flag
                error_entry = dataset[i].copy()
                error_entry['translation_error'] = str(e)
                error_entry['language_code'] = language['code']
                error_entry['language_name'] = language['name']
                results.append(error_entry)

        return (language['code'], results)

    async def translate_all_parallel(self, dataset: List[Dict[str, Any]],
                                    languages: List[Dict[str, str]] = None) -> Dict[str, str]:
        """Translate dataset to all languages with safety checks"""
        if languages is None:
            languages = self.languages

        os.makedirs("multilingual_datasets", exist_ok=True)
        output_files = {}

        # Save original English
        english_output = os.path.join("multilingual_datasets", "mhj_dataset_eng.Latn.json")
        eng_dataset = []
        for i, entry in enumerate(dataset):
            eng_entry = entry.copy()
            eng_entry['language_code'] = 'eng.Latn'
            eng_entry['language_name'] = 'English'
            eng_entry['entry_index'] = i
            eng_dataset.append(eng_entry)

        with open(english_output, 'w', encoding='utf-8') as f:
            json.dump(eng_dataset, f, indent=2, ensure_ascii=False)
        output_files['eng.Latn'] = english_output

        # Create task assignments
        total_entries = len(dataset)
        tasks = []

        # Strategy: Assign languages to APIs in round-robin
        for lang_idx, language in enumerate(languages):
            api_idx = lang_idx % len(self.api_instances)

            # Each API processes entire dataset for assigned languages
            task = self.process_language_segment(
                api_idx, dataset, language, 0, total_entries
            )
            tasks.append(task)

            # Process in batches of 5 to avoid overwhelming
            if (lang_idx + 1) % len(self.api_instances) == 0 or lang_idx == len(languages) - 1:
                print(f"\n{'='*60}")
                print(f"Processing batch {(lang_idx // len(self.api_instances)) + 1}")
                print(f"Languages in this batch: {[languages[i]['name'] for i in range(lang_idx - len(tasks) + 1, lang_idx + 1)]}")
                print('='*60)

                start_time = time.time()
                results = await asyncio.gather(*tasks)

                # Save results with verification
                for lang_code, translated_data in results:
                    # Verify no duplicates
                    entry_indices = [entry.get('entry_index', -1) for entry in translated_data]
                    if len(entry_indices) != len(set(entry_indices)):
                        print(f"WARNING: Duplicate entries detected for {lang_code}!")

                    output_file = os.path.join("multilingual_datasets", f"mhj_dataset_{lang_code}.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(translated_data, f, indent=2, ensure_ascii=False)
                    output_files[lang_code] = output_file
                    print(f"✓ Saved {lang_code}: {len(translated_data)} entries")

                elapsed = time.time() - start_time
                print(f"Batch completed in {elapsed:.2f} seconds")

                # Clear tasks for next batch
                tasks = []

        # Final status
        final_status = self.tracker.get_status()
        print(f"\n{'='*60}")
        print("FINAL STATUS")
        print(f"Total processed: {final_status['processed']}")
        print(f"Failed: {final_status['failed']}")
        print('='*60)

        return output_files

    def verify_output(self, output_dir: str = "multilingual_datasets"):
        """Verify all outputs for duplicates and completeness"""
        print("\n" + "="*60)
        print("VERIFICATION REPORT")
        print("="*60)

        issues = []
        files = [f for f in os.listdir(output_dir) if f.endswith('.json')]

        for file in files:
            with open(os.path.join(output_dir, file), 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check for duplicates
            entry_indices = [entry.get('entry_index', -1) for entry in data]
            unique_indices = set(entry_indices)

            if len(entry_indices) != len(unique_indices):
                issues.append(f"{file}: Has duplicate entries!")

            # Check completeness
            if -1 in entry_indices:
                issues.append(f"{file}: Missing entry_index in some entries")

            # Check for errors
            errors = [entry for entry in data if 'translation_error' in entry]
            if errors:
                issues.append(f"{file}: {len(errors)} entries have translation errors")

            print(f"✓ {file}: {len(data)} entries, {len(unique_indices)} unique")

        if issues:
            print("\n⚠️ ISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✅ All files verified successfully - NO DUPLICATES!")

        return len(issues) == 0

async def run_safe_translation():
    """Run translation with safety guarantees"""
    with open("mhj_dataset.json", 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    translator = SafeParallelTranslator()

    print(f"Starting SAFE parallel translation")
    print(f"Dataset: {len(dataset)} entries")
    print(f"Languages: {len(translator.languages)}")
    print(f"API keys: {len(translator.api_instances)}")

    start_time = time.time()
    output_files = await translator.translate_all_parallel(dataset)

    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")

    # Verify outputs
    translator.verify_output()

    return output_files

if __name__ == "__main__":
    asyncio.run(run_safe_translation())