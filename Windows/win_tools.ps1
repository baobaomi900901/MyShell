function tool_ {
    param (
        [Parameter(Position = 0)]
        [ArgumentCompleter({
            param ($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
            $validActions = @('build-lite','clean-image','lite_alias','license-lite','license-rpa')
            $validActions -like "$wordToComplete*"
        })]
        [string]$action,

        [Parameter(Position = 1, Mandatory = $false)]
        [string]$path = ".",  # 默认当前目录

        [switch]$root  # 仅用于 license-lite
    )

    switch ($action) {
        "build-lite" {
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
        "clean-image" {
            try {
                # 将相对路径转换为绝对路径
                $targetPath = Convert-Path $path
                
                # 找到脚本路径
                $scriptPath = $PSScriptRoot
                $toolsPath = Join-Path $scriptPath "../_tools"
                $nodeScriptPath = Join-Path $toolsPath "cleanUnusedImages.js"

                # 检查Node.js脚本是否存在
                if (-not (Test-Path $nodeScriptPath)) {
                    Write-Host "找不到 cleanUnusedImages.js 脚本: $nodeScriptPath" -ForegroundColor Red
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
        "lite_alias" {
            try {
                if ([string]::IsNullOrWhiteSpace($path) -or $path -eq ".") {
                    Write-Host "请提供要转换的字符串，例如: tool_ lite_alias Data.ExtractContentFromTextV4" -ForegroundColor Yellow
                    return
                }

                $inputString = $path
                
                # 转换规则：
                # 1. 添加前缀 "RPA"
                # 2. 去掉所有点（.）
                # 3. 去掉最后的版本号（V后跟数字，不区分大小写）
                
                # 步骤1: 去掉点号
                $step1 = $inputString -replace '\.', ''
                
                # 步骤2: 去掉最后的版本号（V/v后跟数字，如V4、v2等）
                $step2 = $step1 -replace '[Vv]\d+$', ''
                
                # 步骤3: 添加前缀 "RPA"
                $result = "RPA" + $step2
                
                # 创建输出字符串（适合嵌入到现有JSON中的格式）
                $outputText = @"
    "$result":  {
        "alias":  []
    }
"@
                
                Write-Host "`n输出JSON的格式:" -ForegroundColor Cyan
                Write-Host $outputText -ForegroundColor Green
                
                # 尝试复制到剪贴板
                try {
                    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
                        $outputText | Set-Clipboard
                        Write-Host "嵌入格式已复制到剪贴板" -ForegroundColor Green
                    }
                    elseif ([System.Windows.Forms.Clipboard]::GetText) {
                        Add-Type -AssemblyName System.Windows.Forms
                        [System.Windows.Forms.Clipboard]::SetText($outputText)
                        Write-Host "嵌入格式已复制到剪贴板" -ForegroundColor Green
                    }
                }
                catch {
                    Write-Host "无法复制到剪贴板，请手动复制结果" -ForegroundColor Yellow
                }
            }
            catch {
                Write-Error $_
            }
        }
        "license-lite" {
            # 处理 lite 授权工具（路径硬编码）
            $targetPath = "D:\Code\aom\KingAutomate\Licenses\LiteLicense\LiteLicense.exe"
            
            if (-not (Test-Path $targetPath)) {
                Write-Host "错误: 文件不存在 - $targetPath" -ForegroundColor Red
                return
            }

            if ($root) {
                # 从密码文件中读取 lite-forever 密码
                $passwordFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\password.json"
                if (-not (Test-Path $passwordFile)) {
                    Write-Host "错误: 密码文件不存在 - $passwordFile" -ForegroundColor Red
                    Write-Host "请创建该文件并添加 'lite-forever' 密码后再使用 -root 参数。" -ForegroundColor Yellow
                    return
                }
                
                try {
                    $passwordConfig = Get-Content $passwordFile -Raw | ConvertFrom-Json
                } catch {
                    Write-Host "错误: 密码文件格式错误，请检查 JSON 语法。" -ForegroundColor Red
                    return
                }

                $liteForever = $passwordConfig.'lite-forever'
                if (-not $liteForever -or [string]::IsNullOrEmpty($liteForever.password)) {
                    Write-Host "错误: 密码文件中未找到 'lite-forever' 的有效密码。" -ForegroundColor Red
                    Write-Host "请确保文件包含以下结构：" -ForegroundColor Yellow
                    Write-Host '{' -ForegroundColor Yellow
                    Write-Host '  "lite-forever": {' -ForegroundColor Yellow
                    Write-Host '    "password": "your_password",' -ForegroundColor Yellow
                    Write-Host '    "description": "lite永久授权"' -ForegroundColor Yellow
                    Write-Host '  }' -ForegroundColor Yellow
                    Write-Host '}' -ForegroundColor Yellow
                    return
                }

                $password = $liteForever.password
                & $targetPath "kingauto"
                Set-Clipboard -Value $password
                Write-Host "已打开 LiteLicense（带参数），密码: $password (已复制)" -ForegroundColor Green
            } else {
                # 无 -root：使用原硬编码密码
                & $targetPath
                $password = "kingautomate"
                Set-Clipboard -Value $password
                Write-Host "已打开 LiteLicense，密码: $password (已复制)" -ForegroundColor Green
            }
        }
        "license-rpa" {
            # 处理 RPA 授权工具（路径硬编码）- 忽略 -root 参数，始终不带附加参数
            $targetPath = "D:\Code\aom\Tools\LicensesMake\LicensesMake.exe"
            if (Test-Path $targetPath) {
                & $targetPath   # 直接运行，不附加参数
                $password = "kingswarekcaom"
                Set-Clipboard -Value $password
                Write-Host "已打开 RPALicense，密码: $password (已复制)" -ForegroundColor Green
            } else {
                Write-Host "错误: 文件不存在 - $targetPath" -ForegroundColor Red
            }
        }
        default {
            Write-Host "使用方法:" -ForegroundColor Blue
            Write-Host "  build-lite                     # 打包 KRPA Lite" -ForegroundColor Yellow
            Write-Host "  clean-image [路径]             # 清理指定路径下md文档中没有被引用的图片资源" -ForegroundColor Yellow
            Write-Host "                                 # 默认路径为当前目录" -ForegroundColor Yellow
            Write-Host "  lite_alias <字符串>            # 转换字符串为RPA别名格式并生成适合嵌入JSON的格式" -ForegroundColor Yellow
            Write-Host "                                 # 示例: Data.ExtractContentFromTextV4" -ForegroundColor Yellow
            Write-Host "                                 # 输出:" -ForegroundColor DarkGray
            Write-Host '                                 #     "RPADataExtractContentFromText":  {' -ForegroundColor DarkGray
            Write-Host '                                 #         "alias":  []' -ForegroundColor DarkGray
            Write-Host '                                 #     }' -ForegroundColor DarkGray
            Write-Host "  license-lite [-root]           # 打开 Lite 授权工具，-root 时从密码文件读取 'lite-forever' 密码并传递参数" -ForegroundColor Yellow
            Write-Host "  license-rpa                    # 打开 RPA 授权工具" -ForegroundColor Yellow
        }
    }
}