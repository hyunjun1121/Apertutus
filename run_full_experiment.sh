#!/bin/bash

echo "=========================================="
echo "FULL SAFETY FINE-TUNING EXPERIMENT"
echo "Date: $(date)"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Phase 1: Data Preparation
echo -e "\n${YELLOW}[Phase 1] Data Preparation${NC}"
echo "----------------------------------------"

echo "1.1 Splitting dataset (80/20)..."
python3 split_dataset_for_evaluation.py --action split

echo "1.2 Verifying train/test separation..."
python3 split_dataset_for_evaluation.py --action verify

echo "1.3 Preparing fine-tuning dataset..."
python3 split_dataset_for_evaluation.py --action prepare

# Phase 2: Fine-tuning
echo -e "\n${YELLOW}[Phase 2] LoRA Fine-tuning${NC}"
echo "----------------------------------------"
echo "Starting fine-tuning..."
# TODO: Add actual fine-tuning command when script is ready
echo -e "${RED}Note: Fine-tuning script needed!${NC}"

# Phase 3: Generate Responses
echo -e "\n${YELLOW}[Phase 3] Generate Test Responses${NC}"
echo "----------------------------------------"

echo "3.1 Generating base model responses..."
# TODO: Add response generation for base model

echo "3.2 Generating fine-tuned model responses..."
# TODO: Add response generation for fine-tuned model

# Phase 4: Evaluation
echo -e "\n${YELLOW}[Phase 4] StrongReject Evaluation${NC}"
echo "----------------------------------------"

echo "4.1 Evaluating base model..."
# Run evaluation on base responses

echo "4.2 Evaluating fine-tuned model..."
# Run evaluation on fine-tuned responses

# Phase 5: Comparison
echo -e "\n${YELLOW}[Phase 5] Results Comparison${NC}"
echo "----------------------------------------"

echo "Comparing results..."
# TODO: Add comparison script

echo -e "\n${GREEN}=========================================="
echo "EXPERIMENT COMPLETE!"
echo "==========================================${NC}"

echo ""
echo "Results saved in:"
echo "  - Training data: experiment_datasets/train/"
echo "  - Test data: experiment_datasets/test/"
echo "  - Fine-tuning: lora_adapter/"
echo "  - Evaluations: evaluation_results/"
echo ""
echo "Key findings will be in: final_comparison_report.html"