# git
ga() {
    if [ $# -eq 0 ]; then
        git add .
    else
        git add "$@"
    fi
    }

# 让 ga 使用 git add 的补全规则
compdef _git ga=git-add

gs() {
    git status
}

gcmt () 
{ 
    git commit -m "$@"
}

greset() {
    # if [ "$1" = "all" ]; then
    #     git reset --hard HEAD
    #     echo "已执行 git reset --hard HEAD（强制重置工作区和暂存区）"
    
    # # 定义 greset back（软重置到上一个提交，保留更改到暂存区）
    # elif [ "$1" = "back" ]; then
    #     git reset --soft HEAD~1
    #     echo "已执行 git reset --soft HEAD~1（撤销最新提交，保留更改到暂存区）"
    
    # else
    #     echo "用法:"
    #     echo "  greset all   # 强制重置到 HEAD（丢弃所有未提交的更改）"
    #     echo "  greset back  # 软重置到上一个提交（保留更改到暂存区）"
    # fi
    case "$1" in
        all)
            git reset --hard HEAD
            echo "已执行 git reset --hard HEAD（强制重置工作区和暂存区）"
            ;;
        back)
            git reset --soft HEAD~1
            echo "已执行 git reset --soft HEAD~1（撤销最新提交，保留更改到暂存区）"
            ;;
        *)
            echo "用法:"
            echo "  greset all   # 强制重置到 HEAD（丢弃所有未提交的更改）"
            echo "  greset back  # 软重置到上一个提交（保留更改到暂存区）"
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
    git pull --rebase
}

gpo() {
    git push origin
}

gsuk() {
    git stash -u -k
}
gspop() {
    git stash pop
}