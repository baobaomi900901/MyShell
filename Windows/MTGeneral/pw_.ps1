# Windows/MTGeneral/pw_.ps1

function pw_ {
    $myshell = $env:MYSHELL
    if (-not $myshell) {
        Write-Host "❌ 环境变量 MYSHELL 未设置" -ForegroundColor Red
        return
    }
    
    $pyScript = Join-Path $myshell "public\_script\pw.py"
    $configPath = Join-Path $myshell "config\private\password.json"

    if (-not (Test-Path $pyScript)) {
        Write-Host "❌ 找不到 Python 脚本: $pyScript" -ForegroundColor Red
        return
    }

    $tempFile = [System.IO.Path]::GetTempFileName()

    try {
        python $pyScript $configPath $tempFile
        
        $password = Get-Content -Path $tempFile -Raw
        
        if (-not [string]::IsNullOrWhiteSpace($password)) {
            $password = $password.Trim()
            Set-Clipboard -Value $password
            Write-Host "✅ 密码已复制到剪贴板" -ForegroundColor Green
        }
    } finally {
        if (Test-Path $tempFile) {
            Remove-Item -Path $tempFile -Force
        }
    }
}