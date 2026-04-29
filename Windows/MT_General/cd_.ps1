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

# Tab 补全功能（保持不变）
Register-ArgumentCompleter -CommandName cd_ -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    # 确定配置文件路径（优先使用 $env:MYSHELL，否则回退到默认路径）
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

        $completionItems = $config.PSObject.Properties | Where-Object {
            $_.Value.win -or $_.Value.mac
        } | ForEach-Object {
            $displayName = $_.Name -replace '_', '-'
            $description = $_.Value.description -replace "`n", " "
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