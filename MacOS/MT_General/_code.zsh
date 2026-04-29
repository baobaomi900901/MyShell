# code_ 函数 for macOS / Linux (zsh)
_code() {
    # 用途: 用 VS Code 打开当前目录、项目、文件、文件夹
    # 检查环境变量 MYSHELL 是否设置
    if [[ -z "$MYSHELL" ]]; then
        echo "❌ 环境变量 MYSHELL 未设置" >&2
        return 1
    fi

    local py_script="$MYSHELL/public/_script/vscode.py"
    local config_path="$MYSHELL/config/private/path_code.json"

    if [[ ! -f "$py_script" ]]; then
        echo "❌ 找不到 Python 脚本: $py_script" >&2
        return 1
    fi

    # 生成临时文件
    local temp_file=$(mktemp)

    # 有首参则直达对应项，否则交互选择（与 Windows _code 一致）
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

        if [[ -n "$target_path" ]]; then
            # 检查目标是否存在（code 命令可以打开不存在的文件/目录，但此处给出提示）
            if [[ -e "$target_path" ]]; then
                code "$target_path"
                echo "👉 已在 VS Code 中打开: $target_path"
            else
                echo "⚠️ 目标路径不存在，但尝试用 VS Code 打开: $target_path"
                code "$target_path"
            fi
        else
            echo "❌ 未选择任何项目" >&2
            return 1
        fi
    else
        rm -f "$temp_file"
        if [[ $exit_code -ne 0 ]]; then
            echo "❌ 操作已取消或出错 (退出码: $exit_code)" >&2
        fi
        return 1
    fi
}