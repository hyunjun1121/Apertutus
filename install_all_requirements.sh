#!/bin/bash

echo "=========================================="
echo "INSTALL ALL REQUIREMENTS - ONE COMMAND FIX"
echo "Date: $(date)"
echo "=========================================="

echo -e "\n[1] Uninstalling conflicting packages..."
pip3 uninstall -y numpy networkx

echo -e "\n[2] Installing all requirements from scratch..."
pip3 install -r requirements_complete.txt

echo -e "\n[3] Verifying installation..."
python3 -c "
print('Testing all imports:')
import numpy as np
print(f'✓ NumPy {np.__version__}')
import networkx as nx
print(f'✓ NetworkX {nx.__version__}')
import torch
print(f'✓ PyTorch {torch.__version__}')
import transformers
print(f'✓ Transformers {transformers.__version__}')
import accelerate
print(f'✓ Accelerate {accelerate.__version__}')
import deepspeed
print(f'✓ DeepSpeed {deepspeed.__version__}')
import peft
print(f'✓ PEFT {peft.__version__}')
import trl
print(f'✓ TRL {trl.__version__}')

print('\nTesting DeepSpeed import chain:')
from deepspeed.launcher.runner import DEEPSPEED_ENVIRONMENT_NAME
print('✓ DeepSpeed launcher works!')

print('\nAll packages installed correctly!')
"

echo -e "\n=========================================="
echo "Installation complete!"
echo "Now you can run:"
echo "  ./launch_safety_finetuning_corrected.sh"
echo "=========================================="