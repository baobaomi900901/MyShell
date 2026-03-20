#!/usr/bin/env zsh

# 获取当前脚本所在目录的绝对路径，并导出为环境变量，供补全函数使用
export HOOKS_ZSH_DIR="${0:A:h}"

# 路径解析函数
resolve_path() {
    local path="$1"
    local resolved

    # 处理 @MYSHELL 前缀
    if [[ "$path" == "@MYSHELL"* ]]; then
        local myshell="${MYSHELL:-$HOOKS_ZSH_DIR/..}"
        # 去掉 @MYSHELL 前缀，拼接到 myshell 后
        resolved="${myshell}/${path#@MYSHELL}"
        # 去掉可能重复的 / 并转换为绝对路径
        resolved="${resolved:a}"
        echo "$resolved"
        return 0
    fi

    # 处理相对路径（以 ./ 或 ../ 开头）
    if [[ "$path" == "./"* ]] || [[ "$path" == "../"* ]]; then
        resolved="${HOOKS_ZSH_DIR}/${path}"
        resolved="${resolved:a}"
        echo "$resolved"
        return 0
    fi

    # 处理 ~ 扩展
    if [[ "$path" == "~"* ]]; then
        resolved="${path:a}"
        echo "$resolved"
        return 0
    fi

    # 绝对路径或其它，转换为绝对路径
    echo "${path:a}"
    return 0
}

# 定义 hooks_ 函数
hooks_() {
    local info_file="$HOOKS_ZSH_DIR/info.json"
    if [[ ! -f "$info_file" ]]; then
        echo "info.json not found in $HOOKS_ZSH_DIR" >&2
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
for name, info in data.items():
    desc = info.get("description", "")
    print(f"  {name:<{max_len}}    {desc}")
' "$info_file"
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
' "$info_file" "$cmd") || {
        echo "Command '$cmd' not found in info.json" >&2
        return 1
    }

    if [[ -z "$script_path" ]]; then
        echo "Command '$cmd' has no script_path defined" >&2
        return 1
    fi

    # 解析路径
    local resolved
    resolved=$(resolve_path "$script_path")
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

# 定义补全函数：从 info.json 中提取所有方法名作为候选项
_hooks() {
    local -a commands
    local info_file="$HOOKS_ZSH_DIR/info.json"
    if [[ -f "$info_file" ]]; then
        commands=(${(f)"$(python3 -c '
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
    for key in data.keys():
        print(key)
' "$info_file")"})
    fi
    _describe 'command' commands
}

# 注册补全函数到 hooks_ 命令
compdef _hooks hooks_