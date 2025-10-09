#!/bin/bash

# Script to setup database for User Management feature

echo "=== Setting up User Management Database ==="
echo ""

cd /mnt/c/Users/HP/kp-ai-hr-recruitement-assistant

# Check if database exists
if [ ! -f "hr_recruitment.db" ]; then
    echo "Database file not found. Creating new database..."
    touch hr_recruitment.db
fi

# Apply migration
echo "Applying User Management migration..."
python3 apply_migration.py migrations/010_create_user_management_tables.sql

# Verify tables were created
echo ""
echo "Verifying database tables..."
sqlite3 hr_recruitment.db ".tables"

echo ""
echo "Checking user_roles..."
sqlite3 hr_recruitment.db "SELECT name, display_name FROM user_roles;"

echo ""
echo "=== Database setup complete ==="
