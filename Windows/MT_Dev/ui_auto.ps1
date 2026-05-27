function Resolve-WinUiAutoAppDir {
    $here = (Get-Location).Path
    foreach ($rel in @("win_ui_auto\app", "app", ".")) {
        $dir = if ($rel -eq ".") { $here } else { Join-Path $here $rel }
        if (Test-Path (Join-Path $dir "package-lock.json")) {
            return (Resolve-Path $dir).Path
        }
    }
    throw @"
package-lock.json not found.
  cd to a worktree root (e.g. phase1-t1-bridge) or win_ui_auto/app, then retry.
  lockfile: win_ui_auto/app/package-lock.json
"@
}

function Resolve-WinUiAutoRoot {
    param([string] $AppDir)
    $parent = Split-Path -Parent ([System.IO.Path]::GetFullPath($AppDir))
    if (Test-Path (Join-Path $parent "bridge_subprocess.py")) {
        return $parent
    }
    throw "Cannot find win_ui_auto root above $AppDir"
}

function bdauto {
    param([switch] $FullRuntime)

    $ErrorActionPreference = "Stop"
    $orig = Get-Location
    $appDir = Resolve-WinUiAutoAppDir
    $winUiRoot = Resolve-WinUiAutoRoot $appDir
    $ensureZip = Join-Path $winUiRoot "scripts\ensure_nauto_runtime_zip.ps1"

    try {
        Set-Location $appDir
        Write-Host "==> app: $appDir" -ForegroundColor DarkGray
        Write-Host "==> win_ui_auto: $winUiRoot" -ForegroundColor DarkGray

        Write-Host "==> Running npm ci..." -ForegroundColor Cyan
        npm ci
        if ($LASTEXITCODE -ne 0) { throw "npm ci failed" }

        Write-Host "==> Running npm run build..." -ForegroundColor Cyan
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "npm run build failed" }

        if ($FullRuntime) {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $ensureZip -Full
        }
        else {
            & powershell -NoProfile -ExecutionPolicy Bypass -File $ensureZip
        }
        if ($LASTEXITCODE -ne 0) { throw "ensure_nauto_runtime_zip.ps1 failed" }

        $env:NAuto_FORCE_UV = "1"
        $env:WIN_UI_AUTO_ROOT = $winUiRoot
        Write-Host "==> NAuto_FORCE_UV=1 WIN_UI_AUTO_ROOT=$winUiRoot" -ForegroundColor DarkGray

        Write-Host "==> Running npm run tauri dev..." -ForegroundColor Cyan
        npm run tauri dev
        if ($LASTEXITCODE -ne 0) { throw "npm run tauri dev failed" }
    }
    finally {
        Set-Location $orig
    }
}

function msiauto {
    $ErrorActionPreference = "Stop"
    $origPath = Get-Location

    $winUi = $null
    foreach ($rel in @("win_ui_auto", ".")) {
        $dir = if ($rel -eq ".") { $origPath.Path } else { Join-Path $origPath $rel }
        if (Test-Path (Join-Path $dir "scripts\pack_nauto.ps1")) {
            $winUi = (Resolve-Path $dir).Path
            break
        }
    }
    if (-not $winUi) {
        $winUi = "D:\study_pywinauto-worktrees\phase1-integration\win_ui_auto"
        Write-Host "==> fallback win_ui_auto: $winUi" -ForegroundColor Yellow
    }

    Write-Host "==> cd to $winUi ..." -ForegroundColor Cyan
    Set-Location $winUi

    Write-Host "==> Running pack_nauto.ps1..." -ForegroundColor Cyan
    powershell -ExecutionPolicy Bypass -File scripts\pack_nauto.ps1 -SkipRuntimeZip -CleanCargo -StableRustBuild
    if ($LASTEXITCODE -ne 0) { throw "pack_nauto.ps1 failed" }

    Write-Host "==> cd back to $origPath" -ForegroundColor Cyan
    Set-Location $origPath
}
