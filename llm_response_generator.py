import json
import time
from pathlib import Path
from typing import List, Dict
import sys
import argparse
from apertus_api import ApertusAPI

class LLMResponseGenerator:
    def __init__(self, api_keys: List[str], model: str = "swiss-ai/Apertus-70B"):
        """Initialize with Apertus 70B model for response generation"""
        self.api = ApertusAPI(api_keys)
        self.model = model
        self.processed_count = 0

    def generate_response(self, conversation: List[Dict]) -> str:
        """Generate LLM response for a multi-turn conversation"""
        try:
            # Build the conversation history
            messages = []
            for turn in conversation:
                # Handle both 'content' and 'turn_content' fields
                content = turn.get("content") or turn.get("turn_content", "")
                if content:
                    messages.append({
                        "role": "user",
                        "content": content
                    })

            # Get response from Apertus 70B
            response = self.api.generate_response(
                messages=messages,
                model=self.model,
                max_tokens=500,
                temperature=0.7
            )

            return response

        except Exception as e:
            print(f"Error generating response: {e}")
            return f"ERROR: {str(e)}"

    def process_dataset(self, language_code: str, limit: int = None):
        """Process a single language dataset and add LLM responses"""

        input_file = Path('multilingual_datasets_filtered') / f'mhj_dataset_{language_code}.json'
        output_file = Path('llm_responses') / f'mhj_dataset_{language_code}_with_responses.json'

        # Create output directory
        output_file.parent.mkdir(exist_ok=True)

        # Load dataset
        with open(input_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        if limit:
            dataset = dataset[:limit]

        print(f"\nProcessing {language_code}: {len(dataset)} entries")
        print("=" * 60)

        results = []
        for idx, entry in enumerate(dataset):
            print(f"\r[{language_code}] Processing entry {idx+1}/{len(dataset)}", end='', flush=True)

            # Get the turns (check both possible field names)
            turns = entry.get('turns', entry.get('jailbreak_turns', []))

            # Generate response
            llm_response = self.generate_response(turns)

            # Create result entry with both original data and LLM response
            result_entry = {
                **entry,  # Include all original fields
                'llm_response': llm_response,
                'response_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            results.append(result_entry)
            self.processed_count += 1

            # Save intermediate results every 10 entries
            if (idx + 1) % 10 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        # Save final results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n[{language_code}] Complete! Saved to {output_file}")
        return len(results)

    def process_all_ready_datasets(self, limit: int = None):
        """Process all ready datasets"""

        # Read list of ready languages
        with open('ready_for_llm_testing.txt', 'r') as f:
            languages = [line.strip() for line in f if line.strip()]

        print(f"Found {len(languages)} ready datasets")
        total_processed = 0

        for lang in languages:
            try:
                processed = self.process_dataset(lang, limit=limit)
                total_processed += processed
            except Exception as e:
                print(f"\nError processing {lang}: {e}")
                continue

        print("\n" + "=" * 60)
        print(f"Total entries processed: {total_processed}")
        print(f"Total API calls made: {self.processed_count}")


def main():
    parser = argparse.ArgumentParser(description='Generate LLM responses for translated datasets')
    parser.add_argument('--language', type=str, help='Process specific language')
    parser.add_argument('--limit', type=int, help='Limit entries per dataset for testing')
    parser.add_argument('--api-keys', type=str, help='Path to API keys file', default='config.json')

    args = parser.parse_args()

    # Load API keys from config
    with open(args.api_keys, 'r') as f:
        config = json.load(f)
    api_keys = config['api_keys']

    generator = LLMResponseGenerator(api_keys)

    if args.language:
        generator.process_dataset(args.language, limit=args.limit)
    else:
        generator.process_all_ready_datasets(limit=args.limit)


if __name__ == "__main__":
    main()