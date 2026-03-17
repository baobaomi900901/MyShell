# .\Windows\win_git.ps1
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
    # 用途: 执行 "git reset --hard" 或 "git reset --soft"
    param (
        [Parameter(Position = 0)]
        [ArgumentCompleter({
            param ($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
            $validActions = @('all', 'back')
            $validActions -like "$wordToComplete*"
        })]
        [string]$action
    )

    switch ($action) {
        "all" {
            git reset --hard HEAD
            Write-Host "Executed: git reset --hard HEAD (强制重置工作区和暂存区)"
        }
        "back" {
            git reset --soft HEAD~1
            Write-Host "Executed: git reset --soft HEAD~1 (撤销最新提交，保留更改到暂存区)"
        }
        default {
            Write-Host "使用方法:" -ForegroundColor blue
            Write-Host "  greset all   # Hard reset to HEAD (丢弃所有未提交的更改)" -ForegroundColor Yellow
            Write-Host "  greset back  # Soft reset to previous commit (保留更改到暂存区)" -ForegroundColor Yellow 
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