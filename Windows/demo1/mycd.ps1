function mycd {
    $myshell = $env:MYSHELL
    if (-not $myshell) {
        Write-Host "❌ 环境变量 MYSHELL 未设置，无法定位脚本" -ForegroundColor Red
        return
    }

    $scriptPath = Join-Path $myshell "Windows\demo\cd_.py"
    $configPath = Join-Path $myshell "config\private\path.json"

    # 调用 Python 脚本并捕获标准输出（路径字符串）
    $targetPath = python $scriptPath $configPath

    # 去除可能的首尾空白字符
    $targetPath = $targetPath.Trim()

    if (-not $targetPath) {
        # 用户按 w + q 退出或输出为空，不做任何操作
        Write-Host "操作取消" -ForegroundColor Yellow
        return
    }

    if (Test-Path $targetPath -PathType Container) {
        Set-Location $targetPath
        Write-Host "已切换到: $targetPath" -ForegroundColor Green
    }
    else {
        Write-Host "❌ 路径无效或不存在: $targetPath" -ForegroundColor Red
    }
}