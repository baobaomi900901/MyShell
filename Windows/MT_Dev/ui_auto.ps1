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

function Test-WinUiAutoRoot {
    param([Parameter(Mandatory = $true)][string] $Root)

    # Current UIAutoma source layout: package root + runtime.bootstrap.
    if (
        (Test-Path -LiteralPath (Join-Path $Root "pyproject.toml")) -and
        (Test-Path -LiteralPath (Join-Path $Root "runtime\bootstrap.py"))
    ) {
        return $true
    }

    # Legacy UiPilot / pre-bootstrap Desktop Bridge launcher.
    if (Test-Path -LiteralPath (Join-Path $Root "bridge_subprocess.py")) {
        return $true
    }

    return $false
}

function Resolve-WinUiAutoRoot {
    param([string] $AppDir)
    $parent = Split-Path -Parent ([System.IO.Path]::GetFullPath($AppDir))
    if (Test-WinUiAutoRoot $parent) {
        return $parent
    }
    throw "Cannot find UIAutoma/win_ui_auto root above $AppDir (expected pyproject.toml + runtime\bootstrap.py, or legacy bridge_subprocess.py)"
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

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock] $Command,

        [Parameter(Mandatory = $true)]
        [string] $FailureMessage,

        [long[]] $AllowedExitCodes = @(0)
    )

    # Cargo/npm/vite/tauri write progress to stderr even on success. With
    # $ErrorActionPreference=Stop (and PS7 native-error preference), that stderr
    # becomes a terminating NativeCommandError before LASTEXITCODE is checked.
    $previousErrorAction = $ErrorActionPreference
    $hadNativePreference = $false
    $previousNativePreference = $null
    if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
        $hadNativePreference = $true
        $previousNativePreference = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
    }
    $ErrorActionPreference = "Continue"
    $exitCode = [int64]0
    try {
        # Do not assign/capture this call: child stdout must stream to the host.
        & $Command
        if ($null -ne $LASTEXITCODE) {
            $exitCode = [int64]$LASTEXITCODE
        }
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $previousNativePreference
        }
    }

    if ($AllowedExitCodes -notcontains $exitCode) {
        throw "$FailureMessage (exit=$exitCode)"
    }
}

function bdauto {
    param(
        [switch] $FullRuntime,
        [switch] $InstallWeb,
        [switch] $PlanOnly
    )

    $ErrorActionPreference = "Stop"
    if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
        $PSNativeCommandUseErrorActionPreference = $false
    }
    $orig = Get-Location
    $appDir = Resolve-WinUiAutoAppDir
    $winUiRoot = Resolve-WinUiAutoRoot $appDir

    if ($InstallWeb) {
        $bdautoEntry = Join-Path $winUiRoot "scripts\bdauto.py"
        if (-not (Test-Path -LiteralPath $bdautoEntry)) {
            $worktreeOutput = & git -C $winUiRoot worktree list --porcelain
            if ($LASTEXITCODE -ne 0) {
                throw "Cannot enumerate Git worktrees for $winUiRoot"
            }
            foreach ($line in $worktreeOutput) {
                if (-not $line.StartsWith("worktree ")) {
                    continue
                }
                $candidateRoot = $line.Substring("worktree ".Length)
                $candidateEntry = Join-Path $candidateRoot "scripts\bdauto.py"
                if (Test-Path -LiteralPath $candidateEntry) {
                    $bdautoEntry = (Resolve-Path -LiteralPath $candidateEntry).Path
                    break
                }
            }
        }
        if (-not (Test-Path -LiteralPath $bdautoEntry)) {
            throw "Project bdauto entry not found in this repository's worktrees: scripts\bdauto.py"
        }

        $bdautoArgs = @(
            "run",
            "--project", $winUiRoot,
            "python", $bdautoEntry,
            "--root", $winUiRoot,
            "--install-web"
        )
        if ($PlanOnly) {
            $bdautoArgs += "--print-plan"
        }
        Invoke-NativeChecked -FailureMessage "project bdauto command failed" -Command {
            & uv @bdautoArgs
        }
        return
    }
    if ($PlanOnly) {
        throw "-PlanOnly requires -InstallWeb"
    }
    $uiautomaIdentityPath = Join-Path $winUiRoot "config\uiautoma_identity_contract.json"
    $uiautomaIdentity = $null
    if (Test-Path -LiteralPath $uiautomaIdentityPath) {
        try {
            $uiautomaIdentity = Get-Content -Raw -Encoding UTF8 -LiteralPath $uiautomaIdentityPath | ConvertFrom-Json
        }
        catch {
            throw "Invalid UIAutoma identity contract: $($_.Exception.Message)"
        }
        if (
            $uiautomaIdentity.product.slug -ne "uiautoma" -or
            $uiautomaIdentity.runtime.environmentPrefix -ne "UIAUTOMA_"
        ) {
            throw "Unsupported UIAutoma identity contract: $uiautomaIdentityPath"
        }
    }
    $isUiAutomaRepo = $null -ne $uiautomaIdentity

    if ($isUiAutomaRepo -and $FullRuntime) {
        throw "-FullRuntime is unavailable for UIAutoma: legacy runtime ZIP production is retired. Omit -FullRuntime."
    }

    $ensureZip = $null
    if (-not $isUiAutomaRepo) {
        $ensureZip = Resolve-FirstExistingPath $winUiRoot @(
            "scripts\ensure_uipilot_runtime_zip.ps1",
            "scripts\ensure_nauto_runtime_zip.ps1"
        )
    }
    $nativeHostBuild = $null
    $nativeHostBuildCandidate = Join-Path $winUiRoot "chrome\native_host\build_native_host.py"
    if (Test-Path -LiteralPath $nativeHostBuildCandidate) {
        $nativeHostBuild = (Resolve-Path -LiteralPath $nativeHostBuildCandidate).Path
    }
    $storePluginBuild = $null
    $storePluginBuildCandidate = Join-Path $winUiRoot "chrome\build_store_plugin.mjs"
    if (Test-Path -LiteralPath $storePluginBuildCandidate) {
        $storePluginBuild = (Resolve-Path -LiteralPath $storePluginBuildCandidate).Path
    }
    $storePluginOut = if ($isUiAutomaRepo) {
        $uiautomaUserDataRoot = [Environment]::ExpandEnvironmentVariables(
            [string] $uiautomaIdentity.app.userDataRoot
        )
        if (
            [string]::IsNullOrWhiteSpace($uiautomaUserDataRoot) -or
            $uiautomaUserDataRoot -match "%[^%]+%"
        ) {
            throw "Cannot resolve UIAutoma userDataRoot from identity contract"
        }
        Join-Path $uiautomaUserDataRoot "bdauto-store-plugin"
    }
    else {
        Join-Path $env:LOCALAPPDATA "UiPilot\bdauto-store-plugin"
    }
    $webStackInstaller = $null
    $webStackInstallerCandidate = Join-Path $winUiRoot "chrome\build_install_local.py"
    if ($InstallWeb) {
        if (-not (Test-Path -LiteralPath $webStackInstallerCandidate)) {
            throw "Web Stack installer not found: $webStackInstallerCandidate"
        }
        $webStackInstaller = (Resolve-Path -LiteralPath $webStackInstallerCandidate).Path
    }
    $devTauri = Join-Path $winUiRoot "scripts\dev_tauri.ps1"

    try {
        Set-Location $appDir
        Write-Host "==> app: $appDir" -ForegroundColor DarkGray
        Write-Host "==> win_ui_auto: $winUiRoot" -ForegroundColor DarkGray

        if (Test-Path -LiteralPath $devTauri) {
            Invoke-NativeChecked -FailureMessage "dev_tauri cleanup failed" -Command {
                & $devTauri -CleanupOnly
            }
        }

        Write-Host "==> Running npm ci..." -ForegroundColor Cyan

        cls

        Invoke-NativeChecked -FailureMessage "npm ci failed" -Command { npm ci }

        Write-Host "==> Running npm run build..." -ForegroundColor Cyan
        Invoke-NativeChecked -FailureMessage "npm run build failed" -Command { npm run build }

        if ($InstallWeb) {
            Write-Host "==> Building and installing Chrome Web Stack..." -ForegroundColor Cyan
            $previousPythonUtf8 = $env:PYTHONUTF8
            $previousConsoleOutputEncoding = [Console]::OutputEncoding
            $previousPowerShellOutputEncoding = $OutputEncoding
            try {
                $utf8 = [System.Text.UTF8Encoding]::new($false)
                [Console]::OutputEncoding = $utf8
                $OutputEncoding = $utf8
                $env:PYTHONUTF8 = "1"
                Push-Location $winUiRoot
                try {
                    Invoke-NativeChecked -FailureMessage "build_install_local.py failed" -Command {
                        & uv run python $webStackInstaller
                    }
                }
                finally {
                    Pop-Location
                }
            }
            finally {
                [Console]::OutputEncoding = $previousConsoleOutputEncoding
                $OutputEncoding = $previousPowerShellOutputEncoding
                if ($null -eq $previousPythonUtf8) {
                    Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
                }
                else {
                    $env:PYTHONUTF8 = $previousPythonUtf8
                }
            }
        }
        else {
            if ($storePluginBuild) {
                Write-Host "==> Building Chrome store plugin: $storePluginOut" -ForegroundColor Cyan
                Invoke-NativeChecked -FailureMessage "build_store_plugin.mjs failed" -Command {
                    & node $storePluginBuild --out-dir $storePluginOut
                }
            }

            if ($nativeHostBuild) {
                Write-Host "==> Running build_native_host.py..." -ForegroundColor Cyan
                Invoke-NativeChecked -FailureMessage "build_native_host.py failed" -Command {
                    & uv run python $nativeHostBuild
                }
            }
        }

        if (-not $isUiAutomaRepo) {
            if ($FullRuntime) {
                Invoke-NativeChecked -FailureMessage "$([System.IO.Path]::GetFileName($ensureZip)) failed" -Command {
                    & $ensureZip -Full
                }
            }
            else {
                Invoke-NativeChecked -FailureMessage "$([System.IO.Path]::GetFileName($ensureZip)) failed" -Command {
                    & $ensureZip
                }
            }
        }
        else {
            Write-Host "==> Legacy runtime ZIP skipped for UIAutoma" -ForegroundColor DarkGray
        }

        if ($isUiAutomaRepo) {
            $env:UIAUTOMA_FORCE_UV = "1"
            $env:UIAUTOMA_ROOT = $winUiRoot
            Write-Host "==> UIAUTOMA_FORCE_UV=1 UIAUTOMA_ROOT=$winUiRoot" -ForegroundColor DarkGray
        }
        else {
            $env:UIPILOT_FORCE_UV = "1"
            $env:UIPILOT_ROOT = $winUiRoot
            $env:NAuto_FORCE_UV = "1"
            $env:WIN_UI_AUTO_ROOT = $winUiRoot
            Write-Host "==> UIPILOT_FORCE_UV=1 UIPILOT_ROOT=$winUiRoot" -ForegroundColor DarkGray
        }

        if (Test-Path -LiteralPath $devTauri) {
            Write-Host "==> Running dev_tauri.ps1..." -ForegroundColor Cyan
            # CTRL+C / console close on Windows often surfaces as these statuses.
            Invoke-NativeChecked `
                -FailureMessage "dev_tauri.ps1 failed" `
                -AllowedExitCodes @(0, -1073741510, 3221225786) `
                -Command { & $devTauri }
        }
        else {
            Write-Host "==> Running npm run tauri dev..." -ForegroundColor Cyan
            Invoke-NativeChecked -FailureMessage "npm run tauri dev failed" -Command {
                npm run tauri dev
            }
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
