# 激活当前目录下的 .venv 虚拟环境
function venv_star {
    # 用途: 激活当前目录下的 .venv 虚拟环境
    if (Test-Path ".\.venv\Scripts\Activate.ps1") {
        .\.venv\Scripts\Activate.ps1
        Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
    } else {
        Write-Host "❌ 未找到 .\.venv\Scripts\Activate.ps1，请确认当前目录是项目根目录且已运行 uv sync" -ForegroundColor Red
    }
}

function venv_end {
    # 用途: 退出当前虚拟环境
    if ($env:VIRTUAL_ENV) {
        deactivate
        Write-Host "✅ 已退出虚拟环境" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 当前未激活任何虚拟环境" -ForegroundColor Yellow
    }
}