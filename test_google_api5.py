"""Test with exact username"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

# Test with hyphenated username
query = "vijay-anand-bommaji linkedin.com"
url = 'https://www.googleapis.com/customsearch/v1'
params = {
    'key': API_KEY,
    'cx': ENGINE_ID,
    'q': query,
    'num': 10
}

print(f"Testing search: {query}\n")

response = requests.get(url, params=params, timeout=10)
data = response.json()

if 'items' in data:
    print(f"✅ Found {len(data['items'])} results:\n")
    for i, item in enumerate(data['items'], 1):
        title = item['title']
        link = item['link']
        
        # Highlight if contains the username
        if 'vijay-anand-bommaji' in link.lower():
            print(f"🎯 MATCH! {i}. {title}")
        else:
            print(f"{i}. {title}")
        print(f"   {link}")
        print()
else:
    print(f"❌ No items found")
    if 'error' in data:
        print(f"Error: {data['error']}")
