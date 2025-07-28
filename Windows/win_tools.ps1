function tool_ {
    param (
        [Parameter(Position = 0)]
        [ArgumentCompleter({
            param ($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
            $validActions = @('buildlite','cleanimage')
            $validActions -like "$wordToComplete*"
        })]
        [string]$action,

        [Parameter(Position = 1, Mandatory = $false)]
        [string]$path = "."  # 默认当前目录
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
        "cleanimage" {
            try {
                # 将相对路径转换为绝对路径
                $targetPath = Convert-Path $path
                
                # 1. 打印目标路径
                # Write-Host "目标清理路径: $targetPath" -ForegroundColor Cyan
                # 2. 打印当前脚本所在路径
                $scriptPath = $PSScriptRoot
                # Write-Host "当前脚本所在路径: $scriptPath" -ForegroundColor Cyan
                # 3. 找到脚本路径
                $toolsPath = Join-Path $scriptPath "../_tools"
                $nodeScriptPath = Join-Path $toolsPath "filterUnusedImages.js"
                # Write-Host "cleanimage脚本所在路径: $nodeScriptPath" -ForegroundColor Cyan

                # 检查Node.js脚本是否存在
                if (-not (Test-Path $nodeScriptPath)) {
                    Write-Host "找不到 filterUnusedImages.js 脚本: $nodeScriptPath" -ForegroundColor Red
                    return
                }

                # 检查Node.js
                try {
                    $nodeVersion = node -v
                    Write-Host "检测到Node.js版本: $nodeVersion" -ForegroundColor Cyan
                } catch {
                    Write-Host "未检测到Node.js，请先安装Node.js" -ForegroundColor Red
                    return
                }

                # 修正参数传递方式
                $arguments = @(
                    $nodeScriptPath,
                    "`"$targetPath`""  # 传递转换后的绝对路径
                )
                
                Write-Host "执行命令: node $arguments"

                # 使用Start-Process确保参数正确传递
                $process = Start-Process -FilePath "node" -ArgumentList $arguments -NoNewWindow -Wait -PassThru
                    
                if ($process.ExitCode -eq 0) {
                    Write-Host "图片清理脚本执行结束" -ForegroundColor Green
                } else {
                    Write-Host "图片清理脚本执行失败 (退出代码: $($process.ExitCode))" -ForegroundColor Red
                }
            }
            catch {
                Write-Error $_
            }
        }
        default {
            Write-Host "使用方法:" -ForegroundColor Blue
            Write-Host "  buildlite      # 打包 KRPA Lite" -ForegroundColor Yellow
            Write-Host "  cleanimage [路径] # 清理指定路径下md文档中没有被引用的图片资源" -ForegroundColor Yellow
            Write-Host "                # 默认路径为当前目录" -ForegroundColor Yellow
        }
    }
}