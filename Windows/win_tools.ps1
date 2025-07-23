function tools_ {
    param (
        [Parameter(Position = 0)]
        [ArgumentCompleter({
            param ($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
            $validActions = @('buildlite')
            $validActions -like "$wordToComplete*"
        })]
        [string]$action
    )

    switch ($action) {
        "buildlite" {
            try {
                # 1. 切换到 aom 目录
                Write-Host "正在切换到 aom 目录..." -ForegroundColor Cyan
                cd_ aom
                if (-not $?) { throw "cd_aom 执行失败" }

                # 2. 执行 git 重置
                Write-Host "正在重置 git 仓库..." -ForegroundColor Cyan
                greset all
                if (-not $?) { throw "greset all 执行失败" }

                # 3. 执行 git pull --rebase
                Write-Host "正在更新代码(git pull --rebase)..." -ForegroundColor Cyan
                git pull --rebase
                if (-not $?) { throw "git pull --rebase 执行失败" }

                # 4. 执行 Build.exe
                $buildPath = "D:\Code\aom\KingAutomate\Build\Build\Build.exe"
                if (Test-Path $buildPath) {
                    Write-Host "正在运行 Build.exe..." -ForegroundColor Cyan
                    & $buildPath
                    if (-not $?) { throw "Build.exe 执行失败" }
                } else {
                    throw "找不到 Build.exe，路径: $buildPath"
                }

                Write-Host "所有操作成功完成！" -ForegroundColor Green
            }
            catch {
                Write-Error $_
                return
            }
        }
        default {
            Write-Host "使用方法:" -ForegroundColor Blue
            Write-Host "  buildlite      # 打包 KRPA Lite" -ForegroundColor Yellow
        }
    }

}