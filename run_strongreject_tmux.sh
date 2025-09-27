#!/bin/bash

echo "=========================================="
echo "STRONGREJECT EVALUATION WITH PROGRESS"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Kill any existing session
tmux kill-session -t strongreject 2>/dev/null

# Pull latest code
git pull

# Create output directories
mkdir -p evaluation_results
mkdir -p logs

echo ""
echo "Configuration:"
echo "  - 16 languages to evaluate"
echo "  - 382 entries per language (6,112 total)"
echo "  - ~1,323 turns per language (21,168 total)"
echo "  - Judge model: Apertus-70B"
echo ""

# Start in tmux session with unbuffered output
tmux new-session -d -s strongreject \
    "python3 -u run_strongreject_evaluation.py --dir llm_responses 2>&1 | tee logs/strongreject_$(date +%Y%m%d_%H%M%S).log"

echo "=========================================="
echo "StrongReject evaluation started!"
echo ""
echo "Monitor real-time progress:"
echo "  tmux attach -t strongreject"
echo ""
echo "The display will show:"
echo "  - Progress bar for each language"
echo "  - Current entry being evaluated"
echo "  - ETA for each language"
echo "  - Refusal rate after each language completes"
echo ""
echo "Results will be saved to:"
echo "  - evaluation_results/strongreject_report.json"
echo "  - evaluation_results/strongreject_report.csv"
echo ""
echo "Estimated time: 2-3 hours"
echo "=========================================="