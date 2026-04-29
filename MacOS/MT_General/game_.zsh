# 与 Windows game_ 一致：游戏存档目录备份到同父目录下带时间戳的副本（Mac 使用配置项中的 mac 路径）
# 配置：$MYSHELL/config/private/game.json

game_() {
  if [[ -z "${MYSHELL:-}" ]]; then
    echo "❌ 环境变量 MYSHELL 未设置" >&2
    return 1
  fi

  local config="${MYSHELL}/config/private/game.json"
  if [[ ! -f "$config" ]]; then
    echo "❌ 配置文件不存在: $config" >&2
    return 1
  fi

  local action="$1"

  if [[ -z "$action" ]]; then
    echo "游戏存档备份工具 (Mac)" >&2
    echo "用法: game_ <游戏名称>" >&2
    echo "" >&2
    python3 -c '
import json, sys
p = sys.argv[1]
with open(p, encoding="utf-8") as f:
    d = json.load(f)
print("可用游戏:")
for k in sorted(d.keys()):
    v = d[k]
    path = v.get("mac") or v.get("win")
    if not path:
        continue
    desc = v.get("description") or ""
    print("  %s - %s" % (k, desc))
' "$config" >&2
    return 0
  fi

  local source_path
  source_path=$(python3 -c '
import json, sys, os
p, key = sys.argv[1], sys.argv[2]
with open(p, encoding="utf-8") as f:
    d = json.load(f)
if key not in d:
    sys.exit(2)
v = d[key]
path = v.get("mac") or v.get("win")
if not path:
    sys.exit(3)
print(os.path.expanduser(path))
' "$config" "$action") || {
    echo "错误: 游戏 '\''$action'\'' 未配置或当前系统无路径" >&2
    return 1
  }

  if [[ ! -d "$source_path" ]]; then
    echo "错误: 源目录不存在 - $source_path" >&2
    return 1
  fi

  local parent folder timestamp backup_path
  parent=$(dirname "$source_path")
  folder=$(basename "$source_path")
  timestamp=$(date "+%Y_%m_%d_%H_%M")
  backup_path="${parent}/${folder}_${timestamp}"

  echo "正在备份到: $backup_path" >&2
  if cp -R "$source_path" "$backup_path"; then
    echo "✓ 备份完成: $backup_path" >&2
    return 0
  fi
  echo "❌ 备份失败" >&2
  return 1
}

_myshell_game_tab() {
  [[ -n "${MYSHELL:-}" ]] || return 1
  local json="${MYSHELL}/config/private/game.json"
  [[ -f "$json" ]] || return 1
  local -a opts
  opts=()
  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] && opts+=("$line")
  done < <(python3 -c '
import json, sys
p = sys.argv[1]
with open(p, encoding="utf-8") as f:
    d = json.load(f)
for k in sorted(d.keys()):
    v = d[k]
    if not (v.get("mac") or v.get("win")):
        continue
    desc = (v.get("description") or "").replace("\n", " ").replace("\r", " ")
    print("%s:%s" % (k, desc))
' "$json")
  (( ${#opts[@]} )) || return 1
  _describe -t targets game opts
}

compdef _myshell_game_tab game_
