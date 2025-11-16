# C:\Users\mobytang\Documents\WindowsPowerShell\MyShell\Windows\win_general.ps1

# 生效脚本
# . $PROFILE 
# 查询所有自定义别名 
# Get-Alias | Where-Object { $_.Options -eq "None" } | Select-Object Name, Definition
# 查询所有自定义函数 
# Get-ChildItem Function: | Select-Object Name, Definition

function reloadsh {
    Write-Host "reloadsh" -ForegroundColor Green

    # 定义一些变量
    $jsonFile = "C:\Users\mobytang\Documents\WindowsPowerShell\MyShell\Windows\function_tracker.json"
    $oldFuncNames = @()
    $newFuncNames = @()
    $newAddFuncNames = @()
    $newDelFuncNames = @()

    # 步骤一, 读取 json_file 中的 functionName 数组内容
    if (Test-Path $jsonFile) {
        Write-Host "📖 执行前读取已生效方法..." -ForegroundColor Cyan
        $jsonContent = Get-Content $jsonFile -Raw | ConvertFrom-Json
        $oldFuncNames = $jsonContent.functionName
        Write-Host "📋 已生效方法: $($oldFuncNames.Count)" -ForegroundColor Cyan
    } else {
        Write-Host "📝 没有找到任何方法" -ForegroundColor Yellow
    }

    # 步骤二, 循环获取 Windows\*.ps1 文件中的方法名称
    # Write-Host "📁 Loading functions from Windows\*.ps1:" -ForegroundColor Cyans
    $functionCount = 0
    $scriptFiles = Get-ChildItem "C:\Users\mobytang\Documents\WindowsPowerShell\MyShell\Windows\*.ps1"

    foreach ($scriptFile in $scriptFiles) {
        # Write-Host "🔍 Scanning: $($scriptFile.Name)" -ForegroundColor Magenta
        
        $content = Get-Content $scriptFile.FullName
        foreach ($line in $content) {
            if ($line -match '^\s*function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{') {
                $funcName = $matches[1]
                if ($funcName -notmatch '^_') {
                    # Write-Host "   ✅ Function: $funcName" -ForegroundColor Green
                    $newFuncNames += $funcName
                    $functionCount++
                }
            }
        }
    }
    
    Write-Host "📊 准备加载方法: $functionCount" -ForegroundColor Cyan

    # 步骤三, 对比数组
    # Write-Host "🔍 对比变化..." -ForegroundColor Cyan
    
    foreach ($func in $newFuncNames) {
        if ($func -notin $oldFuncNames) {
            $newAddFuncNames += $func
        }
    }
    
    foreach ($func in $oldFuncNames) {
        if ($func -notin $newFuncNames) {
            $newDelFuncNames += $func
        }
    }

    # 步骤四, 打印变更
    if ($newAddFuncNames.Count -gt 0) {
        Write-Host "🆕 新增方法 ($($newAddFuncNames.Count)):" -ForegroundColor Green
        foreach ($func in $newAddFuncNames) {
            Write-Host "   ✅ $func" -ForegroundColor Green
        }
    } else {
        Write-Host "✅ 没有新增方法" -ForegroundColor Green
    }
    
    if ($newDelFuncNames.Count -gt 0) {
        Write-Host "🗑️  删除方法 ($($newDelFuncNames.Count)):" -ForegroundColor Red
        foreach ($func in $newDelFuncNames) {
            Write-Host "   ❌ $func" -ForegroundColor Red
        }
    } else {
        Write-Host "✅ 没有删除方法" -ForegroundColor Green
    }

    # 步骤五, 清理删除的函数
    if ($newDelFuncNames.Count -gt 0) {
        Write-Host "🧹 Cleaning up deleted functions..." -ForegroundColor Yellow
        foreach ($func in $newDelFuncNames) {
            Write-Host "   🧹 Removing: $func" -ForegroundColor Yellow
            Remove-Item "function:$func" -ErrorAction SilentlyContinue
        }
        Write-Host "✅ Cleanup completed" -ForegroundColor Green
    }

    # 更新 JSON 文件
    # Write-Host "💾 Updating function tracker JSON file..." -ForegroundColor Cyan
    $jsonObject = @{
        functionName = $newFuncNames
    }
    $jsonObject | ConvertTo-Json | Set-Content $jsonFile
    
    if (Test-Path $jsonFile) {
        Write-Host "✅ 更新json" -ForegroundColor Green
    } else {
        Write-Host "❌ json更新失败" -ForegroundColor Red
    }

    # 重新加载配置 - 重新导入所有 ps1 文件
    # Write-Host "🔄 Reloading shell configuration..." -ForegroundColor Cyan
    
    $functionsDir = "C:\Users\mobytang\Documents\WindowsPowerShell\MyShell\Windows"
    if (Test-Path $functionsDir) {
        Get-ChildItem "$functionsDir\*.ps1" | ForEach-Object {
            . $_.FullName
            # Write-Host "   ✅ Reloaded: $($_.Name)" -ForegroundColor Green
        }
    }
    Set-Clipboard -Value ". `$PROFILE"
    Write-Host "🚫 不支持自动执行 . `$PROFILE, 已复制到剪贴板" -ForegroundColor Red
    # Write-Host "✅ Reload completed!" -ForegroundColor Green
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