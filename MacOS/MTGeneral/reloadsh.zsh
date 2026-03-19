reloadsh() {
    # 用途: 重新加载 .zsh 方法
    echo "开始执行 reloadsh 函数"
    if [[ -z "$MYSHELL" ]]; then
        echo "错误: 环境变量 MYSHELL 未设置" >&2
        return 1
    fi

    local system_type="mac"
    local system_dir="${MYSHELL}/MacOS"
    local public_script_dir="${MYSHELL}/public"
    local json_file="${MYSHELL}/config/function_tracker.json"
    local script_path="${MYSHELL}/public/_script/reloadsh.py"

    echo "检查 Python3"
    if ! command -v python3 >/dev/null 2>&1; then
        echo "错误: 未找到 python3" >&2
        return 1
    fi

    echo "检查脚本文件: $script_path"
    if [[ ! -f "$script_path" ]]; then
        echo "错误: 未找到 reloadsh.py" >&2
        return 1
    fi

    local tmp_removed=$(mktemp)
    export RELOADSH_REMOVED_FILE="$tmp_removed"
    echo "临时文件: $tmp_removed"

    echo "开始执行 Python 脚本..."
    python3 "$script_path" \
        --system-type "$system_type" \
        --system-dir "$system_dir" \
        --public-script-dir "$public_script_dir" \
        --json-file "$json_file"

    local exit_code=$?
    # echo "Python 脚本退出码: $exit_code"
    unset RELOADSH_REMOVED_FILE

    if [[ $exit_code -eq 42 ]]; then
        # echo "退出码 42，处理删除函数..."
        if [[ -s "$tmp_removed" ]]; then
            # echo "临时文件内容:"
            cat "$tmp_removed"
            while IFS= read -r func; do
                if [[ -n "$func" ]]; then
                    # echo "移除函数: $func"
                    unfunction "$func" 2>/dev/null || echo "警告: 函数 $func 不存在"
                fi
            done < "$tmp_removed"
        else
            echo "临时文件为空"
        fi
        # echo "重新加载 ~/.zshrc ..."
        source ~/.zshrc
        echo "重新加载完成"
    elif [[ $exit_code -ne 0 ]]; then
        echo "reloadsh 执行失败，退出码: $exit_code" >&2
        rm -f "$tmp_removed"
        return $exit_code
    else
        # echo "退出码 0，重新加载 ~/.zshrc ..."
        source ~/.zshrc
        # echo "重新加载完成"
    fi

    rm -f "$tmp_removed"
}
