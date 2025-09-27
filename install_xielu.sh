#!/bin/bash

echo "=========================================="
echo "INSTALLING XIELU FOR CUDA OPTIMIZATION"
echo "(Optional - not critical for training)"
echo "=========================================="

# Install XIELU for CUDA-fused xIELU (optional performance improvement)
pip3 install git+https://github.com/nickjbrowning/XIELU || {
    echo "XIELU installation failed - this is optional, training will still work"
    echo "Using Python fallback version instead"
}

echo "Done. The warning about XIELU can be ignored - it's just a performance optimization."