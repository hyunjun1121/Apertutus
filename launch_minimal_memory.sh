#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "ULTRA MINIMAL MEMORY TRAINING (3GB LIMIT)"
echo "For shared GPU environment"
echo "=========================================="

echo -e "\n[1] Finding best GPU..."
echo "GPU memory status:"
nvidia-smi --query-gpu=index,memory.free --format=csv

# Use GPU with most free memory (likely GPU 4)
export CUDA_VISIBLE_DEVICES=4

cat > minimal_config.yaml << EOF
# Ultra minimal config for 3GB memory limit
model_name_or_path: microsoft/phi-2  # Much smaller model (2.7B)
torch_dtype: float16
load_in_8bit: true

# Dataset
dataset_name: tatsu-lab/alpaca  # Smaller dataset
dataset_num_proc: 2
dataset_text_field: text
max_samples: 100  # Limit samples for testing

# Minimal training settings
learning_rate: 2.0e-4
gradient_checkpointing: true
num_train_epochs: 1
logging_steps: 50
per_device_train_batch_size: 1
gradient_accumulation_steps: 4
max_grad_norm: 0.3

# Minimal LoRA
use_peft: true
lora_r: 2  # Minimal rank
lora_alpha: 4
lora_dropout: 0.1
lora_target_modules: ["q_proj", "v_proj"]

# Very short sequences
max_length: 128
packing: false

# Memory optimizations
optim: adafactor  # More memory efficient than adam
fp16: true
tf32: false
dataloader_pin_memory: false

# Output
output_dir: ./minimal_lora_${TIMESTAMP}
report_to: "none"
seed: 42
save_strategy: "no"  # Don't save checkpoints
EOF

echo -e "\n[2] Running minimal training on GPU $CUDA_VISIBLE_DEVICES..."
cd apertus-finetuning-recipes

python3 -c "
import torch
print(f'Using GPU: {torch.cuda.get_device_name()}')
print(f'Free memory: {torch.cuda.mem_get_info()[0]/1e9:.2f} GB')
"

python sft_train.py --config ../minimal_config.yaml

cd ..

echo "=========================================="
echo "Minimal training complete!"
echo "=========================================="