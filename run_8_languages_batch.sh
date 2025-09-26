#!/bin/bash

# Run 8 languages at a time (like the first successful batch)
# Total: 32 remaining languages / 8 = 4 batches

echo "=========================================="
echo "8 LANGUAGES BATCH TRANSLATION SYSTEM"
echo "=========================================="
echo ""

# All 32 remaining languages
ALL_REMAINING=(
    "por.Latn" "pol.Latn" "nld.Latn" "ind.Latn" "tur.Latn" "ces.Latn" "arb.Arab" "ron.Latn"     # Batch 1
    "fas.Arab" "ukr.Cyrl" "hun.Latn" "swe.Latn" "ell.Grek" "dan.Latn" "vie.Latn" "tha.Thai"     # Batch 2
    "nob.Latn" "fin.Latn" "slk.Latn" "bul.Cyrl" "hrv.Latn" "hin.Deva" "bos.Latn" "cat.Latn"     # Batch 3
    "ben.Beng" "heb.Hebr" "lit.Latn" "slv.Latn" "ekk.Latn" "zsm.Latn" "als.Latn" "lvs.Latn"     # Batch 4
)

# Configuration
ENTRIES_PER_SESSION=100
TOTAL_ENTRIES=537

# Function to start one batch of 8 languages
start_batch() {
    local batch_num=$1
    shift
    local languages=("$@")

    echo ""
    echo "=========================================="
    echo "BATCH $batch_num: Starting 8 languages"
    echo "=========================================="
    echo "Languages: ${languages[*]}"
    echo ""

    local session_count=0

    for LANG in "${languages[@]}"; do
        echo "Starting sessions for $LANG..."

        for START in 0 100 200 300 400 500; do
            END=$((START + ENTRIES_PER_SESSION))
            if [ $END -gt $TOTAL_ENTRIES ]; then
                END=$TOTAL_ENTRIES
            fi

            # Distribute API keys across sessions
            API_KEY_INDEX=$((session_count % 5))
            SESSION_NAME="trans_${LANG}_${START}"
            COMMAND="python3 tmux_batch_translator.py --language $LANG --start $START --end $END --api-key $API_KEY_INDEX"

            echo "  Starting $SESSION_NAME (API key $API_KEY_INDEX)"
            tmux new-session -d -s "$SESSION_NAME" "$COMMAND"

            session_count=$((session_count + 1))
            sleep 0.5  # Small delay between sessions
        done

        echo "  ✓ Started 6 sessions for $LANG"
    done

    echo ""
    echo "Batch $batch_num started with $session_count sessions"
    echo "Active tmux sessions: $(tmux ls | grep trans_ | wc -l)"
}

# Main execution
echo "Select batch to run:"
echo "  1) Batch 1: Portuguese, Polish, Dutch, Indonesian, Turkish, Czech, Arabic, Romanian"
echo "  2) Batch 2: Persian, Ukrainian, Hungarian, Swedish, Greek, Danish, Vietnamese, Thai"
echo "  3) Batch 3: Norwegian, Finnish, Slovak, Bulgarian, Croatian, Hindi, Bosnian, Catalan"
echo "  4) Batch 4: Bengali, Hebrew, Lithuanian, Slovenian, Estonian, Malay, Albanian, Latvian"
echo "  5) Run all batches sequentially (with wait time between)"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        # Kill existing sessions
        echo "Cleaning up existing sessions..."
        tmux ls 2>/dev/null | grep trans_ | cut -d: -f1 | xargs -I{} tmux kill-session -t {} 2>/dev/null

        # Batch 1
        BATCH1=("por.Latn" "pol.Latn" "nld.Latn" "ind.Latn" "tur.Latn" "ces.Latn" "arb.Arab" "ron.Latn")
        start_batch 1 "${BATCH1[@]}"
        ;;

    2)
        # Kill existing sessions
        echo "Cleaning up existing sessions..."
        tmux ls 2>/dev/null | grep trans_ | cut -d: -f1 | xargs -I{} tmux kill-session -t {} 2>/dev/null

        # Batch 2
        BATCH2=("fas.Arab" "ukr.Cyrl" "hun.Latn" "swe.Latn" "ell.Grek" "dan.Latn" "vie.Latn" "tha.Thai")
        start_batch 2 "${BATCH2[@]}"
        ;;

    3)
        # Kill existing sessions
        echo "Cleaning up existing sessions..."
        tmux ls 2>/dev/null | grep trans_ | cut -d: -f1 | xargs -I{} tmux kill-session -t {} 2>/dev/null

        # Batch 3
        BATCH3=("nob.Latn" "fin.Latn" "slk.Latn" "bul.Cyrl" "hrv.Latn" "hin.Deva" "bos.Latn" "cat.Latn")
        start_batch 3 "${BATCH3[@]}"
        ;;

    4)
        # Kill existing sessions
        echo "Cleaning up existing sessions..."
        tmux ls 2>/dev/null | grep trans_ | cut -d: -f1 | xargs -I{} tmux kill-session -t {} 2>/dev/null

        # Batch 4
        BATCH4=("ben.Beng" "heb.Hebr" "lit.Latn" "slv.Latn" "ekk.Latn" "zsm.Latn" "als.Latn" "lvs.Latn")
        start_batch 4 "${BATCH4[@]}"
        ;;

    5)
        echo "This will run all 4 batches with 30-minute wait between each."
        echo "Total estimated time: 2-3 hours"
        read -p "Continue? (y/n): " confirm

        if [ "$confirm" = "y" ]; then
            # Kill all existing
            echo "Cleaning up all existing sessions..."
            tmux ls 2>/dev/null | grep trans_ | cut -d: -f1 | xargs -I{} tmux kill-session -t {} 2>/dev/null

            # Run all batches
            BATCH1=("por.Latn" "pol.Latn" "nld.Latn" "ind.Latn" "tur.Latn" "ces.Latn" "arb.Arab" "ron.Latn")
            BATCH2=("fas.Arab" "ukr.Cyrl" "hun.Latn" "swe.Latn" "ell.Grek" "dan.Latn" "vie.Latn" "tha.Thai")
            BATCH3=("nob.Latn" "fin.Latn" "slk.Latn" "bul.Cyrl" "hrv.Latn" "hin.Deva" "bos.Latn" "cat.Latn")
            BATCH4=("ben.Beng" "heb.Hebr" "lit.Latn" "slv.Latn" "ekk.Latn" "zsm.Latn" "als.Latn" "lvs.Latn")

            start_batch 1 "${BATCH1[@]}"
            echo "Waiting 30 minutes before next batch..."
            sleep 1800

            start_batch 2 "${BATCH2[@]}"
            echo "Waiting 30 minutes before next batch..."
            sleep 1800

            start_batch 3 "${BATCH3[@]}"
            echo "Waiting 30 minutes before next batch..."
            sleep 1800

            start_batch 4 "${BATCH4[@]}"
            echo "All batches started!"
        fi
        ;;

    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "MONITORING COMMANDS"
echo "=========================================="
echo "Check progress:"
echo "  ./check_progress.sh"
echo ""
echo "Check specific language:"
echo "  tmux attach -t trans_por.Latn_0"
echo ""
echo "After completion, merge results:"
echo "  ./merge_remaining_32.sh"
echo ""