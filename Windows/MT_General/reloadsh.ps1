# 生效脚本
# . $PROFILE 
# 查询所有自定义别名 
# Get-Alias | Where-Object { $_.Options -eq "None" } | Select-Object Name, Definition
# 查询所有自定义函数 
# Get-ChildItem Function: | Select-Object Name, Definition

function reloadsh {
    # 用途: 重新加载 powershell 脚本方法
    <#
    .SYNOPSIS
        调用 reloadsh.py 并根据其退出码决定是否关闭当前 PowerShell 窗口。
    #>
    # 检查环境变量 $env:myshell 是否存在
    if (-not $env:myshell) {
        Write-Error "环境变量 'myshell' 未设置，无法确定 Windows 目录和 JSON 文件路径。"
        $global:LASTEXITCODE = 1
        return
    }

    $pythonScript = Join-Path $env:myshell "public\_script\reloadsh.py"
    if (-not (Test-Path -LiteralPath $pythonScript -PathType Leaf)) {
        Write-Error "找不到 reloadsh.py，预期路径：$pythonScript"
        $global:LASTEXITCODE = 1
        return
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $pythonCommand) {
        $global:LASTEXITCODE = 10
        Write-Error "未找到 Python，请确认已安装并加入 PATH。当前终端已保留。"
        return
    }

    # 构建参数路径
    $windowsDir = Join-Path $env:myshell "windows"
    $public_script_dir = Join-Path $env:myshell "public"
    $system_type = "windows"
    $jsonFile = Join-Path $env:myshell "config\private\function_tracker.json"

    # 调用 Python 脚本，传递必需参数，同时保留用户可能传入的额外参数
    # 禁止上次命令遗留的 43 被误认为本次已经确认可以关闭终端。
    $global:LASTEXITCODE = 10
    # 43 是正常交互结果，不应被 PowerShell 7 的原生命令错误策略拦截。
    $PSNativeCommandUseErrorActionPreference = $false
    try {
        & $pythonCommand $pythonScript --system-dir "$windowsDir" --public-script-dir "$public_script_dir" --system-type "$system_type" --json-file "$jsonFile" @args
        $exitCode = $LASTEXITCODE
    } catch {
        $global:LASTEXITCODE = 10
        Write-Error "无法运行 reloadsh.py: $($_.Exception.Message)。当前终端已保留。"
        return
    }

    # 43 只表示用户已确认新终端正常打开；其他非零退出码都是执行错误。
    if ($exitCode -eq 43) {
        # 调用 closeTerminal 函数（需要提前定义）
        if (Get-Command closeTerminal -ErrorAction SilentlyContinue) {
            closeTerminal -Seconds 3
        } else {
            Write-Host "正在关闭当前窗口..."
            Start-Sleep -Seconds 1
            [Environment]::Exit(0)
        }
    } elseif ($exitCode -ne 0) {
        Write-Error "reloadsh 执行失败，退出码: $exitCode。当前终端已保留。"
    }
}

function closeTerminal {
    param(
        [int]$Seconds = 3
    )
    Write-Host "即将关闭终端窗口..." -ForegroundColor Yellow
    for ($i = $Seconds; $i -gt 0; $i--) {
        Write-Host "  剩余 $i 秒" -ForegroundColor Cyan
        Start-Sleep -Seconds 1
    }
    [Environment]::Exit(0) 
}
