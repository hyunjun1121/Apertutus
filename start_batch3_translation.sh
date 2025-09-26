#!/bin/bash

# Batch 3: Next 8 languages
echo "=========================================="
echo "Starting Batch 3 Translation (8 languages)"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Batch 3 languages
LANGUAGES=(
    "fas.Arab:Persian"
    "ukr.Cyrl:Ukrainian"
    "hun.Latn:Hungarian"
    "swe.Latn:Swedish"
    "ell.Grek:Modern Greek"
    "dan.Latn:Danish"
    "vie.Latn:Vietnamese"
    "tha.Thai:Thai"
)

echo ""
echo "Languages to translate:"
for lang_pair in "${LANGUAGES[@]}"; do
    IFS=':' read -r code name <<< "$lang_pair"
    echo "  - $name ($code)"
done

echo ""
echo "Starting tmux sessions..."
echo "=========================================="

# Start tmux sessions for each language
for lang_pair in "${LANGUAGES[@]}"; do
    IFS=':' read -r code name <<< "$lang_pair"

    # Replace dots with underscores for tmux session names
    session_base=$(echo "$code" | tr '.' '_')

    echo "Starting translation for $name ($code)..."

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

        # Create new session
        tmux new-session -d -s "$session_name" \
            "python3 tmux_batch_translator.py --language-code '$code' --language-name '$name' --start $start --end $end 2>&1 | tee logs/trans_${session_base}_${i}.log"

        echo "  Started: $session_name (entries $start-$end)"
    done
done

echo ""
echo "=========================================="
echo "All Batch 3 sessions started!"
echo ""
echo "Monitor with:"
echo "  tmux ls | grep trans_"
echo "  ./check_progress.sh"
echo ""
echo "Attach to a session:"
echo "  tmux attach -t trans_fas_Arab_0"
echo "=========================================="