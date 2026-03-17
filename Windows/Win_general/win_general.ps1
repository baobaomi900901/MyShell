# .\Windows\Win_general\win_general.ps1

# 生效脚本
# . $PROFILE 
# 查询所有自定义别名 
# Get-Alias | Where-Object { $_.Options -eq "None" } | Select-Object Name, Definition
# 查询所有自定义函数 
# Get-ChildItem Function: | Select-Object Name, Definition

function reloadsh {
    <#
    .SYNOPSIS
        调用 reloadsh.py 并根据其退出码决定是否关闭当前 PowerShell 窗口。
    #>
    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) {
        Write-Error "无法获取脚本所在目录。请确保函数定义在 .ps1 文件中并通过点 source 方式加载。"
        return
    }

    $pythonScript = Join-Path $scriptDir "src\reloadsh.py"
    if (-not (Test-Path $pythonScript)) {
        Write-Error "找不到 reloadsh.py，预期路径：$pythonScript"
        return
    }

    # 检查环境变量 $env:myshell 是否存在
    if (-not $env:myshell) {
        Write-Error "环境变量 'myshell' 未设置，无法确定 Windows 目录和 JSON 文件路径。"
        return
    }

    # 构建参数路径
    $windowsDir = Join-Path $env:myshell "windows"
    $jsonFile = Join-Path $env:myshell "windows\function_tracker.json"

    # 调用 Python 脚本，传递必需参数，同时保留用户可能传入的额外参数
    & python $pythonScript --windows-dir "$windowsDir" --json-file "$jsonFile" @args
    $exitCode = $LASTEXITCODE

    # 如果退出码为 1，表示用户选择了 Yes 并希望关闭当前窗口
    if ($exitCode -eq 1) {
        Write-Host "正在关闭当前窗口..."
        Start-Sleep -Seconds 1  # 让用户看到最后的消息
        [Environment]::Exit(0)  # 结束当前 PowerShell 进程，从而关闭窗口
    }
}

function hsh {
    Write-Host "内置方法:" -ForegroundColor Blue
    Write-Host "  setsh         # vscode 打开 自定义shell ( MyShell ) 配置文件" -ForegroundColor Yellow
    Write-Host "  remove_sh     # 删除别名或函数" -ForegroundColor Yellow
    Write-Host "  type_         # 查看 cd_ 方法是否存在" -ForegroundColor Yellow
    Write-Host "  cd_           # 切换到指定目录" -ForegroundColor Yellow
    Write-Host "  code_         # 打开 vscode 并切换到指定目录" -ForegroundColor Yellow
    Write-Host "  tool_         # 工具类指令" -ForegroundColor Yellow
    Write-Host "  op_           # 执行 open ." -ForegroundColor Yellow
    Write-Host "  new_          # 新建文件夹或文件 " -ForegroundColor Yellow
    Write-Host "git相关操作:" -ForegroundColor Blue
    Write-Host "  gs            # git status" -ForegroundColor Yellow
    Write-Host "  gcmt          # git commit -m" -ForegroundColor Yellow
    Write-Host "  ga            # git add" -ForegroundColor Yellow
    Write-Host "  gpr           # git pull" -ForegroundColor Yellow
    Write-Host "  gpo           # git push" -ForegroundColor Yellow
    Write-Host "  glocal       # git log origin/develop..HEAD --oneline " -ForegroundColor Yellow
}

function setsh { 
  $shellPath = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell"
  code $shellPath
  Write-Host "已打开 MyShell 配置文件, 请自行跳转到 \MyShell\Windows 文件夹下" -ForegroundColor Green
}



# 添加到您的 PowerShell Profile
function type_ {
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

# 默认执行 open .
function op_ {
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



# 设置命令别名
Set-Alias -Name new -Value new_ -Force