function cd_ {
    # 用途: 用于 cd 到指定目录
    param (
        [Parameter(Position = 0)]
        [string]$action
    )
    
    # 检查环境变量 MYSHELL 是否设置
    $myshell = $env:MYSHELL
    if (-not $myshell) {
        Write-Host "❌ 环境变量 MYSHELL 未设置，无法定位 Python 脚本" -ForegroundColor Red
        return
    }

    # 构建脚本路径：$myshell\public\_script\cd.py
    $scriptPath = Join-Path $myshell "public"
    $scriptPath = Join-Path $scriptPath "_script"
    $scriptPath = Join-Path $scriptPath "cd.py"

    if (-not (Test-Path $scriptPath)) {
        Write-Host "❌ 找不到 Python 脚本: $scriptPath" -ForegroundColor Red
        return
    }

    Write-Host ""

    # 调用 Python 脚本，将用户输入作为参数传递（不隐藏错误输出）
    $output = & python $scriptPath $action 2>&1

    # 检查输出是否为空
    if (-not $output) {
        return
    }

    # 将输出转换为字符串（如果是数组，则用换行连接）
    if ($output -is [array]) {
        $outputString = $output -join "`r`n"
    } else {
        $outputString = $output
    }

    # 如果输出以 "Set-Location" 开头，则执行该命令
    if ($outputString -match '^Set-Location') {
        Invoke-Expression $outputString
    } else {
        # 否则直接打印输出（帮助信息或错误信息）
        Write-Host $outputString
    }
    Write-Host ""
}

# Tab 补全功能（保持不变）
Register-ArgumentCompleter -CommandName cd_ -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\path.json"

    if (-not (Test-Path $configFile)) {
        return
    }

    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json

        $completionItems = $config.PSObject.Properties | Where-Object {
            $_.Value.win -and $_.Value.win -ne $null
        } | ForEach-Object {
            $displayName = $_.Name -replace '_', '-'
            $description = $_.Value.description
            [System.Management.Automation.CompletionResult]::new(
                $displayName,
                $displayName,
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