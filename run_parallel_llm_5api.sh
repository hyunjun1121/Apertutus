#!/bin/bash

echo "=========================================="
echo "PARALLEL LLM RESPONSE GENERATION (5 APIs)"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Kill any existing session
tmux kill-session -t llm_5api 2>/dev/null

# Pull latest code
git pull

# Create logs directory
mkdir -p logs
mkdir -p llm_responses

echo ""
echo "Configuration:"
echo "  - 16 completed languages"
echo "  - 5 API keys (each processes 3-4 languages)"
echo "  - 382 entries per language"
echo "  - Total: 6,112 entries"
echo ""
echo "Language Assignment:"
echo "  API 0: kor.Hang, cmn.Hani, deu.Latn"
echo "  API 1: spa.Latn, jpn.Jpan, fra.Latn"
echo "  API 2: ita.Latn, rus.Cyrl, por.Latn"
echo "  API 3: pol.Latn, nld.Latn, ind.Latn"
echo "  API 4: tur.Latn, ces.Latn, arb.Arab, ron.Latn"
echo ""

# Start parallel LLM response generator
tmux new-session -d -s llm_5api \
    "python3 parallel_llm_5api_optimized.py --all 2>&1 | tee logs/parallel_llm_5api.log"

echo "=========================================="
echo "LLM Response generation started!"
echo ""
echo "Monitor with:"
echo "  tmux attach -t llm_5api"
echo "  tail -f logs/parallel_llm_5api.log"
echo ""
echo "Check progress:"
echo "  ls -la llm_responses/*.json | wc -l"
echo "  watch -n 30 'ls -la llm_responses/*.json | tail -5'"
echo ""
echo "View specific API progress:"
echo "  grep 'API 0' logs/parallel_llm_5api.log | tail"
echo "  grep 'API 1' logs/parallel_llm_5api.log | tail"
echo ""
echo "Estimated time: 1-2 hours for all 16 languages"
echo "=========================================="