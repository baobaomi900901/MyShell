# .\Windows\MTGit\index.ps1
# Git 简写命令：终端入口保留，实际执行交给共用 Python 脚本。
function _myshell_git {
    param(
        [string]$CommandName,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )
    if (-not $env:MYSHELL) {
        Write-Error '环境变量 MYSHELL 未设置'
        return
    }
    $scriptPath = Join-Path $env:MYSHELL 'public\_script\git_commands.py'
    python $scriptPath win $CommandName @Arguments
}

function ga {
    # 用途: 执行 "git add ."
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Paths
    )

    if ($Paths.Count -gt 0) { _myshell_git ga @Paths }
    else { _myshell_git ga }
}
Register-ArgumentCompleter -CommandName ga -ScriptBlock {
    param($commandName, $wordToComplete, $cursorPosition)
    git status --short | ForEach-Object {
        $_.Substring(3)  # 提取文件名部分
    } | Where-Object { $_ -like "*$wordToComplete*" }
}

function gs { 
    # 用途: 执行 "git status"
    _myshell_git gs
}

function gcmt {
    # 用途: 执行 "git commit -m"
    _myshell_git gcmt @args
}
function gpr { 
    # 用途: 执行 "git pull --rebase"
    _myshell_git gpr
}
function gpo { 
    # 用途: 执行 "git push"
    _myshell_git gpo
}

function greset {
    # 用途: 调用 Python 交互式 greset
    if (-not $env:MYSHELL) {
        Write-Error '环境变量 MYSHELL 未设置'
        return
    }
    $scriptPath = Join-Path $env:MYSHELL 'public\_script\greset.py'
    python $scriptPath @args
}

function gsuk {
    # 用途: 执行 "git stash -u -k", 忽略暂存区的更改
    _myshell_git gsuk
}
function gspop { 
    # 用途: 执行 "git stash pop", 恢复最近的暂存区更改
    _myshell_git gspop
}
function grecmt { 
    # 用途: 软重置最新提交，保留改动到暂存区
    _myshell_git grecmt
}
function glocal { 
    # 用途: 查看相对 origin/develop 的本地提交
    _myshell_git glocal
}

function gswitch {
    # 用途: 无参时交互选择分支，有参时直接 git switch <Branch>
    param(
        [Parameter(Mandatory = $false, Position = 0)]
        [string]$Branch
    )
    if (-not $env:MYSHELL) {
        Write-Error '环境变量 MYSHELL 未设置'
        return
    }
    $scriptPath = Join-Path $env:MYSHELL 'public\_script\gswitch.py'
    if ($Branch) {
        python $scriptPath $Branch
    } else {
        python $scriptPath
    }
}

$script:myshell_gswitchCompleter = {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

    $wc = if ($null -eq $wordToComplete) { '' } else { $wordToComplete }

    $locals = @()
    $remotes = @()
    try {
        $locals = @(git for-each-ref refs/heads/ --format="%(refname:short)" 2>$null)
        $remotes = @(git for-each-ref refs/remotes/ --format="%(refname:short)" 2>$null | Where-Object { $_ -and ($_ -notmatch '/HEAD$') })
    } catch {
        return
    }

    foreach ($name in @($locals) + @($remotes)) {
        if ($name -like "$wc*") {
            [System.Management.Automation.CompletionResult]::new($name, $name, 'ParameterValue', $name)
        }
    }
}
Register-ArgumentCompleter -CommandName gswitch -ParameterName Branch -ScriptBlock $script:myshell_gswitchCompleter
