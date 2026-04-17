# Windows/MTGeneral/pw_.ps1

function _pw {
    # 用途: 将选择的密码复制到剪切板
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
        python $pyScript $configPath $tempFile $Query
        
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

# Tab 补全（保持原有逻辑，但确保配置文件读取编码正确）
Register-ArgumentCompleter -CommandName pw_ -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $configFile = Join-Path $env:MYSHELL "config\private\password.json"
    
    if (-not (Test-Path $configFile)) {
        return
    }
    
    try {
        # 指定 UTF8 编码读取
        $raw = Get-Content -Path $configFile -Raw -Encoding UTF8
        $config = $raw | ConvertFrom-Json
        
        $completionItems = $config.PSObject.Properties | Where-Object {
            $_.Value.password -and $_.Value.password -ne $null
        } | ForEach-Object {
            $key = $_.Name
            $description = $_.Value.description
            
            [System.Management.Automation.CompletionResult]::new(
                $key,
                $key,
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