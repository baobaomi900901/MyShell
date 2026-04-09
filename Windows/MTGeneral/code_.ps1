# .\Windows\MTGeneral\code_.ps1

# code_ 函数：在 VS Code 中打开配置的路径
function code_ {
    # 用途: 在 VS Code 中打开配置的路径
    param([string]$name)

    # 构造 Python 脚本的完整路径（基于环境变量 $env:MYSHELL）
    $script = Join-Path $env:MYSHELL "public\_script\vscode_open.py"

    if (-not (Test-Path $script)) {
        Write-Host "❌ Python 脚本不存在: $script" -ForegroundColor Red
        return
    }

    $configFile = Join-Path $env:MYSHELL "config\private\path_code.json"
    if (-not (Test-Path $configFile)) {
        Write-Host ""
        Write-Host "❌ 配置文件不存在: $configFile" -ForegroundColor Red
        Write-Host "请手动创建该文件，模板如下：" -ForegroundColor Yellow
        Write-Host @'
{
  "ShIndex": {
    "win": "C:\\Users\\mobytang\\Documents\\WindowsPowerShell\\Microsoft.PowerShell_profile.ps1",
    "mac": "/Users/mobytang/.zshrc",
    "description": "打开 sh 入口文件"
  },
}
'@ -ForegroundColor DarkGray
        Write-Host ""
        return
    }

    # 调用 Python 脚本，合并输出
    $output = & python "$script" $name 2>&1
    $exitCode = $LASTEXITCODE

    # 将输出统一转为字符串，保留换行（模仿 cd_ 的处理）
    if ($output -is [array]) {
        $outputString = $output -join "`r`n"
    } else {
        $outputString = $output
    }

    if ($exitCode -eq 0) {
        # 成功时，如果输出是 "code ..." 命令则执行，否则直接显示（如帮助信息）
        if ($outputString -match "^code ") {
            Invoke-Expression $outputString
        } else {
            Write-Host $outputString
        }
    } else {
        # 失败时以红色显示错误
        Write-Host $outputString -ForegroundColor Red
    }
    Write-Host ""
}

# 注册 Tab 补全（保持之前正确的实现）
Register-ArgumentCompleter -CommandName code_ -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    # 确定配置文件路径（优先使用 $env:MYSHELL，否则回退到默认路径）
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