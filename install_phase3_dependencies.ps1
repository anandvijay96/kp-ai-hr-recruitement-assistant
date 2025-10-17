# Install Phase 3 Optional Dependencies (PowerShell)

Write-Host "🚀 Installing Phase 3 Optional Dependencies..." -ForegroundColor Cyan
Write-Host ""

Write-Host "📦 Installing reportlab (for PDF reports)..." -ForegroundColor Yellow
pip install reportlab

Write-Host "📦 Installing openpyxl (for Excel reports)..." -ForegroundColor Yellow
pip install openpyxl

Write-Host ""
Write-Host "✅ Phase 3 dependencies installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now:" -ForegroundColor White
Write-Host "  - Generate PDF reports" -ForegroundColor White
Write-Host "  - Generate Excel reports" -ForegroundColor White
Write-Host "  - Export activity data in multiple formats" -ForegroundColor White
