#!/bin/bash

echo "=========================================="
echo "APERTUS ENVIRONMENT SETUP"
echo "Date: $(date)"
echo "=========================================="

echo -e "\n[1] Installing requirements from apertus-finetuning-recipes..."
cd apertus-finetuning-recipes
pip3 install -r requirements.txt

echo -e "\n[2] Verifying all packages..."
python3 -c "
import sys
packages = ['kernels', 'peft', 'trl', 'transformers', 'deepspeed']
for pkg in packages:
    try:
        module = __import__(pkg)
        version = getattr(module, '__version__', 'installed')
        print(f'✓ {pkg}: {version}')
    except ImportError as e:
        print(f'✗ {pkg}: NOT INSTALLED')
        sys.exit(1)
"

cd ..

echo -e "\n=========================================="
echo "Setup complete! Now you can run:"
echo "  ./launch_safety_finetuning_corrected.sh"
echo "=========================================="