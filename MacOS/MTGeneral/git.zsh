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
    # 用途:
    # - 无参数：调用 Python 交互式 greset
    # - 有参数：兼容旧用法，并新增 back -1 / back gcmt

    local py_script=""
    if [[ -n "$MYSHELL" ]]; then
        py_script="$MYSHELL/public/_script/greset.py"
    fi

    if [[ $# -eq 0 ]]; then
        if [[ -f "$py_script" ]]; then
            python3 "$py_script"
            return $?
        fi
        echo -e "${c_b}用法:${c_x}"
        echo -e "${c_y}  greset all          # 强制重置到 HEAD（丢弃所有未提交的更改）${c_x}"
        echo -e "${c_y}  greset back         # 软重置到上一个提交（保留更改到暂存区）${c_x}"
        echo -e "${c_y}  greset back -1      # 软重置 HEAD~1（撤销最近 1 次提交，保留更改到暂存区）${c_x}"
        echo -e "${c_y}  greset back gcmt    # 取消暂存（保留工作区改动）${c_x}"
        return 1
    fi

    case "$1" in
        all)
            git reset --hard HEAD
            echo -e "${c_g}已执行 git reset --hard HEAD（强制重置工作区和暂存区）${c_x}"
            ;;
        back)
            if [[ "$2" == "gcmt" ]]; then
                git reset
                echo -e "${c_g}已执行 git reset（取消暂存，保留工作区改动）${c_x}"
                return $?
            fi
            if [[ -z "$2" ]]; then
                git reset --soft HEAD~1
                echo -e "${c_g}已执行 git reset --soft HEAD~1（撤销最新提交，保留更改到暂存区）${c_x}"
                return $?
            fi
            if [[ "$2" =~ ^-([0-9]+)$ ]]; then
                local n="${match[1]}"
                git reset --soft "HEAD~${n}"
                echo -e "${c_g}已执行 git reset --soft HEAD~${n}（撤销最近 ${n} 次提交，保留更改到暂存区）${c_x}"
                return $?
            fi
            echo -e "${c_r}错误: back 参数不支持。可用: -1/-2/... 或 gcmt${c_x}" >&2
            return 1
            ;;
        *)
            if [[ -f "$py_script" ]]; then
                python3 "$py_script" "$@"
                return $?
            fi
            echo -e "${c_b}用法:${c_x}"
            echo -e "${c_y}  greset all          # 强制重置到 HEAD（丢弃所有未提交的更改）${c_x}"
            echo -e "${c_y}  greset back         # 软重置到上一个提交（保留更改到暂存区）${c_x}"
            echo -e "${c_y}  greset back -1      # 软重置 HEAD~1（撤销最近 1 次提交，保留更改到暂存区）${c_x}"
            echo -e "${c_y}  greset back gcmt    # 取消暂存（保留工作区改动）${c_x}"
            return 1
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