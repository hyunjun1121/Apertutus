#!/usr/bin/env python3
"""
Parallel translator with real-time monitoring and proper rate limiting
Processes remaining 24 languages efficiently with 5 API keys
"""

import json
import time
import threading
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from datetime import datetime, timedelta
from apertus_api import ApertusAPI
import sys
import os

# Force unbuffered output for real-time display
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)

class ProgressTracker:
    """Global progress tracker for all translation APIs"""
    def __init__(self, total_languages, entries_per_language=382):
        self.total_languages = total_languages
        self.entries_per_language = entries_per_language
        self.total_entries = entries_per_language * total_languages
        self.start_time = time.time()
        self.api_status = {}
        self.language_status = {}
        self.lock = threading.Lock()
        self.completed_languages = set()

    def update(self, api_idx, language, entries_done, total_entries, turns_done):
        with self.lock:
            self.api_status[api_idx] = {
                'language': language,
                'entries_done': entries_done,
                'total_entries': total_entries,
                'turns_done': turns_done,
                'last_update': time.time()
            }

            # Update language status
            self.language_status[language] = {
                'entries_done': entries_done,
                'total_entries': total_entries,
                'progress': (entries_done / total_entries) * 100 if total_entries > 0 else 0
            }

            if entries_done >= total_entries:
                self.completed_languages.add(language)

            self.display()

    def display(self):
        os.system('clear' if os.name == 'posix' else 'cls')

        elapsed = time.time() - self.start_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))

        print("=" * 90)
        print(f"🌍 MULTILINGUAL TRANSLATION - REAL-TIME MONITOR")
        print(f"⏱️  Running Time: {elapsed_str}")
        print("=" * 90)

        # API Status
        total_entries_done = 0
        total_turns_done = 0

        for api_idx in range(5):
            if api_idx in self.api_status:
                status = self.api_status[api_idx]
                total_entries_done += status['entries_done']
                total_turns_done += status['turns_done']

                progress = (status['entries_done'] / status['total_entries']) * 100 if status['total_entries'] > 0 else 0
                bar_length = 40
                filled = int(bar_length * progress / 100)
                bar = '█' * filled + '░' * (bar_length - filled)

                lang_name = status['language'].split('.')[0].upper()
                print(f"\n[API {api_idx}] {lang_name}")
                print(f"  [{bar}] {progress:.1f}%")
                print(f"  {status['entries_done']}/{status['total_entries']} entries | {status['turns_done']} turns")
            else:
                print(f"\n[API {api_idx}] Waiting...")
                print(f"  [{'░' * 40}] 0.0%")

        # Overall statistics
        overall_progress = (total_entries_done / self.total_entries) * 100 if self.total_entries > 0 else 0

        print("\n" + "=" * 90)
        print(f"📊 OVERALL PROGRESS")
        print(f"  Languages: {len(self.completed_languages)}/{self.total_languages} completed")
        print(f"  Total Entries: {total_entries_done}/{self.total_entries} ({overall_progress:.1f}%)")
        print(f"  Total Turns: {total_turns_done}")

        # Performance metrics
        if elapsed > 0:
            rate = total_turns_done / elapsed
            entry_rate = total_entries_done / elapsed * 60  # entries per minute
            print(f"\n⚡ PERFORMANCE")
            print(f"  Processing Rate: {rate:.1f} turns/sec | {entry_rate:.1f} entries/min")

            # ETA calculation
            if rate > 0 and total_entries_done > 0:
                remaining_entries = self.total_entries - total_entries_done
                avg_turns_per_entry = total_turns_done / total_entries_done
                remaining_turns = remaining_entries * avg_turns_per_entry
                eta_seconds = remaining_turns / rate
                eta_str = str(timedelta(seconds=int(eta_seconds)))
                completion_time = datetime.now() + timedelta(seconds=eta_seconds)
                print(f"  ETA: {eta_str} (Completion: {completion_time.strftime('%H:%M:%S')})")

        # Language summary
        if self.language_status:
            print(f"\n📝 LANGUAGE SUMMARY (Top 5)")
            sorted_langs = sorted(self.language_status.items(),
                                key=lambda x: x[1]['progress'], reverse=True)[:5]
            for lang, status in sorted_langs:
                lang_name = lang.split('.')[0].upper()
                print(f"  {lang_name}: {status['progress']:.1f}% ({status['entries_done']}/{status['total_entries']})")

        print("=" * 90)
        print("Press Ctrl+C to stop | Output: multilingual_datasets/")
        sys.stdout.flush()

# Global progress tracker
progress_tracker = None

class TranslationWorker:
    """Worker that translates one language using one API key"""
    def __init__(self, api_key: str, api_index: int):
        self.api = ApertusAPI([api_key])
        self.api_index = api_index
        self.last_request_time = 0
        self.min_interval = 0.25  # 4 req/sec per API (conservative)
        self.processed_count = 0
        self.turns_processed = 0

    def wait_for_rate_limit(self):
        """Ensure we respect rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        self.last_request_time = time.time()

    def translate_turn(self, turn: Dict, target_lang: Dict) -> Dict:
        """Translate a single turn"""
        try:
            self.wait_for_rate_limit()

            translated_content = self.api.translate_text(
                text=turn['content'],
                target_language=target_lang['code'],
                language_name=target_lang['name']
            )

            self.turns_processed += 1

            return {
                'turn_number': turn['turn_number'],
                'content': translated_content if translated_content else turn['content'],
                'original_content': turn['content']
            }

        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'rate_limit' in error_str.lower():
                time.sleep(5)
                return self.translate_turn(turn, target_lang)  # Retry
            else:
                print(f"\n[API {self.api_index}] Error: {error_str}")
                return {
                    'turn_number': turn['turn_number'],
                    'content': turn['content'],
                    'original_content': turn['content'],
                    'error': error_str
                }

    def translate_language(self, language: Dict, dataset: List[Dict], output_dir: Path):
        """Translate entire language dataset"""
        global progress_tracker

        lang_code = language['code']
        output_file = output_dir / f"mhj_dataset_{lang_code}.json"

        # Check if already exists
        if output_file.exists():
            print(f"[API {self.api_index}] {lang_code} already translated, skipping")
            return

        print(f"[API {self.api_index}] Starting {language['name']} ({lang_code})")

        translated_entries = []
        total_entries = len(dataset)

        for idx, entry in enumerate(dataset):
            translated_turns = []

            # Translate each turn
            for turn in entry['turns']:
                translated_turn = self.translate_turn(turn, language)
                translated_turns.append(translated_turn)

            # Create translated entry
            translated_entry = {
                'entry_index': entry.get('entry_index', idx),
                'source': entry.get('source', 'MHJ'),
                'base_prompt': entry['base_prompt'],
                'turn_type': entry.get('turn_type', 'multi'),
                'num_turns': len(translated_turns),
                'turns': translated_turns,
                'language_code': lang_code,
                'language_name': language['name']
            }

            translated_entries.append(translated_entry)
            self.processed_count += 1

            # Update progress
            if progress_tracker:
                progress_tracker.update(
                    self.api_index,
                    lang_code,
                    self.processed_count,
                    total_entries,
                    self.turns_processed
                )

            # Save periodically
            if (idx + 1) % 50 == 0:
                temp_file = output_dir / f"mhj_dataset_{lang_code}_temp.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(translated_entries, f, indent=2, ensure_ascii=False)

        # Save final file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translated_entries, f, indent=2, ensure_ascii=False)

        print(f"\n[API {self.api_index}] ✅ Completed {lang_code}: {len(translated_entries)} entries")

        # Clean up temp file
        temp_file = output_dir / f"mhj_dataset_{lang_code}_temp.json"
        if temp_file.exists():
            temp_file.unlink()

        return translated_entries


def get_remaining_languages(config_path='config.json'):
    """Get languages that haven't been translated yet"""
    # Check existing translations
    output_dir = Path("multilingual_datasets")
    existing_files = list(output_dir.glob("mhj_dataset_*.json"))

    # Also check filtered directory
    filtered_dir = Path("multilingual_datasets_filtered")
    filtered_files = list(filtered_dir.glob("mhj_dataset_*.json"))

    completed = set()
    for f in existing_files + filtered_files:
        # Extract language code
        if '_temp' not in f.stem and '_part' not in f.stem:
            lang_code = f.stem.replace('mhj_dataset_', '')
            completed.add(lang_code)

    # Get all languages from config
    with open(config_path, 'r') as f:
        config = json.load(f)

    all_languages = config['languages']
    remaining = [lang for lang in all_languages if lang['code'] not in completed]

    print(f"Found {len(completed)} completed languages")
    print(f"Remaining: {len(remaining)} languages")

    return remaining, config['api_keys']


def main():
    parser = argparse.ArgumentParser(description='Parallel translation with real-time monitoring')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--dataset', default='mhj_dataset_filtered.json', help='Source dataset')
    parser.add_argument('--output-dir', default='multilingual_datasets', help='Output directory')
    parser.add_argument('--max-workers', type=int, default=5, help='Max parallel workers')

    args = parser.parse_args()

    # Setup
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Load source dataset
    print("Loading source dataset...")
    with open(args.dataset, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    print(f"Loaded {len(dataset)} entries")

    # Get remaining languages
    remaining_languages, api_keys = get_remaining_languages(args.config)

    if not remaining_languages:
        print("All languages have been translated!")
        return

    # Initialize progress tracker
    global progress_tracker
    progress_tracker = ProgressTracker(len(remaining_languages), len(dataset))

    # Assign languages to API keys
    api_assignments = {}
    for i, lang in enumerate(remaining_languages):
        api_idx = i % len(api_keys)
        if api_idx not in api_assignments:
            api_assignments[api_idx] = []
        api_assignments[api_idx].append(lang)

    print("\nAPI Key Assignments:")
    for api_idx, langs in api_assignments.items():
        lang_names = [l['code'] for l in langs[:3]]
        if len(langs) > 3:
            lang_names.append(f"...+{len(langs)-3} more")
        print(f"  API {api_idx}: {', '.join(lang_names)}")

    print("\nStarting parallel translation...")
    print("=" * 90)
    time.sleep(2)

    # Start parallel translation
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = []

        for api_idx, languages in api_assignments.items():
            if api_idx < len(api_keys):
                worker = TranslationWorker(api_keys[api_idx], api_idx)

                for language in languages:
                    future = executor.submit(
                        worker.translate_language,
                        language,
                        dataset,
                        output_dir
                    )
                    futures.append((future, language['code']))

        # Wait for completion
        for future, lang_code in futures:
            try:
                future.result()
            except Exception as e:
                print(f"\nError processing {lang_code}: {e}")

    print("\n" + "=" * 90)
    print("✅ TRANSLATION COMPLETE!")
    print(f"All {len(remaining_languages)} languages have been translated")
    print(f"Output directory: {output_dir}")
    print("=" * 90)


if __name__ == "__main__":
    main()