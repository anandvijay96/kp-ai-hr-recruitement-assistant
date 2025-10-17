"""Check if soft delete columns exist in candidates table"""
from sqlalchemy import create_engine, inspect

engine = create_engine('sqlite:///./hr_assistant.db')
inspector = inspect(engine)

print("Checking 'candidates' table columns...")
columns = inspector.get_columns('candidates')

delete_columns = [c for c in columns if 'delete' in c['name'].lower()]

if delete_columns:
    print("\n✅ Soft delete columns found:")
    for col in delete_columns:
        print(f"  - {col['name']}: {col['type']}")
else:
    print("\n❌ No soft delete columns found!")
    print("\nAll columns:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
