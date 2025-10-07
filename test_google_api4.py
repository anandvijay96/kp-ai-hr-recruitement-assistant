"""Test with site: operator"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

# Different query strategies
queries = [
    "vijay anand bommaji site:linkedin.com",
    "\"vijay anand bommaji\" site:linkedin.com/in",
    "vijayanand.bommaji site:linkedin.com",
]

url = 'https://www.googleapis.com/customsearch/v1'

for query in queries:
    print(f"\n{'='*70}")
    print(f"Testing: {query}")
    print('='*70)
    
    params = {
        'key': API_KEY,
        'cx': ENGINE_ID,
        'q': query,
        'num': 3
    }
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    if 'items' in data:
        print(f"✅ Found {len(data['items'])} results:\n")
        for i, item in enumerate(data['items'], 1):
            print(f"{i}. {item['title'][:70]}")
            print(f"   {item['link']}")
    else:
        print(f"❌ No items found")
