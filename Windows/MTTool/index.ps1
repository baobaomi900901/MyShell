# .\Windows\MTTool\index.ps1
# 作用: tool_ 方法集的入口文件，显示可用命令列表，支持 Tab 补全，并执行对应的脚本

function tool_ {
    <#
    .SYNOPSIS
        执行由 config.json 定义的命令脚本。
    .DESCRIPTION
        根据第一个参数查找 config.json 中对应的命令，执行关联的脚本（支持 .ps1, .py, .js）。
        若未提供命令，则显示所有可用命令列表。
        支持在 config.json 中为命令配置 "ignore_exit_code": true 来忽略非零退出码。
    .PARAMETER Command
        要执行的命令名称（对应 config.json 中的键）。
    .PARAMETER ScriptArgs
        传递给目标脚本的额外参数。
    .EXAMPLE
        tool_                      # 列出所有命令
        tool_ fun3 "Hello" -Force  # 执行 fun3 命令，传递参数
    #>
    [CmdletBinding()]
    param(
        [Parameter(Position = 0, Mandatory = $false)]
        [string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$ScriptArgs
    )

    # 设置输出编码
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8

    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        if (-not $scriptDir) {
            Write-Error "无法确定脚本目录"
            return
        }
    }

    # 读取配置
    $jsonPath = Join-Path $scriptDir "config.json"
    $config = Get-CustomConfig -JsonPath $jsonPath
    if (-not $config) { return }

    # 无命令：显示列表s
    if (-not $Command) {
        Write-Host "可用命令:" -ForegroundColor Green
        $config.PSObject.Properties | Sort-Object Name | ForEach-Object {
            $cmdName = $_.Name
            $desc = $_.Value.description
            $pathInfo = if ($_.Value.script_path) { " ($($_.Value.script_path))" } else { " (默认 src\$cmdName.ps1)" }
            Write-Host ("    {0,-20} - {1}{2}" -f $cmdName, $desc, $pathInfo)
        }
        return
    }

    # 检查命令是否存在
    if (-not $config.$Command) {
        Write-Error "未知命令: $Command"
        Write-Host "可用命令: $($config.PSObject.Properties.Name -join ', ')" -ForegroundColor Yellow
        return
    }

    $cmdConfig = $config.$Command
    $configuredPath = $cmdConfig.script_path
    $description = $cmdConfig.description

    # 解析脚本路径（扩展名只用于默认路径，如果配置了 script_path 则完全使用配置路径）
    try {
        $scriptPath = Resolve-ScriptPath -Command $Command -ConfiguredPath $configuredPath -ScriptDir $scriptDir -Extension '.ps1'
    }
    catch {
        Write-Error $_.Exception.Message
        return
    }

    # 检查脚本是否存在
    if (-not (Test-Path $scriptPath)) {
        Write-Error "脚本文件不存在: $scriptPath"
        Write-Host "  请检查 config.json 中的 script_path 配置，或确保默认路径 src\$Command.ps1 存在。" -ForegroundColor Yellow
        return
    }

    Write-Host "▶️ 执行命令 '$Command': $description" -ForegroundColor Cyan

    # 根据文件扩展名选择执行方式
    $extension = [System.IO.Path]::GetExtension($scriptPath).ToLower()
    switch ($extension) {
        '.ps1' {
            Write-Host "🔧 执行: & $scriptPath $ScriptArgs" -ForegroundColor Gray
            try {
                & $scriptPath @ScriptArgs
                $exitCode = $LASTEXITCODE
                $ignoreExitCode = $cmdConfig.ignore_exit_code -eq $true
                if ($exitCode -ne 0) {
                    if ($ignoreExitCode) {
                        Write-Warning "脚本退出码为 $exitCode，但已配置忽略，继续执行。"
                    } else {
                        throw "脚本退出码: $exitCode"
                    }
                } else {
                    Write-Host "✅ 脚本执行成功" -ForegroundColor Green
                }
            }
            catch {
                Write-Error "执行异常: $_"
                $global:LASTEXITCODE = 1
            }
        }
        '.py' {
            $interpreter = 'python'
            if (-not (Get-Command $interpreter -ErrorAction SilentlyContinue)) {
                Write-Error "未找到 $interpreter，请确保已安装并加入 PATH"
                return
            }
            Write-Host "🔧 执行: $interpreter $scriptPath $ScriptArgs" -ForegroundColor Gray
            try {
                & $interpreter $scriptPath $ScriptArgs
                $exitCode = $LASTEXITCODE
                $ignoreExitCode = $cmdConfig.ignore_exit_code -eq $true
                if ($exitCode -ne 0) {
                    if ($ignoreExitCode) {
                        Write-Warning "脚本退出码为 $exitCode，但已配置忽略，继续执行。"
                    } else {
                        throw "脚本退出码: $exitCode"
                    }
                } else {
                    Write-Host "✅ 脚本执行成功" -ForegroundColor Green
                }
            }
            catch {
                Write-Error "执行异常: $_"
                $global:LASTEXITCODE = 1
            }
        }
        '.js' {
            $interpreter = 'node'
            if (-not (Get-Command $interpreter -ErrorAction SilentlyContinue)) {
                Write-Error "未找到 $interpreter，请确保已安装并加入 PATH"
                return
            }
            Write-Host "🔧 执行: $interpreter $scriptPath $ScriptArgs" -ForegroundColor Gray
            try {
                & $interpreter $scriptPath $ScriptArgs
                $exitCode = $LASTEXITCODE
                $ignoreExitCode = $cmdConfig.ignore_exit_code -eq $true
                if ($exitCode -ne 0) {
                    if ($ignoreExitCode) {
                        Write-Warning "脚本退出码为 $exitCode，但已配置忽略，继续执行。"
                    } else {
                        throw "脚本退出码: $exitCode"
                    }
                } else {
                    Write-Host "✅ 脚本执行成功" -ForegroundColor Green
                }
            }
            catch {
                Write-Error "执行异常: $_"
                $global:LASTEXITCODE = 1
            }
        }
        # 可按需添加其他类型，如 '.bat', '.cmd', '.exe'
        default {
            Write-Error "不支持的脚本类型: $extension (文件: $scriptPath)"
        }
    }
}

# --- Tab 补全器 ---
$scriptDirForCompletion = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$script:tool_configPath = Join-Path $scriptDirForCompletion "config.json"

Register-ArgumentCompleter -CommandName tool_ -ParameterName Command -ScriptBlock {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

    $config = Get-CustomConfig -JsonPath $script:tool_configPath
    if (-not $config) { return $null }

    $allCommands = $config.PSObject.Properties.Name
    $allCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
        $cmdName = $_
        $desc = $config.$cmdName.description
        [System.Management.Automation.CompletionResult]::new($cmdName, $cmdName, 'ParameterValue', $desc)
    }
}