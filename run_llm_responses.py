import json
import subprocess
import time
from pathlib import Path
import sys

def check_progress():
    """Check progress of LLM response generation"""
    input_dir = Path('multilingual_datasets_filtered')
    output_dir = Path('llm_responses')

    # Get all datasets
    dataset_files = sorted(input_dir.glob('mhj_dataset_*.json'))
    total_languages = len(dataset_files)

    completed = 0
    in_progress = 0
    pending = 0

    print("\nLLM Response Generation Progress:")
    print("=" * 60)

    for dataset_file in dataset_files:
        language_code = dataset_file.stem.replace('mhj_dataset_', '')
        output_file = output_dir / f'mhj_dataset_{language_code}_with_responses.json'

        # Load original dataset to get total count
        with open(dataset_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        total_entries = len(original_data)

        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                response_data = json.load(f)

            # Count entries with valid responses
            valid_responses = sum(1 for entry in response_data
                                 if entry.get('llm_response') and
                                 not entry['llm_response'].startswith('ERROR'))

            if len(response_data) >= total_entries:
                status = "COMPLETE"
                completed += 1
            else:
                status = "IN PROGRESS"
                in_progress += 1

            print(f"{language_code:12} {status:12} {len(response_data)}/{total_entries} entries "
                  f"({valid_responses} valid responses)")
        else:
            print(f"{language_code:12} PENDING      0/{total_entries} entries")
            pending += 1

    print("\n" + "=" * 60)
    print(f"Total: {total_languages} languages")
    print(f"  Completed:   {completed}")
    print(f"  In Progress: {in_progress}")
    print(f"  Pending:     {pending}")

    return completed == total_languages


def main():
    """Run LLM response generation with monitoring"""

    print("Starting LLM Response Generation")
    print("=" * 60)

    # Start the process in background
    cmd = ["python", "parallel_llm_response_generator.py"]

    print(f"Running: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, bufsize=1)

    # Monitor progress
    try:
        last_check = 0
        while process.poll() is None:  # While process is running
            # Read output
            if process.stdout:
                line = process.stdout.readline()
                if line:
                    print(line.strip())

            # Check progress every 30 seconds
            current_time = time.time()
            if current_time - last_check > 30:
                check_progress()
                last_check = current_time

            time.sleep(0.1)

        # Process finished
        return_code = process.poll()

        # Read remaining output
        if process.stdout:
            for line in process.stdout:
                print(line.strip())

        if process.stderr:
            stderr = process.stderr.read()
            if stderr:
                print("Errors:", stderr)

        print(f"\nProcess finished with return code: {return_code}")

        # Final progress check
        check_progress()

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        process.terminate()
        process.wait()
        check_progress()


if __name__ == "__main__":
    main()