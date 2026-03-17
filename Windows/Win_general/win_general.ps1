# .\Windows\Win_general\win_general.ps1

# 生效脚本
# . $PROFILE 
# 查询所有自定义别名 
# Get-Alias | Where-Object { $_.Options -eq "None" } | Select-Object Name, Definition
# 查询所有自定义函数 
# Get-ChildItem Function: | Select-Object Name, Definition

function reloadsh {
    # 用途: 重新加载 powershell 脚本方法
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
# 用途: 描述内置方法
function hsh {
    <#
    .SYNOPSIS
        列出所有内置方法及其描述。
    .DESCRIPTION
        从 function_tracker.json 中读取函数名称和描述，并格式化打印。
    #>
    
    # 检查环境变量
    if (-not $env:myshell) {
        Write-Error "环境变量 'myshell' 未设置，无法定位 function_tracker.json。"
        return
    }

    $jsonPath = Join-Path $env:myshell "Windows\function_tracker.json"
    
    if (-not (Test-Path $jsonPath)) {
        Write-Error "找不到 function_tracker.json，预期路径：$jsonPath"
        return
    }

    try {
        # 以 UTF8 编码读取原始内容
        $content = Get-Content $jsonPath -Raw -Encoding UTF8

        # 移除可能的 BOM（U+FEFF）
        if ($content.Length -gt 0 -and $content[0] -eq [char]0xFEFF) {
            $content = $content.Substring(1)
        }

        # 尝试解析 JSON
        $json = $content | ConvertFrom-Json
    } catch {
        Write-Error "无法解析 JSON 文件：$_"
        Write-Host "文件内容预览（前200字符）：" -ForegroundColor Yellow
        Write-Host $content.Substring(0, [Math]::Min(200, $content.Length))
        return
    }

    # 提取函数描述（仅当 description 不为空）
    $functions = @()
    if ($json.function) {
        $json.function.PSObject.Properties | ForEach-Object {
            $name = $_.Name
            $desc = $_.Value.description
            if ($desc -and $desc -ne '') {
                $functions += [PSCustomObject]@{
                    Name = $name
                    Description = $desc
                }
            }
        }
    }

    if ($functions.Count -eq 0) {
        Write-Host "没有找到带有描述的内置方法。" -ForegroundColor Yellow
        return
    }

    # 计算最大函数名长度（用于对齐）
    $maxLen = ($functions | ForEach-Object { $_.Name.Length } | Measure-Object -Maximum).Maximum

    Write-Host "内置方法:" -ForegroundColor Cyan

    foreach ($f in $functions) {
        # 左对齐函数名，右侧填充空格至 maxLen+2，然后加上 "# " 和描述
        $line = "  " + $f.Name.PadRight($maxLen + 2) + "# " + $f.Description
        Write-Host $line -ForegroundColor Yellow
    }
}

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



# 设置命令别名
Set-Alias -Name new -Value new_ -Force