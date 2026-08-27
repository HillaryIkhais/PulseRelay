#!/usr/bin/env python3
"""Deployment verification script for PulseRelay."""

import sys
import requests
import json


def verify_deployment(url: str) -> bool:
    """Verify the deployed application is working."""
    print(f"Verifying deployment at: {url}")
    print("=" * 50)
    
    # 1. Health check
    print("\n1. Health check...")
    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Status: {data.get('status')}")
            print(f"   ✓ Service: {data.get('service')}")
            print(f"   ✓ Version: {data.get('version')}")
        else:
            print(f"   ✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Health check error: {e}")
        return False
    
    # 2. Start session
    print("\n2. Starting session...")
    try:
        response = requests.post(
            f"{url}/api/session/start",
            json={},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            print(f"   ✓ Session ID: {session_id[:8]}...")
        else:
            print(f"   ✗ Session start failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Session start error: {e}")
        return False
    
    # 3. Submit observation
    print("\n3. Submitting observation...")
    try:
        response = requests.post(
            f"{url}/api/observe",
            json={
                "session_id": session_id,
                "text": "Patient is a 64-year-old male with chest pain. BP 104 over 67. Heart rate 108. Pain 7 out of 10."
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            state = data.get("state", {})
            print(f"   ✓ BP: {state.get('latest_bp', {}).get('systolic')}/{state.get('latest_bp', {}).get('diastolic')}")
            print(f"   ✓ HR: {state.get('latest_hr', {}).get('value')}")
            print(f"   ✓ Pain: {state.get('latest_pain', {}).get('value')}/10")
        else:
            print(f"   ✗ Observation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Observation error: {e}")
        return False
    
    # 4. Get state
    print("\n4. Getting state...")
    try:
        response = requests.get(f"{url}/api/state/{session_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Session: {data.get('session_id')[:8]}...")
            print(f"   ✓ Timeline events: {len(data.get('timeline', []))}")
        else:
            print(f"   ✗ State retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ State retrieval error: {e}")
        return False
    
    # 5. Get handoff
    print("\n5. Getting handoff...")
    try:
        response = requests.get(f"{url}/api/handoff/{session_id}/text", timeout=10)
        if response.status_code == 200:
            data = response.json()
            handoff = data.get("handoff", "")
            print(f"   ✓ Handoff generated ({len(handoff)} chars)")
            if "64M" in handoff:
                print("   ✓ Patient info correct")
        else:
            print(f"   ✗ Handoff failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Handoff error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ Deployment verification PASSED")
    print("=" * 50)
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_deployment.py <cloud-run-url>")
        print("Example: python verify_deployment.py https://pulserelay-xxxxxx-uc.a.run.app")
        sys.exit(1)
    
    url = sys.argv[1].rstrip("/")
    success = verify_deployment(url)
    sys.exit(0 if success else 1)
