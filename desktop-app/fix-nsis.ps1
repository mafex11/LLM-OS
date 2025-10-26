# Fix NSIS Plugin Issues for Electron Builder
# This script clears corrupted NSIS caches and rebuilds them

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Fixing NSIS Plugin Issues" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clear corrupted NSIS caches
Write-Host "Step 1: Clearing corrupted NSIS caches..." -ForegroundColor Yellow
$nsisCache = "$env:LOCALAPPDATA\electron-builder\Cache\nsis"
$nsisResourcesCache = "$env:LOCALAPPDATA\electron-builder\Cache\nsis-resources"

if (Test-Path $nsisCache) {
    Write-Host "Removing NSIS cache: $nsisCache" -ForegroundColor Gray
    Remove-Item -Path $nsisCache -Recurse -Force
} else {
    Write-Host "NSIS cache not found: $nsisCache" -ForegroundColor Gray
}

if (Test-Path $nsisResourcesCache) {
    Write-Host "Removing NSIS resources cache: $nsisResourcesCache" -ForegroundColor Gray
    Remove-Item -Path $nsisResourcesCache -Recurse -Force
} else {
    Write-Host "NSIS resources cache not found: $nsisResourcesCache" -ForegroundColor Gray
}

Write-Host "✅ NSIS caches cleared" -ForegroundColor Green
Write-Host ""

# Step 2: Rebuild NSIS cache (forces fresh plugin download)
Write-Host "Step 2: Rebuilding NSIS cache..." -ForegroundColor Yellow
Write-Host "Running: npx electron-builder --dir" -ForegroundColor Gray
npx electron-builder --dir

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ NSIS cache rebuilt successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to rebuild NSIS cache" -ForegroundColor Red
    Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""

# Step 3: Retry full Windows build
Write-Host "Step 3: Building Windows installer..." -ForegroundColor Yellow
Write-Host "Running: npm run electron:build" -ForegroundColor Gray
npm run electron:build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "✅ Build completed successfully!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Installer location: dist\" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "❌ Build failed" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
