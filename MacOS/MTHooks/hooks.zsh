#!/usr/bin/env zsh
# hooks.zsh - 提供 hooks_ 命令，支持执行方法对应的脚本
# MTHooks/hooks.zsh

# 获取脚本所在目录（保证 info.json 在同级）
HOOKS_SCRIPT_DIR="${0:A:h}"
HOOKS_JSON_FILE="$HOOKS_SCRIPT_DIR/info.json"

# 辅助函数：解析路径中的 @MYSHELL 为环境变量，并将相对路径转为绝对路径（相对于脚本目录）
_resolve_path() {
    local raw_path="$1"
    if [[ "$raw_path" == @MYSHELL/* ]]; then
        if [[ -z "$MYSHELL" ]]; then
            echo "hooks: error: MYSHELL environment variable not set" >&2
            return 1
        fi
        echo "${MYSHELL}/${raw_path#@MYSHELL/}"
    else
        # 如果不是绝对路径，则视为相对于脚本所在目录
        if [[ "$raw_path" != /* ]]; then
            echo "${HOOKS_SCRIPT_DIR}/$raw_path"
        else
            echo "$raw_path"
        fi
    fi
    return 0
}

# 主命令
hooks_() {
    if [[ $# -eq 0 ]]; then
        # 无参数：列出所有方法及描述
        if [[ ! -f "$HOOKS_JSON_FILE" ]]; then
            echo "hooks: error: info.json not found at $HOOKS_JSON_FILE" >&2
            return 1
        fi

        if command -v jq >/dev/null 2>&1; then
            jq -r 'to_entries[] | [.key, .value.description] | @tsv' "$HOOKS_JSON_FILE" 2>/dev/null | while IFS=$'\t' read -r name desc; do
                printf "%-20s # %s\n" "$name" "$desc"
            done
            return 0
        elif command -v python3 >/dev/null 2>&1; then
            python3 -c "
import json
import sys

try:
    with open('$HOOKS_JSON_FILE', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print(f'hooks: error parsing $HOOKS_JSON_FILE: {e}', file=sys.stderr)
    sys.exit(1)

for name, attrs in data.items():
    desc = attrs.get('description', '')
    print(f'{name:<20} # {desc}')
"
            return 0
        else
            echo "hooks: error: neither jq nor python3 found" >&2
            return 1
        fi
    else
        # 有参数：执行指定方法
        local method_name="$1"
        if [[ ! -f "$HOOKS_JSON_FILE" ]]; then
            echo "hooks: error: info.json not found at $HOOKS_JSON_FILE" >&2
            return 1
        fi

        # 从 JSON 中提取 script_path
        local script_path
        if command -v jq >/dev/null 2>&1; then
            script_path=$(jq -r ".\"$method_name\".script_path" "$HOOKS_JSON_FILE" 2>/dev/null)
            if [[ "$script_path" == "null" ]]; then
                echo "hooks: error: method '$method_name' not found in info.json" >&2
                return 1
            fi
        elif command -v python3 >/dev/null 2>&1; then
            script_path=$(python3 -c "
import json
import sys

try:
    with open('$HOOKS_JSON_FILE', encoding='utf-8') as f:
        data = json.load(f)
    print(data.get('$method_name', {}).get('script_path', ''))
except Exception as e:
    print(f'hooks: error parsing $HOOKS_JSON_FILE: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
            if [[ -z "$script_path" ]]; then
                echo "hooks: error: method '$method_name' not found in info.json" >&2
                return 1
            fi
        else
            echo "hooks: error: neither jq nor python3 found" >&2
            return 1
        fi

        # 解析路径中的 @MYSHELL 并处理相对路径
        local resolved_path
        resolved_path=$(_resolve_path "$script_path") || return $?

        # 检查文件是否存在
        if [[ ! -f "$resolved_path" ]]; then
            echo "hooks: error: script file not found: $resolved_path" >&2
            return 1
        fi

        # 根据扩展名执行并捕获退出码
        local ext="${resolved_path##*.}"
        local exit_code=0
        case "$ext" in
            zsh)
                zsh "$resolved_path" "${@:2}"
                exit_code=$?
                ;;
            py)
                python3 "$resolved_path" "${@:2}"
                exit_code=$?
                ;;
            js)
                node "$resolved_path" "${@:2}"
                exit_code=$?
                ;;
            *)
                echo "hooks: error: unsupported script type: .$ext" >&2
                return 1
                ;;
        esac
        # 打印返回值（退出码）
        echo "脚本返回值: $exit_code"
        return $exit_code
    fi
}

# 补全函数：提取所有方法名供 Tab 补全
_hooks() {
    local -a methods
    if [[ ! -f "$HOOKS_JSON_FILE" ]]; then
        _message "info.json not found"
        return 1
    fi

    if command -v jq >/dev/null 2>&1; then
        methods=(${(f)"$(jq -r 'keys[]' "$HOOKS_JSON_FILE" 2>/dev/null)"})
    elif command -v python3 >/dev/null 2>&1; then
        methods=(${(f)"$(python3 -c "import json; f=open('$HOOKS_JSON_FILE'); data=json.load(f); f.close(); print('\n'.join(data.keys()))" 2>/dev/null)"})
    else
        _message "neither jq nor python3 found"
        return 1
    fi

    if [[ ${#methods} -eq 0 ]]; then
        _message "no methods found"
        return 1
    fi

    _describe 'method' methods
}

# 注册补全
compdef _hooks hooks_