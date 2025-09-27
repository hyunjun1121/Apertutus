#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "APERTUS SAFETY LORA FINE-TUNING - 8B TEST"
echo "Date: $(date)"
echo "Using smaller 8B model for testing"
echo "=========================================="

# Create test config with 8B model
cat > safety_lora_config_8b_test.yaml << EOF
# Model - Using 8B for testing (much smaller and faster)
model_name_or_path: swiss-ai/Apertus-8B-Instruct-2509
attn_implementation: flash-attention-3
dtype: bfloat16

# Dataset - Using existing HuggingFace dataset
dataset_name: HuggingFaceH4/Multilingual-Thinking
dataset_num_proc: 12

# Hyperparameters
learning_rate: 2.0e-4
gradient_checkpointing: true
num_train_epochs: 1
logging_steps: 10
per_device_train_batch_size: 4
gradient_accumulation_steps: 2

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
output_dir: ./safety_lora_8b_test_${TIMESTAMP}
report_to: "none"
seed: 42
save_strategy: steps
save_steps: 100
save_total_limit: 2
EOF

echo "Created test config: safety_lora_config_8b_test.yaml"

echo -e "\n[Step 1] Checking environment..."
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
python3 -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python3 -c "import accelerate; print(f'Accelerate: {accelerate.__version__}')"
python3 -c "import trl; print(f'TRL: {trl.__version__}')"

echo -e "\n[Step 2] Entering apertus-finetuning-recipes directory..."
cd apertus-finetuning-recipes

echo -e "\n[Step 3] Starting fine-tuning with 8B model..."
echo "This should work on a single GPU and download ~16GB"
echo ""

# For single GPU, we can use python directly instead of accelerate
python sft_train.py --config ../safety_lora_config_8b_test.yaml

cd ..

echo "=========================================="
echo "8B model fine-tuning complete!"
echo "LoRA adapter saved to: ./safety_lora_8b_test_${TIMESTAMP}"
echo "=========================================="