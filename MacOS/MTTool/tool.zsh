#!/usr/bin/env zsh
# Mac 侧 MT 工具入口：_tool（与 Windows 一致）

# 本文件所在目录（解析 config 内相对路径、tool_menu 相对路径用）
tool_SELFPATH="${0:A:h}"

# 从 config.json 读取某命令的 ignore_exit_code（true / false）
_tool_json_ignore_exit() {
    local cfg="$1" c="$2"
    python3 -c '
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
cmd = sys.argv[2]
entry = data.get(cmd) or {}
print("true" if entry.get("ignore_exit_code") is True else "false")
' "$cfg" "$c"
}

# 从 config.json 读取 description
_tool_json_description() {
    local cfg="$1" c="$2"
    python3 -c '
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
cmd = sys.argv[2]
print((data.get(cmd) or {}).get("description", "") or "")
' "$cfg" "$c"
}

# 与 Windows _tool 对齐：无参走 questionary 菜单，有参按 config 执行脚本
_tool() {
    local config_file="$tool_SELFPATH/config.json"
    if [[ ! -f "$config_file" ]]; then
        echo "config.json not found in $tool_SELFPATH" >&2
        return 1
    fi

    # 无参数：tool_menu.py 交互选命令
    if [[ $# -eq 0 ]]; then
        local menu_script="" temp="" picked="" exit_menu=1
        if [[ -n "${MYSHELL:-}" && -f "$MYSHELL/public/_script/tool_menu.py" ]]; then
            menu_script="$MYSHELL/public/_script/tool_menu.py"
        else
            local rel="$tool_SELFPATH/../../public/_script/tool_menu.py"
            rel="${rel:a}"
            [[ -f "$rel" ]] && menu_script="$rel"
        fi

        if [[ -n "$menu_script" ]] && command -v python3 >/dev/null 2>&1; then
            temp=$(mktemp)
            python3 "$menu_script" "$config_file" "$temp"
            exit_menu=$?
            if [[ $exit_menu -eq 0 && -f "$temp" ]]; then
                picked=$(python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); print(p.read_text(encoding="utf-8").strip() if p.exists() else "")' "$temp")
            else
                picked=""
            fi
            [[ -f "$temp" ]] && rm -f "$temp"

            if [[ -n "$picked" ]]; then
                _tool "$picked"
                return $?
            fi
            if [[ $exit_menu -ne 0 ]]; then
                echo "提示: 交互菜单异常 (退出码: $exit_menu)，改为文本列表。" >&2
            fi
        else
            if [[ -z "$menu_script" ]]; then
                echo "提示: 未找到 public/_script/tool_menu.py，请设置 MYSHELL 或将 tool_menu.py 置于 MyShell/public/_script/。" >&2
            elif ! command -v python3 >/dev/null 2>&1; then
                echo "提示: 未找到 python3，无法启动交互菜单。" >&2
            fi
        fi

        python3 -c '
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

if not data:
    sys.exit(0)

max_len = max(len(k) for k in data.keys())
print("可用命令:")
for name, config in sorted(data.items()):
    desc = config.get("description", "")
    sp = config.get("script_path", "")
    extra = f" ({sp})" if sp else ""
    print(f"  {name:<{max_len}}  - {desc}{extra}")
' "$config_file"
        return 0
    fi

    # 有参数：执行对应命令
    local cmd="$1"
    shift

    local script_path
    script_path=$(python3 -c '
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

cmd = sys.argv[2]
if cmd in data:
    print(data[cmd].get("script_path", ""))
else:
    sys.exit(1)
' "$config_file" "$cmd") || {
        echo "未知命令: $cmd" >&2
        python3 -c '
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
print("可用命令:", ", ".join(sorted(d.keys())))
' "$config_file" >&2
        return 1
    }

    if [[ -z "$script_path" ]]; then
        echo "Command '$cmd' has no script_path defined" >&2
        return 1
    fi

    local resolved
    resolved=$(resolve_path "$script_path" "$tool_SELFPATH")
    if [[ $? -ne 0 ]]; then
        echo "Failed to resolve path: $script_path" >&2
        return 1
    fi

    if [[ ! -f "$resolved" ]]; then
        echo "脚本文件不存在: $resolved" >&2
        echo "  请检查 config.json 中的 script_path。" >&2
        return 1
    fi

    local desc
    desc=$(_tool_json_description "$config_file" "$cmd")
    echo "▶️ 执行命令 '$cmd': $desc"

    local ignore
    ignore=$(_tool_json_ignore_exit "$config_file" "$cmd")

    local ec=0
    if [[ -x "$resolved" ]]; then
        echo "🔧 执行: $resolved $@" >&2
        "$resolved" "$@"
        ec=$?
    else
        case "$resolved" in
            *.py)
                echo "🔧 执行: python3 $resolved $@" >&2
                python3 "$resolved" "$@"
                ec=$?
                ;;
            *.js)
                echo "🔧 执行: node $resolved $@" >&2
                node "$resolved" "$@"
                ec=$?
                ;;
            *.zsh|*.sh)
                if source "$resolved" 2>/dev/null; then
                    if typeset -f "$cmd" >/dev/null 2>&1; then
                        echo "🔧 执行: $cmd $@" >&2
                        "$cmd" "$@"
                        ec=$?
                    else
                        echo "Warning: No function named '$cmd' found in script, running as normal." >&2
                        if [[ -x "$resolved" ]]; then
                            "$resolved" "$@"
                            ec=$?
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

    if [[ $ec -ne 0 ]]; then
        if [[ "$ignore" == "true" ]]; then
            echo "脚本退出码为 $ec，但已配置 ignore_exit_code，继续。" >&2
            return 0
        fi
        echo "执行异常: 脚本退出码 $ec" >&2
        return "$ec"
    fi
    echo "✅ 脚本执行成功"
    return 0
}

_tool_tab_for() {
    local -a commands
    local config_file="$tool_SELFPATH/config.json"
    if [[ -f "$config_file" ]]; then
        commands=(${(f)"$(python3 -c '
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
    for key in sorted(data.keys()):
        print(key)
' "$config_file")"})
    fi
    _describe 'command' commands
}

compdef _tool_tab_for _tool
