#!/usr/bin/env python3
"""
LoRA Fine-tuning for Apertus-70B Safety
Using HuggingFace PEFT and Swiss AI API
"""

import json
import torch
from pathlib import Path
import argparse
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    prepare_model_for_kbit_training
)
from datasets import Dataset
import os
from datetime import datetime

def load_jsonl_dataset(file_path):
    """Load JSONL file into dataset"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def format_messages_for_training(example):
    """Format messages into training text"""
    messages = example['messages']

    # Simple format: User: xxx\nAssistant: xxx
    formatted = ""
    for msg in messages:
        if msg['role'] == 'user':
            formatted += f"User: {msg['content']}\n"
        elif msg['role'] == 'assistant':
            formatted += f"Assistant: {msg['content']}\n"

    return {"text": formatted.strip()}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_file', type=str,
                       default='finetuning_datasets/safety_train_20250926_204606.jsonl')
    parser.add_argument('--val_file', type=str,
                       default='finetuning_datasets/safety_val_20250926_204606.jsonl')
    parser.add_argument('--model_name', type=str,
                       default='meta-llama/Llama-2-7b-hf',  # Use smaller model for testing
                       help='Model to fine-tune (use smaller for testing)')
    parser.add_argument('--output_dir', type=str,
                       default='./lora_adapter')
    parser.add_argument('--num_epochs', type=int, default=3)
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--learning_rate', type=float, default=2e-4)
    parser.add_argument('--max_length', type=int, default=512)
    parser.add_argument('--use_8bit', action='store_true',
                       help='Use 8-bit quantization')
    parser.add_argument('--test_mode', action='store_true',
                       help='Test mode with small subset')

    args = parser.parse_args()

    print("=" * 60)
    print("LORA FINE-TUNING FOR SAFETY")
    print("=" * 60)

    # Load datasets
    print("Loading datasets...")
    train_data = load_jsonl_dataset(args.train_file)
    val_data = load_jsonl_dataset(args.val_file)

    if args.test_mode:
        # Use small subset for testing
        train_data = train_data[:100]
        val_data = val_data[:20]
        print(f"TEST MODE: Using {len(train_data)} train, {len(val_data)} val examples")
    else:
        print(f"Loaded {len(train_data)} training examples")
        print(f"Loaded {len(val_data)} validation examples")

    # Convert to HF datasets
    train_dataset = Dataset.from_list(train_data)
    val_dataset = Dataset.from_list(val_data)

    # Format for training
    train_dataset = train_dataset.map(format_messages_for_training)
    val_dataset = val_dataset.map(format_messages_for_training)

    # Load tokenizer and model
    print(f"\nLoading model: {args.model_name}")
    print("Note: For actual Apertus-70B, you'll need to use the Swiss AI API")
    print("This script demonstrates the LoRA setup with a smaller model")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # Load model with quantization if specified
    if args.use_8bit:
        print("Loading model with 8-bit quantization...")
        model = AutoModelForCausalLM.from_pretrained(
            args.model_name,
            load_in_8bit=True,
            device_map="auto",
            torch_dtype=torch.float16,
        )
        model = prepare_model_for_kbit_training(model)
    else:
        model = AutoModelForCausalLM.from_pretrained(
            args.model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )

    # LoRA configuration
    print("\nConfiguring LoRA...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,  # Rank
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # For LLaMA
        bias="none",
    )

    # Apply LoRA
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Tokenize datasets
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=args.max_length,
        )

    print("\nTokenizing datasets...")
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_val = val_dataset.map(tokenize_function, batched=True)

    # Training arguments
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{args.output_dir}_{timestamp}"

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=args.num_epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        warmup_steps=100,
        learning_rate=args.learning_rate,
        logging_steps=10,
        save_steps=500,
        evaluation_strategy="steps",
        eval_steps=100,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=True,
        push_to_hub=False,
        report_to=["none"],  # Disable wandb, tensorboard
    )

    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        tokenizer=tokenizer,
        data_collator=DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,
        ),
    )

    # Train
    print("\n" + "=" * 60)
    print("Starting training...")
    print(f"Output directory: {output_dir}")
    print("=" * 60)

    trainer.train()

    # Save final model
    print("\nSaving LoRA adapter...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Save training info
    info = {
        "model_name": args.model_name,
        "train_file": args.train_file,
        "val_file": args.val_file,
        "num_train_examples": len(train_data),
        "num_val_examples": len(val_data),
        "num_epochs": args.num_epochs,
        "learning_rate": args.learning_rate,
        "lora_r": lora_config.r,
        "lora_alpha": lora_config.lora_alpha,
        "timestamp": timestamp
    }

    with open(f"{output_dir}/training_info.json", "w") as f:
        json.dump(info, f, indent=2)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print(f"LoRA adapter saved to: {output_dir}")
    print(f"To use: Load base model + LoRA weights from {output_dir}")

    return output_dir

if __name__ == "__main__":
    # Note: For Apertus-70B, you'll need different approach:
    # 1. Use Swiss AI's fine-tuning API if available
    # 2. Or use smaller proxy model for testing
    # 3. Or wait for Apertus weights to be released

    print("WARNING: This script uses LLaMA-2-7B as proxy for demonstration")
    print("For actual Apertus-70B fine-tuning, use Swiss AI API")
    print()

    main()