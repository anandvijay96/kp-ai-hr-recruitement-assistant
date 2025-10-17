#!/bin/bash
# Install Phase 3 Optional Dependencies

echo "🚀 Installing Phase 3 Optional Dependencies..."
echo ""

echo "📦 Installing reportlab (for PDF reports)..."
pip install reportlab

echo "📦 Installing openpyxl (for Excel reports)..."
pip install openpyxl

echo ""
echo "✅ Phase 3 dependencies installed successfully!"
echo ""
echo "You can now:"
echo "  - Generate PDF reports"
echo "  - Generate Excel reports"
echo "  - Export activity data in multiple formats"
