#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./safety_lora_adapter_${TIMESTAMP}"
PYTHON_CMD="python3"

echo "=========================================="
echo "APERTUS SAFETY LORA FINE-TUNING (DIRECT)"
echo "Date: $(date)"
echo "Output Directory: $OUTPUT_DIR"
echo "=========================================="

echo -e "\n[Step 1] Using Python module directly..."
echo "Python: $($PYTHON_CMD --version)"

echo -e "\n[Step 2] Checking required packages..."
for package in accelerate transformers datasets torch peft; do
    if $PYTHON_CMD -c "import $package; print(f'  ✓ {package.__name__} v{package.__version__}')" 2>/dev/null; then
        :
    else
        echo "  ✗ $package - NOT FOUND"
        exit 1
    fi
done

echo -e "\n[Step 3] Checking GPU..."
$PYTHON_CMD -c "
import torch
print(f'GPU Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU Count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'  GPU {i}: {torch.cuda.get_device_name(i)}')
"

echo -e "\n[Step 4] Checking for safety_finetuning.py..."
if [ ! -f "safety_finetuning.py" ]; then
    echo "ERROR: safety_finetuning.py not found!"
    echo "Creating a basic template..."
    cat > safety_finetuning.py << 'EOF'
#!/usr/bin/env python3
import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
import torch

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", default="meta-llama/Llama-2-7b-hf")
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--num_train_epochs", type=int, default=3)
    parser.add_argument("--per_device_train_batch_size", type=int, default=4)
    parser.add_argument("--learning_rate", type=float, default=5e-5)
    args = parser.parse_args()

    print(f"Loading model: {args.model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # LoRA configuration
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=8,
        lora_alpha=32,
        lora_dropout=0.1,
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Load your dataset here
    # dataset = load_dataset("your_dataset")

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.num_train_epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        learning_rate=args.learning_rate,
        logging_steps=10,
        save_steps=100,
        evaluation_strategy="steps",
        eval_steps=100,
        save_total_limit=2,
        load_best_model_at_end=True,
    )

    # Add your trainer setup here
    print(f"Training would start with output to: {args.output_dir}")
    print("Note: This is a template. Add your dataset and trainer code.")

if __name__ == "__main__":
    main()
EOF
    echo "Template created. Please modify it with your actual training code."
fi

echo -e "\n[Step 5] Starting fine-tuning with Python module..."
echo "Command: $PYTHON_CMD -m accelerate.commands.launch safety_finetuning.py \\"
echo "  --model_name \"meta-llama/Llama-2-7b-hf\" \\"
echo "  --output_dir \"$OUTPUT_DIR\""

$PYTHON_CMD -m accelerate.commands.launch safety_finetuning.py \
    --model_name "meta-llama/Llama-2-7b-hf" \
    --output_dir "$OUTPUT_DIR" \
    --num_train_epochs 3 \
    --per_device_train_batch_size 4 \
    --learning_rate 5e-5 || {
    echo "=========================================="
    echo "ERROR: Fine-tuning failed!"
    echo "Check the error messages above."
    echo "=========================================="
    exit 1
}

echo "=========================================="
echo "Fine-tuning completed successfully!"
echo "LoRA adapter saved to: $OUTPUT_DIR"
echo "=========================================="