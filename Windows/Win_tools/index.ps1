# .\Windows\Win_tools\win_tools.ps1
# 工具方法集:
#   1. build-lite: 打包 KRPA Lite
#   2. clean-image: 清理 Markdown 文档中未引用的图片
#   3. license-lite: 打开 Lite 授权工具并自动输入机器标识生成授权码
#   4. license-rpa: 打开 RPA 授权工具
#   5. set_lite_alias: 设置 lite 内置函数的别名

function tool_ {
    <#
    .SYNOPSIS
        多功能工具函数，支持打包、清理图片、生成别名、打开授权工具等操作。
    .PARAMETER action
        要执行的操作，可选值：build-lite, clean-image, license-lite, license-rpa, set_lite_alias, build_lite_setup。
    .PARAMETER root
        仅用于 license-lite，表示传递特殊参数启动程序。
    .PARAMETER extraArgs
        剩余参数，根据 action 不同含义不同。
    .EXAMPLE
        tool_ build-lite
    .EXAMPLE
        tool_ build_lite_setup bbm      # 运行 build_lite_setup.py bbm
    .EXAMPLE
        tool_ clean-image "D:\docs"
    .EXAMPLE
        tool_ license-lite U0E7B758E3C8D8C94070822D055FA2ED3
    .EXAMPLE
        tool_ license-lite -root U0E7B758E3C8D8C94070822D055FA2ED3
    .EXAMPLE
        tool_ license-rpa
    .EXAMPLE
        tool_ set_lite_alias
    .EXAMPLE
        tool_ build_lite_setup          # 运行 build_lite_setup.py，默认参数 "K-RPA Lite"
    #>
    param (
        [Parameter(Position = 0, Mandatory = $true)]
        [ArgumentCompleter({
            param ($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
            $validActions = @('build-lite','build_lite_setup','clean-image','license-lite','license-rpa', 'set_lite_alias', 'file_tree')
            $validActions -like "$wordToComplete*"
        })]
        [string]$action,

        [switch]$root,  # 仅用于 license-lite

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$extraArgs   # 捕获所有剩余参数
    )

    # 基础路径配置
    $aomRoot = "D:\Code\aom"
    $buildExe = Join-Path $aomRoot "KingAutomate\Build\Build\Build.exe"
    $liteLicenseExe = Join-Path $aomRoot "KingAutomate\Licenses\LiteLicense\LiteLicense.exe"
    $rpaLicenseExe = Join-Path $aomRoot "Tools\LicensesMake\LicensesMake.exe"

    switch ($action) {
        "build-lite" {
            $pythonScript = Join-Path $PSScriptRoot "\src\build_lite.py"
            if (Test-Path $pythonScript) {
                Write-Host "正在调用 Python 构建脚本..." -ForegroundColor Cyan
                & python $pythonScript
                
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "构建失败，退出代码: $LASTEXITCODE"
                } else {
                    Write-Host "构建完成！" -ForegroundColor Green
                }
            } else {
                Write-Error "找不到 build_lite.py 脚本: $pythonScript"
            }
        }

        "clean-image" {
            $targetPath = if ($extraArgs -and $extraArgs.Count -gt 0) { $extraArgs[0] } else { "." }
            $cleanScriptPath = Join-Path $PSScriptRoot "\src\clean-image.ps1"
            if (Test-Path $cleanScriptPath) {
                . $cleanScriptPath
                Invoke-CleanImage -Path $targetPath
            } else {
                Write-Error "找不到 clean-image 脚本: $cleanScriptPath"
            }
        }

        "license-lite" {
            $pythonScript = Join-Path $PSScriptRoot "\src\license_lite.py"
            if (-not (Test-Path $pythonScript)) {
                Write-Error "找不到 license_lite.py 脚本: $pythonScript"
                return
            }

            # 从 extraArgs 获取机器标识
            $machineId = $null
            if ($extraArgs -and $extraArgs.Count -gt 0) {
                $machineId = $extraArgs[0]
            } else {
                Write-Host "错误: 必须提供机器标识参数。" -ForegroundColor Red
                Write-Host "用法: tool_ license-lite [-root] <机器标识>" -ForegroundColor Yellow
                return
            }

            # 构建 python 参数
            $pythonArgs = @()
            if ($root) {
                $pythonArgs += "--root"
            }
            $pythonArgs += $machineId

            # 调试输出（可选）
            Write-Host "执行命令: python $pythonScript $($pythonArgs -join ' ')" -ForegroundColor Cyan

            # 调用 python 脚本，使用 splatting 确保参数正确传递
            & python $pythonScript @pythonArgs
        }

        "license-rpa" {
            $licenseRpaScriptPath = Join-Path $PSScriptRoot "\src\license-rpa.ps1"
            if (Test-Path $licenseRpaScriptPath) {
                . $licenseRpaScriptPath
                Invoke-LicenseRpa -ExePath $rpaLicenseExe
            } else {
                Write-Error "找不到 license-rpa 脚本: $licenseRpaScriptPath"
            }
        }

        "set_lite_alias" {
            $pythonScript = Join-Path $PSScriptRoot "\src\set_lite_alias.py"
            if (Test-Path $pythonScript) {
                python $pythonScript
            } else {
                Write-Error "找不到 set_lite_alias.py 脚本: $pythonScript" 
            }
        }

        # 新增：直接调用 build_lite_setup.py
        "build_lite_setup" {
            $pythonScript = Join-Path $PSScriptRoot "\src\build_lite_setup.py"
            if (-not (Test-Path $pythonScript)) {
                Write-Error "找不到 build_lite_setup.py 脚本: $pythonScript"
                return
            }

            if ($extraArgs -and $extraArgs.Count -gt 0) {
                # 用户提供了参数（可能是多个），直接通过 @extraArgs 传递
                Write-Host "执行命令: python $pythonScript $($extraArgs -join ' ')" -ForegroundColor Cyan
                & python $pythonScript @extraArgs
            } else {
                # 无参数，使用默认值 "K-RPA Lite" 作为单一参数
                Write-Host "执行命令: python $pythonScript \"K-RPA Lite\"" -ForegroundColor Cyan
                & python $pythonScript "K-RPA Lite"
            }
        }

        default {
            Write-Host "使用方法:" -ForegroundColor Blue
            Write-Host "  build-lite                     # 打包 KRPA Lite" -ForegroundColor Yellow
            Write-Host "  build_lite_setup [参数]        # 直接运行 build_lite_setup.py，无参数时默认传入 'K-RPA Lite'" -ForegroundColor Yellow
            Write-Host "  clean-image [路径]             # 清理指定路径下md文档中没有被引用的图片资源" -ForegroundColor Yellow
            Write-Host "                                 # 默认路径为当前目录" -ForegroundColor Yellow
            Write-Host "  license-lite [-root] <机器标识> # 打开 Lite 授权工具并自动完成机器标识输入、生成授权码" -ForegroundColor Yellow
            Write-Host "  license-rpa                    # 打开 RPA 授权工具" -ForegroundColor Yellow
            Write-Host "  set_lite_alias                 # 设置 lite 内置函数的别名" -ForegroundColor Yellow
        }
    }
}
