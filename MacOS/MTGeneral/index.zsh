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

  # 定义颜色变量
  local color_name=$'\e[32m'   # 绿色
  local color_desc=$'\e[34m'    # 蓝色
  local reset=$'\e[0m'

  for entry in "${entries[@]}"; do
    name="${entry%%$'\t'*}"
    desc="${entry#*$'\t'}"
    # 通过 %s 传递颜色码，确保 %-*s 只计算纯文本宽度
    printf "  %s%-*s%s  # %s%s%s\n" \
           "$color_name" $max_len "$name" "$reset" \
           "$color_desc" "$desc" "$reset"
  done
}

# ========== code_ 函数 ==========
# 功能：根据配置文件快速在 VS Code 中打开项目
# 依赖：$MYSHELL 环境变量指向 MyShell 根目录
#       Python3 脚本位于 $MYSHELL/public/_script/vscode_open.py
#       配置文件位于 $MYSHELL/config/path_code.json

function code_ {
    local name="$1"
    local script="${MYSHELL}/public/_script/vscode_open.py"
    local output exit_code

    # 检查 Python 脚本是否存在
    if [[ ! -f "$script" ]]; then
        print -P "%F{red}❌ Python 脚本不存在: $script%f"
        return 1
    fi

    # 调用 Python3 脚本，捕获输出和退出码
    output=$(python3 "$script" "$name" 2>&1)
    exit_code=$?

    # 根据退出码处理
    if [[ $exit_code -eq 0 ]]; then
        # 成功：如果输出以 "code " 开头则执行，否则直接显示
        if [[ "$output" =~ ^code\  ]]; then
            eval "$output"
        else
            print "$output"
        fi
    else
        # 失败：红色显示错误信息
        print -P "%F{red}${output}%f"
    fi
    print ""  # 空行分隔
}

# ========== 补全配置 ==========
# 补全函数：读取 path_code.json，生成“名称:描述”列表
_code_completion() {
    local json_file="${MYSHELL}/config/path_code.json"
    local -a suggestions

    # 如果 JSON 文件不存在，直接返回
    [[ -f "$json_file" ]] || return 1

    # 使用 Python3 解析 JSON，输出每行 "名称:描述"
    suggestions=(${(f)"$(python3 -c "
import sys, json
try:
    with open('$json_file', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
except:
    sys.exit(1)
for key, val in data.items():
    if val.get('win') or val.get('mac'):   # 至少在一个系统上有路径
        name = key.replace('_', '-')
        desc = val.get('description', '').replace('\n', ' ')
        print(f'{name}:{desc}')
")"})

    # 将列表提供给 _describe 进行补全（自动过滤已输入部分）
    _describe -t 'code projects' 'VS Code project' suggestions
}

# 注册补全函数到命令 code_
compdef _code_completion code_
