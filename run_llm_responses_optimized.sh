#!/bin/bash

echo "=========================================="
echo "OPTIMIZED LLM RESPONSE GENERATION"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Kill any existing session
tmux kill-session -t llm_optimized 2>/dev/null

# Pull latest code
git pull

# Create logs directory
mkdir -p logs
mkdir -p llm_responses

echo ""
echo "Configuration:"
echo "  - 16 completed languages in multilingual_datasets_filtered/"
echo "  - 5 API keys (20 req/sec total)"
echo "  - 382 entries per language"
echo "  - Total: 6,112 entries"
echo ""

# Start optimized LLM response generator
tmux new-session -d -s llm_optimized \
    "python3 optimized_llm_response_generator.py --all 2>&1 | tee logs/llm_responses_optimized.log"

echo "=========================================="
echo "LLM Response generation started!"
echo ""
echo "Monitor with:"
echo "  tmux attach -t llm_optimized"
echo "  tail -f logs/llm_responses_optimized.log"
echo ""
echo "Check progress:"
echo "  ls -la llm_responses/ | wc -l"
echo "  watch -n 30 'ls -la llm_responses/*.json | tail -10'"
echo ""
echo "Estimated time: 2-3 hours for all 16 languages"
echo "=========================================="