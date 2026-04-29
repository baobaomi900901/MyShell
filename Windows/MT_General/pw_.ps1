# Windows/MTGeneral/_pw.ps1

function pw_ {
    param(
        [Parameter(Mandatory = $false, Position = 0)]
        [string]$Query
    )

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
        if ($Query) {
            python $pyScript $configPath $tempFile $Query
        } else {
            python $pyScript $configPath $tempFile
        }
        
        # 关键：非零退出码表示取消或错误，直接返回
        if ($LASTEXITCODE -ne 0) {
            return
        }
        
        $password = Get-Content -Path $tempFile -Raw -ErrorAction SilentlyContinue
        if (-not [string]::IsNullOrWhiteSpace($password)) {
            $password = $password.Trim()
            Set-Clipboard -Value $password
            Write-Host "✅ 密码已复制到剪贴板" -ForegroundColor Green
        } else {
            # 用户在交互菜单中取消时，Python 会正常退出但不会写入 tempFile；
            # 这里不再报错提示，保持安静返回。
            return
        }
    } finally {
        if (Test-Path $tempFile) {
            Remove-Item -Path $tempFile -Force
        }
    }
}

# Tab 补全（保持不变）
Register-ArgumentCompleter -CommandName pw_ -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $configFile = Join-Path $env:MYSHELL "config\private\password.json"
    
    if (-not (Test-Path $configFile)) {
        return
    }
    
    try {
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