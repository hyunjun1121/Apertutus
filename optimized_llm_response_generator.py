import json
import time
import threading
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from datetime import datetime
from apertus_api import ApertusAPI
import os

class RateLimiter:
    """Rate limiter for each API key"""
    def __init__(self, requests_per_second=4):
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


class OptimizedLLMResponseGenerator:
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.api_keys = self.config['api_keys']
        self.model = "swiss-ai/Apertus-70B"

        # Create separate API client and rate limiter for each key
        self.api_clients = []
        self.rate_limiters = []

        for key in self.api_keys:
            api = ApertusAPI([key])
            self.api_clients.append(api)
            # 4 req/sec per key = 20 req/sec total
            self.rate_limiters.append(RateLimiter(requests_per_second=4))

        self.processed_count = 0
        self.error_count = 0
        self.count_lock = threading.Lock()

    def truncate_content(self, content: str, max_chars: int = 1500) -> str:
        """Truncate content to avoid 400 errors"""
        if len(content) > max_chars:
            return content[:max_chars] + "..."
        return content

    def generate_response_with_retry(self, entry: Dict, api_index: int, retry_count: int = 3) -> Dict:
        """Generate LLM response with retry logic"""
        for attempt in range(retry_count):
            try:
                # Wait for rate limit
                self.rate_limiters[api_index].wait_if_needed()

                # Get turns
                turns = entry.get('turns', [])

                # Build messages - limit to first 3 turns
                messages = []
                turn_limit = min(3, len(turns))

                for i, turn in enumerate(turns[:turn_limit]):
                    content = turn.get("content", "")
                    if content:
                        # Truncate long content
                        content = self.truncate_content(content, max_chars=1200)
                        messages.append({
                            "role": "user",
                            "content": content
                        })

                if not messages:
                    messages = [{"role": "user", "content": "Hello"}]

                # Call API
                api = self.api_clients[api_index]
                response = api.call_model(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=250  # Reduced to avoid token limit
                )

                if response:
                    with self.count_lock:
                        self.processed_count += 1
                        if self.processed_count % 50 == 0:
                            print(f"[Progress] {self.processed_count} entries processed")

                    return {
                        **entry,
                        'llm_response': response,
                        'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'api_key_index': api_index,
                        'turns_used': turn_limit,
                        'attempt': attempt + 1
                    }

            except Exception as e:
                error_str = str(e)

                if "429" in error_str or "rate_limit" in error_str.lower():
                    # Rate limit - wait longer
                    print(f"  Rate limit on API {api_index}, waiting...")
                    time.sleep(5 * (attempt + 1))

                elif "400" in error_str:
                    # Bad request - try with even shorter content
                    print(f"  400 error, reducing content size...")
                    # Reduce max_chars for next attempt
                    max_chars = 800 - (attempt * 200)

                elif attempt == retry_count - 1:
                    # Final attempt failed
                    with self.count_lock:
                        self.error_count += 1

                    return {
                        **entry,
                        'llm_response': f"ERROR after {retry_count} attempts: {error_str[:100]}",
                        'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'api_key_index': api_index,
                        'error': True
                    }

                # Wait before retry
                time.sleep(1 * (attempt + 1))

        # Should not reach here
        return {
            **entry,
            'llm_response': "ERROR: Max retries exceeded",
            'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'api_key_index': api_index,
            'error': True
        }

    def process_language_parallel(self, language_code: str):
        """Process a language dataset using all API keys in parallel"""
        input_file = Path('multilingual_datasets_filtered') / f'mhj_dataset_{language_code}.json'
        output_dir = Path('llm_responses')
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f'mhj_dataset_{language_code}_with_responses.json'

        # Check if already processed
        if output_file.exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                if len(existing) >= 382:
                    print(f"[SKIP] {language_code} already complete with {len(existing)} entries")
                    return 'skipped'
            except:
                pass

        if not input_file.exists():
            print(f"[ERROR] Input file not found: {input_file}")
            return 'error'

        print(f"\n[START] Processing {language_code}")
        print("=" * 60)

        # Load dataset
        with open(input_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        print(f"Loaded {len(dataset)} entries")

        results = []
        start_time = time.time()

        # Process in parallel using all API keys
        with ThreadPoolExecutor(max_workers=len(self.api_clients) * 2) as executor:
            futures = {}

            for i, entry in enumerate(dataset):
                # Round-robin API key assignment
                api_index = i % len(self.api_clients)

                future = executor.submit(
                    self.generate_response_with_retry,
                    entry,
                    api_index
                )
                futures[future] = i

                # Limit concurrent futures
                if len(futures) >= len(self.api_clients) * 10:
                    # Wait for some to complete
                    done, _ = concurrent.futures.wait(
                        futures.keys(),
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )
                    for completed in done:
                        idx = futures[completed]
                        try:
                            result = completed.result()
                            results.append(result)
                        except Exception as e:
                            print(f"Error processing entry {idx}: {e}")
                        del futures[completed]

            # Collect remaining results
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    results.append(result)

                    # Save intermediate results
                    if len(results) % 50 == 0:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(results, f, ensure_ascii=False, indent=2)
                        print(f"[{language_code}] Saved {len(results)} entries")

                except Exception as e:
                    print(f"Error processing entry {idx}: {e}")

        # Sort by entry_index
        results.sort(key=lambda x: x.get('entry_index', 0))

        # Save final results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        elapsed = time.time() - start_time
        print(f"\n[COMPLETE] {language_code}")
        print(f"  Entries: {len(results)}")
        print(f"  Success: {self.processed_count}")
        print(f"  Errors: {self.error_count}")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Rate: {len(results)/elapsed:.1f} entries/sec")

        return 'completed'

    def process_all_languages(self):
        """Process all 16 completed languages"""
        languages = [
            "kor.Hang", "cmn.Hani", "deu.Latn", "spa.Latn",
            "jpn.Jpan", "fra.Latn", "ita.Latn", "rus.Cyrl",
            "por.Latn", "pol.Latn", "nld.Latn", "ind.Latn",
            "tur.Latn", "ces.Latn", "arb.Arab", "ron.Latn"
        ]

        print("=" * 60)
        print("OPTIMIZED LLM RESPONSE GENERATION")
        print(f"Languages: {len(languages)}")
        print(f"API Keys: {len(self.api_keys)}")
        print(f"Max Rate: {len(self.api_keys) * 4} req/sec")
        print("=" * 60)

        completed = 0
        skipped = 0

        for lang in languages:
            result = self.process_language_parallel(lang)

            if result == 'completed':
                completed += 1
                # Short delay between languages
                time.sleep(10)
            elif result == 'skipped':
                skipped += 1

        print("\n" + "=" * 60)
        print("ALL LANGUAGES PROCESSED!")
        print(f"  Completed: {completed}")
        print(f"  Skipped: {skipped}")
        print(f"  Total processed: {self.processed_count}")
        print(f"  Total errors: {self.error_count}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', type=str, help='Process specific language')
    parser.add_argument('--all', action='store_true', help='Process all 16 languages')

    args = parser.parse_args()

    generator = OptimizedLLMResponseGenerator()

    if args.all:
        generator.process_all_languages()
    elif args.language:
        generator.process_language_parallel(args.language)
    else:
        print("Usage:")
        print("  python optimized_llm_response_generator.py --language kor.Hang")
        print("  python optimized_llm_response_generator.py --all")


if __name__ == "__main__":
    main()