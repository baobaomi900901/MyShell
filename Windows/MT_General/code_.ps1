# Windows/MTGeneral/code_.ps1

function code_ {
    # 用途: 用 VS Code 打开配置项；无参时交互选择，有参时直接打开（键名可与 Tab 补全一致，支持 - 写法）
    param(
        [Parameter(Mandatory = $false, Position = 0)]
        [string]$Query
    )

    $myshell = $env:MYSHELL
    if (-not $myshell) {
        Write-Host "❌ 环境变量 MYSHELL 未设置" -ForegroundColor Red
        return
    }
    
    $pyScript = Join-Path $myshell "public\_script\vscode.py"
    $configPath = Join-Path $myshell "config\private\path_code.json"

    if (-not (Test-Path $pyScript)) {
        Write-Host "❌ 找不到 Python 脚本: $pyScript" -ForegroundColor Red
        return
    }

    $tempFile = [System.IO.Path]::GetTempFileName()

    try {
        if ($Query) {
            python $pyScript $configPath $tempFile $Query
        }
        else {
            python $pyScript $configPath $tempFile
        }

        $targetPath = Get-Content -Path $tempFile -Raw
        
        if (-not [string]::IsNullOrWhiteSpace($targetPath)) {
            $targetPath = $targetPath.Trim()
            
            if (Test-Path $targetPath) {
                code $targetPath
                Write-Host "👉 已在 VS Code 中打开: $targetPath" -ForegroundColor Cyan
            } else {
                Write-Host "❌ 目标路径不存在: $targetPath" -ForegroundColor Red
            }
        }
    } finally {
        if (Test-Path $tempFile) {
            Remove-Item -Path $tempFile -Force
        }
    }
}

# Tab 补全（绑定参数 Query）
$script:myshell_codeCompleter = {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

    if ($env:MYSHELL) {
        $configFile = Join-Path $env:MYSHELL "config\private\path_code.json"
    } else {
        $userProfile = if ($env:USERPROFILE) { $env:USERPROFILE } else { [Environment]::GetFolderPath('UserProfile') }
        $configFile = Join-Path $userProfile "Documents\WindowsPowerShell\MyShell\config\private\path_code.json"
    }

    if (-not (Test-Path $configFile)) {
        return
    }

    try {
        $config = Get-Content $configFile -Raw -Encoding UTF8 | ConvertFrom-Json

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
Register-ArgumentCompleter -CommandName code_ -ParameterName Query -ScriptBlock $script:myshell_codeCompleter