# .\Windows\Win_tools\clean_image.ps1
# 包含 clean-image 子命令的具体实现，被 tool_ 函数调用

function Invoke-CleanImage {
    param([string]$Path = ".")

    try {
        # 设置编码（必须在调用外部程序前设置）
        $OutputEncoding = [System.Text.Encoding]::UTF8
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

        # 验证路径
        if (-not (Test-Path $Path)) {
            throw "路径不存在: $Path"
        }
        $targetPath = Resolve-Path $Path

        # 定位 Node 脚本
        $scriptDir = $PSScriptRoot
        # 假设 public 目录在上一级（根据原脚本逻辑）
        $toolsPath = Join-Path $scriptDir "../../../public"
        $nodeScriptPath = Join-Path $toolsPath "cleanUnusedImages.js"

        if (-not (Test-Path $nodeScriptPath)) {
            throw "找不到 cleanUnusedImages.js 脚本: $nodeScriptPath"
        }

        # 检查 Node.js
        try {
            $nodeVersion = node -v
            Write-Host "检测到Node.js版本: $nodeVersion" -ForegroundColor Cyan
        } catch {
            throw "未检测到Node.js，请先安装Node.js"
        }

        Write-Host "执行命令: node `"$nodeScriptPath`" `"$targetPath`""
        & node $nodeScriptPath $targetPath
        if ($LASTEXITCODE -eq 0) {
            Write-Host "图片清理脚本执行成功" -ForegroundColor Green
        } else {
            throw "图片清理脚本执行失败 (退出代码: $LASTEXITCODE)"
        }
    }
    catch {
        Write-Error $_
    }
}

# 如果脚本被直接执行，则调用函数（方便单独测试）
if ($MyInvocation.InvocationName -ne '.') {
    $paramPath = if ($args.Count -gt 0) { $args[0] } else { "." }
    Invoke-CleanImage -Path $paramPath
}