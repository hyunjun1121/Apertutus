"""
Prepare safety fine-tuning dataset from filtered multilingual datasets
Uses StrongReject results to create high-quality refusal training data
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import random
import argparse

class SafetyFinetuningPreparer:
    def __init__(self,
                 source_dir: str = "multilingual_datasets_filtered",
                 response_dir: str = "llm_responses",
                 output_dir: str = "finetuning_datasets"):
        """
        Initialize dataset preparer

        Args:
            source_dir: Directory containing filtered translated datasets
            response_dir: Directory containing LLM responses
            output_dir: Directory to save fine-tuning datasets
        """
        self.source_dir = Path(source_dir)
        self.response_dir = Path(response_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Language-specific refusal templates
        self.refusal_templates = {
            "kor.Hang": [
                "죄송하지만, 그런 요청은 도와드릴 수 없습니다.",
                "그러한 내용에 대해서는 안내해 드릴 수 없습니다.",
                "위험하거나 해로운 정보는 제공할 수 없습니다."
            ],
            "cmn.Hani": [
                "抱歉，我不能协助处理这个请求。",
                "我无法提供这类信息。",
                "这种内容可能有害，我不能帮助。"
            ],
            "jpn.Jpan": [
                "申し訳ありませんが、そのようなリクエストにはお応えできません。",
                "その種の情報は提供できません。",
                "危険な内容についてはお手伝いできません。"
            ],
            "default": [
                "I cannot and will not provide assistance with that request.",
                "I'm not able to help with harmful or dangerous content.",
                "That request goes against safety guidelines."
            ]
        }

    def get_refusal_message(self, language: str) -> str:
        """Get appropriate refusal message for language"""
        templates = self.refusal_templates.get(language, self.refusal_templates["default"])
        return random.choice(templates)

    def create_single_turn_example(self, content: str, language: str, metadata: Dict) -> Dict:
        """Create a single-turn training example"""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": content
                },
                {
                    "role": "assistant",
                    "content": self.get_refusal_message(language)
                }
            ],
            "metadata": {
                "language": language,
                "type": "single_turn_refusal",
                **metadata
            }
        }

    def create_multi_turn_example(self, turns: List[Dict], language: str, metadata: Dict) -> Dict:
        """Create a multi-turn conversation example"""
        messages = []

        for idx, turn in enumerate(turns):
            content = turn.get('content', '')
            if not content:
                continue

            # User message
            messages.append({
                "role": "user",
                "content": content
            })

            # Assistant refusal
            messages.append({
                "role": "assistant",
                "content": self.get_refusal_message(language)
            })

        return {
            "messages": messages,
            "metadata": {
                "language": language,
                "type": "multi_turn_refusal",
                "num_turns": len(turns),
                **metadata
            }
        }

    def process_language(self, language: str) -> Dict:
        """Process a single language dataset"""
        input_file = self.source_dir / f"mhj_dataset_{language}.json"

        if not input_file.exists():
            print(f"Warning: {input_file} not found")
            return {"error": f"File not found: {input_file}"}

        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        single_turn_examples = []
        multi_turn_examples = []

        for entry_idx, entry in enumerate(data):
            turns = entry.get('turns', [])

            # Create metadata
            metadata = {
                "source": "MHJ",
                "entry_index": entry.get('entry_index', entry_idx),
                "base_prompt": turns[0].get('content', '') if turns else ""
            }

            # Create single-turn examples (each turn separately)
            for turn in turns:
                content = turn.get('content', '')
                if content:
                    example = self.create_single_turn_example(
                        content, language,
                        {**metadata, "turn_number": turn.get('turn_number', 0)}
                    )
                    single_turn_examples.append(example)

            # Create multi-turn example (full conversation)
            if len(turns) > 1:
                example = self.create_multi_turn_example(turns, language, metadata)
                multi_turn_examples.append(example)

        return {
            "language": language,
            "single_turn": single_turn_examples,
            "multi_turn": multi_turn_examples,
            "stats": {
                "total_entries": len(data),
                "single_turn_examples": len(single_turn_examples),
                "multi_turn_examples": len(multi_turn_examples)
            }
        }

    def prepare_all_languages(self, train_split: float = 0.9) -> Dict:
        """Prepare datasets for all available languages"""

        # Find all language files
        language_files = list(self.source_dir.glob("mhj_dataset_*.json"))
        languages = [f.stem.split('_')[2] for f in language_files]

        print(f"Found {len(languages)} languages to process")

        all_single_turn = []
        all_multi_turn = []
        stats = {}

        for language in languages:
            print(f"Processing {language}...")
            result = self.process_language(language)

            if "error" not in result:
                all_single_turn.extend(result["single_turn"])
                all_multi_turn.extend(result["multi_turn"])
                stats[language] = result["stats"]

        # Shuffle data
        random.shuffle(all_single_turn)
        random.shuffle(all_multi_turn)

        # Split into train/validation
        split_idx_single = int(len(all_single_turn) * train_split)
        split_idx_multi = int(len(all_multi_turn) * train_split)

        train_data = {
            "single_turn": all_single_turn[:split_idx_single],
            "multi_turn": all_multi_turn[:split_idx_multi]
        }

        val_data = {
            "single_turn": all_single_turn[split_idx_single:],
            "multi_turn": all_multi_turn[split_idx_multi:]
        }

        # Save datasets
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Combined dataset
        combined_train = train_data["single_turn"] + train_data["multi_turn"]
        combined_val = val_data["single_turn"] + val_data["multi_turn"]

        train_file = self.output_dir / f"safety_train_{timestamp}.jsonl"
        val_file = self.output_dir / f"safety_val_{timestamp}.jsonl"

        # Save as JSONL (one JSON per line)
        with open(train_file, 'w', encoding='utf-8') as f:
            for example in combined_train:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')

        with open(val_file, 'w', encoding='utf-8') as f:
            for example in combined_val:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')

        # Save statistics
        stats_file = self.output_dir / f"safety_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                "languages": list(stats.keys()),
                "language_stats": stats,
                "total_train": len(combined_train),
                "total_val": len(combined_val),
                "train_single_turn": len(train_data["single_turn"]),
                "train_multi_turn": len(train_data["multi_turn"]),
                "val_single_turn": len(val_data["single_turn"]),
                "val_multi_turn": len(val_data["multi_turn"]),
                "timestamp": timestamp
            }, f, ensure_ascii=False, indent=2)

        print("\n" + "="*60)
        print("FINE-TUNING DATASET PREPARED")
        print("="*60)
        print(f"Languages: {len(stats)}")
        print(f"Total training examples: {len(combined_train)}")
        print(f"  - Single-turn: {len(train_data['single_turn'])}")
        print(f"  - Multi-turn: {len(train_data['multi_turn'])}")
        print(f"Total validation examples: {len(combined_val)}")
        print(f"  - Single-turn: {len(val_data['single_turn'])}")
        print(f"  - Multi-turn: {len(val_data['multi_turn'])}")
        print(f"\nFiles saved:")
        print(f"  - Training: {train_file}")
        print(f"  - Validation: {val_file}")
        print(f"  - Statistics: {stats_file}")

        return {
            "train_file": str(train_file),
            "val_file": str(val_file),
            "stats_file": str(stats_file),
            "stats": stats
        }


def main():
    parser = argparse.ArgumentParser(description='Prepare safety fine-tuning dataset')
    parser.add_argument('--source-dir', type=str, default='multilingual_datasets_filtered',
                       help='Directory containing filtered datasets')
    parser.add_argument('--output-dir', type=str, default='finetuning_datasets',
                       help='Output directory for fine-tuning datasets')
    parser.add_argument('--train-split', type=float, default=0.9,
                       help='Train/validation split ratio')

    args = parser.parse_args()

    preparer = SafetyFinetuningPreparer(
        source_dir=args.source_dir,
        output_dir=args.output_dir
    )

    result = preparer.prepare_all_languages(train_split=args.train_split)

    # Save result summary
    with open('finetuning_preparation_result.json', 'w') as f:
        json.dump(result, f, indent=2)

    print("\nReady for fine-tuning!")
    print("Use the generated JSONL files with your fine-tuning script.")

if __name__ == "__main__":
    main()