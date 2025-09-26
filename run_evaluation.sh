#!/bin/bash

echo "=========================================="
echo "STRONG REJECT EVALUATION"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Check if response files exist
echo "Checking response files..."
RESPONSE_COUNT=$(ls -1 llm_responses/mhj_dataset_*_with_responses.json 2>/dev/null | wc -l)

if [ "$RESPONSE_COUNT" -eq 0 ]; then
    echo "No response files found in llm_responses/"
    echo "Please run LLM response generation first."
    exit 1
fi

echo "Found $RESPONSE_COUNT response files"
echo ""

# Run evaluation
echo "Running strong reject evaluation..."
python3 evaluate_strong_reject.py --dir llm_responses --output evaluation_results/strong_reject_report.json

echo ""
echo "=========================================="
echo "Evaluation complete!"
echo ""
echo "Results saved to:"
echo "  - evaluation_results/strong_reject_report.json (detailed)"
echo "  - evaluation_results/strong_reject_report.csv (summary)"
echo ""
echo "View summary:"
echo "  cat evaluation_results/strong_reject_report.csv"
echo ""
echo "View detailed JSON:"
echo "  jq '.overall_statistics' evaluation_results/strong_reject_report.json"
echo "=========================================="