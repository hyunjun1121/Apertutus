#!/bin/bash

# Run remaining 32 languages translation
# Total: 32 languages × 6 sessions = 192 tmux sessions

echo "=========================================="
echo "STARTING REMAINING 32 LANGUAGES"
echo "=========================================="
echo ""

# Remaining 32 languages (excluding already completed 8)
REMAINING_LANGUAGES=(
    "por.Latn"  # Portuguese
    "pol.Latn"  # Polish
    "nld.Latn"  # Dutch
    "ind.Latn"  # Indonesian
    "tur.Latn"  # Turkish
    "ces.Latn"  # Czech
    "arb.Arab"  # Arabic
    "ron.Latn"  # Romanian
    "fas.Arab"  # Persian
    "ukr.Cyrl"  # Ukrainian
    "hun.Latn"  # Hungarian
    "swe.Latn"  # Swedish
    "ell.Grek"  # Greek
    "dan.Latn"  # Danish
    "vie.Latn"  # Vietnamese
    "tha.Thai"  # Thai
    "nob.Latn"  # Norwegian
    "fin.Latn"  # Finnish
    "slk.Latn"  # Slovak
    "bul.Cyrl"  # Bulgarian
    "hrv.Latn"  # Croatian
    "hin.Deva"  # Hindi
    "bos.Latn"  # Bosnian
    "cat.Latn"  # Catalan
    "ben.Beng"  # Bengali
    "heb.Hebr"  # Hebrew
    "lit.Latn"  # Lithuanian
    "slv.Latn"  # Slovenian
    "ekk.Latn"  # Estonian
    "zsm.Latn"  # Malay
    "als.Latn"  # Albanian
    "lvs.Latn"  # Latvian
)

# Configuration
ENTRIES_PER_SESSION=100
TOTAL_ENTRIES=537
SESSION_COUNT=0
LANG_COUNT=0

# Kill any existing sessions for these languages (cleanup)
echo "Cleaning up any existing sessions for remaining languages..."
for LANG in "${REMAINING_LANGUAGES[@]}"; do
    tmux ls 2>/dev/null | grep "trans_${LANG}_" | cut -d: -f1 | xargs -I{} tmux kill-session -t {} 2>/dev/null
done

echo "Starting translation sessions..."
echo ""

# Start sessions for each language
for LANG in "${REMAINING_LANGUAGES[@]}"; do
    LANG_COUNT=$((LANG_COUNT + 1))
    echo "[$LANG_COUNT/32] Starting sessions for $LANG..."

    API_KEY_INDEX=$((LANG_COUNT % 5))  # Distribute across 5 API keys

    for START in 0 100 200 300 400 500; do
        END=$((START + ENTRIES_PER_SESSION))
        if [ $END -gt $TOTAL_ENTRIES ]; then
            END=$TOTAL_ENTRIES
        fi

        SESSION_NAME="trans_${LANG}_${START}"
        COMMAND="python3 tmux_batch_translator.py --language $LANG --start $START --end $END --api-key $API_KEY_INDEX"

        echo "  Starting $SESSION_NAME (entries $START-$END, API key $API_KEY_INDEX)"
        tmux new-session -d -s "$SESSION_NAME" "$COMMAND"

        SESSION_COUNT=$((SESSION_COUNT + 1))
        API_KEY_INDEX=$(((API_KEY_INDEX + 1) % 5))  # Rotate API keys

        # Small delay to avoid overwhelming
        sleep 0.3
    done

    echo "  ✓ Started 6 sessions for $LANG"
    echo ""
done

echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo "Languages processed: ${#REMAINING_LANGUAGES[@]}"
echo "Total sessions started: $SESSION_COUNT"
echo ""
echo "Active sessions:"
tmux ls | grep trans_ | wc -l

echo ""
echo "=========================================="
echo "NEXT STEPS"
echo "=========================================="
echo "1. Monitor progress:"
echo "   ./check_progress.sh"
echo ""
echo "2. Watch real-time (updates every 60 seconds):"
echo "   watch -n 60 './check_progress.sh'"
echo ""
echo "3. After completion (~30-40 minutes), merge results:"
echo "   ./merge_remaining_32.sh"
echo ""
echo "4. Or merge all 40 languages at once:"
echo "   ./merge_results.sh"
echo ""