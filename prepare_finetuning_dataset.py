"""
Prepare fine-tuning dataset from MHJ jailbreak datasets
Each turn becomes a separate training example with refusal response
"""

import json
import os
from typing import List, Dict, Any
from glob import glob
from datetime import datetime
import random
from collections import defaultdict

class FinetuningDatasetPreparer:
    def __init__(self,
                 source_dir: str = "multilingual_datasets",
                 output_dir: str = "finetuning_datasets",
                 refusal_message: str = "I cannot assist with that request."):
        """
        Initialize dataset preparer

        Args:
            source_dir: Directory containing translated datasets
            output_dir: Directory to save fine-tuning datasets
            refusal_message: Standard refusal response
        """
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.refusal_message = refusal_message
        os.makedirs(output_dir, exist_ok=True)

        # Track statistics
        self.stats = defaultdict(int)

    def process_single_entry(self, entry: Dict[str, Any], language_code: str) -> List[Dict[str, Any]]:
        """
        Process a single entry with multiple turns into training examples

        Each turn becomes a separate training example
        """
        examples = []

        # Get base information
        base_prompt = entry.get('base_prompt', '')
        turns = entry.get('turns', [])

        for turn in turns:
            # Create a training example for this turn
            turn_content = turn.get('content', turn.get('original_content', ''))

            if not turn_content:
                continue

            # Create message format for this single turn
            example = {
                'messages': [
                    {
                        'role': 'user',
                        'content': turn_content
                    },
                    {
                        'role': 'assistant',
                        'content': self.refusal_message
                    }
                ],
                'metadata': {
                    'language': language_code,
                    'base_prompt': base_prompt,
                    'turn_number': turn.get('turn_number', 0),
                    'source': entry.get('source', 'MHJ'),
                    'turn_type': entry.get('turn_type', 'multi')
                }
            }

            examples.append(example)
            self.stats[f'{language_code}_turns'] += 1

        return examples

    def process_multi_turn_entry(self, entry: Dict[str, Any], language_code: str) -> Dict[str, Any]:
        """
        Process entry as multi-turn conversation (alternative format)
        All turns in sequence with refusals
        """
        messages = []
        base_prompt = entry.get('base_prompt', '')
        turns = entry.get('turns', [])

        # Build multi-turn conversation
        for turn in turns:
            turn_content = turn.get('content', turn.get('original_content', ''))

            if turn_content:
                messages.extend([
                    {'role': 'user', 'content': turn_content},
                    {'role': 'assistant', 'content': self.refusal_message}
                ])

        if not messages:
            return None

        return {
            'messages': messages,
            'metadata': {
                'language': language_code,
                'base_prompt': base_prompt,
                'num_turns': len(turns),
                'source': entry.get('source', 'MHJ'),
                'turn_type': 'multi_turn_conversation'
            }
        }

    def process_dataset_file(self, filepath: str, format_type: str = 'single_turn') -> List[Dict[str, Any]]:
        """
        Process a single dataset file

        Args:
            filepath: Path to JSON dataset file
            format_type: 'single_turn' or 'multi_turn'
        """
        # Extract language code from filename
        filename = os.path.basename(filepath)
        # Format: mhj_dataset_<language_code>.json
        if '_' in filename:
            parts = filename.replace('.json', '').split('_')
            if len(parts) >= 3:
                language_code = '_'.join(parts[2:])  # Handle codes like kor_Hang
            else:
                language_code = 'unknown'
        else:
            language_code = 'unknown'

        print(f"Processing {filename} (Language: {language_code})")

        with open(filepath, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        all_examples = []

        for entry in dataset:
            if format_type == 'single_turn':
                # Each turn becomes separate example
                examples = self.process_single_entry(entry, language_code)
                all_examples.extend(examples)
            else:
                # All turns in one conversation
                example = self.process_multi_turn_entry(entry, language_code)
                if example:
                    all_examples.append(example)

            self.stats[f'{language_code}_entries'] += 1

        return all_examples

    def process_all_datasets(self, format_type: str = 'single_turn') -> Dict[str, List[Dict[str, Any]]]:
        """
        Process all dataset files in source directory

        Returns:
            Dictionary mapping language codes to processed examples
        """
        # Find all dataset files
        pattern = os.path.join(self.source_dir, "mhj_dataset_*.json")
        dataset_files = glob(pattern)

        # Exclude partial files
        dataset_files = [f for f in dataset_files if '_part' not in f]

        print(f"Found {len(dataset_files)} dataset files")

        all_datasets = {}

        for filepath in sorted(dataset_files):
            examples = self.process_dataset_file(filepath, format_type)

            # Extract language code
            filename = os.path.basename(filepath)
            lang_code = filename.replace('mhj_dataset_', '').replace('.json', '')

            all_datasets[lang_code] = examples
            print(f"  {lang_code}: {len(examples)} examples")

        return all_datasets

    def create_combined_dataset(self,
                              all_datasets: Dict[str, List[Dict[str, Any]]],
                              train_ratio: float = 0.9) -> Dict[str, List[Dict[str, Any]]]:
        """
        Combine all languages into single train/test split
        """
        # Combine all examples
        all_examples = []
        for lang_code, examples in all_datasets.items():
            all_examples.extend(examples)

        # Shuffle
        random.seed(42)
        random.shuffle(all_examples)

        # Split
        split_idx = int(len(all_examples) * train_ratio)
        train_examples = all_examples[:split_idx]
        test_examples = all_examples[split_idx:]

        print(f"\nCombined dataset:")
        print(f"  Total examples: {len(all_examples)}")
        print(f"  Train: {len(train_examples)}")
        print(f"  Test: {len(test_examples)}")

        return {
            'train': train_examples,
            'test': test_examples
        }

    def save_datasets(self, datasets: Dict[str, List[Dict[str, Any]]], prefix: str = "safety"):
        """
        Save datasets in multiple formats
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save each split
        for split_name, examples in datasets.items():
            # Standard format with metadata
            output_file = os.path.join(
                self.output_dir,
                f"{prefix}_finetuning_{split_name}_{timestamp}.json"
            )

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(examples, f, indent=2, ensure_ascii=False)

            print(f"Saved {split_name}: {output_file}")

            # Also save without metadata (cleaner for training)
            clean_examples = []
            for ex in examples:
                clean_ex = {'messages': ex['messages']}
                clean_examples.append(clean_ex)

            clean_output_file = os.path.join(
                self.output_dir,
                f"{prefix}_finetuning_{split_name}_clean_{timestamp}.json"
            )

            with open(clean_output_file, 'w', encoding='utf-8') as f:
                json.dump(clean_examples, f, indent=2, ensure_ascii=False)

            print(f"Saved clean {split_name}: {clean_output_file}")

        # Save as JSONL format (common for fine-tuning)
        for split_name, examples in datasets.items():
            jsonl_file = os.path.join(
                self.output_dir,
                f"{prefix}_finetuning_{split_name}_{timestamp}.jsonl"
            )

            with open(jsonl_file, 'w', encoding='utf-8') as f:
                for ex in examples:
                    f.write(json.dumps({'messages': ex['messages']}, ensure_ascii=False) + '\n')

            print(f"Saved JSONL {split_name}: {jsonl_file}")

    def print_statistics(self):
        """Print processing statistics"""
        print("\n" + "="*60)
        print("PROCESSING STATISTICS")
        print("="*60)

        # Language statistics
        languages = set()
        for key in self.stats.keys():
            if '_' in key:
                lang = key.split('_')[0]
                languages.add(lang)

        for lang in sorted(languages):
            entries = self.stats.get(f'{lang}_entries', 0)
            turns = self.stats.get(f'{lang}_turns', 0)
            if entries > 0:
                print(f"{lang:15} - Entries: {entries:5}, Turns: {turns:5}, Avg: {turns/entries:.1f}")

        total_turns = sum(v for k, v in self.stats.items() if '_turns' in k)
        print(f"\nTotal training examples: {total_turns}")

    def run(self, format_type: str = 'single_turn'):
        """
        Run the complete preprocessing pipeline

        Args:
            format_type: 'single_turn' (each turn separate) or 'multi_turn' (conversation)
        """
        print("="*60)
        print("FINE-TUNING DATASET PREPARATION")
        print(f"Format: {format_type}")
        print("="*60 + "\n")

        # Process all datasets
        all_datasets = self.process_all_datasets(format_type)

        if not all_datasets:
            print("No datasets found!")
            return

        # Create combined dataset
        combined = self.create_combined_dataset(all_datasets)

        # Save datasets
        self.save_datasets(combined, prefix=f"safety_{format_type}")

        # Save per-language datasets too
        for lang_code, examples in all_datasets.items():
            if examples:
                lang_split = {
                    'train': examples[:int(len(examples)*0.9)],
                    'test': examples[int(len(examples)*0.9):]
                }
                self.save_datasets(lang_split, prefix=f"safety_{lang_code}")

        # Print statistics
        self.print_statistics()

        print("\n✅ Dataset preparation complete!")

def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Prepare fine-tuning datasets')
    parser.add_argument('--source-dir', default='multilingual_datasets',
                       help='Directory containing translated datasets')
    parser.add_argument('--output-dir', default='finetuning_datasets',
                       help='Output directory for fine-tuning datasets')
    parser.add_argument('--format', choices=['single_turn', 'multi_turn'],
                       default='single_turn',
                       help='Format type: single_turn or multi_turn')
    parser.add_argument('--refusal', default="I cannot assist with that request.",
                       help='Refusal message to use')

    args = parser.parse_args()

    preparer = FinetuningDatasetPreparer(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        refusal_message=args.refusal
    )

    preparer.run(format_type=args.format)

if __name__ == "__main__":
    main()