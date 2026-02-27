# .\Windows\Win_tools\clean_image.ps1
# 包含 clean-image 子命令的具体实现，被 tool_ 函数调用

function Invoke-CleanImage {
    <#
    .SYNOPSIS
        清理指定目录下 Markdown 文档中未被引用的图片资源
    .PARAMETER Path
        要清理的目录路径（默认当前目录）
    #>
    param(
        [string]$Path = "."
    )

    try {
        # 验证路径是否存在
        if (-not (Test-Path $Path)) {
            throw "路径不存在: $Path"
        }
        # 转换为绝对路径
        $targetPath = Resolve-Path $Path

        # 获取当前脚本所在目录（Clean-Image.ps1 所在目录）
        $scriptDir = $PSScriptRoot
        # 假设 _tools 目录在上一级（根据原脚本逻辑）
        $toolsPath = Join-Path $scriptDir "../../_tools"
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
        # 直接调用，捕获退出代码
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