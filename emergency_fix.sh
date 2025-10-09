#!/bin/bash

echo "=========================================="
echo "  EMERGENCY DATABASE FIX"
echo "=========================================="
echo ""

cd /mnt/c/Users/HP/kp-ai-hr-recruitement-assistant

# Check if database exists
if [ ! -f "hr_recruitment.db" ]; then
    echo "❌ Database file not found!"
    exit 1
fi

echo "Fixing database schema..."
echo ""

# Use sqlite3 to add missing columns directly
sqlite3 hr_recruitment.db <<EOF
-- Add missing columns
ALTER TABLE users ADD COLUMN status VARCHAR(50) DEFAULT 'active';
ALTER TABLE users ADD COLUMN deactivation_reason TEXT;
ALTER TABLE users ADD COLUMN last_activity_at TIMESTAMP;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;

-- Verify columns were added
.schema users
EOF

echo ""
echo "=========================================="
echo "✅ Database fixed!"
echo "=========================================="
echo ""
echo "Now restart your server:"
echo "  python -m uvicorn main:app --reload"
echo ""
