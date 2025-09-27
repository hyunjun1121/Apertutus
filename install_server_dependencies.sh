#!/bin/bash

echo "=========================================="
echo "APERTUS SERVER DEPENDENCY INSTALLER"
echo "Date: $(date)"
echo "=========================================="

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo "ERROR: Python not found!"
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"
echo "Using pip: $($PIP_CMD --version)"

echo -e "\n[1] Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip

echo -e "\n[2] Installing PyTorch with CUDA support..."
$PIP_CMD install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo -e "\n[3] Installing Hugging Face libraries..."
$PIP_CMD install transformers datasets accelerate peft

echo -e "\n[4] Installing additional dependencies..."
$PIP_CMD install numpy pandas scikit-learn tqdm tensorboard

echo -e "\n[5] Verifying installations..."
echo "Checking installed packages:"
for package in torch transformers datasets accelerate peft; do
    echo -n "  $package: "
    $PYTHON_CMD -c "import $package; print($package.__version__)" 2>/dev/null || echo "ERROR"
done

echo -e "\n[6] Testing accelerate command..."
if command -v accelerate &> /dev/null; then
    echo "✓ Accelerate command is available"
    accelerate --version
else
    echo "✗ Accelerate command not found in PATH"
    echo "  Try: export PATH=\$HOME/.local/bin:\$PATH"
    echo "  Or use: $PYTHON_CMD -m accelerate.commands.launch"
fi

echo -e "\n[7] Testing GPU availability..."
$PYTHON_CMD -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
    print(f'GPU name: {torch.cuda.get_device_name(0)}')
" 2>/dev/null || echo "Could not test GPU"

echo -e "\n=========================================="
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. If accelerate is not in PATH, run:"
echo "   export PATH=\$HOME/.local/bin:\$PATH"
echo ""
echo "2. Test the setup with:"
echo "   ./debug_server_setup.sh"
echo ""
echo "3. Run fine-tuning with:"
echo "   ./launch_safety_finetuning_fixed.sh"
echo "=========================================="