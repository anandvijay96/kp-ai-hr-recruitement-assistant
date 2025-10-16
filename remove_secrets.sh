#!/bin/bash

# Script to remove secrets from git history
# WARNING: This rewrites git history!

echo "🚨 Removing secrets from git history..."
echo "This will rewrite history - all collaborators need to re-clone!"
echo ""

# Remove the API key from all commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch PRODUCTION_CHECKLIST.md .env.production.example POSTGRES_DEPLOYMENT_GUIDE.md" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: Destructive!)
echo ""
echo "To force push and rewrite remote history, run:"
echo "git push origin --force --all"
echo "git push origin --force --tags"
