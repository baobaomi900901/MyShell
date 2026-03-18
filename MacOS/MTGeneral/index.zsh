# 快速目录跳转函数（调用 cd.py）
cd_() {
    local action="$1"

    if [[ -z "$MYSHELL" ]]; then
        echo -e "\033[91m❌ 环境变量 MYSHELL 未设置，无法定位 Python 脚本\033[0m" >&2
        return 1
    fi

    local script_path="$MYSHELL/_tools/_pythonScript/cd.py"

    if [[ ! -f "$script_path" ]]; then
        echo -e "\033[91m❌ 找不到 Python 脚本: $script_path\033[0m" >&2
        return 1
    fi

    echo ""

    local output
    output=$(python3 "$script_path" "$action" 2>&1)   # 确保使用 python3

    if [[ -z "$output" ]]; then
        return
    fi

    if [[ "$output" == cd\ * ]]; then
        eval "$output"
    else
        echo "$output"
    fi

    echo ""
}

_cd_completion() {
    local config_file="$HOME/MyShell/config/path.json"
    
    if [[ ! -f "$config_file" ]]; then
        return 1
    fi
    
    # 检查是否安装了 jq
    if ! command -v jq &> /dev/null; then
        return 1
    fi
    
    local -a options=()
    
    # 使用 jq 获取所有 macOS 可用的路径
    local keys=($(jq -r 'to_entries[] | select(.value.mac != null) | .key' "$config_file" 2>/dev/null))
    
    for key in "${keys[@]}"; do
        local desc=$(jq -r ".[\"$key\"].description" "$config_file")
        # 将内部的下划线键名转换回用户友好的连字符格式
        local display_name="${key//_/-}"
        # 只使用显示名称，不要包含描述（避免重复显示）
        options+=("$display_name")
    done
    
    _describe 'cd_ options' options
}

# 将补全函数关联到 cd_ 命令
compdef _cd_completion cd_




reloadsh() {
    if [[ -z "$MYSHELL" ]]; then
        echo "错误: 环境变量 MYSHELL 未设置" >&2
        return 1
    fi

    local system_type="mac"
    local system_dir="${MYSHELL}/MacOS"
    local public_script_dir="${MYSHELL}/_tools"
    local json_file="${MYSHELL}/config/function_tracker.json"
    local script_path="${MYSHELL}/_tools/_pythonScript/reloadsh.py"

    if ! command -v python3 >/dev/null 2>&1; then
        echo "错误: 未找到 python3，请安装 Python 或将其加入 PATH" >&2
        return 1
    fi

    if [[ ! -f "$script_path" ]]; then
        echo "错误: 未找到 reloadsh.py，预期路径: $script_path" >&2
        return 1
    fi

    # 创建临时文件用于接收删除的函数列表
    local tmp_removed=$(mktemp)
    # 设置环境变量传递给 Python 脚本
    export RELOADSH_REMOVED_FILE="$tmp_removed"

    python3 "$script_path" \
        --system-type "$system_type" \
        --system-dir "$system_dir" \
        --public-script-dir "$public_script_dir" \
        --json-file "$json_file"

    local exit_code=$?
    unset RELOADSH_REMOVED_FILE

    if [[ $exit_code -eq 42 ]]; then
        echo "检测到有删除的函数，正在清理内存中的函数定义..."
        if [[ -s "$tmp_removed" ]]; then
            # 读取临时文件中的函数名，每行一个，并执行 unfunction
            while IFS= read -r func; do
                if [[ -n "$func" ]]; then
                    echo "移除函数: $func"
                    # 使用 unfunction 移除（zsh 内建），忽略可能不存在的错误
                    unfunction "$func" 2>/dev/null || echo "警告: 函数 $func 不存在或无法移除" >&2
                fi
            done < "$tmp_removed"
        else
            echo "警告: 临时文件为空，但退出码为 42" >&2
        fi
        echo "重新加载 ~/.zshrc ..."
        source ~/.zshrc
        echo "重新加载完成。"
    elif [[ $exit_code -ne 0 ]]; then
        echo "reloadsh 执行失败，退出码: $exit_code" >&2
        rm -f "$tmp_removed"
        return $exit_code
    fi

    # 清理临时文件
    rm -f "$tmp_removed"
}