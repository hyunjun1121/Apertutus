#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "ULTRA MINIMAL 8B TRAINING (< 3GB VRAM)"
echo "For heavily occupied GPUs"
echo "=========================================="

echo -e "\n[GPU Status]"
nvidia-smi --query-gpu=index,memory.free --format=csv
echo ""
echo "Using GPU ${CUDA_VISIBLE_DEVICES:-4}"

cat > ultra_minimal_8b_${TIMESTAMP}.yaml << EOF
# Ultra minimal config for < 3GB VRAM
model_name_or_path: swiss-ai/Apertus-8B-Instruct-2509
dtype: float16
load_in_4bit: true  # 4-bit quantization (even more aggressive)
bnb_4bit_compute_dtype: float16
bnb_4bit_use_double_quant: true

# Minimal dataset
dataset_name: tatsu-lab/alpaca
dataset_num_proc: 1
max_samples: 50  # Very few samples for testing

# Minimal training
learning_rate: 2.0e-4
gradient_checkpointing: true
num_train_epochs: 1
per_device_train_batch_size: 1
gradient_accumulation_steps: 1
max_grad_norm: 0.3

# Real-time logging
logging_steps: 1
logging_first_step: true

# Ultra minimal LoRA
use_peft: true
lora_r: 2  # Minimum rank
lora_alpha: 4
lora_dropout: 0.1
lora_target_modules: ["q_proj"]  # Only one module

# Very short sequences
max_length: 64  # Very short
packing: false

# Memory optimizations
optim: adafactor
fp16: true
dataloader_num_workers: 0
dataloader_pin_memory: false

# Output
output_dir: ./ultra_minimal_8b_${TIMESTAMP}
report_to: "none"
save_strategy: "no"  # No checkpointing
seed: 42
EOF

echo -e "\n[Installing bitsandbytes for 4-bit quantization...]"
pip3 install -q bitsandbytes accelerate

echo -e "\n[Starting ultra minimal training...]"
cd apertus-finetuning-recipes

python3 -u sft_train.py --config ../ultra_minimal_8b_${TIMESTAMP}.yaml 2>&1 | \
    grep -E "step|loss|epoch|%|Downloading" --line-buffered | \
    while IFS= read -r line; do
        echo -e "\033[1;32m$(date +%H:%M:%S)\033[0m $line"
    done

cd ..

echo "=========================================="
echo "Completed! Check ./ultra_minimal_8b_${TIMESTAMP}"
echo "=========================================="