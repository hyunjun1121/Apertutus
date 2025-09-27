#!/bin/bash

echo "=========================================="
echo "QUICK FIX: Installing DeepSpeed and Running 70B"
echo "=========================================="

echo -e "\n[1] Installing DeepSpeed (may take a few minutes)..."
pip3 install deepspeed || {
    echo "Standard install failed, trying without build isolation..."
    DS_BUILD_CUDA_EXT=0 pip3 install deepspeed --no-build-isolation
}

echo -e "\n[2] Verifying installation..."
python3 -c "import deepspeed; print(f'✓ DeepSpeed {deepspeed.__version__} installed')"

echo -e "\n[3] Running the corrected 70B fine-tuning script..."
./launch_safety_finetuning_corrected.sh