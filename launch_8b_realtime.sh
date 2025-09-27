#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "APERTUS 8B LORA FINE-TUNING WITH REAL-TIME PROGRESS"
echo "Date: $(date)"
echo "=========================================="

echo -e "\n[GPU SPECS]"
echo "Server: 8x NVIDIA RTX A5000 (23GB VRAM each, 184GB total)"
echo "Current GPU allocation:"
nvidia-smi --query-gpu=index,name,memory.used,memory.free,memory.total --format=csv

echo -e "\n[Step 1] Finding best available GPU..."
BEST_GPU=$(nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits | sort -t',' -k2 -rn | head -1 | cut -d',' -f1)
FREE_MEM=$(nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits | sort -t',' -k2 -rn | head -1 | cut -d',' -f2)
echo "Selected GPU $BEST_GPU with ${FREE_MEM}MB free memory"

if [ $FREE_MEM -lt 3000 ]; then
    echo "WARNING: Less than 3GB free. Training may fail."
fi

echo -e "\n[Step 2] Creating config for 8B model..."
cat > apertus_8b_config_${TIMESTAMP}.yaml << EOF
# Model - Apertus 8B
model_name_or_path: swiss-ai/Apertus-8B-Instruct-2509
torch_dtype: float16
attn_implementation: eager
load_in_8bit: true  # 8-bit quantization to save memory

# Dataset
dataset_name: HuggingFaceH4/Multilingual-Thinking
dataset_num_proc: 4
dataset_text_field: messages

# Training parameters - Optimized for 8B model
learning_rate: 2.0e-4
gradient_checkpointing: true
gradient_checkpointing_kwargs:
  use_reentrant: false
num_train_epochs: 1
per_device_train_batch_size: 1
gradient_accumulation_steps: 8  # Effective batch size = 8
max_grad_norm: 0.3

# Logging for real-time progress
logging_steps: 1  # Log every step for real-time feedback
logging_first_step: true
logging_strategy: steps
report_to: "none"  # Disable wandb/tensorboard for cleaner output

# LoRA Configuration for 8B
use_peft: true
lora_r: 8  # Standard rank for 8B
lora_alpha: 16
lora_dropout: 0.05
lora_target_modules: ["q_proj", "v_proj", "k_proj", "o_proj"]

# Sequence length
max_length: 512
packing: false

# Memory optimizations
optim: adamw_torch_fused
fp16: true
tf32: false
dataloader_num_workers: 0

# Output & checkpointing
output_dir: ./apertus_8b_lora_${TIMESTAMP}
save_strategy: steps
save_steps: 100
save_total_limit: 2
seed: 42
EOF

echo "Config created: apertus_8b_config_${TIMESTAMP}.yaml"

echo -e "\n[Step 3] Setting environment for optimal performance..."
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True,max_split_size_mb:512"
export TOKENIZERS_PARALLELISM=false
export CUDA_VISIBLE_DEVICES=$BEST_GPU

echo -e "\n[Step 4] Clearing GPU cache..."
python3 -c "
import torch
import gc
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    print(f'Using GPU: {torch.cuda.get_device_name()}')
    free, total = torch.cuda.mem_get_info()
    print(f'GPU Memory: {free/1e9:.2f}GB free / {total/1e9:.2f}GB total')
"

echo -e "\n[Step 5] Starting training with REAL-TIME progress..."
echo "You will see progress updates every step!"
echo "=========================================="

cd apertus-finetuning-recipes

# Run with unbuffered output for real-time display
python3 -u sft_train.py \
    --config ../apertus_8b_config_${TIMESTAMP}.yaml 2>&1 | \
    while IFS= read -r line; do
        # Highlight important lines
        if [[ $line == *"loss"* ]] || [[ $line == *"step"* ]] || [[ $line == *"epoch"* ]]; then
            echo -e "\033[1;32m$line\033[0m"  # Green for training progress
        elif [[ $line == *"error"* ]] || [[ $line == *"Error"* ]]; then
            echo -e "\033[1;31m$line\033[0m"  # Red for errors
        elif [[ $line == *"WARNING"* ]] || [[ $line == *"warning"* ]]; then
            echo -e "\033[1;33m$line\033[0m"  # Yellow for warnings
        elif [[ $line == *"Downloading"* ]] || [[ $line == *"%"* ]]; then
            echo -e "\033[1;36m$line\033[0m"  # Cyan for downloads
        else
            echo "$line"
        fi
    done

cd ..

echo -e "\n=========================================="
echo "Training completed!"
echo "Model saved to: ./apertus_8b_lora_${TIMESTAMP}"
echo ""
echo "To use the fine-tuned model:"
echo "from peft import PeftModel"
echo "model = PeftModel.from_pretrained(base_model, './apertus_8b_lora_${TIMESTAMP}')"
echo "=========================================="