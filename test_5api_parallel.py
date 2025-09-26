import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from apertus_api import ApertusAPI

def test_single_api(api_key, api_idx):
    """Test a single API key"""
    print(f"[API {api_idx}] Starting test...", flush=True)

    api = ApertusAPI([api_key])
    messages = [{"role": "user", "content": f"Hello from API {api_idx}"}]

    start = time.time()
    try:
        print(f"[API {api_idx}] Calling API...", flush=True)
        response = api.call_model(
            messages=messages,
            temperature=0.7,
            max_tokens=50
        )
        elapsed = time.time() - start

        if response:
            print(f"[API {api_idx}] SUCCESS in {elapsed:.1f}s - Response: {response[:50]}...", flush=True)
            return {'api': api_idx, 'success': True, 'time': elapsed}
        else:
            print(f"[API {api_idx}] FAILED - No response", flush=True)
            return {'api': api_idx, 'success': False, 'time': elapsed}

    except Exception as e:
        elapsed = time.time() - start
        print(f"[API {api_idx}] ERROR after {elapsed:.1f}s: {e}", flush=True)
        return {'api': api_idx, 'success': False, 'time': elapsed, 'error': str(e)}

def test_all_apis():
    """Test all 5 APIs in parallel"""
    print("=" * 60, flush=True)
    print("TESTING 5 APIs IN PARALLEL", flush=True)
    print("=" * 60, flush=True)

    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)

    api_keys = config['api_keys'][:5]
    print(f"Testing {len(api_keys)} API keys...", flush=True)

    # Test all APIs in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for i, key in enumerate(api_keys):
            future = executor.submit(test_single_api, key, i)
            futures[future] = i

        # Collect results
        results = []
        for future in as_completed(futures):
            api_idx = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"[API {api_idx}] Exception: {e}", flush=True)
                results.append({'api': api_idx, 'success': False, 'error': str(e)})

    # Summary
    print("\n" + "=" * 60, flush=True)
    print("RESULTS:", flush=True)
    successful = sum(1 for r in results if r.get('success'))
    print(f"  Successful: {successful}/{len(api_keys)}", flush=True)

    for r in sorted(results, key=lambda x: x['api']):
        status = "✓" if r.get('success') else "✗"
        print(f"  API {r['api']}: {status} ({r.get('time', 0):.1f}s)", flush=True)

    if successful == len(api_keys):
        print("\n✅ All APIs working! Safe to run parallel processing.", flush=True)
    else:
        print(f"\n⚠️  Only {successful}/{len(api_keys)} APIs working.", flush=True)

if __name__ == "__main__":
    test_all_apis()