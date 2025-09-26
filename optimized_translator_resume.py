import json
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from datetime import datetime
from collections import deque
from apertus_api import ApertusAPI
import os

class RateLimiter:
    """Rate limiter to ensure we don't exceed 5 req/sec per API key"""
    def __init__(self, requests_per_second=1):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.lock = threading.Lock()

    def wait_if_needed(self):
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            self.last_request_time = time.time()


class OptimizedTranslatorWithResume:
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.api_keys = self.config['api_keys']
        self.languages = {lang['code']: lang for lang in self.config['languages']}

        # Create API client and rate limiter for each key
        self.api_clients = []
        self.rate_limiters = []
        for key in self.api_keys:
            api = ApertusAPI([key])
            self.api_clients.append(api)
            self.rate_limiters.append(RateLimiter(requests_per_second=4))

        self.processed_count = 0
        self.count_lock = threading.Lock()

    def check_language_status(self, language_code):
        """Check if a language is already complete or in progress"""
        dataset_dir = Path('multilingual_datasets')

        # Check for complete file
        complete_file = dataset_dir / f'mhj_dataset_{language_code}.json'
        if complete_file.exists():
            try:
                with open(complete_file, 'r') as f:
                    data = json.load(f)
                # Check if it's the filtered dataset (382 entries)
                if len(data) == 382 or any(e.get('language_code') == language_code for e in data[:1]):
                    print(f"[SKIP] {language_code}: Already complete with {len(data)} entries")
                    return 'complete'
            except:
                pass

        # Check for part files (indicates in progress)
        part_files = list(dataset_dir.glob(f'mhj_dataset_{language_code}_part*.json'))
        if part_files:
            print(f"[IN PROGRESS] {language_code}: Found {len(part_files)} part files")
            return 'in_progress'

        return 'not_started'

    def translate_turn(self, turn, target_lang, api_index):
        """Translate a single turn with rate limiting"""
        self.rate_limiters[api_index].wait_if_needed()

        try:
            api = self.api_clients[api_index]
            translated = api.translate_text(
                text=turn['content'],
                target_language=target_lang['code'],
                language_name=target_lang['name']
            )

            with self.count_lock:
                self.processed_count += 1
                if self.processed_count % 100 == 0:
                    print(f"[Progress] {self.processed_count} turns translated")

            return {
                'turn_number': turn['turn_number'],
                'content': translated if translated else turn['content'],
                'original_content': turn['content']
            }
        except Exception as e:
            print(f"Error translating turn: {e}")
            return {
                'turn_number': turn['turn_number'],
                'content': turn['content'],
                'original_content': turn['content'],
                'error': str(e)
            }

    def translate_entry_parallel(self, entry, entry_index, target_lang):
        """Translate all turns in an entry using parallel workers"""
        turns = entry['turns']
        translated_turns = [None] * len(turns)

        with ThreadPoolExecutor(max_workers=min(5, len(turns))) as executor:
            futures = {}

            for i, turn in enumerate(turns):
                api_index = i % len(self.api_clients)
                future = executor.submit(
                    self.translate_turn, turn, target_lang, api_index
                )
                futures[future] = i

            for future in as_completed(futures):
                turn_index = futures[future]
                try:
                    result = future.result()
                    translated_turns[turn_index] = result
                except Exception as e:
                    print(f"Error in turn {turn_index}: {e}")
                    translated_turns[turn_index] = turns[turn_index]

        return {
            'entry_index': entry_index,
            'source': entry['source'],
            'base_prompt': entry['base_prompt'],
            'original_base_prompt': entry['base_prompt'],
            'turn_type': entry['turn_type'],
            'num_turns': entry['num_turns'],
            'turns': translated_turns,
            'language_code': target_lang['code'],
            'language_name': target_lang['name']
        }

    def translate_language(self, language_code, limit=None):
        """Translate entire dataset for one language"""
        # Check if already done
        status = self.check_language_status(language_code)
        if status == 'complete':
            return 'skipped'
        elif status == 'in_progress':
            print(f"[WARNING] {language_code} is in progress by another process")
            return 'in_progress'

        if language_code not in self.languages:
            print(f"Language {language_code} not found")
            return 'error'

        target_lang = self.languages[language_code]
        print(f"\n[START] Translating to {target_lang['name']} ({language_code})")
        print("=" * 60)

        # Load dataset
        with open('mhj_dataset.json', 'r') as f:
            dataset = json.load(f)

        # Filter to 382 entries
        dataset = [e for e in dataset if e.get('num_turns', 0) <= 6][:382]

        if limit:
            dataset = dataset[:limit]

        print(f"Processing {len(dataset)} entries")

        # Output directory
        output_dir = Path('multilingual_datasets')
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f'mhj_dataset_{language_code}.json'

        # Process entries
        translated_entries = []
        start_time = time.time()

        # Process in batches
        batch_size = 5
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i+batch_size]
            batch_results = []

            with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                futures = []
                for j, entry in enumerate(batch):
                    future = executor.submit(
                        self.translate_entry_parallel,
                        entry,
                        i + j,
                        target_lang
                    )
                    futures.append(future)

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        batch_results.append(result)
                    except Exception as e:
                        print(f"Error processing entry: {e}")

            translated_entries.extend(batch_results)

            # Save intermediate results
            if (i + batch_size) % 20 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(translated_entries, f, ensure_ascii=False, indent=2)
                print(f"[{language_code}] Saved {len(translated_entries)} entries")

        # Save final results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translated_entries, f, ensure_ascii=False, indent=2)

        elapsed = time.time() - start_time
        print(f"\n[COMPLETE] {language_code}")
        print(f"  Entries: {len(translated_entries)}")
        print(f"  Time: {elapsed:.1f} seconds")
        print(f"  Rate: {self.processed_count / elapsed:.1f} turns/second")

        return 'completed'

    def get_remaining_languages(self):
        """Get list of languages that haven't been completed yet"""
        all_remaining = [
            "fas.Arab", "ukr.Cyrl", "hun.Latn", "swe.Latn",
            "ell.Grek", "dan.Latn", "vie.Latn", "tha.Thai",
            "nob.Latn", "fin.Latn", "slk.Latn", "bul.Cyrl",
            "hrv.Latn", "hin.Deva", "bos.Latn", "cat.Latn",
            "ben.Beng", "heb.Hebr", "lit.Latn", "slv.Latn",
            "ekk.Latn", "zsm.Latn", "als.Latn", "lvs.Latn"
        ]

        actually_remaining = []
        for lang_code in all_remaining:
            status = self.check_language_status(lang_code)
            if status == 'not_started':
                actually_remaining.append(lang_code)
            elif status == 'in_progress':
                print(f"[INFO] {lang_code} is currently being processed")

        return actually_remaining

    def translate_all_remaining(self):
        """Translate only the remaining languages"""
        remaining = self.get_remaining_languages()

        print("=" * 60)
        print("OPTIMIZED PARALLEL TRANSLATION (RESUME MODE)")
        print(f"Languages to process: {len(remaining)}")
        print(f"Using {len(self.api_keys)} API keys")
        print(f"Max rate: {len(self.api_keys) * 4} requests/second")
        print("=" * 60)
        print("\nRemaining languages:")
        for lang in remaining:
            print(f"  - {lang}")
        print()

        if not remaining:
            print("All languages are already complete or in progress!")
            return

        completed_count = 0
        for lang_code in remaining:
            result = self.translate_language(lang_code)
            if result == 'completed':
                completed_count += 1
                print(f"\nWaiting 30 seconds before next language...")
                time.sleep(30)
            elif result == 'skipped':
                print(f"Skipped {lang_code} (already complete)")

        print("\n" + "=" * 60)
        print(f"TRANSLATION BATCH COMPLETE!")
        print(f"Newly completed: {completed_count} languages")
        print(f"Total turns processed: {self.processed_count}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', type=str, help='Specific language to translate')
    parser.add_argument('--limit', type=int, help='Limit number of entries (for testing)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume translation, skip completed languages')

    args = parser.parse_args()

    translator = OptimizedTranslatorWithResume()

    if args.resume:
        translator.translate_all_remaining()
    elif args.language:
        translator.translate_language(args.language, args.limit)
    else:
        print("Usage:")
        print("  python optimized_translator_resume.py --language fas.Arab")
        print("  python optimized_translator_resume.py --resume")


if __name__ == "__main__":
    main()