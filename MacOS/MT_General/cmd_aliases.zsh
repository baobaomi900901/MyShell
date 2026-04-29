# 与 Windows 一致的命令名：cd_ / pw_ / code_（转发到 _cd / _pw / _code），并注册与下划线版相同的 Tab 补全
# 依赖：_cd、_pw、_code 已定义（同目录下 _cd.zsh 等需先被加载；本文件因字母序在 _*.zsh 之后执行）

cd_() { _cd "$@" }
pw_() { _pw "$@" }
code_() { _code "$@" }

# path.json：仅含当前系统有路径的项；显示名中 _ 换为 -（与 Windows 一致）
_myshell_path_tab() {
  [[ -n "${MYSHELL:-}" ]] || return 1
  local json="${MYSHELL}/config/private/path.json"
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
    if not (v.get("win") or v.get("mac")):
        continue
    desc = (v.get("description") or "").replace("\n", " ").replace("\r", " ")
    disp = k.replace("_", "-")
    print("%s:%s" % (disp, desc))
' "$json")
  (( ${#opts[@]} )) || return 1
  _describe -t targets bookmark opts
}

compdef _myshell_path_tab cd_ _cd

# path_code.json
_myshell_code_tab() {
  [[ -n "${MYSHELL:-}" ]] || return 1
  local json="${MYSHELL}/config/private/path_code.json"
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
    if not (v.get("win") or v.get("mac")):
        continue
    desc = (v.get("description") or "").replace("\n", " ").replace("\r", " ")
    disp = k.replace("_", "-")
    print("%s:%s" % (disp, desc))
' "$json")
  (( ${#opts[@]} )) || return 1
  _describe -t targets bookmark opts
}

compdef _myshell_code_tab code_ _code

# password.json：含 password 字段的键
_myshell_pw_tab() {
  [[ -n "${MYSHELL:-}" ]] || return 1
  local json="${MYSHELL}/config/private/password.json"
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
    if v.get("password") is None:
        continue
    desc = (v.get("description") or "").replace("\n", " ").replace("\r", " ")
    print("%s:%s" % (k, desc))
' "$json")
  (( ${#opts[@]} )) || return 1
  _describe -t targets password opts
}

compdef _myshell_pw_tab pw_ _pw
