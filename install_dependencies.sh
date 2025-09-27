#!/bin/bash

echo "============================================"
echo "Installing dependencies for Apertus fine-tuning"
echo "============================================"

# Install required packages
pip install datasets transformers peft trl accelerate

echo ""
echo "Dependencies installed!"
echo "Now you can run: ./run_experiment.sh"