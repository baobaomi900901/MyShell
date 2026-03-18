# 快速目录跳转函数（调用 cd.py）
cd_() {
    # 用途: 跳转到指定目录
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
    echo "开始执行 reloadsh 函数"
    if [[ -z "$MYSHELL" ]]; then
        echo "错误: 环境变量 MYSHELL 未设置" >&2
        return 1
    fi

    local system_type="mac"
    local system_dir="${MYSHELL}/MacOS"
    local public_script_dir="${MYSHELL}/_tools"
    local json_file="${MYSHELL}/config/function_tracker.json"
    local script_path="${MYSHELL}/_tools/_pythonScript/reloadsh.py"

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

# 定义 hsh 函数
hsh() {
  local json_file="${MYSHELL}/config/function_tracker.json"

  # 检查文件是否存在
  if [[ ! -f "$json_file" ]]; then
    echo "错误：文件 $json_file 不存在" >&2
    return 1
  fi

  # 检查是否安装了 jq
  if ! command -v jq >/dev/null 2>&1; then
    echo "错误：需要 jq 命令来解析 JSON，请安装 jq" >&2
    return 1
  fi

  # 使用 jq 提取函数名和描述（忽略空描述）
  local entries=("${(@f)$(jq -r '.function | to_entries[] | select(.value.description != "") | "\(.key)\t\(.value.description)"' "$json_file")}")

  if [[ ${#entries} -eq 0 ]]; then
    echo "没有找到有描述的函数。"
    return 0
  fi

  # 计算最大函数名长度，用于对齐
  local max_len=0
  local entry name desc
  for entry in "${entries[@]}"; do
    name="${entry%%$'\t'*}"
    if [[ ${#name} -gt $max_len ]]; then
      max_len=${#name}
    fi
  done

  # 打印标题
  echo "内置方法:"

  # 遍历并格式化输出
  for entry in "${entries[@]}"; do
    name="${entry%%$'\t'*}"
    desc="${entry#*$'\t'}"
    printf "  %-*s  # %s\n" $max_len "$name" "$desc"
  done
}
