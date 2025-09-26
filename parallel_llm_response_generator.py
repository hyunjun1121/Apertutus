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

    def generate_response_for_entry(self, entry: Dict, api_index: int) -> Dict:
        """Generate LLM response for a single entry"""
        try:
            # Get the turns
            turns = entry.get('turns', entry.get('jailbreak_turns', []))

            # Build messages
            messages = []
            for turn in turns:
                content = turn.get("content") or turn.get("turn_content", "")
                if content:
                    messages.append({
                        "role": "user",
                        "content": content
                    })

            # Get response using specific API
            api = self.apis[api_index]
            response = api.generate_response(
                messages=messages,
                model=self.model,
                max_tokens=500,
                temperature=0.7
            )

            # Create result with response
            result = {
                **entry,
                'llm_response': response,
                'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'api_key_index': api_index
            }

            with self.lock:
                self.processed_count += 1

            return result

        except Exception as e:
            print(f"\nError processing entry {entry.get('entry_index', 'unknown')}: {e}")
            return {
                **entry,
                'llm_response': f"ERROR: {str(e)}",
                'response_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'api_key_index': api_index
            }

    def process_language_batch(self, language_code: str, entries: List[Dict],
                             api_index: int, output_dir: Path) -> int:
        """Process a batch of entries for a language using a specific API key"""
        results = []
        output_file = output_dir / f'mhj_dataset_{language_code}_with_responses.json'

        print(f"\n[API {api_index}] Processing {len(entries)} entries for {language_code}")

        for idx, entry in enumerate(entries):
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
                        with open(output_file, 'r', encoding='utf-8') as f:
                            existing = json.load(f)

                    # Merge and save
                    all_results = existing + results[max(0, len(existing)-len(results)):]
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(all_results, f, ensure_ascii=False, indent=2)

            # Rate limiting - 5 requests per second per key
            time.sleep(0.2)

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

        # Prepare work items
        work_items = []

        for dataset_file in dataset_files:
            language_code = dataset_file.stem.replace('mhj_dataset_', '')

            # Skip if already processed
            output_file = output_dir / f'mhj_dataset_{language_code}_with_responses.json'
            if output_file.exists():
                print(f"Skipping {language_code} (already processed)")
                continue

            # Load dataset
            with open(dataset_file, 'r', encoding='utf-8') as f:
                dataset = json.load(f)

            if limit:
                dataset = dataset[:limit]

            # Split dataset into chunks for parallel processing
            chunk_size = max(1, len(dataset) // len(self.api_keys))

            for i, api_index in enumerate(range(len(self.api_keys))):
                start = i * chunk_size
                end = start + chunk_size if i < len(self.api_keys) - 1 else len(dataset)

                if start < len(dataset):
                    chunk = dataset[start:end]
                    if chunk:
                        work_items.append({
                            'language_code': language_code,
                            'entries': chunk,
                            'api_index': api_index,
                            'start_idx': start,
                            'end_idx': end
                        })

        if not work_items:
            print("No datasets to process!")
            return

        # Process in parallel
        print(f"\nStarting parallel processing with {len(work_items)} work items...")
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=len(self.api_keys)) as executor:
            futures = []

            for item in work_items:
                future = executor.submit(
                    self.process_language_batch,
                    item['language_code'],
                    item['entries'],
                    item['api_index'],
                    output_dir
                )
                futures.append((future, item))

            # Wait for completion and gather results
            for future, item in futures:
                try:
                    count = future.result()
                    print(f"[API {item['api_index']}] Completed {item['language_code']} "
                          f"(entries {item['start_idx']}-{item['end_idx']}): {count} processed")
                except Exception as e:
                    print(f"Error in worker: {e}")

        # Merge results for each language
        print("\n" + "=" * 60)
        print("Merging results...")

        for dataset_file in dataset_files:
            language_code = dataset_file.stem.replace('mhj_dataset_', '')
            self.merge_language_results(language_code, output_dir)

        elapsed_time = time.time() - start_time
        print(f"\n" + "=" * 60)
        print(f"Total processing time: {elapsed_time:.2f} seconds")
        print(f"Total entries processed: {self.processed_count}")
        print(f"Average time per entry: {elapsed_time/max(1, self.processed_count):.2f} seconds")

    def merge_language_results(self, language_code: str, output_dir: Path):
        """Merge partial results for a language into final file"""
        output_file = output_dir / f'mhj_dataset_{language_code}_with_responses.json'

        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Sort by entry_index to maintain order
            data.sort(key=lambda x: x.get('entry_index', 0))

            # Remove duplicates (keep first occurrence)
            seen = set()
            unique_data = []
            for item in data:
                idx = item.get('entry_index', -1)
                if idx not in seen:
                    seen.add(idx)
                    unique_data.append(item)

            # Save final merged result
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(unique_data, f, ensure_ascii=False, indent=2)

            print(f"Merged {language_code}: {len(unique_data)} unique entries")


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