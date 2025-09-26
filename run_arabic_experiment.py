import sys
from llm_response_generator import main

# Run Arabic dataset experiment using original Swisscom API
if __name__ == "__main__":
    # Process Arabic dataset
    # Arguments: language_code [start_index] [end_index]
    print("Starting Arabic dataset experiment with Apertus-70B...")

    # You can specify start and end indices if you want to process a subset
    # For example: main(["arb.Arab", "0", "100"]) for first 100 samples

    # Process entire Arabic dataset
    main(["arb.Arab"])

    print("Arabic dataset processing complete!")