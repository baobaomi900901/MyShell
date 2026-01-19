# MyShell\Windows\win_password_fun.ps1

function pw_ {
    param (
        [Parameter(Position = 0)]
        [string]$action
    )

    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\password.json"
    
    if (-not (Test-Path $configFile)) {
        Write-Host "错误: 密码配置文件不存在" -ForegroundColor Red
        Write-Host "请手动创建: $configFile" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "示例配置文件内容:" -ForegroundColor Cyan
        Write-Host '{
  "lite-root": {
    "password": "Kingsware#%0417",
    "description": "lite 服务器 root 密码"
  }
}' -ForegroundColor Gray
        return
    }
    
    # 读取配置
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
    } catch {
        Write-Host "错误: 配置文件格式错误" -ForegroundColor Red
        return
    }
    
    # 检查是否安装了 Set-Clipboard（Windows PowerShell 5.1+ 自带）
    if (-not (Get-Command Set-Clipboard -ErrorAction SilentlyContinue)) {
        Write-Host "警告: Set-Clipboard 命令不可用，将使用备用方法" -ForegroundColor Yellow
    }
    
    # 显示帮助
    if (-not $action) {
        Write-Host "密码管理工具" -ForegroundColor Cyan
        Write-Host "用法: pw_ <密码项名称>" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "可用密码项:" -ForegroundColor Green
        
        $hasItems = $false
        $config.PSObject.Properties | ForEach-Object {
            $key = $_.Name
            $item = $_.Value
            if ($item.password -and $item.password -ne $null) {
                $hasItems = $true
                Write-Host "  $key" -ForegroundColor Yellow -NoNewline
                Write-Host " - $($item.description)"
            }
        }
        
        if (-not $hasItems) {
            Write-Host "  (没有配置任何密码项)" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "示例:" -ForegroundColor Cyan
        Write-Host "  pw_ lite-root     # 复制 lite-root 密码到剪贴板" -ForegroundColor White
        
        return
    }
    
    # 获取密码项
    if (-not $config.$action) {
        Write-Host "错误: 密码项 '$action' 不存在" -ForegroundColor Red
        Write-Host "使用 'pw_' 查看所有可用密码项" -ForegroundColor Yellow
        return
    }
    
    $item = $config.$action
    $password = $item.password
    $description = $item.description
    
    if (-not $password -or $password -eq $null) {
        Write-Host "错误: 密码项 '$action' 未配置密码" -ForegroundColor Red
        return
    }
    
    # 复制密码到剪贴板
    try {
        Set-Clipboard -Value $password -ErrorAction Stop
        Write-Host "✓ 已复制 '$action' 的密码到剪贴板" -ForegroundColor Green
        Write-Host "描述: $description" -ForegroundColor Cyan
        Write-Host "提示: 使用 Ctrl+V 粘贴密码" -ForegroundColor Yellow
        
        # 安全提示
        Write-Host ""
        Write-Host "⚠️  安全提示:" -ForegroundColor Red
        Write-Host "  • 使用后请及时清除剪贴板 (Win+V 打开剪贴板历史)" -ForegroundColor DarkYellow
        Write-Host "  • 不要在公共场合粘贴敏感密码" -ForegroundColor DarkYellow
        Write-Host "  • 定期更换重要密码" -ForegroundColor DarkYellow
        
    } catch {
        # 如果 Set-Clipboard 失败，尝试其他方法
        try {
            # 使用 .NET 方法
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.Clipboard]::SetText($password)
            Write-Host "✓ 已复制 '$action' 的密码到剪贴板" -ForegroundColor Green
            Write-Host "描述: $description" -ForegroundColor Cyan
        } catch {
            Write-Host "错误: 无法复制到剪贴板" -ForegroundColor Red
            Write-Host "描述: $description" -ForegroundColor Cyan
            Write-Host "密码: $password" -ForegroundColor Gray
            Write-Host "警告: 密码已显示在屏幕上，请确保周围无人窥视" -ForegroundColor Red
        }
    }
}

# Tab 补全功能
Register-ArgumentCompleter -CommandName pw_ -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\password.json"
    
    if (-not (Test-Path $configFile)) {
        return
    }
    
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
        
        # 获取所有可用的密码项
        $completionItems = $config.PSObject.Properties | Where-Object {
            $_.Value.password -and $_.Value.password -ne $null
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

# 辅助函数：编辑密码配置文件
function edit-pw-config {
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\password.json"
    
    # 确保目录存在
    $configDir = Split-Path $configFile -Parent
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    
    # 如果文件不存在，创建示例配置
    if (-not (Test-Path $configFile)) {
        @'
{
  "lite-root": {
    "password": "Kingsware#%0417",
    "description": "lite 服务器 root 密码"
  },
  "mysql-root": {
    "password": "root123456",
    "description": "MySQL root 密码"
  },
  "vpn-password": {
    "password": "vpn@2023",
    "description": "公司 VPN 密码"
  }
}
'@ | Set-Content $configFile -Encoding UTF8
        
        Write-Host "✓ 已创建示例配置文件" -ForegroundColor Green
    }
    
    # 使用 VSCode 打开，如果没有则使用记事本
    if (Get-Command code -ErrorAction SilentlyContinue) {
        code $configFile
    } elseif (Get-Command notepad++ -ErrorAction SilentlyContinue) {
        notepad++ $configFile
    } else {
        notepad $configFile
    }
    
    Write-Host "已打开密码配置文件" -ForegroundColor Cyan
}

# 辅助函数：显示所有密码项（不显示密码）
function show-pw-items {
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\password.json"
    
    if (-not (Test-Path $configFile)) {
        Write-Host "配置文件不存在" -ForegroundColor Red
        Write-Host "使用 'edit-pw-config' 创建配置文件" -ForegroundColor Yellow
        return
    }
    
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
    } catch {
        Write-Host "错误: 配置文件格式错误" -ForegroundColor Red
        return
    }
    
    Write-Host "所有密码项:" -ForegroundColor Cyan
    Write-Host "==========" -ForegroundColor DarkGray
    
    $count = 0
    $config.PSObject.Properties | ForEach-Object {
        $key = $_.Name
        $item = $_.Value
        
        Write-Host "$key" -ForegroundColor Yellow
        Write-Host "  描述: $($item.description)" -ForegroundColor White
        Write-Host "  密码: [已隐藏]" -ForegroundColor DarkGray
        
        $count++
    }
    
    Write-Host "==========" -ForegroundColor DarkGray
    Write-Host "总计: $count 个密码项" -ForegroundColor Green
    Write-Host ""
    Write-Host "使用 'pw_ <项名>' 复制密码到剪贴板" -ForegroundColor Cyan
}

# 辅助函数：清除剪贴板
function clear-clipboard {
    Write-Host "正在清除剪贴板..." -ForegroundColor Yellow
    
    try {
        Set-Clipboard -Value "" -ErrorAction Stop
        Write-Host "✓ 剪贴板已清除" -ForegroundColor Green
        Write-Host "提示: 按 Win+V 可以查看和清除剪贴板历史" -ForegroundColor Cyan
    } catch {
        try {
            # 使用 .NET 方法
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.Clipboard]::Clear()
            Write-Host "✓ 剪贴板已清除" -ForegroundColor Green
        } catch {
            Write-Host "错误: 无法清除剪贴板" -ForegroundColor Red
            Write-Host "请手动清除剪贴板历史 (Win+V)" -ForegroundColor Yellow
        }
    }
}

# 辅助函数：检查依赖
function check-pw-deps {
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\password.json"
    
    Write-Host "检查密码管理工具依赖..." -ForegroundColor Cyan
    
    # 检查配置文件
    if (Test-Path $configFile) {
        Write-Host "✓ 配置文件存在: $configFile" -ForegroundColor Green
        
        # 检查配置文件格式
        try {
            $config = Get-Content $configFile -Raw | ConvertFrom-Json
            $count = ($config.PSObject.Properties | Measure-Object).Count
            Write-Host "✓ JSON 格式正确 ($count 个密码项)" -ForegroundColor Green
        } catch {
            Write-Host "✗ JSON 格式错误" -ForegroundColor Red
        }
    } else {
        Write-Host "✗ 配置文件不存在" -ForegroundColor Red
        Write-Host "  使用 'edit-pw-config' 创建配置文件" -ForegroundColor Yellow
    }
    
    # 检查剪贴板功能
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
        Write-Host "✓ Set-Clipboard 命令可用" -ForegroundColor Green
    } else {
        Write-Host "⚠ Set-Clipboard 命令不可用，将使用备用方法" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "检查完成" -ForegroundColor Cyan
}

# 辅助函数：初始化密码配置
function init-pw-config {
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\password.json"
    $configDir = Split-Path $configFile -Parent
    
    Write-Host "初始化密码配置文件..." -ForegroundColor Cyan
    
    # 创建目录
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
        Write-Host "✓ 创建目录: $configDir" -ForegroundColor Green
    }
    
    # 如果文件不存在，创建示例配置
    if (-not (Test-Path $configFile)) {
        @'
{
  "lite-root": {
    "password": "Kingsware#%0417",
    "description": "lite 服务器 root 密码"
  },
  "mysql-root": {
    "password": "root123456",
    "description": "MySQL root 密码"
  },
  "vpn-password": {
    "password": "vpn@2023",
    "description": "公司 VPN 密码"
  }
}
'@ | Set-Content $configFile -Encoding UTF8
        
        Write-Host "✓ 已创建密码配置文件" -ForegroundColor Green
        Write-Host "位置: $configFile" -ForegroundColor White
        
        Write-Host ""
        Write-Host "现在可以编辑配置文件:" -ForegroundColor Cyan
        Write-Host "  edit-pw-config    # 编辑配置文件" -ForegroundColor Yellow
        Write-Host "  pw_               # 查看所有密码项" -ForegroundColor Yellow
    } else {
        Write-Host "配置文件已存在: $configFile" -ForegroundColor Yellow
    }
}

# 辅助函数：添加到帮助系统
function hsh {
    Write-Host "密码管理相关命令:" -ForegroundColor Cyan
    Write-Host "  pw_              # 密码管理工具" -ForegroundColor Yellow
    Write-Host "  edit-pw-config   # 编辑密码配置文件" -ForegroundColor Yellow
    Write-Host "  show-pw-items    # 显示所有密码项" -ForegroundColor Yellow
    Write-Host "  clear-clipboard  # 清除剪贴板" -ForegroundColor Yellow
    Write-Host "  check-pw-deps    # 检查依赖" -ForegroundColor Yellow
    Write-Host "  init-pw-config   # 初始化密码配置" -ForegroundColor Yellow
}