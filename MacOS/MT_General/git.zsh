# Git 命令保留终端入口，实际执行由共用 Python 脚本负责。
_myshell_git() {
    if [[ -z "${MYSHELL:-}" ]]; then
        print -u2 '错误: 环境变量 MYSHELL 未设置'
        return 1
    fi
    python3 "$MYSHELL/public/_script/git_commands.py" mac "$@"
}

ga() {
    # 用途: 默认执行 git add. 或者 tab 补全文件
    _myshell_git ga "$@"
}

# 让 ga 使用 git add 的补全规则
compdef _git ga=git-add

gs() {
    # 用途: 执行 git status
    _myshell_git gs
}

gcmt () {
    # 用途: 执行 git commit -m 
    _myshell_git gcmt "$@"
}

greset() {
    # 用途: 调用 Python 交互式 greset

    [[ -n "${MYSHELL:-}" ]] || { print -u2 '错误: 环境变量 MYSHELL 未设置'; return 1; }
    python3 "$MYSHELL/public/_script/greset.py" "$@"
}

# 定义 cd_ 的补全函数
_greset_completion() {
    local -a options=(
        "all: 强制重置到 HEAD（丢弃所有未提交的更改）"
        "back: 软重置到上一个提交（保留更改到暂存区）"
    )
    _describe 'cd_ options' options
}

# 将补全函数关联到 greset 命令
compdef _greset_completion greset

gpr() {
    # 用途: 执行 git pull --rebase
    _myshell_git gpr
}

gpo() {
    # 用途: 执行 git push origin
    _myshell_git gpo
}

gsuk() {
    # 用途: 执行 git stash -u -k
    _myshell_git gsuk
}
gspop() {
    # 用途: 执行 git stash pop
    _myshell_git gspop
}

grecmt() {
    # 用途: 软重置最新提交，保留改动到暂存区
    _myshell_git grecmt
}

glocal() {
    # 用途: 查看相对 origin/develop 的本地提交
    _myshell_git glocal
}

gswitch() {
    # 用途: 交互选择 Git 分支，或直接切换到指定分支
    [[ -n "${MYSHELL:-}" ]] || { print -u2 '错误: 环境变量 MYSHELL 未设置'; return 1; }
    python3 "$MYSHELL/public/_script/gswitch.py" "$@"
}
compdef _git gswitch=git-switch
