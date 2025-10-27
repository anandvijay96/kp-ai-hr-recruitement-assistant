"""Fix clients table - add missing columns"""
import sqlite3

def fix_clients_table():
    conn = sqlite3.connect('hr_recruitment.db')
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(clients)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"Existing columns: {existing_columns}")
    
    # Add missing columns if needed
    columns_to_add = [
        ('website', 'VARCHAR(255)'),
        ('description', 'TEXT'),
        ('industry', 'VARCHAR(100)'),
        ('contact_person', 'VARCHAR(100)'),
        ('contact_email', 'VARCHAR(255)'),
        ('contact_phone', 'VARCHAR(20)'),
        ('contract_start_date', 'VARCHAR(50)'),
        ('contract_end_date', 'VARCHAR(50)'),
        ('contract_value', 'VARCHAR(50)'),
        ('payment_terms', 'VARCHAR(255)'),
        ('notes', 'TEXT'),
        ('tags', 'TEXT'),
        ('client_type', 'VARCHAR(20) DEFAULT "direct"'),
        ('priority', 'VARCHAR(20) DEFAULT "medium"'),
    ]
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            try:
                cursor.execute(f'ALTER TABLE clients ADD COLUMN {col_name} {col_type}')
                print(f"✅ Added column: {col_name}")
            except Exception as e:
                print(f"❌ Error adding {col_name}: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Clients table fixed!")

if __name__ == "__main__":
    fix_clients_table()
