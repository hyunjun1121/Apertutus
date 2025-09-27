#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "APERTUS SAFETY LORA FINE-TUNING (FINAL FIXED)"
echo "Date: $(date)"
echo "=========================================="

# Create FIXED config
cat > safety_lora_config_fixed.yaml << EOF
# Model
model_name_or_path: swiss-ai/Apertus-70B-Instruct-2509  # Using 70B model
attn_implementation: eager  # Avoid flash attention issues
dtype: bfloat16

# Dataset
dataset_name: HuggingFaceH4/Multilingual-Thinking
dataset_num_proc: 12

# Hyperparameters
learning_rate: 2.0e-4
gradient_checkpointing: true
num_train_epochs: 1
logging_steps: 10
per_device_train_batch_size: 1  # Reduced for 70B model
gradient_accumulation_steps: 4

# LoRA Configuration
use_peft: true
lora_r: 8
lora_alpha: 16
lora_dropout: 0.05
lora_target_modules: all-linear

# Sequence length
max_length: 512

# Learning rate scheduler
warmup_ratio: 0.1
lr_scheduler_type: cosine

# Output & logging - FIXED: Removed conflicting options
output_dir: ./safety_lora_fixed_${TIMESTAMP}
report_to: "none"
seed: 42
save_strategy: steps
save_steps: 100
save_total_limit: 2
# Removed: load_best_model_at_end (causes conflict)
# Removed: evaluation_strategy (not needed without eval dataset)
# Removed: eval_steps (not needed without eval dataset)
EOF

echo "Created fixed config: safety_lora_config_fixed.yaml"

echo -e "\n[Step 1] Entering apertus-finetuning-recipes directory..."
cd apertus-finetuning-recipes

echo -e "\n[Step 2] Starting fine-tuning with FIXED config..."
echo "Using 70B model - requires ~140GB disk space and multiple GPUs"

# Use accelerate with zero3 config
accelerate launch \
    --config_file configs/zero3.yaml \
    sft_train.py \
    --config ../safety_lora_config_fixed.yaml

cd ..

echo "=========================================="
echo "Fine-tuning completed successfully!"
echo "LoRA adapter saved to: ./safety_lora_fixed_${TIMESTAMP}"
echo "=========================================="