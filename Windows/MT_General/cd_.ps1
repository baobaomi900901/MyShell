# Windows/MTGeneral/cd_.ps1

function cd_ {
    # 用途: cd 到指定目录；无参时交互选择，有参时直接跳转（键名可与 Tab 补全一致，支持 - 写法）
    param(
        [Parameter(Mandatory = $false, Position = 0)]
        [string]$Query
    )

    $myshell = $env:MYSHELL
    if (-not $myshell) {
        Write-Host "❌ 环境变量 MYSHELL 未设置" -ForegroundColor Red
        return
    }
    
    $pyScript = Join-Path $myshell "public\_script\cd.py"
    $configPath = Join-Path $myshell "config\private\path.json"

    if (-not (Test-Path $pyScript)) {
        Write-Host "❌ 找不到 Python 脚本: $pyScript" -ForegroundColor Red
        return
    }

    # 1. 生成一个临时文件路径用于进程间通信
    $tempFile = [System.IO.Path]::GetTempFileName()

    try {
        # 2. 调用 Python：有 Query 则直达，否则走交互菜单
        if ($Query) {
            python $pyScript $configPath $tempFile $Query
        }
        else {
            python $pyScript $configPath $tempFile
        }

        # 3. 读取临时文件中的路径
        $targetPath = Get-Content -Path $tempFile -Raw
        
        if (-not [string]::IsNullOrWhiteSpace($targetPath)) {
            $targetPath = $targetPath.Trim()
            
            # 4. 执行真正的 cd 切换操作
            if (Test-Path $targetPath) {
                Set-Location -Path $targetPath
                # Write-Host "👉 已跳转到: $targetPath" -ForegroundColor Cyan
            } else {
                Write-Host "❌ 目标路径不存在: $targetPath" -ForegroundColor Red
            }
        }
    } finally {
        # 5. 无论如何，最后清理临时文件
        if (Test-Path $tempFile) {
            Remove-Item -Path $tempFile -Force
        }
    }
}

# Tab 补全（必须绑定 -ParameterName Query，否则高级函数第一个参数不会走补全、看不到 ListItem/ToolTip）
$script:myshell_cdCompleter = {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

    if ($env:MYSHELL) {
        $configFile = Join-Path $env:MYSHELL "config\private\path.json"
    } else {
        $userProfile = if ($env:USERPROFILE) { $env:USERPROFILE } else { [Environment]::GetFolderPath('UserProfile') }
        $configFile = Join-Path $userProfile "Documents\WindowsPowerShell\MyShell\config\private\path.json"
    }

    if (-not (Test-Path $configFile)) {
        return
    }

    try {
        $config = Get-Content $configFile -Raw -Encoding UTF8 | ConvertFrom-Json

        # 与 zsh 类似：补全菜单中 ListItem 显示为「名称    -- 描述」（PSReadLine 列表/工具提示）
        $rows = @(
            $config.PSObject.Properties | Where-Object { $_.Value.win -or $_.Value.mac } | ForEach-Object {
                $displayName = $_.Name -replace '_', '-'
                $description = ($_.Value.description -replace "`r`n|`n|`r", ' ').Trim()
                [PSCustomObject]@{ Insert = $displayName; Desc = $description }
            }
        )
        $maxLen = 0
        if ($rows.Count -gt 0) {
            $maxLen = @($rows | ForEach-Object { $_.Insert.Length } | Measure-Object -Maximum).Maximum
        }
        $completionItems = foreach ($r in $rows) {
            $listLabel = if ([string]::IsNullOrWhiteSpace($r.Desc)) {
                $r.Insert
            } else {
                ('{0,-' + $maxLen + '}    -- {1}') -f $r.Insert, $r.Desc
            }
            [System.Management.Automation.CompletionResult]::new(
                $r.Insert,
                $listLabel,
                'ParameterValue',
                $r.Desc
            )
        }

        $wc = if ($null -eq $wordToComplete) { '' } else { $wordToComplete }
        $completionItems | Where-Object {
            $_.CompletionText -like "$wc*"
        }

    } catch {
        return
    }
}
Register-ArgumentCompleter -CommandName cd_ -ParameterName Query -ScriptBlock $script:myshell_cdCompleter