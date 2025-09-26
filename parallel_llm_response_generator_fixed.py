import json
import time
from pathlib import Path
from typing import List, Dict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from datetime import datetime
from apertus_api import ApertusAPI

class ParallelLLMResponseGenerator:
    def __init__(self, api_keys: List[str]):
        """Initialize with multiple API clients for parallel processing"""
        self.api_keys = api_keys
        self.apis = [ApertusAPI([key]) for key in api_keys]
        self.model = "swiss-ai/Apertus-70B"
        self.processed_count = 0
        self.lock = threading.Lock()
        self.results_lock = threading.Lock()

    def truncate_content(self, content: str, max_chars: int = 2000) -> str:
        """Truncate content if it's too long"""
        if len(content) > max_chars:
            return content[:max_chars] + "..."
        return content

    def generate_response_for_entry(self, entry: Dict, api_index: int) -> Dict:
        """Generate LLM response for a single entry"""
        try:
            # Get the turns
            turns = entry.get('turns', entry.get('jailbreak_turns', []))

            # Build messages - limit to first 3 turns to reduce size
            messages = []
            turn_limit = min(3, len(turns))  # Max 3 turns to avoid 400 error

            for i, turn in enumerate(turns[:turn_limit]):
                content = turn.get("content") or turn.get("turn_content", "")
                if content:
                    # Truncate very long content
                    content = self.truncate_content(content, max_chars=1500)
                    messages.append({
                        "role": "user",
                        "content": content
                    })

            if not messages:
                # If no valid messages, create a simple one
                messages = [{"role": "user", "content": "Hello"}]

            # Get response using specific API with reduced max_tokens
            api = self.apis[api_index]
            response = api.generate_response(
                messages=messages,
                model=self.model,
                max_tokens=300,  # Reduced from 500
                temperature=0.7
            )

            # Create result with response
            result = {
                **entry,
                'llm_response': response,
                'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'api_key_index': api_index,
                'turns_used': turn_limit
            }

            with self.lock:
                self.processed_count += 1

            return result

        except Exception as e:
            error_msg = str(e)
            print(f"\nError processing entry {entry.get('entry_index', 'unknown')}: {error_msg[:100]}")

            # Log detailed error for debugging
            if "400" in error_msg or "INVALID_REQUEST" in error_msg:
                print(f"  Request too large or malformed for entry {entry.get('entry_index')}")

            return {
                **entry,
                'llm_response': f"ERROR: {error_msg[:200]}",
                'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'api_key_index': api_index,
                'error': True
            }

    def process_language_batch(self, language_code: str, entries: List[Dict],
                             api_index: int, output_dir: Path) -> int:
        """Process a batch of entries for a language using a specific API key"""
        results = []
        output_file = output_dir / f'mhj_dataset_{language_code}_with_responses.json'

        print(f"\n[API {api_index}] Processing {len(entries)} entries for {language_code}")

        for idx, entry in enumerate(entries):
            try:
                result = self.generate_response_for_entry(entry, api_index)
                results.append(result)

                # Print progress
                if (idx + 1) % 5 == 0:
                    print(f"[API {api_index}] {language_code}: {idx+1}/{len(entries)} completed")

                # Save intermediate results every 10 entries
                if (idx + 1) % 10 == 0:
                    with self.results_lock:
                        # Load existing results if any
                        existing = []
                        if output_file.exists():
                            try:
                                with open(output_file, 'r', encoding='utf-8') as f:
                                    existing = json.load(f)
                            except:
                                existing = []

                        # Merge and save
                        all_results = existing + results[max(0, len(existing)-len(results)):]
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(all_results, f, ensure_ascii=False, indent=2)

                # Rate limiting - slower to avoid 429 errors
                time.sleep(0.5)  # Increased from 0.2

            except Exception as e:
                print(f"[API {api_index}] Failed on entry {idx}: {str(e)[:100]}")
                # Add failed entry with error
                results.append({
                    **entry,
                    'llm_response': "ERROR: Processing failed",
                    'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'api_key_index': api_index,
                    'error': True
                })

        # Save final results
        with self.results_lock:
            existing = []
            if output_file.exists():
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                except:
                    existing = []

            all_results = existing + results[max(0, len(existing)-len(results)):]
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)

        return len(results)

    def process_all_datasets(self, input_dir: Path, output_dir: Path, limit: int = None):
        """Process all datasets in parallel using multiple API keys"""

        # Create output directory
        output_dir.mkdir(exist_ok=True)

        # Get all dataset files
        dataset_files = sorted(input_dir.glob('mhj_dataset_*.json'))

        print(f"Found {len(dataset_files)} datasets to process")
        print(f"Using {len(self.api_keys)} API keys for parallel processing")
        print("=" * 60)

        # Process one language at a time to avoid overwhelming the API
        for dataset_file in dataset_files:
            language_code = dataset_file.stem.replace('mhj_dataset_', '')

            # Skip if already processed
            output_file = output_dir / f'mhj_dataset_{language_code}_with_responses.json'
            if output_file.exists():
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                    if len(existing) >= 382:  # Already complete
                        print(f"Skipping {language_code} (already complete with {len(existing)} entries)")
                        continue
                except:
                    pass

            print(f"\nProcessing {language_code}...")

            # Load dataset
            with open(dataset_file, 'r', encoding='utf-8') as f:
                dataset = json.load(f)

            if limit:
                dataset = dataset[:limit]

            # Process with single API key to avoid conflicts
            # Rotate through API keys for each language
            api_index = dataset_files.index(dataset_file) % len(self.api_keys)

            count = self.process_language_batch(
                language_code,
                dataset,
                api_index,
                output_dir
            )

            print(f"Completed {language_code}: {count} entries processed")

            # Longer delay between languages
            time.sleep(2)

        print("\n" + "=" * 60)
        print(f"Total entries processed: {self.processed_count}")


def main():
    parser = argparse.ArgumentParser(description='Generate LLM responses in parallel')
    parser.add_argument('--input-dir', type=str,
                       default='multilingual_datasets_filtered',
                       help='Input directory with filtered datasets')
    parser.add_argument('--output-dir', type=str,
                       default='llm_responses',
                       help='Output directory for responses')
    parser.add_argument('--limit', type=int,
                       help='Limit entries per dataset for testing')
    parser.add_argument('--config', type=str,
                       default='config.json',
                       help='Config file with API keys')

    args = parser.parse_args()

    # Load API keys
    with open(args.config, 'r') as f:
        config = json.load(f)
    api_keys = config['api_keys']

    # Create generator
    generator = ParallelLLMResponseGenerator(api_keys)

    # Process all datasets
    generator.process_all_datasets(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        limit=args.limit
    )


if __name__ == "__main__":
    main()