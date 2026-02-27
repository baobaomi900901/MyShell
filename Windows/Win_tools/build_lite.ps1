# .\Windows\Win_tools\build_lite.ps1
# 包含 build-lite 子命令的具体实现，被 tool_ 函数调用

function Invoke-BuildLite {
    <#
    .SYNOPSIS
        执行 KRPA Lite 打包流程
    .DESCRIPTION
        切换到 aom 目录，重置 git，拉取最新代码，然后运行 Build.exe
    #>
    try {
        # 基础路径配置（可从外部传入，这里直接定义）
        $aomRoot = "D:\Code\aom"
        $buildExe = Join-Path $aomRoot "KingAutomate\Build\Build\Build.exe"

        # 1. 切换到 aom 目录（假设 cd_ 是自定义命令，需确保存在）
        Write-Host "正在切换到 aom 目录..." -ForegroundColor Cyan
        cd_ aom
        if (-not $?) { throw "cd_ aom 执行失败" }

        # 2. 执行 git 重置（假设 greset 是自定义命令）
        Write-Host "正在重置 git 仓库..." -ForegroundColor Cyan
        greset all
        if (-not $?) { throw "greset all 执行失败" }

        # 3. 执行 git pull --rebase
        Write-Host "正在更新代码(git pull --rebase)..." -ForegroundColor Cyan
        git pull --rebase
        if ($LASTEXITCODE -ne 0) { throw "git pull --rebase 执行失败" }

        # 4. 执行 Build.exe
        if (Test-Path $buildExe) {
            Write-Host "正在运行 Build.exe..." -ForegroundColor Cyan
            & $buildExe
            if ($LASTEXITCODE -ne 0) { throw "Build.exe 执行失败，退出代码: $LASTEXITCODE" }
        } else {
            throw "找不到 Build.exe，路径: $buildExe"
        }

        Write-Host "所有操作成功完成！" -ForegroundColor Green
    }
    catch {
        Write-Error $_
    }
}

# 如果脚本被直接执行，则调用函数（可选，方便单独测试）
if ($MyInvocation.InvocationName -ne '.') {
    Invoke-BuildLite
}