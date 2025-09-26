#!/bin/bash

# Script to check LLM response generation progress

echo "=========================================="
echo "LLM RESPONSE GENERATION PROGRESS"
echo "Date: $(date)"
echo "=========================================="

# Check tmux sessions
echo ""
echo "Active TMux Sessions:"
tmux ls 2>/dev/null | grep llm || echo "  No LLM sessions running"

# Check filtered datasets
echo ""
echo "=========================================="
echo "FILTERED DATASETS (382 entries expected)"
echo "=========================================="

if [ -d "multilingual_datasets_filtered" ]; then
    for file in multilingual_datasets_filtered/mhj_dataset_*.json; do
        if [ -f "$file" ]; then
            lang=$(basename "$file" | sed 's/mhj_dataset_//g' | sed 's/.json//g')
            count=$(python3 -c "import json; data=json.load(open('$file')); print(len(data))" 2>/dev/null)
            if [ "$count" == "382" ]; then
                echo "✓ $lang - $count entries"
            else
                echo "⚠ $lang - $count entries (expected 382)"
            fi
        fi
    done
else
    echo "No filtered datasets found"
fi

# Check LLM responses
echo ""
echo "=========================================="
echo "LLM RESPONSES GENERATED"
echo "=========================================="

if [ -d "llm_responses" ]; then
    total_languages=0
    completed_languages=0

    for file in multilingual_datasets_filtered/mhj_dataset_*.json; do
        if [ -f "$file" ]; then
            ((total_languages++))
            lang=$(basename "$file" | sed 's/mhj_dataset_//g' | sed 's/.json//g')
            response_file="llm_responses/mhj_dataset_${lang}_with_responses.json"

            if [ -f "$response_file" ]; then
                response_count=$(python3 -c "import json; data=json.load(open('$response_file')); print(len(data))" 2>/dev/null)
                valid_count=$(python3 -c "
import json
data = json.load(open('$response_file'))
valid = sum(1 for entry in data if entry.get('llm_response') and not entry['llm_response'].startswith('ERROR'))
print(valid)
" 2>/dev/null)

                if [ "$response_count" == "382" ]; then
                    echo "✓ $lang - $response_count entries ($valid_count valid responses)"
                    ((completed_languages++))
                else
                    echo "◐ $lang - $response_count/382 entries ($valid_count valid responses)"
                fi
            else
                echo "✗ $lang - Not started"
            fi
        fi
    done

    echo ""
    echo "=========================================="
    echo "SUMMARY"
    echo "=========================================="
    echo "Completed: $completed_languages/$total_languages languages"
else
    echo "No responses directory found"
fi

# Check log file
echo ""
echo "=========================================="
echo "RECENT LOG ENTRIES"
echo "=========================================="
if [ -f "llm_response_gen.log" ]; then
    echo "Last 10 lines of log:"
    tail -10 llm_response_gen.log
else
    echo "No log file found"
fi

# Check disk usage
echo ""
echo "=========================================="
echo "DISK USAGE"
echo "=========================================="
echo "Filtered datasets: $(du -sh multilingual_datasets_filtered 2>/dev/null | cut -f1)"
echo "LLM responses: $(du -sh llm_responses 2>/dev/null | cut -f1)"