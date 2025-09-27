"""
Split dataset into train/test for proper evaluation
Train: 80% for fine-tuning
Test: 20% for final evaluation (never seen during training)
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple
import shutil

def split_dataset(input_dir: str = "multilingual_datasets_filtered",
                  output_dir: str = "experiment_datasets",
                  train_ratio: float = 0.8,
                  seed: int = 42):
    """
    Split each language dataset into train/test sets

    Args:
        input_dir: Directory with filtered datasets
        output_dir: Output directory for split datasets
        train_ratio: Ratio for training data (0.8 = 80%)
        seed: Random seed for reproducibility
    """

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directories
    train_dir = output_path / "train"
    test_dir = output_path / "test"
    train_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    # Set seed for reproducibility
    random.seed(seed)

    # Find all language files
    language_files = list(input_path.glob("mhj_dataset_*.json"))

    print(f"Found {len(language_files)} language datasets")
    print("=" * 60)

    stats = {
        "languages": [],
        "total_train": 0,
        "total_test": 0,
        "splits": {}
    }

    for filepath in language_files:
        language = filepath.stem.split('_')[2]
        print(f"Processing {language}...")

        # Load data
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Shuffle data
        shuffled_data = data.copy()
        random.shuffle(shuffled_data)

        # Split
        split_idx = int(len(shuffled_data) * train_ratio)
        train_data = shuffled_data[:split_idx]
        test_data = shuffled_data[split_idx:]

        # Save train data
        train_file = train_dir / f"mhj_dataset_{language}_train.json"
        with open(train_file, 'w', encoding='utf-8') as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)

        # Save test data
        test_file = test_dir / f"mhj_dataset_{language}_test.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        # Update statistics
        stats["languages"].append(language)
        stats["total_train"] += len(train_data)
        stats["total_test"] += len(test_data)
        stats["splits"][language] = {
            "train": len(train_data),
            "test": len(test_data),
            "total": len(data)
        }

        print(f"  - Total: {len(data)} entries")
        print(f"  - Train: {len(train_data)} entries ({len(train_data)/len(data)*100:.1f}%)")
        print(f"  - Test: {len(test_data)} entries ({len(test_data)/len(data)*100:.1f}%)")

    # Save split information
    split_info_file = output_path / "split_info.json"
    with open(split_info_file, 'w', encoding='utf-8') as f:
        json.dump({
            "seed": seed,
            "train_ratio": train_ratio,
            "statistics": stats
        }, f, indent=2)

    print("\n" + "=" * 60)
    print("DATASET SPLIT COMPLETE")
    print("=" * 60)
    print(f"Languages: {len(stats['languages'])}")
    print(f"Total training entries: {stats['total_train']}")
    print(f"Total test entries: {stats['total_test']}")
    print(f"\nOutput directories:")
    print(f"  - Training data: {train_dir}")
    print(f"  - Test data: {test_dir}")
    print(f"  - Split info: {split_info_file}")

    return stats


def prepare_finetuning_from_train_only(train_dir: str = "experiment_datasets/train",
                                       output_dir: str = "finetuning_datasets"):
    """
    Prepare fine-tuning dataset using ONLY training data
    Test data is kept completely separate
    """
    from pathlib import Path
    import json
    import random
    from datetime import datetime

    print("\n" + "=" * 60)
    print("PREPARING FINE-TUNING DATASET FROM TRAIN SPLIT ONLY")
    print("=" * 60)

    train_path = Path(train_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Check if train directory exists
    if not train_path.exists():
        print(f"ERROR: Train directory not found: {train_path}")
        return None

    # Find all train files
    train_files = list(train_path.glob("mhj_dataset_*_train.json"))
    print(f"Found {len(train_files)} training files")

    if len(train_files) == 0:
        print("ERROR: No training files found!")
        print(f"Looking in: {train_path}")
        return None

    # Prepare safety finetuning examples
    all_examples = []

    for filepath in train_files:
        language = filepath.stem.split('_')[2]  # Get language code
        print(f"Processing {language}...")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Fixed refusal message for all languages
        refusal = "I cannot and will not assist with that request."

        # Create training examples
        for entry in data:
            turns = entry.get('turns', [])

            # Single-turn examples
            for turn in turns:
                content = turn.get('content', '')
                if content:
                    example = {
                        "messages": [
                            {"role": "user", "content": content},
                            {"role": "assistant", "content": refusal}
                        ]
                    }
                    all_examples.append(example)

    print(f"\nTotal examples created: {len(all_examples)}")

    # Shuffle and split
    random.seed(42)
    random.shuffle(all_examples)

    # 90/10 train/val split
    split_idx = int(len(all_examples) * 0.9)
    train_examples = all_examples[:split_idx]
    val_examples = all_examples[split_idx:]

    # Save files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    train_file = output_path / f"safety_train_{timestamp}.jsonl"
    val_file = output_path / f"safety_val_{timestamp}.jsonl"

    # Write JSONL files
    with open(train_file, 'w', encoding='utf-8') as f:
        for ex in train_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')

    with open(val_file, 'w', encoding='utf-8') as f:
        for ex in val_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')

    # Save statistics
    stats = {
        "languages": len(train_files),
        "total_examples": len(all_examples),
        "train_examples": len(train_examples),
        "val_examples": len(val_examples),
        "timestamp": timestamp
    }

    stats_file = output_path / f"safety_stats_{timestamp}.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"\nFiles saved:")
    print(f"  - Training: {train_file}")
    print(f"  - Validation: {val_file}")
    print(f"  - Statistics: {stats_file}")

    result = {
        "train_file": str(train_file),
        "val_file": str(val_file),
        "stats": stats
    }

    print("\nIMPORTANT: Test data in 'experiment_datasets/test/' is NOT used for training!")
    print("This ensures unbiased evaluation.")

    return result


def verify_no_overlap():
    """
    Verify that test data doesn't appear in training data
    """
    train_dir = Path("experiment_datasets/train")
    test_dir = Path("experiment_datasets/test")

    print("\n" + "=" * 60)
    print("VERIFYING TRAIN/TEST SEPARATION")
    print("=" * 60)

    for test_file in test_dir.glob("*.json"):
        language = test_file.stem.split('_')[2]
        train_file = train_dir / f"mhj_dataset_{language}_train.json"

        with open(test_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        with open(train_file, 'r', encoding='utf-8') as f:
            train_data = json.load(f)

        # Check for overlaps (using entry_index)
        test_indices = {entry.get('entry_index', -1) for entry in test_data}
        train_indices = {entry.get('entry_index', -1) for entry in train_data}

        overlap = test_indices & train_indices

        if overlap:
            print(f"❌ {language}: Found {len(overlap)} overlapping entries!")
        else:
            print(f"✅ {language}: No overlap (train: {len(train_data)}, test: {len(test_data)})")

    print("\nVerification complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--action', choices=['split', 'prepare', 'verify'],
                       default='split',
                       help='Action to perform')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for splitting')

    args = parser.parse_args()

    if args.action == 'split':
        # Step 1: Split datasets
        split_dataset(seed=args.seed)

    elif args.action == 'prepare':
        # Step 2: Prepare fine-tuning data from train split only
        prepare_finetuning_from_train_only()

    elif args.action == 'verify':
        # Step 3: Verify no overlap
        verify_no_overlap()

    print("\nNext steps:")
    print("1. Run fine-tuning with 'experiment_datasets/train/' data")
    print("2. Evaluate BOTH models on 'experiment_datasets/test/' data")
    print("3. Compare results with StrongReject")