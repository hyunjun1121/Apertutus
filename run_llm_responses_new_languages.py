#!/usr/bin/env python3
"""
Generate LLM responses for newly translated 24 languages
Using 5 APIs in parallel with turn-by-turn processing
"""

import json
import time
import threading
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from apertus_api import ApertusAPI

# Unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1) if hasattr(sys.stdout, 'fileno') else sys.stdout

class ProgressTracker:
    """Track progress across all APIs"""
    def __init__(self, total_languages):
        self.total_languages = total_languages
        self.start_time = time.time()
        self.api_status = {}
        self.completed_languages = set()
        self.total_turns_processed = 0
        self.lock = threading.Lock()

    def update(self, api_idx, language, entries_done, total_entries, turns_done):
        with self.lock:
            self.api_status[api_idx] = {
                'language': language,
                'entries_done': entries_done,
                'total_entries': total_entries,
                'turns_done': turns_done,
                'last_update': time.time()
            }
            self.total_turns_processed += 1
            self.display()

    def complete_language(self, language):
        with self.lock:
            self.completed_languages.add(language)

    def display(self):
        """Display real-time progress"""
        os.system('clear' if os.name == 'posix' else 'cls')

        elapsed = time.time() - self.start_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))

        print("=" * 80)
        print(f"🤖 LLM RESPONSE GENERATION - NEW 24 LANGUAGES")
        print(f"⏱️  Running: {elapsed_str}")
        print("=" * 80)

        # API Status
        total_entries_done = 0
        total_turns_done = 0

        for api_idx in range(5):
            if api_idx in self.api_status:
                status = self.api_status[api_idx]
                total_entries_done += status['entries_done']
                total_turns_done += status['turns_done']

                progress = (status['entries_done'] / status['total_entries']) * 100
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
        print("\n" + "=" * 80)
        print(f"📊 OVERALL PROGRESS")
        print(f"  Languages: {len(self.completed_languages)}/{self.total_languages} completed")
        print(f"  Total Turns Processed: {self.total_turns_processed}")

        if elapsed > 0 and total_turns_done > 0:
            rate = total_turns_done / elapsed
            print(f"  Processing Rate: {rate:.1f} turns/sec")

            # ETA calculation
            estimated_total_turns = self.total_languages * 382 * 5  # Avg 5 turns per entry
            remaining_turns = estimated_total_turns - self.total_turns_processed
            if rate > 0:
                eta_seconds = remaining_turns / rate
                eta_str = str(timedelta(seconds=int(eta_seconds)))
                print(f"  ETA: {eta_str}")

        print("=" * 80)
        sys.stdout.flush()

# Global tracker
progress_tracker = None

class ResponseWorker:
    """Worker for generating LLM responses"""
    def __init__(self, api_key, api_index):
        self.api = ApertusAPI([api_key])
        self.api_index = api_index
        self.last_request_time = 0
        self.min_interval = 0.2  # 5 req/sec

    def wait_for_rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        self.last_request_time = time.time()

    def generate_response(self, turn_content, conversation_history):
        """Generate response for a single turn"""
        try:
            self.wait_for_rate_limit()

            messages = conversation_history.copy()
            messages.append({
                'role': 'user',
                'content': turn_content[:1200] if len(turn_content) > 1200 else turn_content
            })

            response = self.api.call_model(
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )

            return response if response else "ERROR: No response"

        except Exception as e:
            if '429' in str(e):
                time.sleep(5)
                return self.generate_response(turn_content, conversation_history)
            return f"ERROR: {str(e)}"

    def process_language(self, language_code, dataset_path, output_dir):
        """Process one language dataset"""
        global progress_tracker

        # Load translated dataset
        input_file = dataset_path / f"mhj_dataset_{language_code}.json"
        output_file = output_dir / f"mhj_dataset_{language_code}_with_responses.json"

        # Skip if already done
        if output_file.exists():
            print(f"[API {self.api_index}] Skipping {language_code} (already processed)")
            progress_tracker.complete_language(language_code)
            return

        if not input_file.exists():
            print(f"[API {self.api_index}] Warning: {language_code} translation not found")
            return

        print(f"[API {self.api_index}] Starting {language_code}")

        with open(input_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        turns_processed = 0

        for idx, entry in enumerate(dataset):
            conversation_history = []
            all_responses = []

            for turn in entry['turns']:
                # Generate response
                response = self.generate_response(
                    turn['content'],
                    conversation_history
                )

                # Add to turn
                turn['llm_response'] = response
                all_responses.append(response)

                # Update conversation history
                conversation_history.append({'role': 'user', 'content': turn['content']})
                conversation_history.append({'role': 'assistant', 'content': response})

                turns_processed += 1

                # Update progress
                if progress_tracker:
                    progress_tracker.update(
                        self.api_index,
                        language_code,
                        idx + 1,
                        len(dataset),
                        turns_processed
                    )

            # Combine all responses for evaluation
            entry['model_response'] = " ".join(all_responses)

            # Save periodically
            if (idx + 1) % 50 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(dataset[:idx+1], f, indent=2, ensure_ascii=False)

        # Save final
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        print(f"[API {self.api_index}] ✅ Completed {language_code}")
        progress_tracker.complete_language(language_code)

        return True


def get_new_languages():
    """Get the 24 newly translated languages"""
    # Languages that were already done (16)
    already_done = {
        'rus.Cyrl', 'cmn.Hani', 'deu.Latn', 'spa.Latn',
        'jpn.Jpan', 'fra.Latn', 'ita.Latn', 'por.Latn',
        'pol.Latn', 'nld.Latn', 'ind.Latn', 'tur.Latn',
        'ces.Latn', 'kor.Hang', 'arb.Arab', 'ron.Latn'
    }

    # Get all 40 languages from config
    with open('config.json', 'r') as f:
        config = json.load(f)

    all_languages = [lang['code'] for lang in config['languages']]

    # Get the 24 new ones
    new_languages = [lang for lang in all_languages if lang not in already_done]

    # Also check what actually exists in multilingual_datasets_filtered
    filtered_dir = Path("multilingual_datasets_filtered")
    existing_new = []

    for lang in new_languages:
        if (filtered_dir / f"mhj_dataset_{lang}.json").exists():
            existing_new.append(lang)

    return existing_new, config['api_keys']


def main():
    print("=" * 80)
    print("LLM RESPONSE GENERATION FOR NEW LANGUAGES")
    print("=" * 80)

    # Setup
    dataset_dir = Path("multilingual_datasets_filtered")
    output_dir = Path("llm_responses")
    output_dir.mkdir(exist_ok=True)

    # Get new languages
    new_languages, api_keys = get_new_languages()

    if not new_languages:
        print("No new languages found in multilingual_datasets_filtered/")
        return

    print(f"Found {len(new_languages)} new languages to process:")
    for lang in new_languages:
        print(f"  • {lang}")

    # Initialize tracker
    global progress_tracker
    progress_tracker = ProgressTracker(len(new_languages))

    # Distribute languages across APIs
    api_assignments = {i: [] for i in range(5)}
    for idx, lang in enumerate(new_languages):
        api_idx = idx % 5
        api_assignments[api_idx].append(lang)

    print("\nAPI Assignments:")
    for api_idx, langs in api_assignments.items():
        print(f"  API {api_idx}: {', '.join(langs[:3])}{f' +{len(langs)-3}' if len(langs) > 3 else ''}")

    print("\nStarting parallel processing...")
    print("=" * 80)
    time.sleep(2)

    # Process in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []

        for api_idx in range(5):
            if api_idx < len(api_keys) and api_assignments[api_idx]:
                worker = ResponseWorker(api_keys[api_idx], api_idx)

                for language in api_assignments[api_idx]:
                    future = executor.submit(
                        worker.process_language,
                        language,
                        dataset_dir,
                        output_dir
                    )
                    futures.append(future)

        # Wait for all
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Error: {e}")

    print("\n" + "=" * 80)
    print("✅ LLM RESPONSE GENERATION COMPLETE!")
    print(f"Processed {len(new_languages)} new languages")
    print(f"Output: {output_dir}/")
    print("\nNext step: Run StrongReject evaluation")
    print("  python3 run_strongreject_new_languages.py")
    print("=" * 80)


if __name__ == "__main__":
    main()