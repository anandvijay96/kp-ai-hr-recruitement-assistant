#!/bin/bash

echo "=========================================="
echo "  Fixing Database Migration"
echo "=========================================="
echo ""

cd /mnt/c/Users/HP/kp-ai-hr-recruitement-assistant

# Activate venv
source venv/bin/activate

# Apply migration
echo "Applying migration..."
python apply_migration.py migrations/010_create_user_management_tables.sql

# Create admin user
echo ""
echo "Creating admin user..."
python create_admin_user.py

echo ""
echo "=========================================="
echo "  Done! Database is now fixed."
echo "=========================================="
echo ""
echo "Refresh the setup-check page to verify!"
echo "Or go to: http://localhost:8000/users"
