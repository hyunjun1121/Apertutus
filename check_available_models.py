import json
import requests

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

api_key = config['api_keys'][0]
base_url = config['api_base_url']

# Try to get models list
headers = {
    "Authorization": f"Bearer {api_key}"
}

# Common endpoints to check
endpoints = [
    f"{base_url}/models",
    f"{base_url.replace('/v1', '')}/models",
    "https://api.swisscom.com/layer/swiss-ai-weeks/models",
]

print("Checking available models...")
print("=" * 60)

for endpoint in endpoints:
    try:
        print(f"\nTrying: {endpoint}")
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("Response:", json.dumps(data, indent=2))

            # Try to extract model names
            if 'data' in data:
                print("\nAvailable models:")
                for model in data['data']:
                    if 'id' in model:
                        print(f"  - {model['id']}")
        else:
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"Error: {e}")

# Also test specific model names
print("\n" + "=" * 60)
print("Testing specific model names with chat completions:")
print("=" * 60)

test_models = [
    "swiss-ai/Apertus-70B",
    "swiss-ai/Apertus-8B",
    "Apertus-70B",
    "Apertus-8B",
    "apertus-70b",
    "apertus-8b"
]

for model_name in test_models:
    print(f"\nTesting model: {model_name}")

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10
            },
            timeout=10
        )

        if response.status_code == 200:
            print(f"  [SUCCESS] - Model '{model_name}' works!")
            result = response.json()
            if 'model' in result:
                print(f"    Returned model name: {result['model']}")
        else:
            error_data = response.json()
            if 'error' in error_data:
                print(f"  [FAILED] - {error_data['error'].get('message', 'Unknown error')}")
            else:
                print(f"  [FAILED] - Status {response.status_code}")

    except Exception as e:
        print(f"  [ERROR] - {e}")