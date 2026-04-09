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
    # 用途: 文件夹中打开当前路径
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Paths
    )

    # 如果没有传入参数，默认打开当前目录
    if ($Paths.Count -eq 0) {
        $Paths = @('.')
    }

    # 兼容判断操作系统
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        # PowerShell Core 6+ 可直接使用自动变量
        $isWindows = $IsWindows
        $isMacOS = $IsMacOS
        $isLinux = $IsLinux
    } else {
        # Windows PowerShell 5.1 只能通过环境变量或 OS 平台判断
        $isWindows = $env:OS -eq 'Windows_NT'
        $isMacOS = $false  # 默认不认为在 macOS 上运行 Windows PowerShell
        $isLinux = $false
    }

    # 根据操作系统选择打开命令
    if ($isWindows) {
        foreach ($path in $Paths) {
            # 用 Invoke-Item 打开文件或文件夹
            Invoke-Item $path
            Write-Host "已打开: $path"
        }
    } elseif ($isMacOS) {
        # macOS 使用 open 命令
        open $Paths
        Write-Host "执行 open $Paths"
    } elseif ($isLinux) {
        # Linux 使用 xdg-open
        foreach ($path in $Paths) {
            xdg-open $path
            Write-Host "已打开: $path"
        }
    } else {
        Write-Error "无法识别的操作系统"
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

function cl {
    # 用途: 清空终端信息
    Clear
}




# 公共方法区域

# 辅助函数：读取并解析 config.json（支持以 # 开头的注释）
function Get-CustomConfig {
    param(
        [Parameter(Mandatory = $true)]
        [string]$JsonPath
    )

    if (-not (Test-Path $JsonPath)) {
        Write-Error "找不到配置文件: $JsonPath"
        return $null
    }

    try {
        $rawLines = Get-Content $JsonPath -Raw -Encoding UTF8 -ErrorAction Stop
        # 移除以 # 开头的注释行（允许行前有空格）
        $cleanJson = ($rawLines -split "`r`n|`n" | Where-Object { $_ -notmatch '^\s*#' }) -join "`n"
        $config = $cleanJson | ConvertFrom-Json
        return $config
    }
    catch {
        Write-Error "解析 config.json 失败: $_"
        return $null
    }
}

# 内部函数：解析脚本路径，支持默认约定和 @MYSHELL 占位符
function Resolve-ScriptPath {
    param(
        [string]$Command,
        [string]$ConfiguredPath,          # 可能为 $null 或空
        [string]$ScriptDir,
        [string]$Extension                 # 如 '.ps1'
    )

    # 若未配置路径，则使用默认路径: .\src\<Command><Extension>
    if ([string]::IsNullOrEmpty($ConfiguredPath)) {
        $resolved = Join-Path $ScriptDir "src" "$Command$Extension"
        Write-Verbose "未配置 script_path，使用默认路径: $resolved"
        return $resolved
    }

    $path = $ConfiguredPath

    # 处理环境变量占位符 @MYSHELL
    if ($path -like '@MYSHELL*') {
        $myshell = $env:MYSHELL
        if (-not $myshell) {
            throw "环境变量 MYSHELL 未设置，无法解析路径: $path"
        }
        $path = $path -replace '^@MYSHELL', $myshell
        Write-Verbose "已替换 @MYSHELL => $myshell"
    }

    # 若非绝对路径，则基于脚本目录拼接
    if (-not [System.IO.Path]::IsPathRooted($path)) {
        $path = Join-Path $ScriptDir $path
    }

    return $path
}