# .\src\fun3.ps1

function fun3{
    param(
        [string]$Message = "默认消息",
        [switch]$Force
    )

    Write-Host "🚀 这是 fun3.ps1 脚本" -ForegroundColor Green
    Write-Host "收到参数:" -ForegroundColor Cyan
    Write-Host "  Message = $Message"
    Write-Host "  Force   = $Force"

    # 模拟一些操作
    if ($Force) {
        Write-Host "强制模式已开启，执行特殊操作..." -ForegroundColor Yellow
    } else {
        Write-Host "普通模式执行完成。" -ForegroundColor Gray
    }

    # 测试退出码：如果 Message 包含 "error"（不区分大小写），则返回非零退出码
    if ($Message -match "error") {
        Write-Host "❌ 检测到错误指示，脚本将返回退出码 1" -ForegroundColor Red
        exit 1
    }

    exit 0
}