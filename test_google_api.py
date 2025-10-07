"""
Quick test script to verify Google Search API configuration
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

print(f"API Key: {API_KEY[:20]}..." if API_KEY else "API Key: NOT SET")
print(f"Engine ID: {ENGINE_ID}")

if not API_KEY or not ENGINE_ID:
    print("\n❌ ERROR: API credentials not configured in .env file")
    exit(1)

# Test search
query = "Vijay Anand Bommaji LinkedIn"
url = 'https://www.googleapis.com/customsearch/v1'
params = {
    'key': API_KEY,
    'cx': ENGINE_ID,
    'q': query,
    'num': 3
}

print(f"\nTesting search for: {query}")
print("Making API request...")

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if 'error' in data:
            print(f"\n❌ API Error: {data['error']}")
        elif 'items' in data:
            print(f"\n✅ SUCCESS! Found {len(data['items'])} results")
            for i, item in enumerate(data['items'][:3], 1):
                print(f"\n{i}. {item['title']}")
                print(f"   {item['link']}")
        else:
            print(f"\n⚠️  No 'items' in response. Keys: {list(data.keys())}")
            print(f"Response: {data}")
    else:
        print(f"\n❌ HTTP Error {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"\n❌ Exception: {e}")
