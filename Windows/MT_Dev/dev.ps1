function pym {
  <#
  .SYNOPSIS
      简化 python main.py 的调用
  .DESCRIPTION
      将所有传入的参数原样转发给当前路径的下的 main.py。
      相当于每次输入 python main.py 的快捷方式。
  .EXAMPLE
      pym [args1] [args2] [...]
  #>
  python main.py @args
}