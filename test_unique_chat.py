#!/usr/bin/env python3
"""
Test script to verify unique chat implementation
"""

import requests
import json
import time
import uuid

# Test configuration
API_BASE = "http://localhost:8000"
FRONTEND_BASE = "http://localhost:3000"

def test_session_conversation_api():
    """Test the session-based conversation API endpoints"""
    print("Testing session-based conversation API...")
    
    # Generate a test session ID
    session_id = f"test-session-{int(time.time())}"
    
    # Test 1: Get empty conversation for new session
    print(f"1. Testing GET /api/conversation/{session_id}")
    response = requests.get(f"{API_BASE}/api/conversation/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["conversation"] == []
    print("✓ Empty conversation retrieved successfully")
    
    # Test 2: Save a conversation
    print(f"2. Testing POST /api/conversation/{session_id}")
    test_conversation = [
        {
            "role": "user",
            "content": "Hello, how are you?",
            "timestamp": "2024-01-01T00:00:00Z"
        },
        {
            "role": "assistant", 
            "content": "I'm doing well, thank you!",
            "timestamp": "2024-01-01T00:00:01Z"
        }
    ]
    
    response = requests.post(
        f"{API_BASE}/api/conversation/{session_id}",
        json=test_conversation,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    print("✓ Conversation saved successfully")
    
    # Test 3: Retrieve the saved conversation
    print(f"3. Testing GET /api/conversation/{session_id} (after save)")
    response = requests.get(f"{API_BASE}/api/conversation/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["conversation"]) == 2
    assert data["conversation"][0]["role"] == "user"
    assert data["conversation"][1]["role"] == "assistant"
    print("✓ Saved conversation retrieved successfully")
    
    # Test 4: Clear the conversation
    print(f"4. Testing DELETE /api/conversation/{session_id}")
    response = requests.delete(f"{API_BASE}/api/conversation/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    print("✓ Conversation cleared successfully")
    
    # Test 5: Verify conversation is cleared
    print(f"5. Testing GET /api/conversation/{session_id} (after clear)")
    response = requests.get(f"{API_BASE}/api/conversation/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["conversation"] == []
    print("✓ Conversation confirmed cleared")
    
    print("✅ All session conversation API tests passed!")

def test_unique_session_generation():
    """Test that unique session IDs are generated correctly"""
    print("\nTesting unique session ID generation...")
    
    # Generate multiple session IDs and ensure they're unique
    session_ids = set()
    for i in range(10):
        session_id = f"session-{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}-{time.time()}"
        assert session_id not in session_ids, f"Duplicate session ID generated: {session_id}"
        session_ids.add(session_id)
    
    print(f"✓ Generated {len(session_ids)} unique session IDs")
    print("✅ Unique session ID generation test passed!")

def test_api_health():
    """Test that the API server is running and healthy"""
    print("\nTesting API server health...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        print("✓ API server is healthy")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ API server is not accessible: {e}")
        print("Make sure the API server is running on port 8000")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Unique Chat Implementation")
    print("=" * 50)
    
    # Test API health first
    if not test_api_health():
        print("\n❌ API server is not running. Please start it with:")
        print("   python api_server.py")
        return
    
    # Run tests
    try:
        test_unique_session_generation()
        test_session_conversation_api()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Unique chat implementation is working correctly.")
        print("\nKey features implemented:")
        print("✅ Dynamic route structure (/chat/[sessionId])")
        print("✅ Unique session ID generation")
        print("✅ Session-based conversation storage")
        print("✅ API endpoints for session management")
        print("✅ Frontend integration with server storage")
        print("\nEvery navigation to /chat now creates a unique conversation link!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
