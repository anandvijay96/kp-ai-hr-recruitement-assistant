#!/bin/bash

# Phase 2 Deployment Script for Dokploy
# This script will backup the database and run migrations

set -e  # Exit on error

echo "=========================================="
echo "Phase 2 Deployment Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Find database
echo "🔍 Looking for database..."
if [ -f "hr_recruitment.db" ]; then
    DB_PATH="hr_recruitment.db"
    echo -e "${GREEN}✅ Found database: $DB_PATH${NC}"
elif [ -f "./hr_recruitment.db" ]; then
    DB_PATH="./hr_recruitment.db"
    echo -e "${GREEN}✅ Found database: $DB_PATH${NC}"
else
    echo -e "${RED}❌ Database not found in current directory${NC}"
    echo "Please navigate to the app directory first"
    echo "Try: cd /app/ai-hr-assistant"
    exit 1
fi

# Backup database
echo ""
echo "💾 Creating database backup..."
BACKUP_NAME="hr_recruitment.db.backup_$(date +%Y%m%d_%H%M%S)"
cp "$DB_PATH" "$BACKUP_NAME"

if [ -f "$BACKUP_NAME" ]; then
    echo -e "${GREEN}✅ Backup created: $BACKUP_NAME${NC}"
    ls -lh "$BACKUP_NAME"
else
    echo -e "${RED}❌ Backup failed!${NC}"
    exit 1
fi

# Run migrations
echo ""
echo "🔄 Running migrations..."
python migrations/run_all_phase2_migrations.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migrations completed successfully!${NC}"
else
    echo -e "${RED}❌ Migrations failed!${NC}"
    echo "Restoring backup..."
    cp "$BACKUP_NAME" "$DB_PATH"
    echo "Database restored from backup"
    exit 1
fi

# Done
echo ""
echo "=========================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart the application:"
echo "   docker restart <container-name>"
echo "   OR"
echo "   pm2 restart ai-hr-assistant"
echo ""
echo "2. Test the deployment:"
echo "   Visit: http://158.69.219.206/"
echo "   - Upload a test resume"
echo "   - Check work experience bullet points"
echo "   - Check LinkedIn suggestions"
echo ""
echo "Backup saved as: $BACKUP_NAME"
echo ""
