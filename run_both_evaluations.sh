#!/bin/bash

# Create tmux session for GPT-4.1 StrongReject evaluations

# Kill existing sessions if they exist
tmux kill-session -t gpt_english 2>/dev/null
tmux kill-session -t gpt_translated 2>/dev/null

echo "Creating tmux sessions for parallel GPT-4.1 evaluations..."

# Create session for English template evaluation
tmux new-session -d -s gpt_english -n "English_Eval"
tmux send-keys -t gpt_english "cd $(pwd)" C-m
tmux send-keys -t gpt_english "echo 'Starting GPT-4.1 English Template Evaluation...'" C-m
tmux send-keys -t gpt_english "python3 run_strongreject_gpt_parallel.py --workers 40" C-m

# Create session for Translated template evaluation
tmux new-session -d -s gpt_translated -n "Translated_Eval"
tmux send-keys -t gpt_translated "cd $(pwd)" C-m
tmux send-keys -t gpt_translated "echo 'Starting GPT-4.1 Translated Template Evaluation...'" C-m
tmux send-keys -t gpt_translated "python3 run_strongreject_gpt_translated.py --workers 40" C-m

echo ""
echo "✅ Tmux sessions created successfully!"
echo ""
echo "Session 1: gpt_english (English Template)"
echo "Session 2: gpt_translated (Translated Template)"
echo ""
echo "To attach to sessions:"
echo "  tmux attach -t gpt_english"
echo "  tmux attach -t gpt_translated"
echo ""
echo "To list all sessions:"
echo "  tmux ls"
echo ""
echo "To switch between sessions (while attached):"
echo "  Ctrl+B, then D (detach)"
echo "  tmux attach -t <session_name>"
echo ""
echo "To kill sessions when done:"
echo "  tmux kill-session -t gpt_english"
echo "  tmux kill-session -t gpt_translated"
echo ""
