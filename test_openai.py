#!/usr/bin/env python3
"""
Simple OpenAI API test script
"""

import os
from openai import OpenAI

def test_openai_connection():
    """Test OpenAI API connection and quota."""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
        return False
    
    try:
        client = OpenAI(api_key=api_key)
        
        print("🔍 Testing OpenAI API connection...")
        
        # Simple test request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'Hello, API is working!'"}
            ],
            max_tokens=10
        )
        
        print("✅ API connection successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        
        if "quota" in str(e).lower() or "insufficient_quota" in str(e):
            print("\n💡 Quota exceeded. Try:")
            print("1. Check billing at https://platform.openai.com/account/billing")
            print("2. Add payment method")
            print("3. Use a different API key")
            print("4. Wait for quota reset (if on free tier)")
        
        return False

if __name__ == '__main__':
    test_openai_connection() 