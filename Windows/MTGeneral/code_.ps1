# Windows/MTGeneral/code_.ps1

function code_ {
    $myshell = $env:MYSHELL
    if (-not $myshell) {
        Write-Host "❌ 环境变量 MYSHELL 未设置" -ForegroundColor Red
        return
    }
    
    $pyScript = Join-Path $myshell "public\_script\vscode.py"
    $configPath = Join-Path $myshell "config\private\path_code.json"

    if (-not (Test-Path $pyScript)) {
        Write-Host "❌ 找不到 Python 脚本: $pyScript" -ForegroundColor Red
        return
    }

    $tempFile = [System.IO.Path]::GetTempFileName()

    try {
        python $pyScript $configPath $tempFile
        
        $targetPath = Get-Content -Path $tempFile -Raw
        
        if (-not [string]::IsNullOrWhiteSpace($targetPath)) {
            $targetPath = $targetPath.Trim()
            
            if (Test-Path $targetPath) {
                code $targetPath
                Write-Host "👉 已在 VS Code 中打开: $targetPath" -ForegroundColor Cyan
            } else {
                Write-Host "❌ 目标路径不存在: $targetPath" -ForegroundColor Red
            }
        }
    } finally {
        if (Test-Path $tempFile) {
            Remove-Item -Path $tempFile -Force
        }
    }
}