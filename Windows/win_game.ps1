# .\Windows\win_game.ps1
# 游戏存档备份管理函数

function game_ {
    param (
        [Parameter(Position = 0)]
        [string]$action
    )

    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\game.json"
    
    if (-not (Test-Path $configFile)) {
        Write-Host "Error: Config file not found" -ForegroundColor Red
        Write-Host "Please create: $configFile" -ForegroundColor Yellow
        Write-Host "Example content:" -ForegroundColor Cyan
        Write-Host @'
{
  "ark_backup": {
    "win": "D:\\Steam\\steamapps\\common\\ARK\\ShooterGame\\Saved",
    "mac": null,
    "description": "ark single player save"
  }
}
'@
        return
    }
    
    # 读取配置
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
    } catch {
        Write-Host "Error: Config file format error" -ForegroundColor Red
        return
    }
    
    # 显示帮助
    if (-not $action) {
        Write-Host "Game Save Backup Tool" -ForegroundColor Cyan
        Write-Host "Usage: game_ <game_name>" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Available games:" -ForegroundColor Green
        
        $config.PSObject.Properties | ForEach-Object {
            $key = $_.Name
            $item = $_.Value
            if ($item.win -and $item.win -ne $null) {
                Write-Host "  $key" -ForegroundColor Yellow -NoNewline
                Write-Host " - $($item.description)"
            }
        }
        Write-Host ""
        Write-Host "Example:" -ForegroundColor Cyan
        Write-Host "  game_ ark_backup      # Backup ARK game save" -ForegroundColor Yellow
        return
    }
    
    # 处理用户输入
    $internalAction = $action
    
    if (-not $config.$internalAction) {
        Write-Host "Error: Game '$action' not configured" -ForegroundColor Red
        return
    }
    
    $item = $config.$internalAction
    $sourcePath = $item.win
    
    if (-not $sourcePath -or $sourcePath -eq $null) {
        Write-Host "Error: Game '$action' not configured for Windows" -ForegroundColor Red
        return
    }
    
    # 执行备份操作
    if (Test-Path $sourcePath) {
        # 获取当前时间戳
        $timestamp = Get-Date -Format "yyyy_MM_dd_HH_mm"
        
        # 确定备份路径
        $parentDir = Split-Path $sourcePath -Parent
        $folderName = Split-Path $sourcePath -Leaf
        $backupName = "${folderName}_$timestamp"
        $backupPath = Join-Path $parentDir $backupName
        
        Write-Host "Backing up $($item.description)..." -ForegroundColor Green
        Write-Host "Source: $sourcePath" -ForegroundColor Cyan
        Write-Host "Backup to: $backupPath" -ForegroundColor Cyan
        
        try {
            # 复制整个目录
            Copy-Item -Path $sourcePath -Destination $backupPath -Recurse -Force
            
            # 计算备份大小
            $size = (Get-ChildItem -Path $backupPath -Recurse | Measure-Object -Property Length -Sum).Sum
            $sizeMB = [math]::Round($size / 1MB, 2)
            
            Write-Host "✓ Backup completed!" -ForegroundColor Green
            Write-Host "Backup name: $backupName" -ForegroundColor Yellow
            Write-Host "Backup size: $sizeMB MB" -ForegroundColor Yellow
            Write-Host "Backup time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
            
            # 显示备份列表
            Write-Host "`nRecent backups:" -ForegroundColor Cyan
            $backups = Get-ChildItem -Path $parentDir -Directory | Where-Object { 
                $_.Name -like "${folderName}_*" 
            } | Sort-Object CreationTime -Descending | Select-Object -First 5
            
            if ($backups.Count -eq 0) {
                Write-Host "  No backups" -ForegroundColor Gray
            } else {
                $backups | ForEach-Object {
                    $size = (Get-ChildItem $_.FullName -Recurse | Measure-Object Length -Sum).Sum
                    $sizeMB = [math]::Round($size / 1MB, 2)
                    $time = $_.CreationTime.ToString("MM-dd HH:mm")
                    
                    Write-Host "  $($_.Name)" -ForegroundColor Yellow -NoNewline
                    Write-Host " ($sizeMB MB, $time)"
                }
            }
            
        } catch {
            Write-Host "Backup failed: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "Error: Directory not found - $sourcePath" -ForegroundColor Red
    }
}

# Tab 补全功能
Register-ArgumentCompleter -CommandName game_ -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\game.json"
    
    if (-not (Test-Path $configFile)) {
        return
    }
    
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
        
        # 获取所有可用的游戏配置
        $completionItems = $config.PSObject.Properties | Where-Object {
            $_.Value.win -and $_.Value.win -ne $null
        } | ForEach-Object {
            $key = $_.Name
            $description = $_.Value.description
            
            # 创建补全项
            [System.Management.Automation.CompletionResult]::new(
                $key,                    # 补全文本
                $key,                    # 列表文本
                'ParameterValue',        # 结果类型
                $description             # 工具提示
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
function edit-game-config {
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\game.json"
    code $configFile
}

# 查看游戏备份列表
function game_list_backups {
    param(
        [string]$game = "ark_backup"
    )
    
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\game.json"
    
    if (-not (Test-Path $configFile)) {
        Write-Host "Config file not found" -ForegroundColor Red
        return
    }
    
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
        
        if (-not $config.$game) {
            Write-Host "Game '$game' not configured" -ForegroundColor Red
            return
        }
        
        $item = $config.$game
        $sourcePath = $item.win
        
        if (-not $sourcePath) {
            Write-Host "Game '$game' not configured for Windows" -ForegroundColor Red
            return
        }
        
        $parentDir = Split-Path $sourcePath -Parent
        $folderName = Split-Path $sourcePath -Leaf
        
        Write-Host "$($item.description) backup list:" -ForegroundColor Cyan
        Write-Host "=" * 50
        
        $backups = Get-ChildItem -Path $parentDir -Directory | Where-Object { 
            $_.Name -like "${folderName}_*" 
        } | Sort-Object CreationTime -Descending
        
        if ($backups.Count -eq 0) {
            Write-Host "No backups found" -ForegroundColor Gray
            return
        }
        
        $backups | ForEach-Object {
            $size = (Get-ChildItem $_.FullName -Recurse | Measure-Object Length -Sum).Sum
            $sizeMB = [math]::Round($size / 1MB, 2)
            $time = $_.CreationTime.ToString("yyyy-MM-dd HH:mm")
            
            Write-Host "  $($_.Name)" -ForegroundColor Yellow
            Write-Host "    Size: $sizeMB MB" -ForegroundColor Gray
            Write-Host "    Time: $time" -ForegroundColor Gray
            Write-Host "    Path: $($_.FullName)" -ForegroundColor DarkGray
            Write-Host ""
        }
        
    } catch {
        Write-Host "Error reading config: $_" -ForegroundColor Red
    }
}

# 还原游戏备份
function game_restore {
    param(
        [string]$game = "ark_backup",
        [string]$backupName
    )
    
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\game.json"
    
    if (-not (Test-Path $configFile)) {
        Write-Host "Config file not found" -ForegroundColor Red
        return
    }
    
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
        
        if (-not $config.$game) {
            Write-Host "Game '$game' not configured" -ForegroundColor Red
            return
        }
        
        $item = $config.$game
        $sourcePath = $item.win
        
        if (-not $sourcePath) {
            Write-Host "Game '$game' not configured for Windows" -ForegroundColor Red
            return
        }
        
        $parentDir = Split-Path $sourcePath -Parent
        $folderName = Split-Path $sourcePath -Leaf
        
        # 如果没有指定备份名称，显示列表让用户选择
        if (-not $backupName) {
            Write-Host "Select a backup to restore:" -ForegroundColor Green
            
            $backups = Get-ChildItem -Path $parentDir -Directory | Where-Object { 
                $_.Name -like "${folderName}_*" 
            } | Sort-Object CreationTime -Descending
            
            if ($backups.Count -eq 0) {
                Write-Host "Error: No backups found" -ForegroundColor Red
                return
            }
            
            # 显示备份列表
            for ($i = 0; $i -lt $backups.Count; $i++) {
                $time = $backups[$i].CreationTime.ToString("MM-dd HH:mm")
                Write-Host "  [$i] $($backups[$i].Name) ($time)" -ForegroundColor Yellow
            }
            
            # 用户选择
            $choice = Read-Host "`nEnter backup number (0-$($backups.Count-1))"
            
            if ($choice -match "^\d+$" -and [int]$choice -lt $backups.Count) {
                $backupName = $backups[[int]$choice].Name
            } else {
                Write-Host "Invalid input, restore cancelled" -ForegroundColor Red
                return
            }
        }
        
        $backupPath = Join-Path $parentDir $backupName
        
        if (-not (Test-Path $backupPath)) {
            Write-Host "Error: Backup not found - $backupPath" -ForegroundColor Red
            return
        }
        
        # 确认操作
        $confirm = Read-Host "Confirm restore to $backupName? This will overwrite current save. (Enter y to confirm)"
        
        if ($confirm -ne "y") {
            Write-Host "Restore cancelled" -ForegroundColor Yellow
            return
        }
        
        # 备份当前存档
        $timestamp = Get-Date -Format "yyyy_MM_dd_HH_mm"
        $currentBackup = Join-Path $parentDir "${folderName}_before_restore_$timestamp"
        
        if (Test-Path $sourcePath) {
            Copy-Item -Path $sourcePath -Destination $currentBackup -Recurse -Force
            Write-Host "Current save backed up to: $currentBackup" -ForegroundColor Cyan
        }
        
        # 删除原存档
        Remove-Item -Path $sourcePath -Recurse -Force -ErrorAction SilentlyContinue
        
        # 还原备份
        Copy-Item -Path $backupPath -Destination $sourcePath -Recurse -Force
        
        Write-Host "✓ Restore completed!" -ForegroundColor Green
        
    } catch {
        Write-Host "Restore failed: $_" -ForegroundColor Red
    }
}