#!/bin/bash

echo "=========================================="
echo "CLEARING GPU MEMORY"
echo "=========================================="

echo -e "\n[1] Current GPU status:"
nvidia-smi

echo -e "\n[2] Processes using GPU:"
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv

echo -e "\n[3] Kill specific processes? (from error log)"
echo "Process 1020340 using 16.77 GiB"
echo "Process 1930496 using 474.00 MiB"
echo ""
echo "To kill these processes, run:"
echo "  sudo kill -9 1020340 1930496"
echo ""
echo "Or kill all Python processes on GPU:"
echo "  sudo fuser -v /dev/nvidia* 2>&1 | grep python | awk '{print \$2}' | xargs -r kill -9"

echo -e "\n[4] Python GPU memory clear:"
python3 -c "
import torch
import gc

if torch.cuda.is_available():
    print(f'Before cleanup:')
    print(f'  Allocated: {torch.cuda.memory_allocated()/1e9:.2f} GB')
    print(f'  Reserved: {torch.cuda.memory_reserved()/1e9:.2f} GB')

    # Clear cache
    gc.collect()
    torch.cuda.empty_cache()

    print(f'\nAfter cleanup:')
    print(f'  Allocated: {torch.cuda.memory_allocated()/1e9:.2f} GB')
    print(f'  Reserved: {torch.cuda.memory_reserved()/1e9:.2f} GB')
else:
    print('No CUDA available')
"

echo -e "\n[5] Updated GPU status:"
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv