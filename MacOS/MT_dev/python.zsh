pym(){
  python main.py "$@"
}

py_star() {
  # 用途: 激活当前目录下的 .venv 虚拟环境
  [[ -n "${MYSHELL:-}" ]] || { print -u2 '错误: 环境变量 MYSHELL 未设置'; return 1; }
  local activate
  activate=$(python3 "$MYSHELL/public/_script/shell_commands.py" venv-activate mac) || return $?
  source "$activate" || return $?
  print '✅ 虚拟环境已激活'
}

py_end() {
  # 用途: 退出当前虚拟环境
  [[ -n "${MYSHELL:-}" ]] || { print -u2 '错误: 环境变量 MYSHELL 未设置'; return 1; }
  python3 "$MYSHELL/public/_script/shell_commands.py" venv-deactivate || return $?
  deactivate || return $?
  print '✅ 已退出虚拟环境'
}
