# Myshell/MacOS/mac_password.zsh

# 主函数：管理密码
pw_() {
    local config_file="$HOME/MyShell/config/password.json"
    
    if [[ ! -f "$config_file" ]]; then
        echo -e "${c_r}错误: 密码配置文件不存在 $config_file${c_x}"
        echo -e "${c_y}请创建配置文件: $config_file${c_x}"
        return 1
    fi
    
    # 检查是否安装了 jq
    if ! command -v jq &> /dev/null; then
        echo -e "${c_r}错误: 需要安装 jq 命令${c_x}"
        echo -e "${c_y}请运行: brew install jq${c_x}"
        return 1
    fi
    
    # 检查是否安装了 pbcopy (macOS 自带，但检查一下)
    if ! command -v pbcopy &> /dev/null; then
        echo -e "${c_r}错误: 需要 pbcopy 命令${c_x}"
        return 1
    fi
    
    if [[ -z "$1" ]]; then
        # 显示帮助信息和所有密码项（不显示密码）
        echo -e "${c_b}可用密码项:${c_x}"
        
        # 使用 jq 获取所有密码项
        local keys=($(jq -r 'keys[]' "$config_file" 2>/dev/null))
        
        if [[ ${#keys[@]} -eq 0 ]]; then
            echo -e "${c_r}错误: 无法解析 JSON 文件或没有配置的密码项${c_x}"
            return 1
        fi
        
        for key in "${keys[@]}"; do
            local desc=$(jq -r ".[\"$key\"].description" "$config_file")
            echo -e "  ${c_y}pw_ $key${c_x} - $desc"
        done
        
        echo -e "\n${c_g}使用示例:${c_x}"
        echo -e "  ${c_y}pw_ lite-root${c_x}      # 复制 lite-root 密码到剪贴板"
        return 0
    fi
    
    # 获取密码
    local password=$(jq -r ".[\"$1\"].password" "$config_file")
    
    if [[ "$password" == "null" ]] || [[ -z "$password" ]]; then
        echo -e "${c_r}错误: 密码项 '$1' 不存在或未配置密码${c_x}"
        echo -e "${c_y}使用 'pw_' 查看所有可用密码项${c_x}"
        return 1
    fi
    
    # 复制密码到剪贴板
    echo -n "$password" | pbcopy
    
    # 获取描述
    local desc=$(jq -r ".[\"$1\"].description" "$config_file")
    
    echo -e "${c_g}✓ 已复制 '$1' 的密码到剪贴板${c_x}"
    echo -e "${c_b}描述:${c_x} $desc"
    echo -e "${c_y}提示:${c_x} 使用 Cmd+V 粘贴密码"
}

# 增强的补全函数
_pw_completion() {
    local config_file="$HOME/MyShell/config/password.json"
    
    if [[ ! -f "$config_file" ]]; then
        return 1
    fi
    
    if ! command -v jq &> /dev/null; then
        return 1
    fi
    
    local -a options=()
    
    # 使用 jq 获取所有密码项
    local keys=($(jq -r 'keys[]' "$config_file" 2>/dev/null))
    
    for key in "${keys[@]}"; do
        options+=("$key")
    done
    
    _describe 'pw_ options' options
}

# 补全函数
compdef _pw_completion pw_
