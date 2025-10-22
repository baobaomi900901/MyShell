# 生效脚本
# . $PROFILE 
# 查询所有自定义别名 
# Get-Alias | Where-Object { $_.Options -eq "None" } | Select-Object Name, Definition
# 查询所有自定义函数 
# Get-ChildItem Function: | Select-Object Name, Definition

function hsh {
    Write-Host "内置方法:" -ForegroundColor Blue
    Write-Host "  setsh         # vscode 打开 自定义shell ( MyShell ) 配置文件" -ForegroundColor Yellow
    Write-Host "  remove_sh     # 删除别名或函数" -ForegroundColor Yellow
    Write-Host "  type_         # 查看 cd_ 方法是否存在" -ForegroundColor Yellow
    Write-Host "  cd_           # 切换到指定目录" -ForegroundColor Yellow
    Write-Host "  code_         # 打开 vscode 并切换到指定目录" -ForegroundColor Yellow
    Write-Host "  tool_         # 工具类指令" -ForegroundColor Yellow
    Write-Host "  op_           # 执行 open ." -ForegroundColor Yellow
    Write-Host "git相关操作:" -ForegroundColor Blue
    Write-Host "  gs            # git status" -ForegroundColor Yellow
    Write-Host "  gcmt          # git commit -m" -ForegroundColor Yellow
    Write-Host "  ga            # git add" -ForegroundColor Yellow
    Write-Host "  gpr           # git pull" -ForegroundColor Yellow
    Write-Host "  gpo           # git push" -ForegroundColor Yellow
    Write-Host "  greset        # git reset --hard" -ForegroundColor Yellow
}

function setsh { 
  $shellPath = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell"
  code $shellPath
  Write-Host "已打开 MyShell 配置文件, 请自行跳转到 \MyShell\Windows 文件夹下" -ForegroundColor Green
}

function reloadsh {
    try {
        # 重新加载配置文件
        . $PROFILE
        Write-Host "✅ PowerShell 配置文件已成功重新加载！" -ForegroundColor Green
        
        # 显示加载的函数数量（可选）
        $functions = Get-ChildItem Function: | Where-Object { $_.Source -eq $PROFILE }
        Write-Host "📁 已加载 $($functions.Count) 个自定义函数" -ForegroundColor Cyan
    }
    catch {
        Write-Host "❌ 重新加载配置文件时出错: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function remove_sh {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Names
    )

    if ($Names.Count -eq 0) {
        Write-Host "使用方法:" -ForegroundColor Blue
        Write-Host "  remove_sh <name1> <name2>..." -ForegroundColor Yellow
        return
    }

    foreach ($name in $Names) {
        $deleted = $false
        
        # 尝试删除别名
        if (Get-Alias $name -ErrorAction SilentlyContinue) {
            Remove-Item "Alias:\$name" -Force -ErrorAction SilentlyContinue
            $deleted = $true
        }
        
        # 尝试删除函数
        if (Get-Command $name -CommandType Function -ErrorAction SilentlyContinue) {
            Remove-Item "Function:\$name" -Force -ErrorAction SilentlyContinue
            $deleted = $true
        }
        
        # 检查是否删除成功
        $commandExists = Get-Command $name -ErrorAction SilentlyContinue | 
                         Where-Object { $_.CommandType -in @('Alias', 'Function') }
        
        if (-not $commandExists) {
            if ($deleted) {
                Write-Host "✅ '$name' 已删除（别名或函数）" -ForegroundColor Green
            } else {
                Write-Host "⚠️  '$name' 不存在（无法删除）" -ForegroundColor Yellow
            }
        } else {
            Write-Host "❌ '$name' 删除失败（可能受保护）" -ForegroundColor Red
        }
    }

    # 如果成功删除了任何项目，则重新加载配置文件
    if ($deletedAny) {
        Write-Host "`n🔄 正在重新加载配置文件..." -ForegroundColor Cyan
        reloadsh
    }
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