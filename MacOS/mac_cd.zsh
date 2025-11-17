# Myshell/MacOS/mac_cd.zsh

cd_() {
    local config_file="$HOME/MyShell/config/path.json"
    
    if [[ ! -f "$config_file" ]]; then
        echo -e "${c_r}错误: 配置文件不存在 $config_file${c_x}"
        return 1
    fi
    
    # 检查是否安装了 jq
    if ! command -v jq &> /dev/null; then
        echo -e "${c_r}错误: 需要安装 jq 命令${c_x}"
        echo -e "${c_y}请运行: brew install jq${c_x}"
        return 1
    fi
    
    if [[ -z "$1" ]]; then
        # 显示帮助信息
        echo -e "${c_b}可用路径:${c_x}"
        
        # 使用 jq 获取所有 macOS 可用的路径
        local keys=($(jq -r 'to_entries[] | select(.value.mac != null) | .key' "$config_file" 2>/dev/null))
        
        if [[ ${#keys[@]} -eq 0 ]]; then
            echo -e "${c_r}错误: 无法解析 JSON 文件或没有可用的 macOS 路径${c_x}"
            return 1
        fi
        
        for key in "${keys[@]}"; do
            local desc=$(jq -r ".[\"$key\"].description" "$config_file")
            # 将内部的下划线键名转换回用户友好的连字符格式
            local display_name="${key//_/-}"
            echo -e "  ${c_y}cd_ $display_name${c_x} - $desc"
        done
        return 0
    fi
    
    # 将用户输入的连字符转换为下划线用于内部查找
    local internal_action="${1//-/_}"
    
    # 获取路径
    local target_path=$(jq -r ".[\"$internal_action\"].mac" "$config_file")
    
    if [[ "$target_path" == "null" ]] || [[ -z "$target_path" ]]; then
        echo -e "${c_r}错误: 路径 '$1' 在 macOS 上未配置或不存在${c_x}"
        echo -e "${c_y}使用 'cd_' 查看所有可用路径${c_x}"
        return 1
    fi
    
    # 展开 ~ 为家目录
    target_path="${target_path/#\~/$HOME}"
    
    if [[ -d "$target_path" ]]; then
        cd "$target_path"
        echo -e "${c_g}cd to $1: $target_path${c_x}"
    else
        echo -e "${c_r}错误: 目录不存在 - $target_path${c_x}"
        return 1
    fi
}

# 增强的补全函数
# 简洁版补全函数（只显示名称，不显示描述）
# 修复后的补全函数
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

# 辅助函数：编辑 cd_ 配置文件
function edit-cd-config() {
    local config_file="$HOME/MyShell/config/path.json"
    if command -v code &> /dev/null; then
        code "$config_file"
    else
        vim "$config_file"
    fi
    echo -e "${c_g}已打开 cd_ 配置文件${c_x}"
}

# 辅助函数：显示所有配置路径
function show-cd-paths() {
    local config_file="$HOME/MyShell/config/path.json"
    
    if [[ ! -f "$config_file" ]]; then
        echo -e "${c_r}配置文件不存在${c_x}"
        return 1
    fi
    
    if ! command -v jq &> /dev/null; then
        echo -e "${c_r}需要安装 jq 命令: brew install jq${c_x}"
        return 1
    fi
    
    echo -e "${c_b}所有配置路径:${c_x}"
    
    # 使用 jq 漂亮地显示所有配置
    jq -r 'to_entries[] | "\(.key):\n  描述: \(.value.description)\n  Windows: \(.value.win // "未配置")\n  macOS: \(.value.mac // "未配置")\n"' "$config_file" | while IFS= read -r line; do
        if [[ "$line" == *:* && ! "$line" == *描述:* && ! "$line" == *Windows:* && ! "$line" == *macOS:* ]]; then
            # 键名行
            local key="${line%:}"
            local display_name="${key//_/-}"
            echo -e "${c_y}$display_name${c_x}"
        else
            echo "  $line"
        fi
    done
}

# 检查依赖函数
function check-cd-deps() {
    if ! command -v jq &> /dev/null; then
        echo -e "${c_r}缺少依赖: jq${c_x}"
        echo -e "${c_y}请安装: brew install jq${c_x}"
        return 1
    fi
    
    local config_file="$HOME/MyShell/config/path.json"
    if [[ ! -f "$config_file" ]]; then
        echo -e "${c_r}配置文件不存在: $config_file${c_x}"
        echo -e "${c_y}请从 Windows 同步或手动创建${c_x}"
        return 1
    fi
    
    echo -e "${c_g}所有依赖检查通过!${c_x}"
    
    # 测试 JSON 解析
    if jq . "$config_file" &> /dev/null; then
        echo -e "${c_g}JSON 配置文件解析正常${c_x}"
        
        # 显示可用的 macOS 路径数量
        local mac_count=$(jq -r 'to_entries[] | select(.value.mac != null) | .key' "$config_file" | wc -l | tr -d ' ')
        echo -e "${c_b}找到 $mac_count 个 macOS 可用路径${c_x}"
    else
        echo -e "${c_r}JSON 配置文件格式错误${c_x}"
        return 1
    fi
}