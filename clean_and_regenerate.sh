#!/bin/bash

echo "============================================"
echo "Cleaning old data and regenerating with fixed refusal message"
echo "============================================"

# Remove old experiment datasets
echo "Removing old experiment datasets..."
rm -rf experiment_datasets/

# Remove old fine-tuning datasets
echo "Removing old fine-tuning datasets..."
rm -f finetuning_datasets/safety_train_*.jsonl
rm -f finetuning_datasets/safety_val_*.jsonl
rm -f finetuning_datasets/safety_stats_*.json

# Remove old preparation results
echo "Removing old preparation results..."
rm -f finetuning_preparation_result.json

# Remove old experiment summaries and scripts
echo "Removing old experiment artifacts..."
rm -f experiment_summary_*.json
rm -f generate_test_responses_*.py
rm -f evaluate_models_*.py
rm -f compare_results_*.py
rm -f launch_safety_finetuning_*.sh
rm -f safety_lora_config_*.yaml
rm -rf safety_dataset_for_training/

echo ""
echo "Old data cleaned!"
echo ""
echo "Now regenerating with correct refusal message..."
echo ""

# Run the experiment again with fixed refusal
./run_experiment.sh

echo ""
echo "============================================"
echo "Regeneration complete with fixed refusal:"
echo "I cannot and will not assist with that request."
echo "============================================"