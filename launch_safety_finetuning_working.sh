#!/bin/bash
set -e  # Exit on error

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONFIG_FILE="safety_lora_config_${TIMESTAMP}.yaml"

echo "=========================================="
echo "APERTUS SAFETY LORA FINE-TUNING"
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "=========================================="

# Check if we're in the right directory
if [ ! -d "apertus-finetuning-recipes" ]; then
    echo "ERROR: apertus-finetuning-recipes directory not found!"
    exit 1
fi

# Check if config file exists
if [ ! -f "safety_lora_config_20250926_210903.yaml" ]; then
    echo "ERROR: Config file not found!"
    echo "Available yaml files:"
    ls -la *.yaml
    exit 1
fi

# Check accelerate command
if ! command -v accelerate &> /dev/null; then
    echo "ERROR: accelerate not found. Trying Python module..."
    ACCELERATE_CMD="python3 -m accelerate.commands.launch"
else
    ACCELERATE_CMD="accelerate launch"
fi

echo -e "\n[Step 1] Checking Python packages..."
python3 -c "
import sys
packages = ['accelerate', 'transformers', 'datasets', 'torch', 'peft', 'trl']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'  ✓ {pkg}')
    except ImportError:
        print(f'  ✗ {pkg} - MISSING')
        sys.exit(1)
"

echo -e "\n[Step 2] Checking GPU availability..."
python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU count: {torch.cuda.device_count()}')
    for i in range(min(torch.cuda.device_count(), 2)):
        print(f'  GPU {i}: {torch.cuda.get_device_name(i)}')
"

echo -e "\n[Step 3] Entering apertus-finetuning-recipes directory..."
cd apertus-finetuning-recipes

echo -e "\n[Step 4] Starting fine-tuning..."
echo "Command: $ACCELERATE_CMD \\"
echo "    --config_file configs/zero3.yaml \\"
echo "    sft_train.py \\"
echo "    --config ../safety_lora_config_20250926_210903.yaml \\"
echo "    --model_name_or_path swiss-ai/Apertus-70B"
echo ""
echo "Note: This will download the 70B model if not cached locally."
echo "This may take significant time and disk space (~140GB)."
echo ""

# Run the actual training
$ACCELERATE_CMD \
    --config_file configs/zero3.yaml \
    sft_train.py \
    --config ../safety_lora_config_20250926_210903.yaml \
    --model_name_or_path swiss-ai/Apertus-70B || {
    echo "=========================================="
    echo "ERROR: Fine-tuning failed!"
    echo "Check the error messages above."
    echo "=========================================="
    cd ..
    exit 1
}

cd ..

echo "=========================================="
echo "Fine-tuning completed successfully!"
echo "LoRA adapter saved to: ./safety_lora_adapter_20250926_210903"
echo "=========================================="