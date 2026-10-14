# 激活当前目录下的 .venv 虚拟环境
function py_star {
    # 用途: 激活当前目录下的 .venv 虚拟环境
    if (-not $env:MYSHELL) { Write-Error '环境变量 MYSHELL 未设置'; return }
    $helper = Join-Path $env:MYSHELL 'public\_script\shell_commands.py'
    $activate = python $helper venv-activate win
    if ($LASTEXITCODE -ne 0) { return }
    . $activate
    if ($?) { Write-Host '✅ 虚拟环境已激活' -ForegroundColor Green }
}

function py_end {
    # 用途: 退出当前虚拟环境
    if (-not $env:MYSHELL) { Write-Error '环境变量 MYSHELL 未设置'; return }
    $helper = Join-Path $env:MYSHELL 'public\_script\shell_commands.py'
    python $helper venv-deactivate
    if ($LASTEXITCODE -ne 0) { return }
    deactivate
    if ($?) { Write-Host '✅ 已退出虚拟环境' -ForegroundColor Green }
}

function pym {
    # 用途: 简化 python main.py 的调用
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

function wsdk {
    # 用途: 简化 python test_demo_web_sdk.py 的调用
  <#
  .SYNOPSIS
      简化 test_demo_web_sdk.py 的调用
  .DESCRIPTION
      将所有传入的参数原样转发给当前路径的下的 test_demo_web_sdk.py。
      相当于每次输入 python test_demo_web_sdk.py 的快捷方式。
  .EXAMPLE
      wsdk [args1] [args2] [...]
  #>
  py test_demo_web_sdk.py @args
}

function npxserver {
    # 用途: 启动 npx http-server -p [端口] 服务
    param(
        [int]$Port = 1990,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$RemainingArgs
    )

    npx http-server -p $Port @RemainingArgs
}
