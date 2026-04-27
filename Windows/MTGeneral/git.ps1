# .\Windows\MTGit\index.ps1
# Git 简写命令

function ga {
    # 用途: 执行 "git add ."
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Paths
    )

    if ($Paths.Count -eq 0) {
        git add .
        Write-Host "Added all changes to staging area."
    }
    else {
        git add $Paths
        Write-Host "Added specified files to staging area."
    }
}
Register-ArgumentCompleter -CommandName ga -ScriptBlock {
    param($commandName, $wordToComplete, $cursorPosition)
    git status --short | ForEach-Object {
        $_.Substring(3)  # 提取文件名部分
    } | Where-Object { $_ -like "*$wordToComplete*" }
}

function gs { 
    # 用途: 执行 "git status"
    git status 
}

function gcmt {
    # 用途: 执行 "git commit -m"
    git commit -m $args 
}
function gpr { 
    # 用途: 执行 "git pull --rebase"
    git pull --rebase 
}
function gpo { 
    # 用途: 执行 "git push"
    git push 
}

function greset {
    # 用途:
    # - 无参数：调用 Python 交互式 greset
    # - 有参数：兼容旧用法，并新增 back -1 / back gcmt
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    $myshell = $env:MYSHELL
    if ($myshell) {
        $pyScript = Join-Path $myshell "public\_script\greset.py"
    }

    if ($Args.Count -eq 0) {
        if ($pyScript -and (Test-Path $pyScript)) {
            python $pyScript
            return
        }
        Write-Host "使用方法:" -ForegroundColor blue
        Write-Host "  greset all          # Hard reset to HEAD (丢弃所有未提交的更改)" -ForegroundColor Yellow
        Write-Host "  greset back         # Soft reset to previous commit (保留更改到暂存区)" -ForegroundColor Yellow
        Write-Host "  greset back -1      # Soft reset HEAD~1 (撤销最近 1 次提交，保留更改到暂存区)" -ForegroundColor Yellow
        Write-Host "  greset back gcmt    # Unstage (取消暂存，保留工作区改动)" -ForegroundColor Yellow
        return
    }

    $action = $Args[0]
    $mode = if ($Args.Count -ge 2) { $Args[1] } else { $null }

    switch ($action) {
        "all" {
            git reset --hard HEAD
            Write-Host "Executed: git reset --hard HEAD (强制重置工作区和暂存区)"
        }
        "back" {
            if ($mode -eq "gcmt") {
                git reset
                Write-Host "Executed: git reset (取消暂存，保留工作区改动)"
                return
            }
            if (-not $mode) {
                git reset --soft HEAD~1
                Write-Host "Executed: git reset --soft HEAD~1 (撤销最新提交，保留更改到暂存区)"
                return
            }
            if ($mode -match '^-([0-9]+)$') {
                $n = [int]$Matches[1]
                git reset --soft ("HEAD~{0}" -f $n)
                Write-Host ("Executed: git reset --soft HEAD~{0} (撤销最近 {0} 次提交，保留更改到暂存区)" -f $n)
                return
            }
            Write-Host "错误: back 参数不支持。可用: -1/-2/... 或 gcmt" -ForegroundColor Red
        }
        default {
            # 有参数但不识别：尝试转给 Python（如果存在）
            if ($pyScript -and (Test-Path $pyScript)) {
                python $pyScript @Args
                return
            }
            Write-Host "使用方法:" -ForegroundColor blue
            Write-Host "  greset all          # Hard reset to HEAD (丢弃所有未提交的更改)" -ForegroundColor Yellow
            Write-Host "  greset back         # Soft reset to previous commit (保留更改到暂存区)" -ForegroundColor Yellow
            Write-Host "  greset back -1      # Soft reset HEAD~1 (撤销最近 1 次提交，保留更改到暂存区)" -ForegroundColor Yellow
            Write-Host "  greset back gcmt    # Unstage (取消暂存，保留工作区改动)" -ForegroundColor Yellow
        }
    }
}

function gsuk {
    # 用途: 执行 "git stash -u -k", 忽略暂存区的更改
    git stash -u -k 
}
function gspop { 
    # 用途: 执行 "git stash pop", 恢复最近的暂存区更改
    git stash pop 
}
function grecmt { 
    # 用途: 执行 "git rebase -i HEAD~1", 编辑最近 n 次提交
    git reset --soft HEAD~1 
}
function glocal { 
    # 用途: 执行 "git branch -D local", 删除本地分支
    git log origin/develop..HEAD --oneline
}