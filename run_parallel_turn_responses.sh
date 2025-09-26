#!/bin/bash

echo "=========================================="
echo "PARALLEL TURN-BY-TURN LLM RESPONSE GENERATION"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Kill any existing session
tmux kill-session -t llm_turns 2>/dev/null

# Pull latest code
git pull

# Create logs directory
mkdir -p logs
mkdir -p llm_responses

echo ""
echo "Configuration:"
echo "  - 16 completed languages"
echo "  - 5 API keys (turn-by-turn processing)"
echo "  - 382 entries per language"
echo "  - Each turn gets individual response"
echo ""

# Start in tmux session with unbuffered output
tmux new-session -d -s llm_turns \
    "python3 -u parallel_llm_5api_turn_responses.py --all 2>&1 | tee -a logs/llm_turn_responses.log"

echo "=========================================="
echo "Turn-by-turn response generation started!"
echo ""
echo "Monitor with:"
echo "  tmux attach -t llm_turns"
echo "  tail -f logs/llm_turn_responses.log"
echo ""
echo "Check progress:"
echo "  grep 'turns done' logs/llm_turn_responses.log | tail"
echo "  ls -la llm_responses/*.json | wc -l"
echo ""
echo "Estimated time: 3-4 hours (more turns to process)"
echo "=========================================="