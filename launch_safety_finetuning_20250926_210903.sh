#!/bin/bash

echo "=========================================="
echo "APERTUS SAFETY LORA FINE-TUNING"
echo "Date: $(date)"
echo "=========================================="

# Using the apertus-finetuning-recipes framework
cd apertus-finetuning-recipes

accelerate launch \
    --config_file configs/zero3.yaml \
    sft_train.py \
    --config ../safety_lora_config_20250926_210903.yaml \
    --model_name_or_path swiss-ai/Apertus-70B

cd ..

echo "=========================================="
echo "Fine-tuning complete!"
echo "LoRA adapter saved to: ./safety_lora_adapter_20250926_210903"
echo "=========================================="
