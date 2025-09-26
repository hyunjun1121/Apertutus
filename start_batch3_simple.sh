#!/bin/bash

# Batch 3: Next 8 languages (언어 코드만 사용)
echo "=========================================="
echo "Starting Batch 3 Translation (8 languages)"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Create logs directory if it doesn't exist
mkdir -p logs

# Batch 3 languages - 언어 코드만 사용
LANGUAGES=(
    "fas.Arab"
    "ukr.Cyrl"
    "hun.Latn"
    "swe.Latn"
    "ell.Grek"
    "dan.Latn"
    "vie.Latn"
    "tha.Thai"
)

echo ""
echo "Languages to translate:"
for code in "${LANGUAGES[@]}"; do
    echo "  - $code"
done

echo ""
echo "Starting tmux sessions..."
echo "=========================================="

# Start tmux sessions for each language
for code in "${LANGUAGES[@]}"; do
    # Replace dots with underscores for tmux session names
    session_base=$(echo "$code" | tr '.' '_')

    echo "Starting translation for $code..."

    # Create 4 tmux sessions (382 entries / 100 = 4 parts)
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

        # Create new session - 언어 코드만 전달
        tmux new-session -d -s "$session_name" \
            "python3 tmux_batch_translator.py --language '$code' --start $start --end $end 2>&1 | tee logs/trans_${session_base}_${i}.log"

        echo "  Started: $session_name (entries $start-$end)"

        # Small delay to avoid overwhelming the API
        sleep 1
    done
done

echo ""
echo "=========================================="
echo "All Batch 3 sessions started!"
echo ""
echo "Monitor with:"
echo "  tmux ls | grep trans_"
echo "  ./check_progress.sh"
echo "  tail -f logs/trans_*.log"
echo ""
echo "Attach to a session:"
echo "  tmux attach -t trans_fas_Arab_0"
echo "=========================================="