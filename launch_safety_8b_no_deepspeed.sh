#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "APERTUS 8B SAFETY FINE-TUNING (NO DEEPSPEED)"
echo "Avoiding DeepSpeed dependency issues"
echo "Date: $(date)"
echo "=========================================="

# Create config for 8B model
cat > safety_lora_8b_simple.yaml << EOF
# Model - 8B version (much smaller)
model_name_or_path: swiss-ai/Apertus-8B-Instruct-2509
attn_implementation: eager  # Avoid flash attention issues
dtype: bfloat16

# Dataset
dataset_name: HuggingFaceH4/Multilingual-Thinking
dataset_num_proc: 4

# Hyperparameters
learning_rate: 2.0e-4
gradient_checkpointing: true
num_train_epochs: 1
logging_steps: 10
per_device_train_batch_size: 1
gradient_accumulation_steps: 8

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

# Output & logging
output_dir: ./safety_lora_8b_simple_${TIMESTAMP}
report_to: "none"
seed: 42
save_strategy: steps
save_steps: 100
save_total_limit: 2
EOF

echo "Created config: safety_lora_8b_simple.yaml"

echo -e "\n[Step 1] Checking environment (without DeepSpeed)..."
python3 -c "
import torch
print(f'PyTorch: {torch.__version__}')
import transformers
print(f'Transformers: {transformers.__version__}')
import peft
print(f'PEFT: {peft.__version__}')
import trl
print(f'TRL: {trl.__version__}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
"

echo -e "\n[Step 2] Running WITHOUT DeepSpeed (single GPU)..."
cd apertus-finetuning-recipes

# Use Python directly, not accelerate with DeepSpeed
CUDA_VISIBLE_DEVICES=0 python sft_train.py --config ../safety_lora_8b_simple.yaml

cd ..

echo "=========================================="
echo "8B fine-tuning complete (no DeepSpeed)!"
echo "LoRA adapter saved to: ./safety_lora_8b_simple_${TIMESTAMP}"
echo "=========================================="