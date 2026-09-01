#!/usr/bin/env python3
"""
Demo script to test the verification endpoints.
"""

import asyncio
import requests
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

BASE_URL = "http://localhost:8001/api/v1"


def test_signup_with_verification():
    """Test signup endpoint and verify it creates user."""
    print("Testing signup with email verification...")
    
    # Test signup
    signup_data = {
        "email": "testverify@example.com",
        "password": "password123",
        "full_name": "Test Verification User",
        "company_name": "Test Company"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data, timeout=5)
        print(f"Signup response status: {response.status_code}")
        
        if response.status_code == 201:
            user_data = response.json()
            print(f"✅ User created: {user_data['email']}")
            print(f"Email verified: {user_data['email_verified']}")
            print("Check console logs for verification email!")
            return True
        else:
            print(f"❌ Signup failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def test_verify_email_endpoint():
    """Test the verify-email endpoint with a dummy token."""
    print("\nTesting verify-email endpoint with invalid token...")
    
    try:
        response = requests.get(f"{BASE_URL}/auth/verify-email", 
                              params={"token": "invalid_token_123"}, 
                              timeout=5)
        print(f"Verify email response status: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Invalid token correctly rejected")
            return True
        else:
            print(f"Unexpected response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


async def main():
    print("🔐 Email Verification Demo")
    print("=" * 50)
    
    # Note: This requires the FastAPI server to be running
    print("Note: Make sure the FastAPI server is running on localhost:8000")
    print("Run: cd backend && uvicorn app.main:app --reload")
    print()
    
    success1 = test_signup_with_verification()
    success2 = test_verify_email_endpoint()
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
        print("\nTo test the full flow:")
        print("1. Check the console logs for the verification email")
        print("2. Extract the token from the verification URL")
        print("3. Test GET /api/v1/auth/verify-email?token=<extracted_token>")
    else:
        print("\n❌ Some tests failed")


if __name__ == "__main__":
    asyncio.run(main())