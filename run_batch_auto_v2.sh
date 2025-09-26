#!/bin/bash

# Automated batch runner for 8 languages at a time
# Updated for 382 entries (4 sessions per language instead of 6)

echo "=========================================="
echo "AUTOMATED 8-LANGUAGE BATCH RUNNER V2"
echo "=========================================="
echo ""

# Configuration
ENTRIES_PER_SESSION=100
TOTAL_ENTRIES=382  # Updated from 537
BATCH_NUMBER=${1:-1}  # Default to batch 1 if no argument

# Define all 4 batches
declare -a BATCH1=("por.Latn" "pol.Latn" "nld.Latn" "ind.Latn" "tur.Latn" "ces.Latn" "arb.Arab" "ron.Latn")
declare -a BATCH2=("fas.Arab" "ukr.Cyrl" "hun.Latn" "swe.Latn" "ell.Grek" "dan.Latn" "vie.Latn" "tha.Thai")
declare -a BATCH3=("nob.Latn" "fin.Latn" "slk.Latn" "bul.Cyrl" "hrv.Latn" "hin.Deva" "bos.Latn" "cat.Latn")
declare -a BATCH4=("ben.Beng" "heb.Hebr" "lit.Latn" "slv.Latn" "ekk.Latn" "zsm.Latn" "als.Latn" "lvs.Latn")

# Select batch
case $BATCH_NUMBER in
    1) LANGUAGES=("${BATCH1[@]}") ;;
    2) LANGUAGES=("${BATCH2[@]}") ;;
    3) LANGUAGES=("${BATCH3[@]}") ;;
    4) LANGUAGES=("${BATCH4[@]}") ;;
    *) echo "Invalid batch number. Use 1-4"; exit 1 ;;
esac

echo "Starting Batch $BATCH_NUMBER"
echo "Languages: ${LANGUAGES[*]}"
echo "Total entries: $TOTAL_ENTRIES (reduced from 537)"
echo ""

# Kill existing sessions
echo "Cleaning up existing sessions..."
tmux ls 2>/dev/null | grep trans_ | cut -d: -f1 | xargs -I{} tmux kill-session -t {} 2>/dev/null

# Start sessions
SESSION_COUNT=0
for LANG in "${LANGUAGES[@]}"; do
    echo "Starting $LANG..."
    API_KEY_INDEX=0

    # Only need 4 sessions now (0-100, 100-200, 200-300, 300-382)
    for START in 0 100 200 300; do
        END=$((START + ENTRIES_PER_SESSION))
        [ $END -gt $TOTAL_ENTRIES ] && END=$TOTAL_ENTRIES

        # Skip if START >= TOTAL_ENTRIES (shouldn't happen with 382)
        if [ $START -ge $TOTAL_ENTRIES ]; then
            break
        fi

        SESSION_NAME="trans_${LANG}_${START}"
        COMMAND="python3 tmux_batch_translator.py --language $LANG --start $START --end $END --api-key $((API_KEY_INDEX % 5))"

        tmux new-session -d -s "$SESSION_NAME" "$COMMAND"

        API_KEY_INDEX=$((API_KEY_INDEX + 1))
        SESSION_COUNT=$((SESSION_COUNT + 1))
        sleep 0.5
    done

    echo "  Started 4 sessions for $LANG"
done

echo ""
echo "=========================================="
echo "Batch $BATCH_NUMBER started!"
echo "Total sessions: $SESSION_COUNT (should be 32)"
echo "Active sessions: $(tmux ls | grep trans_ | wc -l)"
echo ""
echo "Monitor with: ./check_progress.sh"
echo "Next batch: ./run_batch_auto_v2.sh $((BATCH_NUMBER + 1))"
echo ""
echo "Sessions per language: 4 (0-100, 100-200, 200-300, 300-382)"
echo "Total: 8 languages × 4 sessions = 32 sessions"
echo "=========================================="