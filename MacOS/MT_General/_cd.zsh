# cd_ 函数 for macOS / Linux (zsh)
_cd() {
    # 用途: cd 到目标目录
    # 检查环境变量 MYSHELL 是否设置
    if [[ -z "$MYSHELL" ]]; then
        echo "❌ 环境变量 MYSHELL 未设置" >&2
        return 1
    fi

    local py_script="$MYSHELL/public/_script/cd.py"
    local config_path="$MYSHELL/config/private/path.json"

    if [[ ! -f "$py_script" ]]; then
        echo "❌ 找不到 Python 脚本: $py_script" >&2
        return 1
    fi

    # 生成临时文件
    local temp_file=$(mktemp)

    # 有首参则直达对应项，否则交互选择（与 Windows _cd 一致）
    if [[ $# -gt 0 ]]; then
        python3 "$py_script" "$config_path" "$temp_file" "$1"
    else
        python3 "$py_script" "$config_path" "$temp_file"
    fi
    local exit_code=$?

    # 读取目标路径
    local target_path
    if [[ $exit_code -eq 0 && -s "$temp_file" ]]; then
        target_path=$(<"$temp_file")
        rm -f "$temp_file"

        if [[ -n "$target_path" && -d "$target_path" ]]; then
            cd "$target_path" || return 1
            echo "👉 已跳转到: $target_path"
        else
            echo "❌ 目标路径不存在或不是目录: $target_path" >&2
            return 1
        fi
    else
        rm -f "$temp_file"
        # Python 脚本已经输出了错误信息，这里可额外提示退出码
        if [[ $exit_code -ne 0 ]]; then
            echo "❌ 操作已取消或出错 (退出码: $exit_code)" >&2
        fi
        return 1
    fi
}