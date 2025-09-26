import json
import requests

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

api_key = config['api_keys'][0]

# Check different possible endpoints for 8B model
print("Checking for Apertus-8B model...")
print("=" * 60)

# Try different base URLs
base_urls = [
    "https://api.swisscom.com/layer/swiss-ai-weeks/apertus-8b/v1",
    "https://api.swisscom.com/layer/swiss-ai-weeks/Apertus-8B/v1",
    "https://api.swisscom.com/layer/swiss-ai-weeks/swiss-ai-Apertus-8B/v1",
]

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Test each base URL
for base_url in base_urls:
    print(f"\n1. Testing base URL: {base_url}")

    # Try to get models list
    try:
        response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
        print(f"   Models endpoint status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Available models: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"   Models endpoint error: {e}")

    # Try chat completion
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": "swiss-ai/Apertus-8B",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10
            },
            timeout=10
        )
        print(f"   Chat completion status: {response.status_code}")
        if response.status_code == 200:
            print(f"   [SUCCESS] 8B model works at this endpoint!")
            result = response.json()
            print(f"   Response: {result.get('choices', [{}])[0].get('message', {}).get('content', '')[:50]}")
        else:
            print(f"   Error: {response.json()}")
    except Exception as e:
        print(f"   Chat completion error: {e}")

# Also try different model names on the 70B endpoint
print("\n" + "=" * 60)
print("2. Testing different model names on 70B endpoint:")
base_url = config['api_base_url']

model_names = [
    "swiss-ai/Apertus-8B",
    "swissai/Apertus-8B",
    "Apertus-8B",
    "apertus-8b",
    "swiss-ai/apertus-8b",
    "swissai/apertus-8b"
]

for model_name in model_names:
    print(f"\n   Testing model name: {model_name}")
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10
            },
            timeout=10
        )
        if response.status_code == 200:
            print(f"   [SUCCESS] Model '{model_name}' works!")
        else:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            print(f"   [FAILED] {error_msg}")
    except Exception as e:
        print(f"   [ERROR] {e}")

# Check if there's a separate API key or subscription for 8B
print("\n" + "=" * 60)
print("3. Additional checks:")
print("   - The API keys might have different access levels")
print("   - Check if 8B requires a different subscription or endpoint")
print("   - Contact Swiss AI support if 8B access is needed")