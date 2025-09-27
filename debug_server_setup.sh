#!/bin/bash

echo "=========================================="
echo "APERTUS SERVER ENVIRONMENT DEBUGGING"
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "User: $(whoami)"
echo "=========================================="

echo -e "\n[1] Python Environment Check:"
echo "Python path: $(which python || echo 'Python not found')"
echo "Python3 path: $(which python3 || echo 'Python3 not found')"
echo "Python version:"
python --version 2>&1 || python3 --version 2>&1 || echo "No Python found"

echo -e "\n[2] Pip Check:"
echo "Pip path: $(which pip || echo 'Pip not found')"
echo "Pip3 path: $(which pip3 || echo 'Pip3 not found')"

echo -e "\n[3] Virtual Environment Check:"
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "Virtual environment active: $VIRTUAL_ENV"
else
    echo "No virtual environment active"
fi

echo -e "\n[4] Conda Environment Check:"
if command -v conda &> /dev/null; then
    echo "Conda is installed"
    conda info --envs
else
    echo "Conda not found"
fi

echo -e "\n[5] Accelerate Installation Check:"
if command -v accelerate &> /dev/null; then
    echo "Accelerate found at: $(which accelerate)"
    echo "Accelerate version:"
    accelerate --version
else
    echo "Accelerate NOT FOUND - Installation needed"
    echo "Checking if installed via pip:"
    pip show accelerate 2>/dev/null || pip3 show accelerate 2>/dev/null || echo "Not installed via pip"
fi

echo -e "\n[6] Required Packages Check:"
echo "Checking for required packages..."
for package in accelerate transformers datasets torch peft; do
    echo -n "  $package: "
    if pip show $package &>/dev/null || pip3 show $package &>/dev/null; then
        version=$(pip show $package 2>/dev/null | grep Version || pip3 show $package 2>/dev/null | grep Version)
        echo "INSTALLED - $version"
    else
        echo "NOT INSTALLED"
    fi
done

echo -e "\n[7] GPU/CUDA Check:"
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv
    echo "CUDA Version:"
    nvidia-smi | grep "CUDA Version" || echo "CUDA version not found"
else
    echo "No NVIDIA GPU detected or nvidia-smi not available"
fi

echo -e "\n[8] Directory Structure:"
echo "Current directory: $(pwd)"
echo "Script location: $(dirname "$0")"
echo "Files in current directory:"
ls -la | head -20

echo -e "\n[9] Environment Variables:"
echo "PATH: $PATH"
echo "PYTHONPATH: $PYTHONPATH"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"

echo -e "\n=========================================="
echo "RECOMMENDED FIXES:"
echo "=========================================="

if ! command -v accelerate &> /dev/null; then
    echo "1. Install accelerate and required packages:"
    echo "   pip install accelerate transformers datasets torch peft"
    echo "   OR"
    echo "   pip3 install accelerate transformers datasets torch peft"
    echo ""
    echo "2. If using conda, activate your environment first:"
    echo "   conda activate your_env_name"
    echo ""
    echo "3. If packages are installed but not found, check PATH:"
    echo "   export PATH=\$HOME/.local/bin:\$PATH"
fi

echo "=========================================="