#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./safety_lora_adapter_${TIMESTAMP}"

echo "=========================================="
echo "APERTUS SAFETY LORA FINE-TUNING (FIXED)"
echo "Date: $(date)"
echo "Output Directory: $OUTPUT_DIR"
echo "=========================================="

echo -e "\n[Step 1] Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python not found!"
    exit 1
fi
echo "Using Python: $($PYTHON_CMD --version)"

echo -e "\n[Step 2] Checking for accelerate..."
if ! command -v accelerate &> /dev/null; then
    echo "ERROR: 'accelerate' command not found!"
    echo ""
    echo "Please install it using one of these methods:"
    echo "  1. pip install accelerate"
    echo "  2. pip3 install accelerate"
    echo "  3. $PYTHON_CMD -m pip install accelerate"
    echo ""
    echo "If already installed, ensure it's in your PATH:"
    echo "  export PATH=\$HOME/.local/bin:\$PATH"
    echo ""
    echo "Or run directly with Python:"
    echo "  $PYTHON_CMD -m accelerate.commands.launch"
    exit 1
fi
echo "Accelerate found: $(which accelerate)"

echo -e "\n[Step 3] Checking required packages..."
MISSING_PACKAGES=""
for package in accelerate transformers datasets torch peft; do
    if ! $PYTHON_CMD -c "import $package" 2>/dev/null; then
        MISSING_PACKAGES="$MISSING_PACKAGES $package"
        echo "  ✗ $package - NOT FOUND"
    else
        echo "  ✓ $package - OK"
    fi
done

if [ -n "$MISSING_PACKAGES" ]; then
    echo -e "\nERROR: Missing packages:$MISSING_PACKAGES"
    echo "Install them with:"
    echo "  $PYTHON_CMD -m pip install$MISSING_PACKAGES"
    exit 1
fi

echo -e "\n[Step 4] Checking for safety_finetuning.py..."
if [ ! -f "safety_finetuning.py" ]; then
    echo "WARNING: safety_finetuning.py not found in current directory!"
    echo "Current directory: $(pwd)"
    echo "Files found:"
    ls -la *.py 2>/dev/null || echo "  No Python files found"
    echo ""
    echo "Please ensure safety_finetuning.py exists or update the script path."
    exit 1
fi

echo -e "\n[Step 5] Checking GPU availability..."
if $PYTHON_CMD -c "import torch; print('GPU Available:', torch.cuda.is_available())" 2>/dev/null; then
    $PYTHON_CMD -c "import torch; print(f'GPU Count: {torch.cuda.device_count()}')" 2>/dev/null
    $PYTHON_CMD -c "import torch; print(f'GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')" 2>/dev/null
else
    echo "WARNING: Could not check GPU availability"
fi

echo -e "\n[Step 6] Starting fine-tuning..."
echo "Command: accelerate launch safety_finetuning.py \\"
echo "  --model_name \"meta-llama/Llama-2-7b-hf\" \\"
echo "  --output_dir \"$OUTPUT_DIR\" \\"
echo "  --num_train_epochs 3 \\"
echo "  --per_device_train_batch_size 4 \\"
echo "  --learning_rate 5e-5"

accelerate launch safety_finetuning.py \
    --model_name "meta-llama/Llama-2-7b-hf" \
    --output_dir "$OUTPUT_DIR" \
    --num_train_epochs 3 \
    --per_device_train_batch_size 4 \
    --learning_rate 5e-5 || {
    echo "=========================================="
    echo "ERROR: Fine-tuning failed!"
    echo "Check the error messages above for details."
    echo "=========================================="
    exit 1
}

echo "=========================================="
echo "Fine-tuning completed successfully!"
echo "LoRA adapter saved to: $OUTPUT_DIR"
echo "=========================================="