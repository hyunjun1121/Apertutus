import json
import time
from apertus_api import ApertusAPI

def test_api():
    print("Testing API connection...", flush=True)

    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Test first API key
    api_key = config['api_keys'][0]
    print(f"Using first API key", flush=True)

    api = ApertusAPI([api_key])

    # Simple test message
    messages = [{"role": "user", "content": "Hello"}]

    print("Calling API...", flush=True)
    start = time.time()

    try:
        response = api.call_model(
            messages=messages,
            temperature=0.7,
            max_tokens=50
        )

        elapsed = time.time() - start
        print(f"API call took {elapsed:.1f} seconds", flush=True)

        if response:
            print(f"Success! Response length: {len(response)} chars", flush=True)
            print(f"Response: {response[:100]}...", flush=True)
        else:
            print("Failed: No response", flush=True)

    except Exception as e:
        elapsed = time.time() - start
        print(f"Error after {elapsed:.1f} seconds: {e}", flush=True)

if __name__ == "__main__":
    test_api()