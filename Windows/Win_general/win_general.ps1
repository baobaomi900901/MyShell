# .\Windows\Win_general\win_general.ps1

# 生效脚本
# . $PROFILE 
# 查询所有自定义别名 
# Get-Alias | Where-Object { $_.Options -eq "None" } | Select-Object Name, Definition
# 查询所有自定义函数 
# Get-ChildItem Function: | Select-Object Name, Definition

function reloadsh {
    # 计算基础路径
    $MyShellPath = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell"
    $WindowsPath = Join-Path $MyShellPath "Windows"   # 根目录
    $jsonFile = Join-Path $WindowsPath "function_tracker.json"
    # Python 脚本位于 Windows\Win_general\reloadsh.py
    $pythonScript = Join-Path $WindowsPath "Win_general\reloadsh.py"

    # 检查 Python 脚本是否存在
    if (-not (Test-Path $pythonScript)) {
        Write-Host "❌ 找不到 Python 脚本: $pythonScript" -ForegroundColor Red
        Write-Host "请确保文件位于: $pythonScript" -ForegroundColor Yellow
        return
    }

    Write-Host "🔍 调用 Python 脚本分析函数变更..." -ForegroundColor Cyan

    # 创建临时文件用于捕获 stderr
    $tempStderr = [System.IO.Path]::GetTempFileName()

    # 执行 Python 脚本，将 stderr 重定向到临时文件，stdout 捕获到变量
    $stdout = & python $pythonScript --windows-dir $WindowsPath --json-file $jsonFile 2> $tempStderr

    # 读取 stderr 内容
    $stderr = Get-Content $tempStderr -Raw
    Remove-Item $tempStderr

    # 检查退出码
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Python 脚本执行失败，退出码: $LASTEXITCODE" -ForegroundColor Red
        if ($stderr) {
            Write-Host "错误信息:" -ForegroundColor Red
            Write-Host $stderr -ForegroundColor Red
        }
        return
    }

    if (-not $stdout) {
        Write-Host "❌ Python 脚本未返回任何命令" -ForegroundColor Red
        return
    }

    # 将多行输出合并为单个字符串
    $scriptBlock = $stdout -join "`r`n"
    Invoke-Expression $scriptBlock
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