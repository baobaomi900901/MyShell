# MyShell\Windows\win_cd.ps1
function cd_ {
    param (
        [Parameter(Position = 0)]
        [string]$action
    )

    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\path.json"
    
    if (-not (Test-Path $configFile)) {
        Write-Host "错误: 配置文件不存在" -ForegroundColor Red
        Write-Host "请手动创建: $configFile" -ForegroundColor Yellow
        return
    }
    
    # 读取配置
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
    } catch {
        Write-Host "错误: 配置文件格式错误" -ForegroundColor Red
        return
    }
    
    # 显示帮助
    if (-not $action) {
        Write-Host "快速目录跳转" -ForegroundColor Cyan
        Write-Host "用法: cd_ <名称>" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "可用目录:" -ForegroundColor Green
        
        $config.PSObject.Properties | ForEach-Object {
            $key = $_.Name
            $item = $_.Value
            if ($item.win -and $item.win -ne $null) {
                $displayName = $key -replace '_', '-'
                Write-Host "  $displayName" -ForegroundColor Yellow -NoNewline
                Write-Host " - $($item.description)"
            }
        }
        return
    }
    
    # 处理用户输入
    $internalAction = $action -replace '-', '_'
    
    if (-not $config.$internalAction) {
        Write-Host "错误: 目录 '$action' 不存在" -ForegroundColor Red
        return
    }
    
    $item = $config.$internalAction
    $targetPath = $item.win
    
    if (-not $targetPath -or $targetPath -eq $null) {
        Write-Host "错误: 目录 '$action' 在 Windows 上未配置" -ForegroundColor Red
        return
    }
    
    # 检查路径是否为目录
    if (Test-Path $targetPath -PathType Container) {
        Set-Location $targetPath
        Write-Host "已切换到 $action" -ForegroundColor Green
    } else {
        Write-Host "错误: 路径不是目录 - $targetPath" -ForegroundColor Red
        if (Test-Path $targetPath) {
            Write-Host "提示: 该路径是一个文件，若要运行工具请使用 'tool_ license-lite' 或 'tool_ license-rpa'" -ForegroundColor Yellow
        } else {
            Write-Host "错误: 目录不存在 - $targetPath" -ForegroundColor Red
        }
    }
}

# Tab 补全功能（不变）
Register-ArgumentCompleter -CommandName cd_ -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\path.json"
    
    if (-not (Test-Path $configFile)) {
        return
    }
    
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
        
        $completionItems = $config.PSObject.Properties | Where-Object {
            $_.Value.win -and $_.Value.win -ne $null
        } | ForEach-Object {
            $displayName = $_.Name -replace '_', '-'
            $description = $_.Value.description
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

# 简单的编辑命令
function edit-cd-config {
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\path.json"
    code $configFile
}