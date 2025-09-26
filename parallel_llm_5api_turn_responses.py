import json
import time
import threading
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from datetime import datetime
from apertus_api import ApertusAPI
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

class APIWorker:
    """Single API worker that processes one language completely"""
    def __init__(self, api_key: str, api_index: int):
        self.api = ApertusAPI([api_key])
        self.api_index = api_index
        self.last_request_time = 0
        self.min_interval = 0.25  # 4 req/sec
        self.processed_count = 0
        self.error_count = 0

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
                print(f"[API {self.api_index}] Rate limit hit, waiting...")
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
                            print(f"[API {self.api_index}] {language_code} already complete ({successful_entries}/382 entries)")
                            return 'skipped'
            except:
                pass

        if not input_file.exists():
            print(f"[API {self.api_index}] Input file not found: {input_file}")
            return 'error'

        print(f"[API {self.api_index}] Starting {language_code}")
        start_time = time.time()

        # Load dataset
        with open(input_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        results = []

        # Reset counters for this language
        self.processed_count = 0
        self.error_count = 0

        # Process each entry
        for i, entry in enumerate(dataset):
            result = self.process_entry(entry, i)
            results.append(result)

            # Progress update
            if (i + 1) % 20 == 0:
                elapsed = time.time() - start_time
                rate = self.processed_count / elapsed if elapsed > 0 else 0
                print(f"[API {self.api_index}] {language_code}: Entry {i+1}/{len(dataset)} "
                      f"({self.processed_count} turns done, {rate:.1f} turns/sec)")

            # Save intermediate results
            if (i + 1) % 50 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

        # Save final results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        elapsed = time.time() - start_time
        print(f"[API {self.api_index}] Completed {language_code}: "
              f"{self.processed_count} turns success, {self.error_count} turns error, "
              f"{elapsed:.1f}s")

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
        print("=" * 60, flush=True)
        print("PARALLEL LLM TURN-BY-TURN RESPONSE GENERATION", flush=True)
        print(f"Languages: {len(self.languages)}", flush=True)
        print(f"API Keys: {len(self.api_keys)}", flush=True)
        print("Strategy: Each API processes languages with turn-by-turn responses", flush=True)
        print("=" * 60, flush=True)

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
                    print(f"[API {api_idx}] Assigned to process {lang_code}")

            # Collect results
            for future in as_completed(futures):
                api_idx, lang_code = futures[future]
                try:
                    result = future.result()
                    results[lang_code] = result
                    print(f"[API {api_idx}] {lang_code}: {result}")
                except Exception as e:
                    print(f"[API {api_idx}] {lang_code}: ERROR - {e}")
                    results[lang_code] = 'error'

        # Summary
        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)

        completed = sum(1 for r in results.values() if r == 'completed')
        skipped = sum(1 for r in results.values() if r == 'skipped')
        errors = sum(1 for r in results.values() if r == 'error')

        print(f"Completed: {completed}")
        print(f"Skipped: {skipped}")
        print(f"Errors: {errors}")

        for lang, result in results.items():
            print(f"  {lang}: {result}")

        return results

    def process_single_language(self, language_code: str):
        """Process a single language for testing"""
        if language_code not in self.languages:
            print(f"Language {language_code} not in the list of 16 completed languages")
            return

        # Use first available API key
        worker = APIWorker(self.api_keys[0], 0)
        result = worker.process_language(language_code)
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
        print("  python parallel_llm_5api_turn_responses.py --all")
        print("  python parallel_llm_5api_turn_responses.py --language kor.Hang")
        print("  python parallel_llm_5api_turn_responses.py --test")


if __name__ == '__main__':
    main()