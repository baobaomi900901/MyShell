function bdauto {
    $ErrorActionPreference = "Stop"

    Write-Host "==> Running npm ci..." -ForegroundColor Cyan
    npm ci
    if ($LASTEXITCODE -ne 0) { throw "npm ci failed" }

    Write-Host "==> Running npm run build..." -ForegroundColor Cyan
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build failed" }

    Write-Host "==> Running npm run tauri dev..." -ForegroundColor Cyan
    npm run tauri dev
    if ($LASTEXITCODE -ne 0) { throw "npm run tauri dev failed" }
}

function msiauto {
    $ErrorActionPreference = "Stop"
    $origPath = Get-Location

    Write-Host "==> cd to win_ui_auto..." -ForegroundColor Cyan
    Set-Location "D:\study_pywinauto-worktrees\phase1-integration\win_ui_auto"

    Write-Host "==> Running pack_nauto.ps1..." -ForegroundColor Cyan
    powershell -ExecutionPolicy Bypass -File scripts\pack_nauto.ps1 -SkipRuntimeZip -CleanCargo -StableRustBuild
    if ($LASTEXITCODE -ne 0) { throw "pack_nauto.ps1 failed" }

    Write-Host "==> cd back to $origPath" -ForegroundColor Cyan
    Set-Location $origPath
}
