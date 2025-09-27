#!/usr/bin/env python3
"""
Truly parallel translator - 5 APIs working simultaneously
Each API independently processes its assigned languages
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

# Unbuffered output for real-time display
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1) if hasattr(sys.stdout, 'fileno') else sys.stdout

class GlobalProgress:
    """Track progress across all APIs"""
    def __init__(self):
        self.lock = threading.Lock()
        self.api_status = {}
        self.start_time = time.time()
        self.total_languages = 0
        self.completed_languages = set()

    def update(self, api_idx, current_lang, entries_done, total_entries):
        with self.lock:
            self.api_status[api_idx] = {
                'language': current_lang,
                'entries': entries_done,
                'total': total_entries,
                'time': time.time()
            }

    def mark_complete(self, api_idx, language):
        with self.lock:
            self.completed_languages.add(language)
            print(f"\n✅ [API {api_idx}] Completed: {language}")

    def display(self):
        """Display current progress"""
        with self.lock:
            elapsed = time.time() - self.start_time
            print(f"\n{'='*60}")
            print(f"Progress Update - {datetime.now().strftime('%H:%M:%S')}")
            print(f"Elapsed: {str(timedelta(seconds=int(elapsed)))}")
            print(f"Completed: {len(self.completed_languages)}/{self.total_languages} languages")

            for api_idx in range(5):
                if api_idx in self.api_status:
                    s = self.api_status[api_idx]
                    pct = (s['entries'] / s['total'] * 100) if s['total'] > 0 else 0
                    print(f"[API {api_idx}] {s['language']}: {s['entries']}/{s['total']} ({pct:.1f}%)")
                else:
                    print(f"[API {api_idx}] Waiting...")
            print('='*60)

# Global tracker
progress = GlobalProgress()

def translate_single_api(api_key, api_index, languages, dataset, output_dir):
    """Function for one API to translate its assigned languages"""

    api = ApertusAPI([api_key])

    for lang in languages:
        lang_code = lang['code']
        lang_name = lang['name']

        # Check if already done
        output_file = output_dir / f"mhj_dataset_{lang_code}.json"
        if output_file.exists():
            print(f"[API {api_index}] Skipping {lang_code} (already exists)")
            progress.mark_complete(api_index, lang_code)
            continue

        print(f"\n[API {api_index}] Starting {lang_name} ({lang_code})")

        translated_entries = []

        for idx, entry in enumerate(dataset):
            # Translate all turns
            translated_turns = []

            for turn in entry['turns']:
                try:
                    # Rate limit: 4 req/sec per API
                    time.sleep(0.25)

                    translated_content = api.translate_text(
                        text=turn['content'],
                        target_language=lang_code,
                        language_name=lang_name
                    )

                    translated_turns.append({
                        'turn_number': turn['turn_number'],
                        'content': translated_content if translated_content else turn['content'],
                        'original_content': turn['content']
                    })

                except Exception as e:
                    print(f"[API {api_index}] Error: {e}")
                    translated_turns.append({
                        'turn_number': turn['turn_number'],
                        'content': turn['content'],
                        'original_content': turn['content']
                    })

                    if '429' in str(e):
                        time.sleep(5)  # Rate limit hit, wait longer

            # Create translated entry
            translated_entry = {
                'entry_index': idx,
                'source': entry.get('source', 'MHJ'),
                'base_prompt': entry['base_prompt'],
                'original_base_prompt': entry['base_prompt'],
                'turn_type': entry.get('turn_type', 'multi'),
                'num_turns': len(translated_turns),
                'turns': translated_turns,
                'language_code': lang_code,
                'language_name': lang_name
            }

            translated_entries.append(translated_entry)

            # Update progress
            progress.update(api_index, lang_code, idx + 1, len(dataset))

            # Show progress every 20 entries
            if (idx + 1) % 20 == 0:
                print(f"[API {api_index}] {lang_code}: {idx + 1}/{len(dataset)}")

            # Save periodically
            if (idx + 1) % 50 == 0:
                temp_file = output_dir / f"mhj_dataset_{lang_code}_temp.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(translated_entries, f, indent=2, ensure_ascii=False)

        # Save final file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translated_entries, f, indent=2, ensure_ascii=False)

        # Clean temp file
        temp_file = output_dir / f"mhj_dataset_{lang_code}_temp.json"
        if temp_file.exists():
            temp_file.unlink()

        progress.mark_complete(api_index, lang_code)
        print(f"[API {api_index}] ✅ Saved {lang_code}: {len(translated_entries)} entries")

    print(f"\n[API {api_index}] 🎉 All assigned languages complete!")
    return True

def main():
    # Setup
    output_dir = Path("multilingual_datasets_filtered")
    output_dir.mkdir(exist_ok=True)

    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)

    api_keys = config['api_keys'][:5]  # Use first 5 API keys
    all_languages = config['languages']

    # Load dataset
    print("Loading dataset...")
    with open('mhj_dataset.json', 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    print(f"Loaded {len(dataset)} entries")

    # Check what's already done
    completed = set()
    for f in output_dir.glob("mhj_dataset_*.json"):
        if '_temp' not in f.stem:
            lang_code = f.stem.replace('mhj_dataset_', '')
            completed.add(lang_code)

    print(f"Already completed: {len(completed)} languages")

    # Get remaining languages
    remaining = [lang for lang in all_languages if lang['code'] not in completed]

    if not remaining:
        print("All languages already translated!")
        return

    print(f"Remaining: {len(remaining)} languages")
    progress.total_languages = len(remaining)

    # Distribute languages across APIs
    api_assignments = {i: [] for i in range(5)}
    for idx, lang in enumerate(remaining):
        api_idx = idx % 5
        api_assignments[api_idx].append(lang)

    print("\n📋 API Assignments:")
    for api_idx, langs in api_assignments.items():
        lang_codes = [l['code'] for l in langs]
        print(f"API {api_idx}: {', '.join(lang_codes[:3])}{f' +{len(lang_codes)-3} more' if len(lang_codes) > 3 else ''}")

    print("\n" + "="*60)
    print("🚀 Starting parallel translation with 5 APIs")
    print("="*60)

    # Progress display thread
    def show_progress():
        while True:
            time.sleep(30)  # Update every 30 seconds
            progress.display()

    progress_thread = threading.Thread(target=show_progress, daemon=True)
    progress_thread.start()

    # Start parallel execution - 5 APIs working simultaneously
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []

        for api_idx in range(5):
            if api_idx < len(api_keys) and api_assignments[api_idx]:
                future = executor.submit(
                    translate_single_api,
                    api_keys[api_idx],
                    api_idx,
                    api_assignments[api_idx],
                    dataset,
                    output_dir
                )
                futures.append(future)

        # Wait for all to complete
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Error in thread: {e}")

    print("\n" + "="*60)
    print("✅ ALL TRANSLATIONS COMPLETE!")
    print(f"Translated {len(remaining)} languages")
    print(f"Output: {output_dir}/")
    print("="*60)

if __name__ == "__main__":
    main()