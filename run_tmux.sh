#!/bin/bash

# Tmux parallel translation script
# Run translations in parallel using multiple tmux sessions

echo "=========================================="
echo "TMUX PARALLEL TRANSLATION SYSTEM"
echo "=========================================="

# Configuration
ENTRIES_PER_SESSION=100  # Adjust based on your needs
TOTAL_ENTRIES=537

# Languages to translate (you can modify this list)
LANGUAGES=(
    "kor.Hang"
    "fra.Latn"
    "deu.Latn"
    "spa.Latn"
    "jpn.Jpan"
    "rus.Cyrl"
    "cmn.Hani"
    "ita.Latn"
)

# Kill existing translation sessions
echo "Cleaning up existing sessions..."
tmux ls 2>/dev/null | grep "trans_" | cut -d: -f1 | xargs -I{} tmux kill-session -t {} 2>/dev/null

# Start translation sessions
SESSION_COUNT=0
API_KEY_INDEX=0

for LANG in "${LANGUAGES[@]}"; do
    echo "Starting sessions for $LANG..."

    for START in $(seq 0 $ENTRIES_PER_SESSION $((TOTAL_ENTRIES-1))); do
        END=$((START + ENTRIES_PER_SESSION))
        if [ $END -gt $TOTAL_ENTRIES ]; then
            END=$TOTAL_ENTRIES
        fi

        SESSION_NAME="trans_${LANG}_${START}"
        COMMAND="python3 tmux_batch_translator.py --language $LANG --start $START --end $END --api-key $API_KEY_INDEX"

        echo "  Starting $SESSION_NAME (entries $START-$END, API key $API_KEY_INDEX)"
        tmux new-session -d -s "$SESSION_NAME" "$COMMAND"

        SESSION_COUNT=$((SESSION_COUNT + 1))
        API_KEY_INDEX=$(((API_KEY_INDEX + 1) % 5))  # Rotate through 5 API keys

        # Small delay to avoid overwhelming
        sleep 0.5
    done
done

echo ""
echo "=========================================="
echo "Started $SESSION_COUNT tmux sessions"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  tmux ls                    # List all sessions"
echo "  tmux attach -t <session>   # Attach to a session"
echo "  ./check_progress.sh        # Check progress"
echo "  ./merge_results.sh         # Merge results after completion"
echo ""