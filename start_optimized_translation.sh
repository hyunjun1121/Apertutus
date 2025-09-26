#!/bin/bash

# Optimized translation using all 5 API keys efficiently
echo "=========================================="
echo "OPTIMIZED PARALLEL TRANSLATION"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Clean up any existing sessions
tmux kill-session -t optimized_trans 2>/dev/null

# Pull latest code
git pull

# Create logs directory
mkdir -p logs

echo ""
echo "Configuration:"
echo "  - 5 API keys available"
echo "  - Max 20 requests/second (4 per key)"
echo "  - 24 languages to process"
echo "  - Estimated time: 6-8 hours total"
echo ""

# Start the optimized translator in tmux
tmux new-session -d -s optimized_trans \
    "python3 optimized_parallel_translator.py --all 2>&1 | tee logs/optimized_translation.log"

echo "=========================================="
echo "Translation started in tmux session: optimized_trans"
echo ""
echo "Monitor with:"
echo "  tmux attach -t optimized_trans"
echo "  tail -f logs/optimized_translation.log"
echo ""
echo "Check progress:"
echo "  watch -n 60 'ls -la multilingual_datasets/ | grep -E \"(fas|ukr|hun|swe|ell|dan|vie|tha)\" | head -10'"
echo "=========================================="