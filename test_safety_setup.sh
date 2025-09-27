#!/bin/bash

echo "=========================================="
echo "TESTING SAFETY FINE-TUNING SETUP"
echo "Date: $(date)"
echo "=========================================="

echo -e "\n[1] Testing directory change..."
if cd apertus-finetuning-recipes 2>/dev/null; then
    echo "✓ Can enter apertus-finetuning-recipes"
    pwd
    cd ..
else
    echo "✗ Cannot enter apertus-finetuning-recipes"
fi

echo -e "\n[2] Testing accelerate command..."
if accelerate launch --help > /dev/null 2>&1; then
    echo "✓ accelerate launch works"
else
    echo "✗ accelerate launch failed"
    echo "Trying Python module method..."
    if python3 -m accelerate.commands.launch --help > /dev/null 2>&1; then
        echo "✓ python3 -m accelerate.commands.launch works"
    else
        echo "✗ Python module method also failed"
    fi
fi

echo -e "\n[3] Checking TRL package (needed for SFTTrainer)..."
if python3 -c "import trl; print(f'✓ TRL version: {trl.__version__}')" 2>/dev/null; then
    :
else
    echo "✗ TRL not installed - REQUIRED!"
    echo "Install with: pip3 install trl"
fi

echo -e "\n[4] Checking model access..."
python3 -c "
from huggingface_hub import model_info
try:
    info = model_info('swiss-ai/Apertus-70B')
    print('✓ Can access swiss-ai/Apertus-70B')
    print(f'  Model size: ~{info.safetensors.total / 1e9:.1f}GB')
except Exception as e:
    print('✗ Cannot access model:', str(e))
    print('  You may need to login: huggingface-cli login')
"

echo -e "\n[5] Disk space check..."
df -h . | grep -v Filesystem

echo -e "\n[6] Memory check..."
free -h

echo -e "\n=========================================="
echo "RECOMMENDATIONS:"
echo "=========================================="

if ! python3 -c "import trl" 2>/dev/null; then
    echo "1. Install TRL package:"
    echo "   pip3 install trl"
    echo ""
fi

echo "2. For 70B model, you need:"
echo "   - ~140GB disk space for model download"
echo "   - Multiple GPUs with sufficient VRAM"
echo "   - Consider using smaller model for testing:"
echo "     --model_name_or_path swiss-ai/Apertus-8B-Instruct-2509"
echo ""
echo "3. To run the fixed script:"
echo "   ./launch_safety_finetuning_working.sh"
echo "=========================================="