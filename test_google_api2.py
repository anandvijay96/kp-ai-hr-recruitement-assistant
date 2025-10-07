"""Test with email"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

# Test with email
query = "vijayanand.bommaji@gmail.com LinkedIn"
url = 'https://www.googleapis.com/customsearch/v1'
params = {
    'key': API_KEY,
    'cx': ENGINE_ID,
    'q': query,
    'num': 5
}

print(f"Testing search: {query}\n")

response = requests.get(url, params=params, timeout=10)
data = response.json()

if 'items' in data:
    print(f"✅ Found {len(data['items'])} results:\n")
    for i, item in enumerate(data['items'], 1):
        print(f"{i}. {item['title'][:70]}")
        print(f"   {item['link']}")
        print()
else:
    print(f"❌ No items found")
    print(f"Response keys: {list(data.keys())}")
    if 'error' in data:
        print(f"Error: {data['error']}")
