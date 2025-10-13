"""Quick check if vendor routes are in main.py"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("\n" + "="*60)
print("VENDOR ROUTES CHECK")
print("="*60 + "\n")

# Check for vendor routes
checks = [
    ('Vendor Management comment', '# Vendor Management Web Pages'),
    ('/vendors route', '@app.get("/vendors"'),
    ('vendors_page function', 'async def vendors_page'),
    ('/vendors/create route', '@app.get("/vendors/create"'),
    ('/vendors/{vendor_id} route', '@app.get("/vendors/{vendor_id}"'),
    ('/vendors/{vendor_id}/edit route', '@app.get("/vendors/{vendor_id}/edit"'),
]

all_found = True
for name, pattern in checks:
    if pattern in content:
        print(f"✅ {name}")
    else:
        print(f"❌ {name} - NOT FOUND")
        all_found = False

print("\n" + "="*60)
if all_found:
    print("✅ ALL VENDOR ROUTES ARE IN main.py")
    print("="*60)
    print("\n🔄 NEXT STEP: RESTART YOUR SERVER")
    print("\nIn your terminal where the server is running:")
    print("  1. Press Ctrl+C to stop the server")
    print("  2. Run: uvicorn main:app --reload")
    print("  3. Open: http://localhost:8000/vendors")
else:
    print("❌ SOME ROUTES ARE MISSING")
    print("="*60)
    print("\nThe routes need to be added to main.py")

print()
