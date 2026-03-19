# 快速目录跳转函数（调用 cd.py）
cd_() {
    # 用途: 跳转到指定目录
    local action="$1"

    if [[ -z "$MYSHELL" ]]; then
        echo -e "\033[91m❌ 环境变量 MYSHELL 未设置，无法定位 Python 脚本\033[0m" >&2
        return 1
    fi

    local script_path="$MYSHELL/public/_script/cd.py"

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