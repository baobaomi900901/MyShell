# git
ga() {
    # 用途: 默认执行 git add. 或者 tab 补全文件
    if [ $# -eq 0 ]; then
        git add .
    else
        git add "$@"
    fi
    }

# 让 ga 使用 git add 的补全规则
compdef _git ga=git-add

gs() {
    # 用途: 执行 git status
    git status
}

gcmt () {
    # 用途: 执行 git commit -m 
    git commit -m "$@"
}

greset() {
    # 用途: 执行 git reset
    case "$1" in
        all)
            git reset --hard HEAD
            echo -e "${c_g}已执行 git reset --hard HEAD（强制重置工作区和暂存区）${c_x}"
            ;;
        back)
            git reset --soft HEAD~1
            echo -e "${c_g}已执行 git reset --soft HEAD~1（撤销最新提交，保留更改到暂存区）${c_x}"
            ;;
        *)
            echo -e "${c_b}用法:${c_x}"
            echo -e "${c_y}  greset all   # 强制重置到 HEAD（丢弃所有未提交的更改）${c_x}"
            echo -e "${c_y}  greset back  # 软重置到上一个提交（保留更改到暂存区）${c_x}"
            ;;
    esac
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
    git pull --rebase
}

gpo() {
    # 用途: 执行 git push origin
    git push origin
}

gsuk() {
    # 用途: 执行 git stash -u -k
    git stash -u -k 
}
gspop() {
    # 用途: 执行 git stash pop
    git stash pop
}