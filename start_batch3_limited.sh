#!/bin/bash

# Batch 3a: 처음 3개 언어만 (Rate limit 회피)
echo "=========================================="
echo "Starting Batch 3a Translation (3 languages)"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Create logs directory if it doesn't exist
mkdir -p logs

# Batch 3a - 처음 3개 언어만
LANGUAGES=(
    "fas.Arab"
    "ukr.Cyrl"
    "hun.Latn"
)

echo ""
echo "Languages to translate:"
for code in "${LANGUAGES[@]}"; do
    echo "  - $code"
done

echo ""
echo "Starting tmux sessions (with delays to avoid rate limit)..."
echo "=========================================="

# Start tmux sessions for each language
for code in "${LANGUAGES[@]}"; do
    # Replace dots with underscores for tmux session names
    session_base=$(echo "$code" | tr '.' '_')

    echo "Starting translation for $code..."

    # Create 4 tmux sessions with longer delays
    for i in 0 1 2 3; do
        start=$((i * 100))
        if [ $i -eq 3 ]; then
            end=382
        else
            end=$((start + 100))
        fi

        session_name="trans_${session_base}_${i}"

        # Kill existing session if any
        tmux kill-session -t "$session_name" 2>/dev/null

        # Create new session
        tmux new-session -d -s "$session_name" \
            "python3 tmux_batch_translator.py --language '$code' --start $start --end $end --api-key $i 2>&1 | tee logs/trans_${session_base}_${i}.log"

        echo "  Started: $session_name (entries $start-$end) [API key $i]"

        # Longer delay between sessions
        sleep 3
    done

    # Delay between languages
    echo "  Waiting 10 seconds before next language..."
    sleep 10
done

echo ""
echo "=========================================="
echo "Batch 3a sessions started!"
echo ""
echo "Monitor with:"
echo "  tmux ls | grep trans_"
echo "  ./check_progress.sh"
echo "  tail -f logs/trans_*.log"
echo ""
echo "After Batch 3a completes, run:"
echo "  ./start_batch3b_limited.sh  (for next 3 languages)"
echo "  ./start_batch3c_limited.sh  (for last 2 languages)"
echo "=========================================="