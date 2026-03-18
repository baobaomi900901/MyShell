# cd_ 命令的补全函数
_cd_() {
  local -a candidates
  local config_file

  # 检查环境变量 MYSHELL
  if [[ -z "$MYSHELL" ]]; then
    _message "错误: 环境变量 MYSHELL 未设置"
    return 1
  fi

  config_file="$MYSHELL/config/path.json"
  if [[ ! -f "$config_file" ]]; then
    _message "错误: 配置文件不存在: $config_file"
    return 1
  fi

  # 调用 Python 提取可用的目录名（仅限当前平台）
  # 使用 python3 快速解析 JSON 并输出一行一个候选词
  candidates=($(python3 -c "
import sys, json, platform
try:
    with open('$config_file', encoding='utf-8-sig') as f:
        data = json.load(f)
except Exception:
    sys.exit(1)

system = platform.system()
# 在 macOS 上只取包含 'mac' 字段的键
for key, val in data.items():
    if system == 'Darwin' and val.get('mac') is None:
        continue
    # 将下划线替换为短横线作为显示名
    print(key.replace('_', '-'))
" 2>/dev/null))

  # 如果没有候选词，显示提示并返回
  if [[ ${#candidates} -eq 0 ]]; then
    _message "没有可用的目录"
    return 1
  fi

  # 使用 compadd 将候选词提供给补全系统
  compadd -a candidates
}

# 将补全函数绑定到 cd_ 命令
compdef _cd_ cd_




reloadsh() {
    # 固定参数值
    local system_type="mac"
    local system_dir="${MYSHELL}/MacOS"
    local public_script_dir="${MYSHELL}/_tools"
    local json_file="${MYSHELL}/config/function_tracker.json"
    # 假设 reloadsh.py 位于 _tools 目录下（可根据实际情况调整）
    local script_path="${MYSHELL}/_tools/_pythonScript/reloadsh.py"

    # 检查 Python 环境
    if ! command -v python3 >/dev/null 2>&1; then
        echo "错误: 未找到 python3，请安装 Python 或将其加入 PATH" >&2
        return 1
    fi

    # 检查脚本文件是否存在
    if [[ ! -f "$script_path" ]]; then
        echo "错误: 未找到 reloadsh.py，预期路径: $script_path" >&2
        return 1
    fi

    # 执行 Python 脚本
    python3 "$script_path" \
        --system-type "$system_type" \
        --system-dir "$system_dir" \
        --public-script-dir "$public_script_dir" \
        --json-file "$json_file"

    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        echo "reloadsh 执行失败，退出码: $exit_code" >&2
    fi
    return $exit_code
}