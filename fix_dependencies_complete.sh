#!/bin/bash

echo "=========================================="
echo "COMPLETE DEPENDENCY FIX"
echo "Date: $(date)"
echo "=========================================="

echo -e "\n[1] Upgrading networkx to fix NumPy compatibility..."
pip3 install --upgrade networkx

echo -e "\n[2] Installing compatible NumPy version..."
pip3 install "numpy>=1.21,<2.0" --force-reinstall

echo -e "\n[3] Reinstalling DeepSpeed with updated dependencies..."
pip3 install --upgrade deepspeed

echo -e "\n[4] Verifying all packages..."
python3 -c "
import sys
print('Checking package versions:')
import numpy as np
print(f'  NumPy: {np.__version__}')
import networkx as nx
print(f'  NetworkX: {nx.__version__}')
import torch
print(f'  PyTorch: {torch.__version__}')
import deepspeed
print(f'  DeepSpeed: {deepspeed.__version__}')
print('✓ All packages imported successfully!')
"

echo -e "\n[5] Testing DeepSpeed import chain..."
python3 -c "
from deepspeed.launcher.runner import DEEPSPEED_ENVIRONMENT_NAME
print('✓ DeepSpeed launcher imports work')
"

echo -e "\n=========================================="
echo "Fix complete! Now run:"
echo "  ./launch_safety_finetuning_corrected.sh"
echo "=========================================="