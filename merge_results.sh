#!/bin/bash

# Merge translation results

echo "=========================================="
echo "MERGING TRANSLATION RESULTS"
echo "=========================================="
echo ""

# Languages to merge
LANGUAGES=(
    "kor.Hang"
    "fra.Latn"
    "deu.Latn"
    "spa.Latn"
    "jpn.Jpan"
    "rus.Cyrl"
    "cmn.Hani"
    "ita.Latn"
    "por.Latn"
    "pol.Latn"
    "nld.Latn"
    "ind.Latn"
    "tur.Latn"
    "ces.Latn"
    "arb.Arab"
    "ron.Latn"
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

SUCCESS_COUNT=0
FAIL_COUNT=0

for LANG in "${LANGUAGES[@]}"; do
    # Check if parts exist
    if ls multilingual_datasets/mhj_dataset_${LANG}_part*.json 1> /dev/null 2>&1; then
        echo "Merging $LANG..."
        python3 tmux_batch_translator.py --merge $LANG

        if [ $? -eq 0 ]; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))

            # Optionally remove part files after successful merge
            # rm multilingual_datasets/mhj_dataset_${LANG}_part*.json
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
            echo "  Failed to merge $LANG"
        fi
    else
        echo "No parts found for $LANG, skipping..."
    fi
done

echo ""
echo "=========================================="
echo "MERGE COMPLETE"
echo "=========================================="
echo "Successfully merged: $SUCCESS_COUNT languages"
echo "Failed: $FAIL_COUNT languages"
echo ""

# Show final files
echo "Final translated datasets:"
ls -la multilingual_datasets/mhj_dataset_*.json | grep -v "_part"