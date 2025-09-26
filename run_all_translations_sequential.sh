#!/bin/bash

# Run all remaining translations sequentially with rate limiting
echo "=========================================="
echo "SEQUENTIAL TRANSLATION RUNNER"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Remaining 24 languages to translate
LANGUAGES=(
    "fas.Arab"
    "ukr.Cyrl"
    "hun.Latn"
    "swe.Latn"
    "ell.Grek"
    "dan.Latn"
    "vie.Latn"
    "tha.Thai"
    "nob.Latn"
    "fin.Latn"
    "slk.Latn"
    "bul.Cyrl"
    "hrv.Latn"
    "hin.Deva"
    "bos.Latn"
    "cat.Latn"
    "ben.Beng"
    "heb.Hebr"
    "lit.Latn"
    "slv.Latn"
    "ekk.Latn"
    "zsm.Latn"
    "als.Latn"
    "lvs.Latn"
)

echo "Will process ${#LANGUAGES[@]} languages sequentially"
echo "Estimated time: 24-48 hours total"
echo ""

# Process 2 languages at a time to use API keys efficiently
# But with proper rate limiting
for ((i=0; i<${#LANGUAGES[@]}; i+=2)); do
    lang1=${LANGUAGES[$i]}
    lang2=${LANGUAGES[$((i+1))]}

    echo "=========================================="
    echo "Starting batch: $lang1 and $lang2"
    echo "=========================================="

    # Replace dots with underscores for session names
    session1=$(echo "$lang1" | tr '.' '_')
    session2=$(echo "$lang2" | tr '.' '_')

    # Start first language
    echo "Starting $lang1..."
    tmux new-session -d -s "trans_${session1}" \
        "python3 tmux_batch_translator.py --language '$lang1' --start 0 --end 382 --api-key 0 2>&1 | tee logs/trans_${session1}_full.log"

    # Wait 30 seconds before starting second language
    sleep 30

    if [ ! -z "$lang2" ]; then
        echo "Starting $lang2..."
        tmux new-session -d -s "trans_${session2}" \
            "python3 tmux_batch_translator.py --language '$lang2' --start 0 --end 382 --api-key 2 2>&1 | tee logs/trans_${session2}_full.log"
    fi

    echo "Batch started. Waiting for completion..."
    echo "Check progress with: tmux ls | grep trans_"

    # Wait for sessions to complete (check every 5 minutes)
    while true; do
        sleep 300  # 5 minutes

        # Check if sessions are still running
        running1=$(tmux ls 2>/dev/null | grep "trans_${session1}" | wc -l)
        running2=0
        if [ ! -z "$lang2" ]; then
            running2=$(tmux ls 2>/dev/null | grep "trans_${session2}" | wc -l)
        fi

        if [ $running1 -eq 0 ] && [ $running2 -eq 0 ]; then
            echo "Batch completed!"
            break
        else
            echo "Still running... ($running1 + $running2 sessions active)"
        fi
    done

    echo "Waiting 60 seconds before next batch..."
    sleep 60
done

echo ""
echo "=========================================="
echo "ALL TRANSLATIONS COMPLETE!"
echo "=========================================="
echo ""
echo "Check results in: multilingual_datasets/"
echo "Run: ./check_progress_detailed.sh"