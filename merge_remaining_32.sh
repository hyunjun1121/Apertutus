#!/bin/bash

# Merge results for remaining 32 languages

echo "=========================================="
echo "MERGING REMAINING 32 LANGUAGES"
echo "=========================================="
echo ""

# Remaining 32 languages
REMAINING_LANGUAGES=(
    "por.Latn" "pol.Latn" "nld.Latn" "ind.Latn" "tur.Latn"
    "ces.Latn" "arb.Arab" "ron.Latn" "fas.Arab" "ukr.Cyrl"
    "hun.Latn" "swe.Latn" "ell.Grek" "dan.Latn" "vie.Latn"
    "tha.Thai" "nob.Latn" "fin.Latn" "slk.Latn" "bul.Cyrl"
    "hrv.Latn" "hin.Deva" "bos.Latn" "cat.Latn" "ben.Beng"
    "heb.Hebr" "lit.Latn" "slv.Latn" "ekk.Latn" "zsm.Latn"
    "als.Latn" "lvs.Latn"
)

SUCCESS_COUNT=0
FAIL_COUNT=0

echo "Checking and merging part files..."
echo ""

for LANG in "${REMAINING_LANGUAGES[@]}"; do
    # Check if parts exist
    PART_COUNT=$(ls multilingual_datasets/mhj_dataset_${LANG}_part*.json 2>/dev/null | wc -l)

    if [ $PART_COUNT -gt 0 ]; then
        echo "Merging $LANG ($PART_COUNT parts)..."
        python3 tmux_batch_translator.py --merge $LANG

        if [ $? -eq 0 ]; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            echo "  ✓ Successfully merged $LANG"

            # Optionally remove part files after successful merge
            # rm multilingual_datasets/mhj_dataset_${LANG}_part*.json
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
            echo "  ✗ Failed to merge $LANG"
        fi
    else
        echo "⚠ No parts found for $LANG"
    fi
done

echo ""
echo "=========================================="
echo "MERGE SUMMARY"
echo "=========================================="
echo "Successfully merged: $SUCCESS_COUNT languages"
echo "Failed: $FAIL_COUNT languages"
echo ""

# Count total final files
TOTAL_FINAL=$(ls multilingual_datasets/mhj_dataset_*.json 2>/dev/null | grep -v "_part" | wc -l)
echo "Total final datasets: $TOTAL_FINAL/40"
echo ""

# Show all final files with sizes
echo "All translated datasets:"
ls -lh multilingual_datasets/mhj_dataset_*.json | grep -v "_part"

echo ""
echo "=========================================="
echo "CLEANUP (Optional)"
echo "=========================================="
echo "To remove part files after successful merge:"
echo "  rm multilingual_datasets/*_part*.json"
echo ""