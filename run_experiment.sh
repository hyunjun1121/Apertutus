#!/bin/bash

echo "============================================"
echo "APERTUS-70B SAFETY EXPERIMENT"
echo "Date: $(date)"
echo "============================================"

# Run the complete experiment
python3 run_complete_safety_experiment.py

echo ""
echo "============================================"
echo "SETUP COMPLETE"
echo "============================================"
echo ""
echo "To continue with fine-tuning:"
echo "1. Run the generated launch_safety_finetuning_*.sh script"
echo "2. Wait for fine-tuning to complete"
echo "3. Generate test responses with both models"
echo "4. Run evaluation and comparison"
echo "============================================"