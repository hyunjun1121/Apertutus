#!/bin/bash

echo "=========================================="
echo "DEEPSPEED INSTALLATION"
echo "Date: $(date)"
echo "=========================================="

echo -e "\n[1] Installing DeepSpeed..."
pip3 install deepspeed

echo -e "\n[2] Verifying installation..."
python3 -c "import deepspeed; print(f'DeepSpeed version: {deepspeed.__version__}')" || {
    echo "ERROR: DeepSpeed installation failed!"
    echo ""
    echo "If installation fails, try:"
    echo "1. Install with specific CUDA version:"
    echo "   DS_BUILD_CUDA_EXT=0 pip3 install deepspeed"
    echo ""
    echo "2. Or install pre-built wheel:"
    echo "   pip3 install deepspeed --no-build-isolation"
    exit 1
}

echo -e "\n[3] Checking DeepSpeed ops..."
ds_report

echo -e "\n=========================================="
echo "DeepSpeed installation complete!"
echo "Now you can run: ./launch_safety_finetuning_corrected.sh"
echo "=========================================="