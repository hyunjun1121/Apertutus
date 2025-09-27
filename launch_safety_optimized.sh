#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "APERTUS SAFETY LORA - MEMORY OPTIMIZED"
echo "Date: $(date)"
echo "=========================================="

echo -e "\n[Step 1] Checking GPU status..."
echo "Current GPU usage:"
nvidia-smi --query-gpu=index,name,memory.used,memory.free,memory.total --format=csv
echo ""
echo "Processes using GPU:"
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv

echo -e "\n[Step 2] Killing zombie processes if any..."
# Optional: kill specific PIDs if you know them
# kill -9 1020340 1930496 2>/dev/null || true

echo -e "\n[Step 3] Creating optimized config..."
cat > safety_lora_optimized.yaml << EOF
# Model - Using smaller model with quantization
model_name_or_path: swiss-ai/Apertus-8B-Instruct-2509
torch_dtype: float16  # Use float16 instead of bfloat16
attn_implementation: eager
load_in_8bit: true  # 8-bit quantization to reduce memory

# Dataset
dataset_name: HuggingFaceH4/Multilingual-Thinking
dataset_num_proc: 4
dataset_text_field: messages  # Specify text field

# Training hyperparameters - HEAVILY OPTIMIZED FOR MEMORY
learning_rate: 2.0e-4
gradient_checkpointing: true  # Essential for memory savings
gradient_checkpointing_kwargs:
  use_reentrant: false
num_train_epochs: 1
logging_steps: 50
per_device_train_batch_size: 1  # Minimum batch size
gradient_accumulation_steps: 16  # Effective batch = 16
max_grad_norm: 0.3

# LoRA Configuration - Reduced for memory
use_peft: true
lora_r: 4  # Reduced rank
lora_alpha: 8
lora_dropout: 0.1
lora_target_modules: ["q_proj", "v_proj"]  # Only target specific modules

# Sequence length - Reduced
max_length: 256  # Reduced from 512
packing: false

# Memory optimizations
optim: adamw_torch_fused  # More memory efficient
fp16: true
tf32: false

# Learning rate scheduler
warmup_ratio: 0.1
lr_scheduler_type: cosine

# Output & logging
output_dir: ./safety_lora_optimized_${TIMESTAMP}
report_to: "none"
seed: 42
save_strategy: steps
save_steps: 500
save_total_limit: 1
dataloader_num_workers: 0  # Reduce memory overhead
remove_unused_columns: true
EOF

echo "Created optimized config: safety_lora_optimized.yaml"

echo -e "\n[Step 4] Setting memory optimization environment variables..."
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True,max_split_size_mb:512"
export CUDA_LAUNCH_BLOCKING=1
export OMP_NUM_THREADS=1

echo -e "\n[Step 5] Clearing GPU cache..."
python3 -c "
import torch
import gc
gc.collect()
torch.cuda.empty_cache()
print(f'GPU memory before: {torch.cuda.memory_allocated()/1e9:.2f} GB')
"

echo -e "\n[Step 6] Running with single GPU (no DeepSpeed)..."
cd apertus-finetuning-recipes

# Use only GPU 0, no distributed training
CUDA_VISIBLE_DEVICES=0 python sft_train.py \
    --config ../safety_lora_optimized.yaml \
    2>&1 | tee ../training_log_${TIMESTAMP}.txt

cd ..

echo "=========================================="
echo "Training complete!"
echo "LoRA adapter saved to: ./safety_lora_optimized_${TIMESTAMP}"
echo "Log saved to: ./training_log_${TIMESTAMP}.txt"
echo "=========================================="