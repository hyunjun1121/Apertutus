#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "APERTUS SAFETY LORA - SINGLE GPU (No DeepSpeed)"
echo "Date: $(date)"
echo "=========================================="

# Create config for single GPU without DeepSpeed
cat > safety_lora_single_gpu.yaml << EOF
# Model - Using 8B for single GPU
model_name_or_path: swiss-ai/Apertus-8B-Instruct-2509
attn_implementation: flash-attention-3
dtype: bfloat16

# Dataset
dataset_name: HuggingFaceH4/Multilingual-Thinking
dataset_num_proc: 8

# Hyperparameters
learning_rate: 2.0e-4
gradient_checkpointing: true
num_train_epochs: 1
logging_steps: 10
per_device_train_batch_size: 2
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
lr_scheduler_type: cosine_with_min_lr
lr_scheduler_kwargs:
  min_lr_rate: 0.1

# Output & logging
output_dir: ./safety_lora_single_gpu_${TIMESTAMP}
report_to: "none"
seed: 42
save_strategy: steps
save_steps: 100
save_total_limit: 2
EOF

echo "Created config: safety_lora_single_gpu.yaml"

echo -e "\n[Step 1] Checking GPU..."
python3 -c "
import torch
if torch.cuda.is_available():
    print(f'GPU available: {torch.cuda.get_device_name(0)}')
    print(f'GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
else:
    print('WARNING: No GPU detected!')
"

echo -e "\n[Step 2] Entering apertus-finetuning-recipes directory..."
cd apertus-finetuning-recipes

echo -e "\n[Step 3] Starting SINGLE GPU training (no DeepSpeed)..."
echo "This does NOT require DeepSpeed installation"

# Run directly with Python, not accelerate
python sft_train.py --config ../safety_lora_single_gpu.yaml

cd ..

echo "=========================================="
echo "Single GPU fine-tuning complete!"
echo "LoRA adapter saved to: ./safety_lora_single_gpu_${TIMESTAMP}"
echo "=========================================="