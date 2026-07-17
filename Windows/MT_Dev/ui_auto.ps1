function Resolve-WinUiAutoAppDir {
    $dir = (Get-Location).Path
    while ($true) {
        foreach ($rel in @("win_ui_auto\app", "app", ".")) {
            $candidate = if ($rel -eq ".") { $dir } else { Join-Path $dir $rel }
            if (Test-Path -LiteralPath (Join-Path $candidate "package-lock.json")) {
                return (Resolve-Path -LiteralPath $candidate).Path
            }
        }

        $parent = Split-Path -Parent $dir
        if (-not $parent -or $parent -eq $dir) { break }
        $dir = $parent
    }
    throw @"
package-lock.json not found.
  cd to a worktree root, win_ui_auto, win_ui_auto/app, or a nested path inside them, then retry.
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

function Resolve-FirstExistingPath {
    param(
        [Parameter(Mandatory=$true)][string] $Root,
        [Parameter(Mandatory=$true)][string[]] $RelativePaths
    )

    foreach ($rel in $RelativePaths) {
        $path = Join-Path $Root $rel
        if (Test-Path -LiteralPath $path) {
            return (Resolve-Path -LiteralPath $path).Path
        }
    }

    throw "None of these paths exist under ${Root}: $($RelativePaths -join ', ')"
}

function bdauto {
    param([switch] $FullRuntime)

    $ErrorActionPreference = "Stop"
    $orig = Get-Location
    $appDir = Resolve-WinUiAutoAppDir
    $winUiRoot = Resolve-WinUiAutoRoot $appDir
    $ensureZip = Resolve-FirstExistingPath $winUiRoot @(
        "scripts\ensure_uipilot_runtime_zip.ps1",
        "scripts\ensure_nauto_runtime_zip.ps1"
    )
    $nativeHostBuild = $null
    $nativeHostBuildCandidate = Join-Path $winUiRoot "chrome\native_host\build_native_host.py"
    if (Test-Path -LiteralPath $nativeHostBuildCandidate) {
        $nativeHostBuild = (Resolve-Path -LiteralPath $nativeHostBuildCandidate).Path
    }
    $devTauri = Join-Path $winUiRoot "scripts\dev_tauri.ps1"

    try {
        Set-Location $appDir
        Write-Host "==> app: $appDir" -ForegroundColor DarkGray
        Write-Host "==> win_ui_auto: $winUiRoot" -ForegroundColor DarkGray

        if (Test-Path -LiteralPath $devTauri) {
            & $devTauri -CleanupOnly
            if ($LASTEXITCODE -ne 0) { throw "dev_tauri cleanup failed" }
        }

        Write-Host "==> Running npm ci..." -ForegroundColor Cyan

        cls

        npm ci
        if ($LASTEXITCODE -ne 0) { throw "npm ci failed" }

        Write-Host "==> Running npm run build..." -ForegroundColor Cyan
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "npm run build failed" }

        if ($nativeHostBuild) {
            Write-Host "==> Running build_native_host.py..." -ForegroundColor Cyan
            & uv run python $nativeHostBuild
            if ($LASTEXITCODE -ne 0) { throw "build_native_host.py failed" }
        }

        if ($FullRuntime) {
            & $ensureZip -Full
        }
        else {
            & $ensureZip
        }
        if ($LASTEXITCODE -ne 0) { throw "$([System.IO.Path]::GetFileName($ensureZip)) failed" }

        $env:UIPILOT_FORCE_UV = "1"
        $env:UIPILOT_ROOT = $winUiRoot
        $env:NAuto_FORCE_UV = "1"
        $env:WIN_UI_AUTO_ROOT = $winUiRoot
        Write-Host "==> UIPILOT_FORCE_UV=1 UIPILOT_ROOT=$winUiRoot" -ForegroundColor DarkGray

        if (Test-Path -LiteralPath $devTauri) {
            Write-Host "==> Running dev_tauri.ps1..." -ForegroundColor Cyan
            & $devTauri
            $devExit = if ($null -ne $LASTEXITCODE) { [int64]$LASTEXITCODE } else { 0 }
            if ($devExit -ne 0 -and $devExit -ne -1073741510 -and $devExit -ne 3221225786) {
                throw "dev_tauri.ps1 failed"
            }
        }
        else {
            Write-Host "==> Running npm run tauri dev..." -ForegroundColor Cyan
            npm run tauri dev
            if ($LASTEXITCODE -ne 0) { throw "npm run tauri dev failed" }
        }
    }
    finally {
        Set-Location $orig
    }
}

function msiauto {
    $ErrorActionPreference = "Stop"
    $origPath = Get-Location

    $winUi = $null
    $packScript = $null
    foreach ($rel in @("win_ui_auto", ".")) {
        $dir = if ($rel -eq ".") { $origPath.Path } else { Join-Path $origPath $rel }
        foreach ($packRel in @("scripts\pack_uipilot.ps1", "scripts\pack_nauto.ps1")) {
            $candidate = Join-Path $dir $packRel
            if (-not (Test-Path -LiteralPath $candidate)) { continue }
            $winUi = (Resolve-Path $dir).Path
            $packScript = (Resolve-Path -LiteralPath $candidate).Path
            break
        }
        if ($winUi) { break }
    }
    if (-not $winUi) {
        $winUi = "D:\study_pywinauto-worktrees\phase1-integration\win_ui_auto"
        Write-Host "==> fallback win_ui_auto: $winUi" -ForegroundColor Yellow
        $packScript = Resolve-FirstExistingPath $winUi @(
            "scripts\pack_uipilot.ps1",
            "scripts\pack_nauto.ps1"
        )
    }

    Write-Host "==> cd to $winUi ..." -ForegroundColor Cyan
    Set-Location $winUi

    Write-Host "==> Running $([System.IO.Path]::GetFileName($packScript))..." -ForegroundColor Cyan
    & $packScript -SkipRuntimeZip -CleanCargo -StableRustBuild
    if ($LASTEXITCODE -ne 0) { throw "$([System.IO.Path]::GetFileName($packScript)) failed" }

    Write-Host "==> cd back to $origPath" -ForegroundColor Cyan
    Set-Location $origPath
}
