# Tab 补全：与 Windows 一致，仅对 cd_ / pw_ / code_ 注册（命令实现在 _cd.zsh / _pw.zsh / _code.zsh 中，函数名为后缀下划线）

# path.json
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
with open(p, encoding="utf-8-sig") as f:
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

compdef _myshell_path_tab cd_

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
with open(p, encoding="utf-8-sig") as f:
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

compdef _myshell_code_tab code_

# password.json
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
with open(p, encoding="utf-8-sig") as f:
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

compdef _myshell_pw_tab pw_
