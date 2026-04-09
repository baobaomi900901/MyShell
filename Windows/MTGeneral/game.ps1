# .\Windows\MTGame\index.ps1
# 游戏存档备份管理函数（支持 UTF-8 配置文件）

function game_ {
    # 用途: 游戏存档备份管理工具
    param (
        [Parameter(Position = 0)]
        [string]$action
    )

    # ---------- 编码设置：确保控制台能显示 UTF-8 中文 ----------
    try {
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        $null = & chcp 65001 2>$null
    } catch {
        # 静默处理，避免干扰
    }

    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\private\game.json"
    
    if (-not (Test-Path $configFile)) {
        Write-Host ""
        Write-Host "❌ 配置文件不存在" -ForegroundColor Red
        Write-Host "请手动创建: $configFile" -ForegroundColor Yellow
        Write-Host "示例模板:" -ForegroundColor Cyan
        Write-Host @'
{
  "ark_backup": {
    "win": "D:\\Steam\\steamapps\\common\\ARK\\ShooterGame\\Saved",
    "mac": null,
    "description": "ark single player save"
  }
}
'@ -ForegroundColor DarkGray
        Write-Host ""
        return
    }
    
    # 读取配置（指定 UTF-8 编码）
    try {
        $raw = Get-Content -Path $configFile -Raw -Encoding UTF8
        $config = $raw | ConvertFrom-Json
    } catch {
        Write-Host "错误: 配置文件格式错误，请确保文件为 UTF-8 无 BOM 格式" -ForegroundColor Red
        return
    }
    
    # 显示帮助
    if (-not $action) {
        Write-Host "游戏存档备份工具" -ForegroundColor Cyan
        Write-Host "用法: game_ <游戏名称>" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "可用游戏:" -ForegroundColor Green
        
        $config.PSObject.Properties | ForEach-Object {
            $key = $_.Name
            $item = $_.Value
            if ($item.win -and $null -ne $item.win) {
                Write-Host "  $key" -ForegroundColor Yellow -NoNewline
                Write-Host " - $($item.description)"
            }
        }
        Write-Host ""
        Write-Host "示例:" -ForegroundColor Cyan
        Write-Host "  game_ ark_backup      # 备份 ARK 游戏存档" -ForegroundColor Yellow
        return
    }
    
    # 处理用户输入
    $internalAction = $action
    
    if (-not $config.$internalAction) {
        Write-Host "错误: 游戏 '$action' 未配置" -ForegroundColor Red
        return
    }
    
    $item = $config.$internalAction
    $sourcePath = $item.win
    
    if (-not $sourcePath -or $null -eq $sourcePath) {
        Write-Host "错误: 游戏 '$action' 在 Windows 上未配置路径" -ForegroundColor Red
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
        
        Write-Host "正在备份 $($item.description) ..." -ForegroundColor Green
        Write-Host "源目录: $sourcePath" -ForegroundColor Cyan
        Write-Host "备份到: $backupPath" -ForegroundColor Cyan
        
        try {
            # 复制整个目录
            Copy-Item -Path $sourcePath -Destination $backupPath -Recurse -Force
            
            # 计算备份大小
            $size = (Get-ChildItem -Path $backupPath -Recurse | Measure-Object -Property Length -Sum).Sum
            $sizeMB = [math]::Round($size / 1MB, 2)
            
            Write-Host "✓ 备份完成！" -ForegroundColor Green
            Write-Host "备份名称: $backupName" -ForegroundColor Yellow
            Write-Host "备份大小: $sizeMB MB" -ForegroundColor Yellow
            Write-Host "备份时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
            
            # 显示最近的备份列表
            Write-Host "`n最近的备份:" -ForegroundColor Cyan
            $backups = Get-ChildItem -Path $parentDir -Directory | Where-Object { 
                $_.Name -like "${folderName}_*" 
            } | Sort-Object CreationTime -Descending | Select-Object -First 5
            
            if ($backups.Count -eq 0) {
                Write-Host "  (无备份)" -ForegroundColor Gray
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
            Write-Host "备份失败: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "错误: 目录不存在 - $sourcePath" -ForegroundColor Red
    }
}

# Tab 补全功能（同样使用 UTF-8 读取配置）
Register-ArgumentCompleter -CommandName game_ -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\private\game.json"
    
    if (-not (Test-Path $configFile)) {
        return
    }
    
    try {
        $raw = Get-Content -Path $configFile -Raw -Encoding UTF8
        $config = $raw | ConvertFrom-Json
        
        $completionItems = $config.PSObject.Properties | Where-Object {
            $_.Value.win -and $_.Value.win -ne $null
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

# 简单的编辑命令（用 VS Code 打开配置文件）
function edit-game-config {
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\private\game.json"
    if (Get-Command code -ErrorAction SilentlyContinue) {
        code $configFile
    } else {
        notepad $configFile
    }
}

# 查看游戏备份列表
function game_list_backups {
    param(
        [string]$game = "ark_backup"
    )
    
    # 编码设置
    try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $null = & chcp 65001 2>$null } catch {}
    
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\private\game.json"
    
    if (-not (Test-Path $configFile)) {
        Write-Host "配置文件不存在" -ForegroundColor Red
        return
    }
    
    try {
        $raw = Get-Content -Path $configFile -Raw -Encoding UTF8
        $config = $raw | ConvertFrom-Json
        
        if (-not $config.$game) {
            Write-Host "游戏 '$game' 未配置" -ForegroundColor Red
            return
        }
        
        $item = $config.$game
        $sourcePath = $item.win
        
        if (-not $sourcePath) {
            Write-Host "游戏 '$game' 在 Windows 上未配置路径" -ForegroundColor Red
            return
        }
        
        $parentDir = Split-Path $sourcePath -Parent
        $folderName = Split-Path $sourcePath -Leaf
        
        Write-Host "$($item.description) 备份列表:" -ForegroundColor Cyan
        Write-Host ("=" * 50)
        
        $backups = Get-ChildItem -Path $parentDir -Directory | Where-Object { 
            $_.Name -like "${folderName}_*" 
        } | Sort-Object CreationTime -Descending
        
        if ($backups.Count -eq 0) {
            Write-Host "未找到任何备份" -ForegroundColor Gray
            return
        }
        
        $backups | ForEach-Object {
            $size = (Get-ChildItem $_.FullName -Recurse | Measure-Object Length -Sum).Sum
            $sizeMB = [math]::Round($size / 1MB, 2)
            $time = $_.CreationTime.ToString("yyyy-MM-dd HH:mm")
            
            Write-Host "  $($_.Name)" -ForegroundColor Yellow
            Write-Host "    大小: $sizeMB MB" -ForegroundColor Gray
            Write-Host "    时间: $time" -ForegroundColor Gray
            Write-Host "    路径: $($_.FullName)" -ForegroundColor DarkGray
            Write-Host ""
        }
        
    } catch {
        Write-Host "读取配置失败: $_" -ForegroundColor Red
    }
}

# 还原游戏备份
function game_restore {
    param(
        [string]$game = "ark_backup",
        [string]$backupName
    )
    
    # 编码设置
    try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $null = & chcp 65001 2>$null } catch {}
    
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\private\game.json"
    
    if (-not (Test-Path $configFile)) {
        Write-Host "配置文件不存在" -ForegroundColor Red
        return
    }
    
    try {
        $raw = Get-Content -Path $configFile -Raw -Encoding UTF8
        $config = $raw | ConvertFrom-Json
        
        if (-not $config.$game) {
            Write-Host "游戏 '$game' 未配置" -ForegroundColor Red
            return
        }
        
        $item = $config.$game
        $sourcePath = $item.win
        
        if (-not $sourcePath) {
            Write-Host "游戏 '$game' 在 Windows 上未配置路径" -ForegroundColor Red
            return
        }
        
        $parentDir = Split-Path $sourcePath -Parent
        $folderName = Split-Path $sourcePath -Leaf
        
        # 如果没有指定备份名称，显示列表让用户选择
        if (-not $backupName) {
            Write-Host "请选择要还原的备份:" -ForegroundColor Green
            
            $backups = Get-ChildItem -Path $parentDir -Directory | Where-Object { 
                $_.Name -like "${folderName}_*" 
            } | Sort-Object CreationTime -Descending
            
            if ($backups.Count -eq 0) {
                Write-Host "错误: 未找到任何备份" -ForegroundColor Red
                return
            }
            
            # 显示备份列表
            for ($i = 0; $i -lt $backups.Count; $i++) {
                $time = $backups[$i].CreationTime.ToString("MM-dd HH:mm")
                Write-Host "  [$i] $($backups[$i].Name) ($time)" -ForegroundColor Yellow
            }
            
            # 用户选择
            $choice = Read-Host "`n输入备份编号 (0-$($backups.Count-1))"
            
            if ($choice -match "^\d+$" -and [int]$choice -lt $backups.Count) {
                $backupName = $backups[[int]$choice].Name
            } else {
                Write-Host "输入无效，还原已取消" -ForegroundColor Red
                return
            }
        }
        
        $backupPath = Join-Path $parentDir $backupName
        
        if (-not (Test-Path $backupPath)) {
            Write-Host "错误: 备份不存在 - $backupPath" -ForegroundColor Red
            return
        }
        
        # 确认操作
        $confirm = Read-Host "确认还原到 $backupName ？这将覆盖当前存档。 (输入 y 确认)"
        
        if ($confirm -ne "y") {
            Write-Host "还原已取消" -ForegroundColor Yellow
            return
        }
        
        # 备份当前存档
        $timestamp = Get-Date -Format "yyyy_MM_dd_HH_mm"
        $currentBackup = Join-Path $parentDir "${folderName}_before_restore_$timestamp"
        
        if (Test-Path $sourcePath) {
            Copy-Item -Path $sourcePath -Destination $currentBackup -Recurse -Force
            Write-Host "当前存档已备份到: $currentBackup" -ForegroundColor Cyan
        }
        
        # 删除原存档
        Remove-Item -Path $sourcePath -Recurse -Force -ErrorAction SilentlyContinue
        
        # 还原备份
        Copy-Item -Path $backupPath -Destination $sourcePath -Recurse -Force
        
        Write-Host "✓ 还原完成！" -ForegroundColor Green
        
    } catch {
        Write-Host "还原失败: $_" -ForegroundColor Red
    }
}