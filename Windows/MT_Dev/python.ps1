# 激活当前目录下的 .venv 虚拟环境
function py_star {
    # 用途: 激活当前目录下的 .venv 虚拟环境
    if (Test-Path ".\.venv\Scripts\Activate.ps1") {
        .\.venv\Scripts\Activate.ps1
        Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
    } else {
        Write-Host "❌ 未找到 .\.venv\Scripts\Activate.ps1，请确认当前目录是项目根目录且已运行 uv sync" -ForegroundColor Red
    }
}

function py_end {
    # 用途: 退出当前虚拟环境
    if ($env:VIRTUAL_ENV) {
        deactivate
        Write-Host "✅ 已退出虚拟环境" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 当前未激活任何虚拟环境" -ForegroundColor Yellow
    }
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