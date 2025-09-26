import json
import time
import threading
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from datetime import datetime
from apertus_api import ApertusAPI

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

    def process_entry(self, entry: Dict, entry_index: int) -> Dict:
        """Process a single entry"""
        try:
            # Wait for rate limit
            self.wait_for_rate_limit()

            # Extract turns and prepare messages
            turns = entry.get('turns', [])
            messages = []

            # Use up to 3 turns to avoid token limit
            for i, turn in enumerate(turns[:3]):
                content = turn.get('content', '')
                if content:
                    # Truncate very long content
                    if len(content) > 1200:
                        content = content[:1200] + "..."
                    messages.append({
                        'role': 'user',
                        'content': content
                    })

            if not messages:
                messages = [{'role': 'user', 'content': 'Hello'}]

            # Call API
            response = self.api.call_model(
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )

            if response:
                self.processed_count += 1
                return {
                    **entry,
                    'llm_response': response,
                    'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'api_key_index': self.api_index,
                    'success': True
                }
            else:
                self.error_count += 1
                return {
                    **entry,
                    'llm_response': 'ERROR: No response from API',
                    'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'api_key_index': self.api_index,
                    'error': True
                }

        except Exception as e:
            self.error_count += 1
            error_str = str(e)

            # Handle rate limit errors
            if '429' in error_str or 'rate_limit' in error_str.lower():
                print(f"[API {self.api_index}] Rate limit hit, waiting...")
                time.sleep(5)
                return self.process_entry(entry, entry_index)  # Retry

            return {
                **entry,
                'llm_response': f'ERROR: {error_str[:200]}',
                'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'api_key_index': self.api_index,
                'error': True
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
                valid = sum(1 for e in existing if not e.get('error'))
                if len(existing) >= 382 and valid > 350:
                    print(f"[API {self.api_index}] {language_code} already complete ({valid}/382 valid)")
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
            # Add entry_index to maintain order
            entry_with_index = {**entry, 'entry_index': i}
            result = self.process_entry(entry_with_index, i)
            results.append(result)

            # Progress update
            if (i + 1) % 50 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"[API {self.api_index}] {language_code}: {i+1}/{len(dataset)} "
                      f"({rate:.1f} entries/sec, {self.error_count} errors)")

            # Save intermediate results
            if (i + 1) % 100 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

        # Save final results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        elapsed = time.time() - start_time
        print(f"[API {self.api_index}] Completed {language_code}: "
              f"{self.processed_count} success, {self.error_count} errors, "
              f"{elapsed:.1f}s ({len(dataset)/elapsed:.1f} entries/sec)")

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
        print("=" * 60)
        print("PARALLEL LLM RESPONSE GENERATION")
        print(f"Languages: {len(self.languages)}")
        print(f"API Keys: {len(self.api_keys)}")
        print("Strategy: Each API processes languages independently")
        print("=" * 60)

        # Group languages for processing
        # 16 languages, 5 APIs: 4 APIs get 3 languages, 1 API gets 4 languages
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
        print("  python parallel_llm_5api_optimized.py --all")
        print("  python parallel_llm_5api_optimized.py --language kor.Hang")
        print("  python parallel_llm_5api_optimized.py --test")


if __name__ == '__main__':
    main()