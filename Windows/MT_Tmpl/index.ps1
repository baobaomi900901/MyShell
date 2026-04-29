# .\Windows\MTTmpl\index.ps1
# 作用: tmpl 方法集入口；无参时与 cd_/tool_ 相同，用 tool_menu.py 上下键选择，否则执行对应脚本

function tmpl_ {
    <#
    .SYNOPSIS
        执行由 config.json 定义的命令脚本。
    .DESCRIPTION
        根据第一个参数查找 config.json 中对应的命令，执行关联的脚本（支持 .ps1, .py, .js）。
        若未提供命令，优先通过 public\_script\tool_menu.py 交互选择（需 Python）；失败则打印文本列表。
        支持在 config.json 中为命令配置 "ignore_exit_code": true 来忽略非零退出码。
    .PARAMETER Command
        要执行的命令名称（对应 config.json 中的键）。
    .PARAMETER ScriptArgs
        传递给目标脚本的额外参数。
    .EXAMPLE
        tmpl                      # 交互菜单选命令（或文本列表回退）
        tmpl fun3 "Hello" -Force  # 执行 fun3 命令，传递参数
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

    # 无命令：与 cd_/tool_ 相同，用 questionary 上下键选择（tool_menu.py）
    if (-not $Command) {
        $menuScript = $null
        if ($env:MYSHELL) {
            $c = Join-Path $env:MYSHELL "public\_script\tool_menu.py"
            if (Test-Path $c) { $menuScript = $c }
        }
        if (-not $menuScript) {
            $rel = Join-Path $scriptDir "..\..\public\_script\tool_menu.py"
            $abs = [System.IO.Path]::GetFullPath($rel)
            if (Test-Path $abs) { $menuScript = $abs }
        }

        if ($menuScript -and (Get-Command python -ErrorAction SilentlyContinue)) {
            $tempPick = [System.IO.Path]::GetTempFileName()
            try {
                & python $menuScript $jsonPath $tempPick
                $exitMenu = $LASTEXITCODE
                if ($exitMenu -ne 0) {
                    Write-Warning "交互菜单异常 (退出码: $exitMenu)，改为文本列表。"
                }
                else {
                    $rawPick = Get-Content -Path $tempPick -Raw -ErrorAction SilentlyContinue
                    if (-not [string]::IsNullOrWhiteSpace($rawPick)) {
                        $Command = $rawPick.Trim()
                    }
                    else {
                        return
                    }
                }
            }
            finally {
                if (Test-Path $tempPick) {
                    Remove-Item -Path $tempPick -Force -ErrorAction SilentlyContinue
                }
            }
        }

        if (-not $Command) {
            Write-Host "可用命令:" -ForegroundColor Green
            $config.PSObject.Properties | Sort-Object Name | ForEach-Object {
                $cmdName = $_.Name
                $desc = $_.Value.description
                $pathInfo = if ($_.Value.script_path) { " ($($_.Value.script_path))" } else { " (默认 src\$cmdName.ps1)" }
                Write-Host ("    {0,-20} - {1}{2}" -f $cmdName, $desc, $pathInfo)
            }
            if (-not $menuScript) {
                Write-Host "提示: 将 MyShell 的 public\_script\tool_menu.py 置于可发现路径，或设置 MYSHELL 以启用上下键菜单。" -ForegroundColor DarkGray
            }
            elseif (-not (Get-Command python -ErrorAction SilentlyContinue)) {
                Write-Host "提示: 未找到 python，无法启动交互菜单。" -ForegroundColor DarkGray
            }
            return
        }
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


# Tab 补全：config 与 index.ps1 同目录，避免随当前工作目录变化而失效
$script:MT_Tmpl_ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$script:MT_Tmpl_ConfigPath = Join-Path $script:MT_Tmpl_ScriptDir 'config.json'

$script:myshell_tmplCompleter = {
    param($wordToComplete, $commandAst, $cursorPosition)

    $configFile = $script:MT_Tmpl_ConfigPath

    if (-not (Test-Path -LiteralPath $configFile)) {
        return
    }

    try {
        $config = Get-Content -Path $configFile -Raw -Encoding UTF8 | ConvertFrom-Json

        $completionItems = $config.PSObject.Properties | Where-Object {
            $_.Value -and ($_.Value.script_path -or $_.Value.description)
        } | ForEach-Object {
            $displayName = $_.Name -replace '_', '-'
            $description = ($_.Value.description -replace "`n", " ")
            [System.Management.Automation.CompletionResult]::new(
                $displayName,
                $displayName,
                'ParameterValue',
                $description
            )
        }

        $completionItems | Where-Object {
            $_.CompletionText -like "$wordToComplete*"
        }
    } catch {
        return
    }
}
Register-ArgumentCompleter -CommandName tmpl_ -ScriptBlock $script:myshell_tmplCompleter