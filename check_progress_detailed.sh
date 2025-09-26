#!/bin/bash

# Detailed progress check for all 40 languages

echo "=========================================="
echo "DETAILED TRANSLATION PROGRESS"
echo "$(date)"
echo "=========================================="
echo ""

# All 40 languages
ALL_LANGUAGES=(
    # Already completed (8)
    "kor.Hang" "fra.Latn" "deu.Latn" "spa.Latn"
    "jpn.Jpan" "rus.Cyrl" "cmn.Hani" "ita.Latn"
    # Remaining (32)
    "por.Latn" "pol.Latn" "nld.Latn" "ind.Latn" "tur.Latn"
    "ces.Latn" "arb.Arab" "ron.Latn" "fas.Arab" "ukr.Cyrl"
    "hun.Latn" "swe.Latn" "ell.Grek" "dan.Latn" "vie.Latn"
    "tha.Thai" "nob.Latn" "fin.Latn" "slk.Latn" "bul.Cyrl"
    "hrv.Latn" "hin.Deva" "bos.Latn" "cat.Latn" "ben.Beng"
    "heb.Hebr" "lit.Latn" "slv.Latn" "ekk.Latn" "zsm.Latn"
    "als.Latn" "lvs.Latn"
)

# Count active sessions
ACTIVE=$(tmux ls 2>/dev/null | grep "trans_" | wc -l)
echo "Active tmux sessions: $ACTIVE"
echo ""

# Count completed files
echo "=========================================="
echo "COMPLETED FINAL FILES"
echo "=========================================="
FINAL_COUNT=0
for LANG in "${ALL_LANGUAGES[@]}"; do
    if [ -f "multilingual_datasets/mhj_dataset_${LANG}.json" ]; then
        SIZE=$(ls -lh "multilingual_datasets/mhj_dataset_${LANG}.json" 2>/dev/null | awk '{print $5}')
        echo "✓ $LANG - $SIZE"
        FINAL_COUNT=$((FINAL_COUNT + 1))
    fi
done
echo ""
echo "Total completed: $FINAL_COUNT/40"
echo ""

# Count part files (in progress)
echo "=========================================="
echo "IN PROGRESS (Part files)"
echo "=========================================="
PART_LANGUAGES=()
for LANG in "${ALL_LANGUAGES[@]}"; do
    PART_COUNT=$(ls multilingual_datasets/mhj_dataset_${LANG}_part*.json 2>/dev/null | wc -l)
    if [ $PART_COUNT -gt 0 ]; then
        echo "◐ $LANG: $PART_COUNT/6 parts"
        PART_LANGUAGES+=($LANG)
    fi
done

if [ ${#PART_LANGUAGES[@]} -eq 0 ]; then
    echo "No part files found"
fi
echo ""

# Not started
echo "=========================================="
echo "NOT STARTED"
echo "=========================================="
NOT_STARTED=()
for LANG in "${ALL_LANGUAGES[@]}"; do
    # Check if neither final nor part files exist
    if [ ! -f "multilingual_datasets/mhj_dataset_${LANG}.json" ]; then
        PART_COUNT=$(ls multilingual_datasets/mhj_dataset_${LANG}_part*.json 2>/dev/null | wc -l)
        if [ $PART_COUNT -eq 0 ]; then
            echo "✗ $LANG"
            NOT_STARTED+=($LANG)
        fi
    fi
done

if [ ${#NOT_STARTED[@]} -eq 0 ]; then
    echo "All languages have been started or completed"
fi
echo ""

# Summary
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo "Completed:    $FINAL_COUNT/40 languages"
echo "In Progress:  ${#PART_LANGUAGES[@]} languages"
echo "Not Started:  ${#NOT_STARTED[@]} languages"
echo "Active TMux:  $ACTIVE sessions"
echo ""

# Disk usage
echo "=========================================="
echo "DISK USAGE"
echo "=========================================="
TOTAL_SIZE=$(du -sh multilingual_datasets 2>/dev/null | cut -f1)
echo "Total size of multilingual_datasets: $TOTAL_SIZE"
echo ""

# Estimate completion time
if [ $ACTIVE -gt 0 ]; then
    echo "=========================================="
    echo "ESTIMATED COMPLETION"
    echo "=========================================="
    echo "With $ACTIVE active sessions:"
    echo "Estimated time: ~30-40 minutes from start"
    echo "Check again in 10 minutes"
fi