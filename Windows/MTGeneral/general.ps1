# .\Windows\MTGeneral\index.ps1
function setsh {
  # 用途: 打开 vscode 并切换到 MyShell 配置文件目录
  $shellPath = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell"
  code $shellPath
  Write-Host "已打开 MyShell 配置文件, 请自行跳转到 \MyShell\Windows 文件夹下" -ForegroundColor Green
}

function type_ {
    # 用途: 查看方法是否存在, type_ {方法名}
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Name
    )

    if (Get-Command $Name -ErrorAction SilentlyContinue) {
        Get-Command $Name -ErrorAction SilentlyContinue
        Write-Host ""
        Write-Host "✅ cd_ 方法存在" -ForegroundColor Green
    } else {
        Write-Host "❌ cd_ 方法不存在" -ForegroundColor Red
    }
}

function op_ {
    # 用途: 执行 open .
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Paths
    )

    if ($Paths.Count -eq 0) {
        open .
        Write-Host "执行 open ."
    }
    else {
        open $Paths
        Write-Host "执行 open $Paths"
    }
}

function now_ {
    # 用途: 显示当前时间
    param(
        [string]$format = "default"
    )
    
    switch ($format) {
        "full" {
            $currentTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        "file" {
            $currentTime = Get-Date -Format "yyyyMMdd_HHmmss"
        }
        "time" {
            $currentTime = Get-Date -Format "HH:mm:ss"
        }
        default {
            $currentTime = Get-Date -Format "yyyyMMdd-HH:mm"
        }
    }
    
    Write-Host $currentTime -ForegroundColor Green
    $currentTime | Set-Clipboard
    Write-Host "✅ 时间已复制到剪贴板" -ForegroundColor Cyan
}

function new_ {
    # 用途: 新建文件夹或文件
    param(
        [Parameter(Mandatory=$true)]
        [string]$Name,
        [switch]$Force
    )
    
    # 检查路径是否已存在
    if (Test-Path $Name) {
        if ((Get-Item $Name) -is [System.IO.DirectoryInfo]) {
            if ($Force) {
                Write-Host "⚠️  文件夹已存在，跳过创建: $Name" -ForegroundColor Yellow
                return
            } else {
                Write-Host "📁 文件夹已存在: $Name" -ForegroundColor Red
                Write-Host "使用 'new -Force $Name' 可以强制创建" -ForegroundColor Yellow
                return
            }
        } elseif ((Get-Item $Name) -is [System.IO.FileInfo]) {
            if ($Force) {
                Remove-Item $Name -Force -ErrorAction SilentlyContinue
                Write-Host "⚠️  已删除并重新创建文件: $Name" -ForegroundColor Yellow
            } else {
                Write-Host "📄 文件已存在: $Name" -ForegroundColor Red
                Write-Host "使用 'new -Force $Name' 可以强制创建" -ForegroundColor Yellow
                return
            }
        } else {
            Write-Host "⚠️  路径已存在: $Name" -ForegroundColor Red
            return
        }
    }
    
    # 提取目录路径和基本名称
    $dir_path = Split-Path $Name -Parent
    $base_name = Split-Path $Name -Leaf
    
    # 创建必要的父目录
    if ($dir_path -and $dir_path -ne ".") {
        try {
            New-Item -Path $dir_path -ItemType Directory -Force -ErrorAction Stop | Out-Null
        } catch {
            Write-Host "❌ 无法创建目录: $dir_path" -ForegroundColor Red
            return
        }
    }
    
    # 检查名称是否包含扩展名（包含点且点不在开头）
    if ($base_name -match '^[^.]+[.].+$') {
        # 创建文件
        try {
            New-Item -Path $Name -ItemType File -ErrorAction Stop | Out-Null
            Write-Host "✅ 文件创建成功: $Name" -ForegroundColor Green
        } catch {
            Write-Host "❌ 无法创建文件: $Name" -ForegroundColor Red
        }
    } elseif ($base_name -match '\.') {
        # 处理特殊情况：以点开头的隐藏文件或文件夹
        if ($base_name -match '^\.') {
            # 创建文件
            try {
                New-Item -Path $Name -ItemType File -ErrorAction Stop | Out-Null
                Write-Host "✅ 文件创建成功: $Name" -ForegroundColor Green
            } catch {
                Write-Host "❌ 无法创建文件: $Name" -ForegroundColor Red
            }
        } else {
            # 包含点但不是有效文件格式，作为文件夹创建
            try {
                New-Item -Path $Name -ItemType Directory -ErrorAction Stop | Out-Null
                Write-Host "✅ 文件夹创建成功: $Name" -ForegroundColor Blue
            } catch {
                Write-Host "❌ 无法创建文件夹: $Name" -ForegroundColor Red
            }
        }
    } else {
        # 创建文件夹
        try {
            New-Item -Path $Name -ItemType Directory -ErrorAction Stop | Out-Null
            Write-Host "✅ 文件夹创建成功: $Name" -ForegroundColor Blue
        } catch {
            Write-Host "❌ 无法创建文件夹: $Name" -ForegroundColor Red
        }
    }
}
