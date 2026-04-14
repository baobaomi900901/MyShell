# Windows/MTGeneral/cd_.ps1

function cd_ {
    $myshell = $env:MYSHELL
    if (-not $myshell) {
        Write-Host "❌ 环境变量 MYSHELL 未设置" -ForegroundColor Red
        return
    }
    
    $pyScript = Join-Path $myshell "public\_script\cd.py"
    $configPath = Join-Path $myshell "config\private\path.json"

    if (-not (Test-Path $pyScript)) {
        Write-Host "❌ 找不到 Python 脚本: $pyScript" -ForegroundColor Red
        return
    }

    # 1. 生成一个临时文件路径用于进程间通信
    $tempFile = [System.IO.Path]::GetTempFileName()

    try {
        # 2. 调用 Python，传入 配置文件路径 和 临时文件路径
        python $pyScript $configPath $tempFile
        
        # 3. 读取临时文件中的路径
        $targetPath = Get-Content -Path $tempFile -Raw
        
        if (-not [string]::IsNullOrWhiteSpace($targetPath)) {
            $targetPath = $targetPath.Trim()
            
            # 4. 执行真正的 cd 切换操作
            if (Test-Path $targetPath) {
                Set-Location -Path $targetPath
                # Write-Host "👉 已跳转到: $targetPath" -ForegroundColor Cyan
            } else {
                Write-Host "❌ 目标路径不存在: $targetPath" -ForegroundColor Red
            }
        }
    } finally {
        # 5. 无论如何，最后清理临时文件
        if (Test-Path $tempFile) {
            Remove-Item -Path $tempFile -Force
        }
    }
}