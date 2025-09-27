#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "APERTUS SAFETY LORA FINE-TUNING (CORRECTED)"
echo "Date: $(date)"
echo "=========================================="

# Create corrected config with proper model name
cat > safety_lora_config_corrected.yaml << EOF
# Model - CORRECTED MODEL NAME
model_name_or_path: swiss-ai/Apertus-70B-Instruct-2509  # Fixed: added -Instruct-2509
attn_implementation: flash-attention-3
dtype: bfloat16

# Dataset
dataset_name: HuggingFaceH4/Multilingual-Thinking  # Using existing dataset for testing
dataset_train_split: train
dataset_test_split: validation
dataset_num_proc: 12

# Hyperparameters for safety fine-tuning
learning_rate: 1.0e-4
gradient_checkpointing: true
num_train_epochs: 1
logging_steps: 10
per_device_train_batch_size: 1  # Very small for 70B model
gradient_accumulation_steps: 16

# LoRA Configuration
use_peft: true
lora_r: 16
lora_alpha: 32
lora_dropout: 0.1
lora_target_modules: all-linear

# Sequence length
max_length: 512

# Learning rate scheduler
warmup_ratio: 0.1
lr_scheduler_type: cosine_with_min_lr
lr_scheduler_kwargs:
  min_lr_rate: 0.1

# Output & logging
output_dir: ./safety_lora_adapter_${TIMESTAMP}
report_to: "none"
seed: 42
save_strategy: steps
save_steps: 500
evaluation_strategy: steps
eval_steps: 100
save_total_limit: 3
load_best_model_at_end: true
EOF

echo "Created corrected config: safety_lora_config_corrected.yaml"

echo -e "\n[Step 1] Entering apertus-finetuning-recipes directory..."
cd apertus-finetuning-recipes

echo -e "\n[Step 2] Starting fine-tuning with CORRECTED model name..."
echo "Using model: swiss-ai/Apertus-70B-Instruct-2509"
echo ""
echo "WARNING: 70B model requires:"
echo "  - ~140GB disk space"
echo "  - Multiple high-VRAM GPUs"
echo "  - Significant download time on first run"
echo ""
echo "For testing, consider using 8B model instead:"
echo "  model_name_or_path: swiss-ai/Apertus-8B-Instruct-2509"
echo ""

accelerate launch \
    --config_file configs/zero3.yaml \
    sft_train.py \
    --config ../safety_lora_config_corrected.yaml

cd ..

echo "=========================================="
echo "Fine-tuning complete!"
echo "LoRA adapter saved to: ./safety_lora_adapter_${TIMESTAMP}"
echo "=========================================="