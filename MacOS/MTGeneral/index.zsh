# cd_ 命令 - 快速跳转到预定义目录
cd_() {
    if [[ -z "$MYSHELL" ]]; then
        echo "❌ 环境变量 MYSHELL 未设置，无法定位 Python 脚本" >&2
        return 1
    fi

    local script_path="$MYSHELL/_tools/_pythonScript/cd.py"
    if [[ ! -f "$script_path" ]]; then
        echo "❌ 找不到 Python 脚本: $script_path" >&2
        return 1
    fi

    # 调用 Python 脚本（使用 python3），合并 stdout 和 stderr
    local output
    output=$(python3 "$script_path" "$@" 2>&1)

    [[ -z "$output" ]] && return

    # 如果输出以 "cd " 开头，则执行该命令（已安全转义）
    if [[ "$output" =~ ^cd\  ]]; then
        eval "$output"
    else
        # 否则直接打印（帮助信息或错误信息）
        echo "$output"
    fi
}