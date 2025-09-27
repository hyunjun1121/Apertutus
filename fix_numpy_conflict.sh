#!/bin/bash

echo "=========================================="
echo "FIX NUMPY VERSION CONFLICT"
echo "Date: $(date)"
echo "=========================================="

echo -e "\n[1] Current NumPy version:"
python3 -c "import numpy; print(f'NumPy: {numpy.__version__}')"

echo -e "\n[2] Downgrading NumPy to compatible version..."
pip3 install "numpy<2.0" --force-reinstall

echo -e "\n[3] Verifying fix..."
python3 -c "
import numpy as np
print(f'NumPy version: {np.__version__}')
assert hasattr(np, 'float_'), 'NumPy float_ not available'
print('✓ NumPy float_ is available')
"

echo -e "\n[4] Testing imports..."
python3 -c "
print('Testing critical imports...')
import numpy as np
print('✓ NumPy')
import networkx
print('✓ NetworkX')
import torch
print('✓ PyTorch')
import deepspeed
print('✓ DeepSpeed')
print('All imports successful!')
"

echo -e "\n=========================================="
echo "Fix complete! Now run:"
echo "  ./launch_safety_finetuning_corrected.sh"
echo "=========================================="