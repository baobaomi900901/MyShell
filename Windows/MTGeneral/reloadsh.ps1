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
    $pythonScript = Join-Path $env:myshell "public\_script\reloadsh.py"
    if (-not (Test-Path $pythonScript)) {
        Write-Error "找不到 reloadsh.py，预期路径：$pythonScript"
        return
    }

    # 检查环境变量 $env:myshell 是否存在
    if (-not $env:myshell) {
        Write-Error "环境变量 'myshell' 未设置，无法确定 Windows 目录和 JSON 文件路径。"
        return
    }

    # 构建参数路径
    $windowsDir = Join-Path $env:myshell "windows"
    $public_script_dir = Join-Path $env:myshell "public"
    $system_type = "windows"
    $jsonFile = Join-Path $env:myshell "config\function_tracker.json"

    # 调用 Python 脚本，传递必需参数，同时保留用户可能传入的额外参数
    & python $pythonScript --system-dir "$windowsDir" --public-script-dir "$public_script_dir" --system-type "$system_type" --json-file "$jsonFile" @args
    $exitCode = $LASTEXITCODE

    # 如果退出码为 1，表示用户选择了 Yes 并希望关闭当前窗口
    if ($exitCode -eq 1) {
        Write-Host "正在关闭当前窗口..."
        Start-Sleep -Seconds 1  # 让用户看到最后的消息
        [Environment]::Exit(0)  # 结束当前 PowerShell 进程，从而关闭窗口
    }
}