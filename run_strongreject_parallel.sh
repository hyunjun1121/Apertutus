#!/bin/bash

echo "=========================================="
echo "PARALLEL STRONGREJECT EVALUATION (5 APIs)"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Kill any existing session
tmux kill-session -t strongreject_parallel 2>/dev/null

# Pull latest code
git pull

# Create output directories
mkdir -p evaluation_results
mkdir -p logs

echo ""
echo "Configuration:"
echo "  - 16 languages (382 entries each = 6,112 total)"
echo "  - 5 API keys processing in parallel"
echo "  - Rate limit: 5 req/sec per API (25 req/sec total)"
echo "  - Token limit: 100k tokens/min per API"
echo "  - Judge model: Apertus-70B"
echo ""

# Estimate time
echo "Time Estimation:"
echo "  - Total evaluations: 6,112"
echo "  - Max rate: 25 evaluations/sec (5 APIs × 5 req/sec)"
echo "  - Theoretical minimum: ~4 minutes"
echo "  - Expected time: 20-30 minutes (with API latency)"
echo ""

# Start in tmux session
tmux new-session -d -s strongreject_parallel \
    "python3 -u run_strongreject_parallel.py 2>&1 | tee logs/strongreject_parallel_$(date +%Y%m%d_%H%M%S).log"

echo "=========================================="
echo "Parallel StrongReject evaluation started!"
echo ""
echo "Monitor real-time progress:"
echo "  tmux attach -t strongreject_parallel"
echo ""
echo "The display will show:"
echo "  - Each API's current processing status"
echo "  - Overall progress bar"
echo "  - Processing rate and ETA"
echo ""
echo "Results will be saved to:"
echo "  - evaluation_results/strongreject_parallel_report.json"
echo "  - evaluation_results/strongreject_parallel_report.csv"
echo ""
echo "=========================================="