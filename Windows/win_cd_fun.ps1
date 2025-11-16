# MyShell\Windows\win_cd_fun.ps1
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
    
    # 特殊处理许可证工具
    if ($internalAction -eq "liteLicense" -or $internalAction -eq "rpaLicense") {
        if (Test-Path $targetPath) {
            & $targetPath
            $password = if ($internalAction -eq "liteLicense") { "kingautomate" } else { "kingswarekcaom" }
            Set-Clipboard -Value $password
            Write-Host "已打开 $action, 密码: $password (已复制)" -ForegroundColor Green
        } else {
            Write-Host "错误: 文件不存在 - $targetPath" -ForegroundColor Red
        }
        return
    }
    
    # 普通目录切换
    if (Test-Path $targetPath) {
        Set-Location $targetPath
        Write-Host "已切换到 $action" -ForegroundColor Green
    } else {
        Write-Host "错误: 目录不存在 - $targetPath" -ForegroundColor Red
    }
}

# Tab 补全功能
Register-ArgumentCompleter -CommandName cd_ -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\path.json"
    
    if (-not (Test-Path $configFile)) {
        return
    }
    
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
        
        # 获取所有可用的 Windows 路径名称
        $completionItems = $config.PSObject.Properties | Where-Object {
            $_.Value.win -and $_.Value.win -ne $null
        } | ForEach-Object {
            # 将内部的下划线键名转换回用户友好的连字符格式
            $displayName = $_.Name -replace '_', '-'
            $description = $_.Value.description
            
            # 创建补全项
            [System.Management.Automation.CompletionResult]::new(
                $displayName,                    # 补全文本
                $displayName,                    # 列表文本
                'ParameterValue',                # 结果类型
                $description                     # 工具提示
            )
        }
        
        # 根据当前输入过滤补全项
        $completionItems | Where-Object {
            $_.CompletionText -like "$wordToComplete*"
        }
        
    } catch {
        # 如果解析失败，返回空结果
        return
    }
}

# 简单的编辑命令
function edit-cd-config {
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\path.json"
    code $configFile
}