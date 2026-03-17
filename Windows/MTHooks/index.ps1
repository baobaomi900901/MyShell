# .\Windows\Hooks\index.ps1
# 作用: hooks_ 方法集的入口文件，显示可用命令列表，支持 Tab 补全，并执行对应的脚本

# 辅助函数：读取并解析 info.json（支持以 # 开头的注释）
function Get-HooksConfig {
    param(
        [string]$JsonPath
    )
    if (-not (Test-Path $JsonPath)) {
        Write-Host "❌ 找不到配置文件: $JsonPath" -ForegroundColor Red
        return $null
    }
    try {
        $rawLines = Get-Content $JsonPath -Raw -Encoding UTF8 -ErrorAction Stop
        # 移除以 # 开头的注释行（允许行前有空格）
        $cleanJson = ($rawLines -split "`r`n|`n" | Where-Object { $_ -notmatch '^\s*#' }) -join "`n"
        $config = $cleanJson | ConvertFrom-Json
        return $config
    }
    catch {
        Write-Host "❌ 解析 info.json 失败: $_" -ForegroundColor Red
        return $null
    }
}

function hooks_ {
    # 用途: 这是一个模板脚手架(可以忽略)
    # 启用对 -ErrorAction 等参数的处理
    [CmdletBinding()]

    # 定义参数
    param(
        [Parameter(Position = 0, Mandatory = $false)]
        [string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$ScriptArgs
    )

    # 设置输出编码为 UTF-8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8

    $scriptDir = $PSScriptRoot  # 脚本所在目录

    # 如果未指定脚本目录，则尝试从当前工作目录查找
    if (-not $scriptDir) {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        if (-not $scriptDir) {
            Write-Host "❌ 无法确定脚本目录" -ForegroundColor Red
            return
        }
    }

    # --- 读取与解析配置文件 info.json ---
    $jsonPath = Join-Path $scriptDir "info.json"
    $config = Get-HooksConfig -JsonPath $jsonPath
    if (-not $config) { return }

    # 显示可用命令列表
    if (-not $Command) {
        Write-Host "可用目录:" -ForegroundColor Green
        $config.PSObject.Properties | ForEach-Object {
            $cmdName = $_.Name
            $desc = $_.Value.description
            Write-Host ("    {0,-20} - {1}" -f $cmdName, $desc)
        }
        return
    }

    # --- 执行命令 ---
    if (-not $config.$Command) {
        Write-Host "❌ 未知命令: $Command" -ForegroundColor Red
        Write-Host "可用命令: $($config.PSObject.Properties.Name -join ', ')" -ForegroundColor Yellow
        return
    }

    $scriptPath = $config.$Command.script_path                  # 原始脚本路径
    $description = $config.$Command.description                 # 命令描述

    # --- 处理环境变量占位符 @MYSHELL ---
    if ($scriptPath -like '@MYSHELL*') {
        $myshell = $env:MYSHELL
        if (-not $myshell) {
            Write-Host "❌ 环境变量 MYSHELL 未设置，无法解析路径: $scriptPath" -ForegroundColor Red
            return
        }
        # 将开头的 @MYSHELL 替换为实际环境变量值
        $scriptPath = $scriptPath -replace '^@MYSHELL', $myshell
        Write-Host "🔧 已替换 @MYSHELL => $myshell" -ForegroundColor Gray
    }

    # 若脚本路径不是绝对路径，则尝试从脚本目录查找
    if (-not [System.IO.Path]::IsPathRooted($scriptPath)) {
        $scriptPath = Join-Path $scriptDir $scriptPath
    }

    # 若脚本文件不存在，则提示用户检查路径
    if (-not (Test-Path $scriptPath)) {
        Write-Host "❌ 脚本文件不存在: $scriptPath" -ForegroundColor Red
        return
    }

    Write-Host "▶️ 执行命令 '$Command': $description" -ForegroundColor Cyan    # 显示执行信息

    $extension = [System.IO.Path]::GetExtension($scriptPath).ToLower()
    switch ($extension) {
        '.py'  { $interpreter = 'python' }
        '.js'  { $interpreter = 'node' }
        '.ps1' {
            # 直接调用 PowerShell 脚本（当前会话中执行）
            Write-Host "🔧 执行: & $scriptPath $ScriptArgs" -ForegroundColor Gray
            try {
                & $scriptPath @ScriptArgs
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
            return  # 避免执行后续通用代码
        }
        default {
            Write-Host "❌ 不支持的脚本类型: $extension" -ForegroundColor Red
            return
        }
    }


    # 检查是否已安装 interpreter
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

# --- Tab 补全器（使用相同的配置读取函数）---
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$script:jsonPathForCompletion = Join-Path $scriptDir "info.json"

Register-ArgumentCompleter -CommandName hooks_ -ParameterName Command -ScriptBlock {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

    $config = Get-HooksConfig -JsonPath $script:jsonPathForCompletion
    if (-not $config) { return $null }

    $allCommands = $config.PSObject.Properties.Name
    $allCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
        $cmdName = $_
        $desc = $config.$cmdName.description
        [System.Management.Automation.CompletionResult]::new($cmdName, $cmdName, 'ParameterValue', $desc)
    }
}