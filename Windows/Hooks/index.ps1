# .\Windows\Hooks\index.ps1
# 作用: hooks_ 方法集的入口文件，显示可用命令列表，支持 Tab 补全，并执行对应的脚本

function hooks_ {
    [CmdletBinding()]
    param(
        [Parameter(Position = 0, Mandatory = $false)]
        [string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$ScriptArgs
    )

    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8

    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        if (-not $scriptDir) {
            Write-Host "❌ 无法确定脚本目录" -ForegroundColor Red
            return
        }
    }

    $jsonPath = Join-Path $scriptDir "info.json"

    if (-not (Test-Path $jsonPath)) {
        Write-Host "❌ 找不到配置文件: $jsonPath" -ForegroundColor Red
        return
    }

    try {
        $rawLines = Get-Content $jsonPath -Raw -Encoding UTF8
        $cleanJson = ($rawLines -split "`r`n|`n" | Where-Object { $_ -notmatch '^\s*#' }) -join "`n"
        $config = $cleanJson | ConvertFrom-Json
    }
    catch {
        Write-Host "❌ 解析 info.json 失败: $_" -ForegroundColor Red
        return
    }

    if (-not $Command) {
        Write-Host "可用目录:" -ForegroundColor Green
        $config.PSObject.Properties | ForEach-Object {
            $cmdName = $_.Name
            $desc = $_.Value.description
            Write-Host ("    {0,-20} - {1}" -f $cmdName, $desc)
        }
        return
    }

    if (-not $config.$Command) {
        Write-Host "❌ 未知命令: $Command" -ForegroundColor Red
        Write-Host "可用命令: $($config.PSObject.Properties.Name -join ', ')" -ForegroundColor Yellow
        return
    }

    $scriptPath = $config.$Command.script_path
    $description = $config.$Command.description

    if (-not [System.IO.Path]::IsPathRooted($scriptPath)) {
        $scriptPath = Join-Path $scriptDir $scriptPath
    }

    if (-not (Test-Path $scriptPath)) {
        Write-Host "❌ 脚本文件不存在: $scriptPath" -ForegroundColor Red
        return
    }

    Write-Host "▶️ 执行命令 '$Command': $description" -ForegroundColor Cyan

    $extension = [System.IO.Path]::GetExtension($scriptPath).ToLower()
    switch ($extension) {
        '.py'  { $interpreter = 'python' }
        '.js'  { $interpreter = 'node' }
        default {
            Write-Host "❌ 不支持的脚本类型: $extension" -ForegroundColor Red
            return
        }
    }

    if (-not (Get-Command $interpreter -ErrorAction SilentlyContinue)) {
        Write-Host "❌ 未找到 $interpreter，请确保已安装并加入 PATH" -ForegroundColor Red
        return
    }

    Write-Host "🔧 执行: $interpreter $scriptPath $ScriptArgs" -ForegroundColor Gray

    try {
        & $interpreter $scriptPath $ScriptArgs
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) {
            throw "脚本执行失败，退出码: $exitCode"
        }
        else {
            Write-Host "✅ 脚本执行成功" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "❌ 执行异常: $_" -ForegroundColor Red
        return
    }
}

# --- Tab 补全器保持不变 ---
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$jsonPath = Join-Path $scriptDir "info.json"
$script:jsonPathForCompletion = $jsonPath

Register-ArgumentCompleter -CommandName hooks_ -ParameterName Command -ScriptBlock {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

    if (-not (Test-Path $script:jsonPathForCompletion)) {
        return $null
    }

    try {
        $rawLines = Get-Content $script:jsonPathForCompletion -Raw -Encoding UTF8 -ErrorAction Stop
        $cleanJson = ($rawLines -split "`r`n|`n" | Where-Object { $_ -notmatch '^\s*#' }) -join "`n"
        $config = $cleanJson | ConvertFrom-Json
    }
    catch {
        return $null
    }

    $allCommands = $config.PSObject.Properties.Name
    $allCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
        $cmdName = $_
        $desc = $config.$cmdName.description
        [System.Management.Automation.CompletionResult]::new($cmdName, $cmdName, 'ParameterValue', $desc)
    }
}