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
  done < <(python3 "$MYSHELL/public/_script/config_entries.py" "$json" path zsh)
  (( ${#opts[@]} )) || return 1
  _describe -V -t targets bookmark opts
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
  done < <(python3 "$MYSHELL/public/_script/config_entries.py" "$json" path zsh)
  (( ${#opts[@]} )) || return 1
  _describe -V -t targets bookmark opts
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
  done < <(python3 "$MYSHELL/public/_script/config_entries.py" "$json" password zsh)
  (( ${#opts[@]} )) || return 1
  _describe -V -t targets password opts
}

compdef _myshell_pw_tab pw_
