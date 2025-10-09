#!/bin/bash

# Complete setup script for User Management feature

echo "=========================================="
echo "  User Management Feature Setup"
echo "=========================================="
echo ""

cd /mnt/c/Users/HP/kp-ai-hr-recruitement-assistant

# Activate virtual environment
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Check if database exists
if [ ! -f "hr_recruitment.db" ]; then
    echo "Creating database file..."
    touch hr_recruitment.db
fi

# Apply migration
echo ""
echo "Step 1: Applying database migration..."
echo "----------------------------------------"
python apply_migration.py migrations/010_create_user_management_tables.sql

# Create admin user
echo ""
echo "Step 2: Creating initial admin user..."
echo "----------------------------------------"
python create_admin_user.py

# Verify setup
echo ""
echo "Step 3: Verifying database setup..."
echo "----------------------------------------"
echo "Tables in database:"
sqlite3 hr_recruitment.db ".tables"

echo ""
echo "User roles:"
sqlite3 hr_recruitment.db "SELECT name, display_name FROM user_roles;" 2>/dev/null || echo "(User roles table may not be populated yet)"

echo ""
echo "Users in database:"
sqlite3 hr_recruitment.db "SELECT email, role, status FROM users;" 2>/dev/null || echo "(No users yet)"

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start the server: bash start_server.sh"
echo "  2. Open browser: http://localhost:8000/register"
echo "  3. Register a new account"
echo "  4. Login and access http://localhost:8000/users"
echo ""
echo "Or use the setup endpoint to create initial admin:"
echo "  curl -X POST http://localhost:8000/api/setup/initial-admin"
echo ""
echo "Default admin credentials (if created):"
echo "  Email: admin@example.com"
echo "  Password: Admin@123"
echo "=========================================="
