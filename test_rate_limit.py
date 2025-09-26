"""
Test if API rate limit is cleared
"""

import sys
from apertus_api import ApertusAPI
import time

def test_rate_limit():
    """Quick test to check if rate limit is cleared"""

    print("Testing API rate limit status...")
    print("-" * 40)

    api = ApertusAPI()

    # Simple test message
    messages = [
        {"role": "user", "content": "Say 'OK' if you receive this."}
    ]

    # Test each API key
    success_count = 0
    failed_keys = []

    for i, api_key in enumerate(api.api_keys):
        print(f"\nTesting API key {i+1}/5...")

        try:
            # Use specific API key
            api.api_keys = [api_key]
            api.current_key_index = 0

            # Try to call
            response = api.call_model(messages, temperature=0.1, max_tokens=10)

            if response:
                print(f"  ✓ API key {i+1}: SUCCESS")
                success_count += 1
            else:
                print(f"  ✗ API key {i+1}: No response")
                failed_keys.append(i+1)

        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e):
                print(f"  ✗ API key {i+1}: RATE LIMITED")
                failed_keys.append(i+1)
            else:
                print(f"  ✗ API key {i+1}: Error - {str(e)[:50]}")
                failed_keys.append(i+1)

        time.sleep(1)  # Small delay between tests

    print("\n" + "=" * 40)
    print("RESULT:")
    print(f"  Working keys: {success_count}/5")

    if success_count == 5:
        print("  ✓ ALL KEYS READY - Safe to start!")
        return True
    elif success_count > 0:
        print(f"  ⚠ PARTIAL - Only {success_count} keys working")
        print(f"  Failed keys: {failed_keys}")
        print("  Consider waiting 5 more minutes")
        return False
    else:
        print("  ✗ ALL KEYS RATE LIMITED")
        print("  Wait 10-15 minutes and try again")
        return False

    print("=" * 40)

def test_single_request():
    """Test with just one API key"""
    print("\nQuick single API test...")

    api = ApertusAPI()

    try:
        response = api.call_model(
            [{"role": "user", "content": "Reply with 'OK'"}],
            temperature=0.1,
            max_tokens=10
        )

        if response:
            print("✓ API is working!")
            return True
        else:
            print("✗ No response received")
            return False

    except Exception as e:
        if "429" in str(e) or "rate_limit" in str(e):
            print("✗ RATE LIMITED - Wait before retrying")
        else:
            print(f"✗ Error: {str(e)[:100]}")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test API rate limit status')
    parser.add_argument('--quick', action='store_true',
                       help='Quick test with one API key only')

    args = parser.parse_args()

    if args.quick:
        success = test_single_request()
    else:
        success = test_rate_limit()

    sys.exit(0 if success else 1)