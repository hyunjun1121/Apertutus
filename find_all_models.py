import json
import requests
from typing import List, Dict, Set

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def test_model_endpoint(api_key: str, base_url: str, model_name: str) -> tuple:
    """Test if a specific model works"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5,
                "temperature": 0.1
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            actual_model = result.get('model', model_name)
            return True, actual_model
        else:
            return False, None

    except Exception as e:
        return False, None

def search_models():
    config = load_config()
    api_key = config['api_keys'][0]

    # Different possible base URLs for different models
    base_url_patterns = [
        "https://api.swisscom.com/layer/swiss-ai-weeks/apertus-70b/v1",
        "https://api.swisscom.com/layer/swiss-ai-weeks/apertus-8b/v1",
        "https://api.swisscom.com/layer/swiss-ai-weeks/apertus/v1",
        "https://api.swisscom.com/layer/swiss-ai-weeks/v1",
    ]

    # Different model name variations to test
    model_variations = [
        "swiss-ai/Apertus-70B",
        "swiss-ai/Apertus-8B",
        "swiss-ai/apertus-70b",
        "swiss-ai/apertus-8b",
        "Apertus-70B",
        "Apertus-8B",
        "apertus-70b",
        "apertus-8b",
    ]

    working_models: Set[tuple] = set()

    print("=" * 70)
    print("COMPREHENSIVE MODEL SEARCH")
    print("=" * 70)

    # First, try to get model lists from various endpoints
    print("\n1. CHECKING MODEL LIST ENDPOINTS:")
    print("-" * 40)

    for base_url in base_url_patterns:
        endpoints = [
            f"{base_url}/models",
            base_url.replace('/v1', '/models'),
        ]

        for endpoint in endpoints:
            try:
                print(f"\nChecking: {endpoint}")
                headers = {"Authorization": f"Bearer {api_key}"}
                response = requests.get(endpoint, headers=headers, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        print(f"  [FOUND] Models:")
                        for model in data['data']:
                            if 'id' in model:
                                model_id = model['id']
                                print(f"    - {model_id}")
                                # Store the working combination
                                working_models.add((base_url, model_id))
                else:
                    print(f"  [FAIL] Status {response.status_code}")

            except requests.exceptions.Timeout:
                print(f"  [TIMEOUT]")
            except Exception as e:
                print(f"  [ERROR] {str(e)[:50]}")

    # Test model variations with different base URLs
    print("\n\n2. TESTING MODEL COMBINATIONS:")
    print("-" * 40)

    for base_url in base_url_patterns:
        print(f"\nBase URL: {base_url}")

        for model_name in model_variations:
            success, actual_model = test_model_endpoint(api_key, base_url, model_name)

            if success:
                print(f"  [SUCCESS] {model_name} -> Works! (returns as: {actual_model})")
                working_models.add((base_url, model_name))
            else:
                print(f"  [FAIL] {model_name}")

    # Test alternative API structures
    print("\n\n3. TESTING ALTERNATIVE API STRUCTURES:")
    print("-" * 40)

    # Try without version in URL
    alt_bases = [
        "https://api.swisscom.com/layer/swiss-ai-weeks/apertus-70b",
        "https://api.swisscom.com/layer/swiss-ai-weeks/apertus-8b",
        "https://api.swisscom.com/layer/swiss-ai-weeks",
    ]

    for base_url in alt_bases:
        print(f"\nTesting base: {base_url}")
        for model_name in ["swiss-ai/Apertus-70B", "swiss-ai/Apertus-8B"]:
            for endpoint in ["/chat/completions", "/v1/chat/completions"]:
                try:
                    response = requests.post(
                        f"{base_url}{endpoint}",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model_name,
                            "messages": [{"role": "user", "content": "Test"}],
                            "max_tokens": 5
                        },
                        timeout=5
                    )

                    if response.status_code == 200:
                        print(f"  [SUCCESS] {model_name} works at {base_url}{endpoint}")
                        working_models.add((f"{base_url}{endpoint.replace('/chat/completions', '')}", model_name))

                except:
                    pass

    # Summary
    print("\n\n" + "=" * 70)
    print("SUMMARY OF WORKING MODELS:")
    print("=" * 70)

    if working_models:
        unique_models = {}
        for base_url, model_name in working_models:
            if model_name not in unique_models:
                unique_models[model_name] = []
            unique_models[model_name].append(base_url)

        for model, urls in unique_models.items():
            print(f"\n[WORKING] Model: {model}")
            print(f"  Working at:")
            for url in set(urls):
                print(f"    - {url}")
    else:
        print("\nNo additional working models found beyond what's in config.json")

    # Suggest config updates
    print("\n\n" + "=" * 70)
    print("SUGGESTED CONFIG.JSON UPDATE:")
    print("=" * 70)

    if working_models:
        # Find unique working combinations
        suggestions = {}
        for base_url, model_name in working_models:
            if model_name not in suggestions:
                suggestions[model_name] = base_url

        print("\nYou can add these to your config.json:")
        print(json.dumps({
            "models": [
                {
                    "model_name": model,
                    "api_base_url": url
                }
                for model, url in suggestions.items()
            ]
        }, indent=2))

if __name__ == "__main__":
    search_models()