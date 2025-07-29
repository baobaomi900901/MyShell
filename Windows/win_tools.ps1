function tool_ {
    param (
        [Parameter(Position = 0)]
        [ArgumentCompleter({
            param ($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
            $validActions = @('build-lite','clean-image')
            $validActions -like "$wordToComplete*"
        })]
        [ValidateSet('build-lite', 'clean-image')]
        [string]$action,

        [Parameter(Position = 1, Mandatory = $false)]
        [ValidateScript({
            if (-not (Test-Path $_)) { throw "路径 $_ 不存在" }
            return $true
        })]
        [string]$path = "."  # 默认当前目录
    )

    begin {
        # 公共变量和初始化代码可以放在这里
        $ErrorActionPreference = 'Stop'
    }

    process {
        switch ($action) {
            "build-lite" { BuildLite }
            "clean-image" { CleanImage -path $path }
            default { ShowUsage }
        }
    }
}

function BuildLite {
    try {
        Write-Host "`n=== 开始构建 KRPA Lite ===`n" -ForegroundColor Cyan

        # 1. 切换到 aom 目录
        Write-Progress -Activity "构建流程" -Status "切换到 aom 目录"
        Write-Host "[1/4] 正在切换到 aom 目录..." -ForegroundColor Cyan
        cd_ aom
        if (-not $?) { throw "cd_aom 执行失败" }

        # 2. 执行 git 重置
        Write-Progress -Activity "构建流程" -Status "重置 git 仓库"
        Write-Host "[2/4] 正在重置 git 仓库..." -ForegroundColor Cyan
        greset all
        if (-not $?) { throw "greset all 执行失败" }

        # 3. 执行 git pull --rebase
        Write-Progress -Activity "构建流程" -Status "更新代码"
        Write-Host "[3/4] 正在更新代码(git pull --rebase)..." -ForegroundColor Cyan
        git pull --rebase
        if (-not $?) { throw "git pull --rebase 执行失败" }

        # 4. 执行 Build.exe
        $buildPath = "D:\Code\aom\KingAutomate\Build\Build\Build.exe"
        if (Test-Path $buildPath) {
            Write-Progress -Activity "构建流程" -Status "运行 Build.exe"
            Write-Host "[4/4] 正在运行 Build.exe..." -ForegroundColor Cyan
            & $buildPath
            if (-not $?) { throw "Build.exe 执行失败" }
        } else {
            throw "找不到 Build.exe，路径: $buildPath"
        }

        Write-Host "`n=== 所有操作成功完成！ ===`n" -ForegroundColor Green
    }
    catch {
        Write-Host "`n=== 构建过程中发生错误 ===`n" -ForegroundColor Red
        Write-Error $_
        return
    }
    finally {
        Write-Progress -Activity "构建流程" -Completed
    }
}

function CleanImage {
    param (
        [string]$path
    )
    
    try {
        Write-Host "`n=== 开始清理未使用的图片 ===`n" -ForegroundColor Cyan

        # 将相对路径转换为绝对路径
        $targetPath = Convert-Path $path
        
        # 1. 检查Node.js环境
        Write-Progress -Activity "清理图片" -Status "检查环境"
        try {
            $nodeVersion = node -v
            Write-Host "[1/3] 检测到Node.js版本: $nodeVersion" -ForegroundColor Cyan
        } catch {
            throw "未检测到Node.js，请先安装Node.js"
        }

        # 2. 找到脚本路径
        $scriptPath = $PSScriptRoot
        $toolsPath = Join-Path $scriptPath "../_tools"
        $nodeScriptPath = Join-Path $toolsPath "cleanUnusedImages.js"
        
        # 检查Node.js脚本是否存在
        if (-not (Test-Path $nodeScriptPath)) {
            throw "找不到 cleanUnusedImages.js 脚本: $nodeScriptPath"
        }

        # 3. 执行清理脚本
        Write-Progress -Activity "清理图片" -Status "执行清理脚本"
        Write-Host "[2/3] 正在执行清理脚本..." -ForegroundColor Cyan
        Write-Host "[3/3] 目标路径: $targetPath" -ForegroundColor Cyan
        
        $arguments = @(
            $nodeScriptPath,
            "`"$targetPath`""  # 传递转换后的绝对路径
        )
        
        Write-Host "执行命令: node $arguments" -ForegroundColor DarkGray

        $process = Start-Process -FilePath "node" -ArgumentList $arguments -NoNewWindow -Wait -PassThru -RedirectStandardOutput "output.log" -RedirectStandardError "error.log"
            
        if ($process.ExitCode -eq 0) {
            Write-Host "`n=== 图片清理完成 ===`n" -ForegroundColor Green
        } else {
            $errorContent = Get-Content "error.log" -ErrorAction SilentlyContinue
            throw "图片清理脚本执行失败 (退出代码: $($process.ExitCode))`n$errorContent"
        }
    }
    catch {
        Write-Host "`n=== 清理过程中发生错误 ===`n" -ForegroundColor Red
        Write-Error $_
    }
    finally {
        Remove-Item "output.log", "error.log" -ErrorAction SilentlyContinue
        Write-Progress -Activity "清理图片" -Completed
    }
}

function ShowUsage {
    Write-Host "`n使用方法:`n" -ForegroundColor Blue
    Write-Host "  tool_ build-lite                # 打包 KRPA Lite" -ForegroundColor Yellow
    Write-Host "  tool_ clean-image [路径:选填]    # 清理指定路径下md文档中没有被引用的图片资源" -ForegroundColor Yellow
    Write-Host "                                  # 默认路径为当前目录`n" -ForegroundColor Yellow
}