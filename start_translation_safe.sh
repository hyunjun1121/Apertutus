#!/bin/bash

# Safe translation with proper rate limiting
# 5 API keys, 5 req/sec total = 1 req/sec per key

echo "=========================================="
echo "SAFE TRANSLATION WITH RATE LIMITING"
echo "Date: $(date)"
echo "=========================================="

cd /eic/data/hkim_gpu2/Apertutus

# Create logs directory
mkdir -p logs

# Get language code as argument
LANGUAGE=$1

if [ -z "$LANGUAGE" ]; then
    echo "Usage: ./start_translation_safe.sh <language_code>"
    echo "Example: ./start_translation_safe.sh fas.Arab"
    exit 1
fi

echo "Starting translation for: $LANGUAGE"
echo "Using sequential processing to avoid rate limits"
echo "=========================================="

# Replace dots with underscores for session name
session_base=$(echo "$LANGUAGE" | tr '.' '_')
session_name="trans_${session_base}_safe"

# Kill existing session
tmux kill-session -t "$session_name" 2>/dev/null

# Run single session with all 382 entries
# This will process sequentially with proper delays
tmux new-session -d -s "$session_name" \
    "python3 -c \"
import json
import time
from tmux_batch_translator import TmuxBatchTranslator
import sys

# Load dataset
with open('mhj_dataset.json', 'r') as f:
    dataset = json.load(f)

# Filter to 382 entries
dataset = [e for e in dataset if e.get('num_turns', 0) <= 6][:382]

# Find language
with open('config.json', 'r') as f:
    config = json.load(f)

target_lang = None
for lang in config['languages']:
    if lang['code'] == '$LANGUAGE':
        target_lang = lang
        break

if not target_lang:
    print('Language $LANGUAGE not found')
    sys.exit(1)

print(f'Starting translation to {target_lang[\"name\"]}')
print('Processing 382 entries with rate limiting...')

translator = TmuxBatchTranslator()

# Process in small batches with delays
batch_size = 10
for i in range(0, 382, batch_size):
    end = min(i + batch_size, 382)
    print(f'Processing entries {i}-{end}...')

    translator.translate_language_range(
        dataset,
        target_lang,
        i,
        end
    )

    # 10 second delay between batches
    if end < 382:
        print(f'Waiting 10 seconds before next batch...')
        time.sleep(10)

print('Translation complete!')
\" 2>&1 | tee logs/trans_${session_base}_safe.log"

echo ""
echo "Session started: $session_name"
echo ""
echo "Monitor with:"
echo "  tmux attach -t $session_name"
echo "  tail -f logs/trans_${session_base}_safe.log"
echo ""
echo "This will take approximately 1-2 hours per language"
echo "=========================================="