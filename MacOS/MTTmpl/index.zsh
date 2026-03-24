#!/usr/bin/env zsh

# 获取当前脚本所在目录的绝对路径，并导出为环境变量，供补全函数使用
tmpl_SELFPATH="${0:A:h}"

# 加载公共函数
source "${tmpl_SELFPATH}/utils.zsh"

# 定义 tmpl_ 函数
tmpl() {
    local config_file="$tmpl_SELFPATH/config.json"
    if [[ ! -f "$config_file" ]]; then
        echo "config.json not found in $tmpl_SELFPATH" >&2
        return 1
    fi

    # 无参数：显示命令列表
    if [[ $# -eq 0 ]]; then
        python3 -c '
import json
import sys

with open(sys.argv[1], "r") as f:
    data = json.load(f)

if not data:
    sys.exit(0)

max_len = max(len(k) for k in data.keys())
print("内置命令:")
for name, config in data.items():
    desc = config.get("description", "")
    print(f"  {name:<{max_len}}    {desc}")
' "$config_file"
        return
    fi

    # 有参数：执行对应命令
    local cmd="$1"
    shift

    # 从 JSON 中获取 script_path
    local script_path
    script_path=$(python3 -c '
import json
import sys

with open(sys.argv[1], "r") as f:
    data = json.load(f)

cmd = sys.argv[2]
if cmd in data:
    print(data[cmd].get("script_path", ""))
else:
    sys.exit(1)
' "$config_file" "$cmd") || {
        echo "Command '$cmd' not found in config.json" >&2
        return 1
    }

    if [[ -z "$script_path" ]]; then
        echo "Command '$cmd' has no script_path defined" >&2
        return 1
    fi

    # 解析路径，传入 tmpl_SELFPATH 作为基准目录
    local resolved
    resolved=$(resolve_path "$script_path" "$tmpl_SELFPATH")
    if [[ $? -ne 0 ]]; then
        echo "Failed to resolve path: $script_path" >&2
        return 1
    fi

    if [[ ! -f "$resolved" ]]; then
        echo "Script not found: $resolved" >&2
        return 1
    fi

    # 执行脚本
    if [[ -x "$resolved" ]]; then
        # 如果有执行权限，直接执行（此时脚本应自己处理参数）
        "$resolved" "$@"
    else
        # 尝试根据扩展名调用解释器
        case "$resolved" in
            *.py)
                python3 "$resolved" "$@"
                ;;
            *.js)
                node "$resolved" "$@"
                ;;
            *.zsh|*.sh)
                # 先 source 脚本，然后尝试调用与命令同名的函数
                if source "$resolved" 2>/dev/null; then
                    # 检查函数是否存在
                    if typeset -f "$cmd" >/dev/null 2>&1; then
                        "$cmd" "$@"
                    else
                        echo "Warning: No function named '$cmd' found in script, running as normal." >&2
                        # 回退到直接执行（如果脚本有执行权限）
                        if [[ -x "$resolved" ]]; then
                            "$resolved" "$@"
                        else
                            echo "Cannot execute script: $resolved" >&2
                            return 1
                        fi
                    fi
                else
                    echo "Failed to source script: $resolved" >&2
                    return 1
                fi
                ;;
            *)
                echo "Script is not executable and no known interpreter for: $resolved" >&2
                return 1
                ;;
        esac
    fi
}

# 定义补全函数：从 config.json 中提取所有方法名作为候选项
_tmpl_tab_for() {
    local -a commands
    local config_file="$tmpl_SELFPATH/config.json"
    if [[ -f "$config_file" ]]; then
        commands=(${(f)"$(python3 -c '
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
    for key in data.keys():
        print(key)
' "$config_file")"})
    fi
    _describe 'command' commands
}

# 注册补全函数到 tmpl 命令
compdef _tmpl_tab_for tmpl