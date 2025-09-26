#!/bin/bash

echo "=========================================="
echo "REAL-TIME LLM RESPONSE GENERATION MONITOR"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Kill any existing session
tmux kill-session -t llm_realtime 2>/dev/null

# Pull latest code
git pull

# Create logs directory
mkdir -p logs
mkdir -p llm_responses

echo ""
echo "Configuration:"
echo "  - 16 languages (382 entries each)"
echo "  - 5 API keys processing in parallel"
echo "  - Real-time progress monitoring"
echo ""

# Start in tmux session (using fixed version)
tmux new-session -d -s llm_realtime \
    "python3 -u parallel_llm_5api_realtime_fixed.py --all 2>&1 | tee logs/llm_realtime.log"

echo "=========================================="
echo "Real-time monitoring started!"
echo ""
echo "View real-time progress:"
echo "  tmux attach -t llm_realtime"
echo ""
echo "The dashboard will show:"
echo "  - Progress bar for each API"
echo "  - Entries and turns processed"
echo "  - Processing rate and ETA"
echo ""
echo "=========================================="