"""Fix clients table - create if not exists, then add missing columns"""
import sqlite3

def fix_clients_table():
    conn = sqlite3.connect('hr_recruitment.db')
    cursor = conn.cursor()
    
    # Check if clients table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        print("⚠️ Clients table doesn't exist. Creating it now...")
        # Create clients table with all required columns
        cursor.execute('''
        CREATE TABLE clients (
            id VARCHAR(36) PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL UNIQUE,
            industry VARCHAR(100),
            website VARCHAR(255),
            description TEXT,
            contact_person VARCHAR(100) NOT NULL,
            contact_email VARCHAR(255) NOT NULL,
            contact_phone VARCHAR(20),
            address VARCHAR(255),
            city VARCHAR(100),
            state VARCHAR(100),
            country VARCHAR(100),
            postal_code VARCHAR(20),
            status VARCHAR(20) DEFAULT 'active',
            client_type VARCHAR(20) DEFAULT 'direct',
            priority VARCHAR(20) DEFAULT 'medium',
            contract_start_date VARCHAR(50),
            contract_end_date VARCHAR(50),
            contract_value VARCHAR(50),
            payment_terms VARCHAR(255),
            notes TEXT,
            tags TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(36),
            updated_by VARCHAR(36),
            is_deleted BOOLEAN DEFAULT 0,
            deleted_at DATETIME,
            deleted_by VARCHAR(36),
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL,
            CHECK (status IN ('active', 'inactive', 'on_hold')),
            CHECK (client_type IN ('direct', 'agency', 'partner')),
            CHECK (priority IN ('low', 'medium', 'high'))
        )
        ''')
        conn.commit()
        print("✅ Clients table created successfully!")
        conn.close()
        return
    
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
