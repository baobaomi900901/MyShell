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

# 辅助函数：编辑密码配置文件
function edit-pw-config() {
    local config_file="$HOME/MyShell/config/password.json"
    
    # 确保目录存在
    mkdir -p "$(dirname "$config_file")"
    
    # 如果文件不存在，创建示例配置
    if [[ ! -f "$config_file" ]]; then
        cat > "$config_file" << 'EOF'
{
  "lite-root": {
    "password": "Kingsware#%0417",
    "description": "lite 服务器 root 密码"
  },
  "example": {
    "password": "your-password-here",
    "description": "示例密码项"
  }
}
EOF
        echo -e "${c_y}已创建示例配置文件${c_x}"
    fi
    
    if command -v code &> /dev/null; then
        code "$config_file"
    else
        vim "$config_file"
    fi
    echo -e "${c_g}已打开密码配置文件${c_x}"
}

# 辅助函数：显示所有密码项（不显示密码）
function show-pw-items() {
    local config_file="$HOME/MyShell/config/password.json"
    
    if [[ ! -f "$config_file" ]]; then
        echo -e "${c_r}配置文件不存在${c_x}"
        return 1
    fi
    
    if ! command -v jq &> /dev/null; then
        echo -e "${c_r}需要安装 jq 命令: brew install jq${c_x}"
        return 1
    fi
    
    echo -e "${c_b}所有密码项:${c_x}"
    
    # 使用 jq 漂亮地显示所有配置（不显示密码）
    jq -r 'to_entries[] | "\(.key):\n  描述: \(.value.description)\n  密码: [已隐藏]\n"' "$config_file" | while IFS= read -r line; do
        if [[ "$line" == *:* && ! "$line" == *描述:* && ! "$line" == *密码:* ]]; then
            # 键名行
            echo -e "${c_y}$line${c_x}"
        else
            echo "  $line"
        fi
    done
    
    echo -e "\n${c_g}使用 'pw_ <项名>' 复制密码到剪贴板${c_x}"
}

# 清除剪贴板历史（macOS）
function clear-clipboard() {
    echo -e "${c_y}正在清除剪贴板历史...${c_x}"
    
    # 清除剪贴板
    echo "" | pbcopy
    
    # 尝试清除剪贴板历史（需要开启"剪贴板历史"功能）
    osascript -e 'tell application "System Events" to keystroke "v" using {command down, shift down}' 2>/dev/null
    
    echo -e "${c_g}✓ 剪贴板已清除${c_x}"
    echo -e "${c_y}提示: 可以手动清除剪贴板历史: Cmd+Shift+Delete${c_x}"
}

# 检查依赖函数
function check-pw-deps() {
    if ! command -v jq &> /dev/null; then
        echo -e "${c_r}缺少依赖: jq${c_x}"
        echo -e "${c_y}请安装: brew install jq${c_x}"
        return 1
    fi
    
    if ! command -v pbcopy &> /dev/null; then
        echo -e "${c_r}缺少依赖: pbcopy${c_x}"
        echo -e "${c_y}pbcopy 是 macOS 内置命令，如果缺失请检查系统${c_x}"
        return 1
    fi
    
    local config_file="$HOME/MyShell/config/password.json"
    if [[ ! -f "$config_file" ]]; then
        echo -e "${c_y}配置文件不存在: $config_file${c_x}"
        echo -e "${c_y}使用 'edit-pw-config' 创建配置文件${c_x}"
        return 1
    fi
    
    echo -e "${c_g}所有依赖检查通过!${c_x}"
    
    # 测试 JSON 解析
    if jq . "$config_file" &> /dev/null; then
        echo -e "${c_g}JSON 配置文件解析正常${c_x}"
        
        # 显示密码项数量
        local pw_count=$(jq -r 'keys | length' "$config_file")
        echo -e "${c_b}找到 $pw_count 个密码项${c_x}"
    else
        echo -e "${c_r}JSON 配置文件格式错误${c_x}"
        return 1
    fi
}

# 创建配置文件示例（如果不存在）
function init-pw-config() {
    local config_file="$HOME/MyShell/config/password.json"
    local config_dir="$(dirname "$config_file")"
    
    # 创建目录
    mkdir -p "$config_dir"
    
    # 如果文件不存在，创建示例配置
    if [[ ! -f "$config_file" ]]; then
        cat > "$config_file" << 'EOF'
{
  "lite-root": {
    "password": "Kingsware#%0417",
    "description": "lite 服务器 root 密码"
  },
  "mysql-root": {
    "password": "root123456",
    "description": "MySQL root 密码"
  },
  "vpn-password": {
    "password": "vpn@2023",
    "description": "公司 VPN 密码"
  }
}
EOF
        echo -e "${c_g}✓ 已创建密码配置文件${c_x}"
        echo -e "${c_b}位置:${c_x} $config_file"
        echo -e "\n${c_y}现在可以编辑配置文件:${c_x}"
        echo -e "  ${c_g}edit-pw-config${c_x}   # 编辑配置文件"
        echo -e "  ${c_g}pw_${c_x}             # 查看所有密码项"
    else
        echo -e "${c_y}配置文件已存在${c_x}"
    fi
}