# Git 简写命令
function ga {
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

function gs { git status }
function gcmt { git commit -m $args }
function gpr { git pull --rebase }
function gpo { git push }

function greset {
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
            Write-Host "使用方法:" -ForegroundColor Yellow
            Write-Host "  greset all   # Hard reset to HEAD (丢弃所有未提交的更改)" -ForegroundColor Cyan
            Write-Host "  greset back  # Soft reset to previous commit (保留更改到暂存区)" -ForegroundColor Cyan
        }
    }
}

function gsuk { git stash -u -k }
function gspop { git stash pop }
function grecmt { git reset --soft HEAD~1 }
