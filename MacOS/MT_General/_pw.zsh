# pw_ 函数 for macOS / Linux (zsh)
pw_() {
    # 检查环境变量 MYSHELL 是否设置
    if [[ -z "$MYSHELL" ]]; then
        echo "❌ 环境变量 MYSHELL 未设置" >&2
        return 1
    fi

    local py_script="$MYSHELL/public/_script/pw.py"
    local config_path="$MYSHELL/config/private/password.json"

    if [[ ! -f "$py_script" ]]; then
        echo "❌ 找不到 Python 脚本: $py_script" >&2
        return 1
    fi

    # 检查剪贴板命令是否可用（macOS 自带 pbcopy，Linux 可能需要 xclip）
    local copy_cmd
    if command -v pbcopy &>/dev/null; then
        copy_cmd="pbcopy"
    elif command -v xclip &>/dev/null; then
        copy_cmd="xclip -selection clipboard"
    else
        echo "❌ 未找到可用的剪贴板命令（pbcopy 或 xclip），请手动安装相应工具。" >&2
        return 1
    fi

    # 生成临时文件
    local temp_file=$(mktemp)

    # 有首参则直达对应密码项，否则交互选择（与 Windows _pw 一致）
    if [[ $# -gt 0 ]]; then
        python3 "$py_script" "$config_path" "$temp_file" "$1"
    else
        python3 "$py_script" "$config_path" "$temp_file"
    fi
    local exit_code=$?

    # 读取密码
    local password
    if [[ $exit_code -eq 0 && -s "$temp_file" ]]; then
        password=$(<"$temp_file")
        rm -f "$temp_file"

        if [[ -n "$password" ]]; then
            # 将密码复制到剪贴板
            echo -n "$password" | eval "$copy_cmd"
            if [[ $? -eq 0 ]]; then
                echo "✅ 密码已复制到剪贴板"
            else
                echo "❌ 复制到剪贴板失败" >&2
                return 1
            fi
        else
            # 用户取消时通常不会写入 temp_file；这里保持安静返回
            return 0
        fi
    else
        rm -f "$temp_file"
        # 用户取消：Python 会输出“已取消操作。”并正常退出（exit_code=0），这里不再额外报错
        if [[ $exit_code -eq 0 ]]; then
            return 0
        fi
        # 真错误：保留退出码，静默返回（错误信息由 Python/上游提示）
        return $exit_code
    fi
}