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

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)

class ProgressTracker:
    """Global progress tracker for all APIs"""
    def __init__(self, total_languages=16):
        self.total_languages = total_languages
        self.total_entries = 382 * total_languages  # 382 per language
        self.start_time = time.time()
        self.api_status = {}
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
            self.display()

    def display(self):
        os.system('clear' if os.name == 'posix' else 'cls')

        elapsed = time.time() - self.start_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))

        print("=" * 80)
        print(f"🚀 PARALLEL LLM RESPONSE GENERATION - REAL-TIME MONITOR")
        print(f"⏱️  Running Time: {elapsed_str}")
        print("=" * 80)

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

                print(f"\n[API {api_idx}] {status['language']}")
                print(f"  Progress: [{bar}] {progress:.1f}%")
                print(f"  Entries: {status['entries_done']}/{status['total_entries']} | Turns: {status['turns_done']}")
            else:
                print(f"\n[API {api_idx}] Waiting to start...")
                print(f"  Progress: [{'░' * 40}] 0.0%")

        # Overall statistics
        overall_progress = (total_entries_done / self.total_entries) * 100 if self.total_entries > 0 else 0

        print("\n" + "=" * 80)
        print(f"📊 OVERALL PROGRESS")
        print(f"  Total Entries: {total_entries_done}/{self.total_entries} ({overall_progress:.1f}%)")
        print(f"  Total Turns Processed: {total_turns_done}")

        if elapsed > 0:
            rate = total_turns_done / elapsed
            print(f"  Processing Rate: {rate:.1f} turns/sec")

            if rate > 0 and total_entries_done > 0:
                remaining_entries = self.total_entries - total_entries_done
                avg_turns_per_entry = total_turns_done / total_entries_done
                remaining_turns = remaining_entries * avg_turns_per_entry
                eta_seconds = remaining_turns / rate
                eta_str = str(timedelta(seconds=int(eta_seconds)))
                print(f"  Estimated Time Remaining: {eta_str}")

        print("=" * 80)
        print("\nPress Ctrl+C to stop | Logs: logs/llm_realtime.log")
        sys.stdout.flush()

# Global progress tracker
progress_tracker = None

class APIWorker:
    """Single API worker that processes one language completely"""
    def __init__(self, api_key: str, api_index: int):
        self.api = ApertusAPI([api_key])
        self.api_index = api_index
        self.last_request_time = 0
        self.min_interval = 0.25  # 4 req/sec
        self.processed_count = 0
        self.error_count = 0
        self.turns_processed = 0

    def wait_for_rate_limit(self):
        """Ensure we don't exceed 4 req/sec"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        self.last_request_time = time.time()

    def process_turn(self, turn_content: str, conversation_history: List[Dict]) -> str:
        """Process a single turn and get response"""
        try:
            # Wait for rate limit
            self.wait_for_rate_limit()

            # Build messages with conversation history
            messages = conversation_history.copy()

            # Truncate if needed
            if len(turn_content) > 1200:
                turn_content = turn_content[:1200] + "..."

            messages.append({
                'role': 'user',
                'content': turn_content
            })

            # Call API
            response = self.api.call_model(
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )

            if response:
                return response
            else:
                return "ERROR: No response from API"

        except Exception as e:
            error_str = str(e)

            # Handle rate limit errors
            if '429' in error_str or 'rate_limit' in error_str.lower():
                time.sleep(5)
                return self.process_turn(turn_content, conversation_history)  # Retry

            return f"ERROR: {error_str[:200]}"

    def process_entry(self, entry: Dict, entry_index: int) -> Dict:
        """Process a single entry - generate response for each turn"""
        try:
            turns = entry.get('turns', [])
            processed_turns = []
            conversation_history = []

            for turn_idx, turn in enumerate(turns):
                content = turn.get('content', '')

                if not content:
                    processed_turns.append({
                        **turn,
                        'llm_response': 'ERROR: Empty content',
                        'error': True
                    })
                    continue

                # Get response for this turn
                response = self.process_turn(content, conversation_history)

                # Add to processed turns
                processed_turns.append({
                    **turn,
                    'llm_response': response,
                    'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'error': 'ERROR' in response
                })

                # Update conversation history for next turn
                conversation_history.append({'role': 'user', 'content': content})
                if 'ERROR' not in response:
                    conversation_history.append({'role': 'assistant', 'content': response})
                    self.processed_count += 1
                    self.turns_processed += 1
                else:
                    self.error_count += 1

            return {
                'entry_index': entry.get('entry_index', entry_index),
                'turns': processed_turns,
                'api_key_index': self.api_index,
                'processing_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_turns': len(turns),
                'successful_turns': sum(1 for t in processed_turns if not t.get('error'))
            }

        except Exception as e:
            self.error_count += 1
            return {
                'entry_index': entry.get('entry_index', entry_index),
                'turns': entry.get('turns', []),
                'api_key_index': self.api_index,
                'error': str(e)[:500],
                'processing_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def process_language(self, language_code: str) -> str:
        """Process entire language dataset"""
        global progress_tracker

        input_file = Path('multilingual_datasets_filtered') / f'mhj_dataset_{language_code}.json'
        output_dir = Path('llm_responses')
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f'mhj_dataset_{language_code}_with_responses.json'

        # Check if already complete
        if output_file.exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                # Check if has turn responses
                if len(existing) >= 382:
                    first_entry = existing[0]
                    if 'turns' in first_entry and first_entry['turns']:
                        if 'llm_response' in first_entry['turns'][0]:
                            successful_entries = sum(1 for e in existing if e.get('successful_turns', 0) > 0)
                            return 'skipped'
            except:
                pass

        if not input_file.exists():
            return 'error'

        start_time = time.time()

        # Load dataset
        with open(input_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        results = []

        # Reset counters for this language
        self.processed_count = 0
        self.error_count = 0
        self.turns_processed = 0

        # Process each entry
        for i, entry in enumerate(dataset):
            result = self.process_entry(entry, i)
            results.append(result)

            # Update progress
            if progress_tracker:
                progress_tracker.update(
                    self.api_index,
                    language_code,
                    i + 1,
                    len(dataset),
                    self.turns_processed
                )

            # Save intermediate results every 20 entries
            if (i + 1) % 20 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

        # Save final results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        elapsed = time.time() - start_time
        return 'completed'


class ParallelLLMProcessor:
    """Main processor that coordinates 5 API workers"""
    def __init__(self, config_path='config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.api_keys = self.config['api_keys']
        self.languages = [
            "kor.Hang", "cmn.Hani", "deu.Latn", "spa.Latn",
            "jpn.Jpan", "fra.Latn", "ita.Latn", "rus.Cyrl",
            "por.Latn", "pol.Latn", "nld.Latn", "ind.Latn",
            "tur.Latn", "ces.Latn", "arb.Arab", "ron.Latn"
        ]

    def process_all(self):
        """Process all languages using 5 API keys in parallel"""
        global progress_tracker
        progress_tracker = ProgressTracker(len(self.languages))

        # Group languages for processing
        language_groups = [
            self.languages[0:3],   # API 0: kor, cmn, deu
            self.languages[3:6],   # API 1: spa, jpn, fra
            self.languages[6:9],   # API 2: ita, rus, por
            self.languages[9:12],  # API 3: pol, nld, ind
            self.languages[12:16]  # API 4: tur, ces, arb, ron
        ]

        results = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}

            # Submit jobs for each API
            for api_idx, (api_key, lang_group) in enumerate(zip(self.api_keys, language_groups)):
                worker = APIWorker(api_key, api_idx)

                for lang_code in lang_group:
                    future = executor.submit(worker.process_language, lang_code)
                    futures[future] = (api_idx, lang_code)

            # Collect results
            for future in as_completed(futures):
                api_idx, lang_code = futures[future]
                try:
                    result = future.result()
                    results[lang_code] = result
                except Exception as e:
                    results[lang_code] = 'error'

        # Final summary
        progress_tracker.display()
        print("\n\nPROCESSING COMPLETE!")

        completed = sum(1 for r in results.values() if r == 'completed')
        skipped = sum(1 for r in results.values() if r == 'skipped')
        errors = sum(1 for r in results.values() if r == 'error')

        print(f"Completed: {completed} | Skipped: {skipped} | Errors: {errors}")

        return results

    def process_single_language(self, language_code: str):
        """Process a single language for testing"""
        if language_code not in self.languages:
            print(f"Language {language_code} not in the list of 16 completed languages")
            return

        global progress_tracker
        progress_tracker = ProgressTracker(1)

        # Use first available API key
        worker = APIWorker(self.api_keys[0], 0)
        result = worker.process_language(language_code)

        progress_tracker.display()
        print(f"\nResult for {language_code}: {result}")
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true', help='Process all 16 languages')
    parser.add_argument('--language', type=str, help='Process single language')
    parser.add_argument('--test', action='store_true', help='Test with small dataset')

    args = parser.parse_args()

    processor = ParallelLLMProcessor()

    if args.all:
        processor.process_all()
    elif args.language:
        processor.process_single_language(args.language)
    elif args.test:
        # Test with Korean
        processor.process_single_language('kor.Hang')
    else:
        print("Usage:")
        print("  python parallel_llm_5api_realtime.py --all")
        print("  python parallel_llm_5api_realtime.py --language kor.Hang")
        print("  python parallel_llm_5api_realtime.py --test")


if __name__ == '__main__':
    main()