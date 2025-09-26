#!/bin/bash

# Server script for running LLM response generation
# This script should be run on the server

echo "=========================================="
echo "LLM RESPONSE GENERATION SETUP"
echo "Date: $(date)"
echo "=========================================="

# Check if running on server
if [ ! -d "/eic/data/hkim_gpu2/Apertutus" ]; then
    echo "Error: This script should be run on the server"
    echo "Expected directory: /eic/data/hkim_gpu2/Apertutus"
    exit 1
fi

cd /eic/data/hkim_gpu2/Apertutus

# Step 1: Filter completed datasets to 382 entries
echo ""
echo "Step 1: Filtering completed datasets..."
echo "=========================================="

# Create filtered directory if not exists
mkdir -p multilingual_datasets_filtered

# List of completed languages (16 languages)
COMPLETED_LANGUAGES=(
    "kor.Hang" "fra.Latn" "deu.Latn" "spa.Latn"
    "jpn.Jpan" "rus.Cyrl" "cmn.Hani" "ita.Latn"
    "por.Latn" "pol.Latn" "nld.Latn" "ind.Latn"
    "tur.Latn" "ces.Latn" "arb.Arab" "ron.Latn"
)

# Filter each dataset
for lang in "${COMPLETED_LANGUAGES[@]}"; do
    input_file="multilingual_datasets/mhj_dataset_${lang}.json"
    output_file="multilingual_datasets_filtered/mhj_dataset_${lang}.json"

    if [ -f "$input_file" ]; then
        echo "Filtering $lang..."
        python3 -c "
import json

# Load dataset
with open('$input_file', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter to max 6 turns
filtered = [entry for entry in data if entry.get('num_turns', 0) <= 6]

# Save filtered dataset
with open('$output_file', 'w', encoding='utf-8') as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print(f'  Original: {len(data)} entries')
print(f'  Filtered: {len(filtered)} entries')
"
    else
        echo "  Warning: $input_file not found"
    fi
done

echo ""
echo "Step 2: Setting up LLM response generation"
echo "=========================================="

# Create llm_responses directory
mkdir -p llm_responses

# Check if parallel_llm_response_generator.py exists
if [ ! -f "parallel_llm_response_generator.py" ]; then
    echo "Error: parallel_llm_response_generator.py not found"
    echo "Please upload the required Python scripts"
    exit 1
fi

echo ""
echo "Step 3: Starting LLM response generation"
echo "=========================================="

# Run in tmux for persistence
SESSION_NAME="llm_response_gen"

# Kill existing session if any
tmux kill-session -t $SESSION_NAME 2>/dev/null

# Create new tmux session
echo "Starting tmux session: $SESSION_NAME"
tmux new-session -d -s $SESSION_NAME "python3 parallel_llm_response_generator.py 2>&1 | tee llm_response_gen.log"

echo ""
echo "=========================================="
echo "LLM response generation started in tmux session: $SESSION_NAME"
echo ""
echo "To monitor progress:"
echo "  tmux attach -t $SESSION_NAME"
echo ""
echo "To check logs:"
echo "  tail -f llm_response_gen.log"
echo ""
echo "To check progress:"
echo "  ./check_llm_progress.sh"
echo "=========================================="