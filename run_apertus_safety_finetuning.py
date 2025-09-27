#!/usr/bin/env python3
"""
Fine-tune Apertus-70B for multilingual safety using LoRA
Based on apertus-finetuning-recipes
"""

import json
import os
from pathlib import Path
from datasets import Dataset, DatasetDict
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import (
    ModelConfig,
    ScriptArguments,
    SFTConfig,
    SFTTrainer,
    TrlParser,
    get_peft_config,
)
import argparse
from datetime import datetime

def load_jsonl_to_dataset(file_path):
    """Load JSONL file into HuggingFace dataset format"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            # Convert messages to text format
            text = ""
            for msg in entry['messages']:
                if msg['role'] == 'user':
                    text += f"User: {msg['content']}\n"
                elif msg['role'] == 'assistant':
                    text += f"Assistant: {msg['content']}\n"
            data.append({"text": text.strip()})

    return Dataset.from_list(data)

def main():
    # Find the latest dataset files
    from pathlib import Path
    finetuning_dir = Path('finetuning_datasets')

    # Get latest train and val files
    train_files = sorted(finetuning_dir.glob('safety_train_*.jsonl'))
    val_files = sorted(finetuning_dir.glob('safety_val_*.jsonl'))

    if not train_files or not val_files:
        print("ERROR: No training or validation files found in finetuning_datasets/")
        print("Please run dataset preparation first.")
        return

    latest_train = str(train_files[-1])
    latest_val = str(val_files[-1])

    parser = argparse.ArgumentParser()
    parser.add_argument('--train_file', type=str,
                       default=latest_train,
                       help='Path to training JSONL file')
    parser.add_argument('--val_file', type=str,
                       default=latest_val,
                       help='Path to validation JSONL file')
    parser.add_argument('--model_name', type=str,
                       default='swiss-ai/Apertus-70B',
                       help='Model to fine-tune')
    parser.add_argument('--output_dir', type=str,
                       default='./safety_lora_adapter',
                       help='Output directory for LoRA adapter')
    parser.add_argument('--config_file', type=str,
                       default='apertus-finetuning-recipes/configs/sft_lora.yaml',
                       help='Config file path')

    args = parser.parse_args()

    print("=" * 60)
    print("APERTUS SAFETY FINE-TUNING WITH LORA")
    print("=" * 60)
    print(f"Model: {args.model_name}")
    print(f"Training data: {args.train_file}")
    print(f"Validation data: {args.val_file}")
    print(f"Output: {args.output_dir}")
    print("=" * 60)

    # Load datasets
    print("\nLoading datasets...")
    train_dataset = load_jsonl_to_dataset(args.train_file)
    val_dataset = load_jsonl_to_dataset(args.val_file)

    print(f"Training examples: {len(train_dataset)}")
    print(f"Validation examples: {len(val_dataset)}")

    # Create dataset dict
    dataset = DatasetDict({
        'train': train_dataset,
        'validation': val_dataset
    })

    # Save dataset for future use
    dataset_path = "safety_dataset_for_training"
    dataset.save_to_disk(dataset_path)
    print(f"\nDataset saved to: {dataset_path}")

    # Generate training script
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{args.output_dir}_{timestamp}"

    # Create custom config file
    custom_config = f"""# Model
model_name_or_path: {args.model_name}
attn_implementation: flash-attention-3
dtype: bfloat16

# Dataset
dataset_name: {dataset_path}
dataset_train_split: train
dataset_test_split: validation
dataset_num_proc: 12

# Hyperparameters for safety fine-tuning
learning_rate: 1.0e-4  # Lower LR for safety fine-tuning
gradient_checkpointing: true
num_train_epochs: 2  # More epochs for safety
logging_steps: 10
per_device_train_batch_size: 2  # Smaller batch for 70B model
gradient_accumulation_steps: 8  # Effective batch size = 16

# LoRA Configuration
use_peft: true
lora_r: 16  # Higher rank for complex safety patterns
lora_alpha: 32
lora_dropout: 0.1
lora_target_modules: all-linear

# Sequence length
max_length: 512  # Shorter for safety responses

# Learning rate scheduler
warmup_ratio: 0.1
lr_scheduler_type: cosine_with_min_lr
lr_scheduler_kwargs:
  min_lr_rate: 0.1

# Output & logging
output_dir: {output_dir}
report_to: "none"
seed: 42
save_strategy: steps
save_steps: 500
evaluation_strategy: steps
eval_steps: 100
save_total_limit: 3
load_best_model_at_end: true
"""

    config_path = f"safety_lora_config_{timestamp}.yaml"
    with open(config_path, 'w') as f:
        f.write(custom_config)

    print(f"\nConfig saved to: {config_path}")

    # Generate the launch command
    launch_script = f"""#!/bin/bash

echo "=========================================="
echo "APERTUS SAFETY LORA FINE-TUNING"
echo "Date: $(date)"
echo "=========================================="

# Using the apertus-finetuning-recipes framework
cd apertus-finetuning-recipes

accelerate launch \\
    --config_file configs/zero3.yaml \\
    sft_train.py \\
    --config ../{config_path} \\
    --model_name_or_path {args.model_name}

cd ..

echo "=========================================="
echo "Fine-tuning complete!"
echo "LoRA adapter saved to: {output_dir}"
echo "=========================================="
"""

    launch_script_path = f"launch_safety_finetuning_{timestamp}.sh"
    with open(launch_script_path, 'w') as f:
        f.write(launch_script)

    os.chmod(launch_script_path, 0o755)

    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print(f"\nTo start fine-tuning, run:")
    print(f"  ./{launch_script_path}")
    print("\nOr manually run:")
    print(f"  cd apertus-finetuning-recipes")
    print(f"  accelerate launch --config_file configs/zero3.yaml sft_train.py --config ../{config_path}")

    return output_dir

if __name__ == "__main__":
    main()