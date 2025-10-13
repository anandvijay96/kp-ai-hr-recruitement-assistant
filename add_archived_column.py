import sqlite3

conn = sqlite3.connect('hr_recruitment.db')
try:
    conn.execute('ALTER TABLE jobs ADD COLUMN archived_at TIMESTAMP')
    conn.commit()
    print('✅ Added archived_at column')
except Exception as e:
    print(f'Note: {e}')
conn.close()
