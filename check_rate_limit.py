import json
import time
import concurrent.futures
from apertus_api import ApertusAPI

def test_single_api_key(api_key, key_index):
    """Test rate limit for a single API key"""
    api = ApertusAPI([api_key])

    print(f"\n[API Key {key_index}] Testing rate limit...")

    success_count = 0
    error_count = 0
    rate_limit_errors = 0

    start_time = time.time()

    # Try 10 quick requests
    for i in range(10):
        try:
            # Simple test request
            messages = [{"role": "user", "content": "Hi"}]
            response = api.call_model(messages, temperature=0.1, max_tokens=10)

            if response:
                success_count += 1
                print(f"  Request {i+1}: SUCCESS")
            else:
                error_count += 1
                print(f"  Request {i+1}: FAILED (no response)")

        except Exception as e:
            error_count += 1
            error_str = str(e)
            if "429" in error_str or "rate_limit" in error_str.lower():
                rate_limit_errors += 1
                print(f"  Request {i+1}: RATE LIMITED")
            else:
                print(f"  Request {i+1}: ERROR - {error_str[:50]}")

        # Small delay between requests
        time.sleep(0.2)  # 5 requests per second max

    elapsed = time.time() - start_time

    print(f"\n[API Key {key_index}] Results:")
    print(f"  Success: {success_count}/10")
    print(f"  Errors: {error_count}/10")
    print(f"  Rate limits hit: {rate_limit_errors}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Rate: {success_count/elapsed:.1f} req/sec")

    return {
        'key_index': key_index,
        'success': success_count,
        'errors': error_count,
        'rate_limits': rate_limit_errors,
        'time': elapsed,
        'rate': success_count/elapsed if elapsed > 0 else 0
    }


def test_all_keys_parallel():
    """Test all API keys in parallel"""
    print("=" * 60)
    print("RATE LIMIT TEST FOR ALL API KEYS")
    print("=" * 60)

    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)

    api_keys = config['api_keys']
    print(f"Testing {len(api_keys)} API keys...")

    results = []

    # Test all keys in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(api_keys)) as executor:
        futures = []
        for i, key in enumerate(api_keys):
            future = executor.submit(test_single_api_key, key, i)
            futures.append(future)

        # Collect results
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error testing key: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_success = sum(r['success'] for r in results)
    total_rate_limits = sum(r['rate_limits'] for r in results)
    avg_rate = sum(r['rate'] for r in results)

    print(f"Total successful requests: {total_success}")
    print(f"Total rate limit errors: {total_rate_limits}")
    print(f"Combined rate: {avg_rate:.1f} req/sec")

    if total_rate_limits > 0:
        print("\n⚠️  WARNING: Rate limits detected!")
        print("Recommendation: Use delays between requests (0.2-0.3 sec per key)")
    else:
        print("\n✅ No rate limits detected!")
        print(f"Safe to use up to {avg_rate:.1f} req/sec total")

    print("\nPer-key safe rate: 4-5 req/sec")
    print(f"Total safe rate with {len(api_keys)} keys: {len(api_keys) * 4} req/sec")


if __name__ == "__main__":
    test_all_keys_parallel()