# .\Windows\Win_general\win_cd.ps1
# 快速目录跳转函数，调用 Python 脚本实现


function cd_ {
    # 用途: 用于 cd 到指定目录
    param (
        [Parameter(Position = 0)]
        [string]$action
    )

    $scriptPath = Join-Path $PSScriptRoot "cd.py"
    if (-not (Test-Path $scriptPath)) {
        Write-Host "❌ 找不到 Python 脚本: $scriptPath" -ForegroundColor Red
        return
    }

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