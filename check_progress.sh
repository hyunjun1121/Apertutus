#!/bin/bash

# Check translation progress

echo "=========================================="
echo "TRANSLATION PROGRESS CHECK"
echo "=========================================="
echo ""

# Count active sessions
ACTIVE=$(tmux ls 2>/dev/null | grep "trans_" | wc -l)
echo "Active sessions: $ACTIVE"
echo ""

# Check output files
echo "Completed parts:"
ls -la multilingual_datasets/*_part*.json 2>/dev/null | wc -l
echo ""

# Show details per language
echo "Progress by language:"
for LANG in "kor.Hang" "fra.Latn" "deu.Latn" "spa.Latn" "jpn.Jpan" "rus.Cyrl" "cmn.Hani" "ita.Latn"; do
    COUNT=$(ls multilingual_datasets/mhj_dataset_${LANG}_part*.json 2>/dev/null | wc -l)
    if [ $COUNT -gt 0 ]; then
        echo "  $LANG: $COUNT parts completed"
    fi
done

echo ""
echo "To see specific session output:"
echo "  tmux attach -t <session_name>"
echo ""