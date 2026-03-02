# .\Windows\Win_tools\win_tools.ps1
# 工具方法集:
#   1. build-lite: 打包 KRPA Lite
#   2. clean-image: 清理 Markdown 文档中未引用的图片
#   3. license-lite: 打开 Lite 授权工具
#   4. license-rpa: 打开 RPA 授权工具

function tool_ {
    <#
    .SYNOPSIS
        多功能工具函数，支持打包、清理图片、生成别名、打开授权工具等操作。
    .DESCRIPTION
        根据第一个参数 $action 执行不同任务。详细用法见 default 分支的帮助信息。
    .PARAMETER action
        要执行的操作，可选值：build-lite, clean-image, lite_alias, license-lite, license-rpa。
    .PARAMETER path
        根据 action 不同含义不同：对于 clean-image 为要清理的目录路径（默认当前目录）；
        对于 lite_alias 为要转换的输入字符串（必填）。
    .PARAMETER root
        仅用于 license-lite，表示传递特殊参数启动程序。
    .EXAMPLE
        tool_ build-lite
        执行打包 Lite 的完整流程。
    .EXAMPLE
        tool_ clean-image "D:\docs"
        清理指定目录下 Markdown 文档中未引用的图片。
    .EXAMPLE
        tool_ lite_alias "Data.ExtractContentFromTextV4"
        将字符串转换为 RPA 别名 JSON 片段并复制到剪贴板。
    .EXAMPLE
        tool_ license-lite -root
        以 root 模式打开 Lite 授权工具，密码仍为普通密码。
    .EXAMPLE
        tool_ license-rpa
        打开 RPA 授权工具，密码自动复制。
    #>
    param (
        [Parameter(Position = 0)]
        [ArgumentCompleter({
            param ($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
            $validActions = @('build-lite','clean-image','license-lite','license-rpa', 'set_lite_alias')
            $validActions -like "$wordToComplete*"
        })]
        [string]$action,

        [Parameter(Position = 1, Mandatory = $false)]
        [string]$path = ".",  # 默认当前目录

        [switch]$root,  # 仅用于 license-lite

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$extraArgs   # 捕获所有剩余参数
    )

    # 内部辅助函数：复制文本到剪贴板
    function Copy-ToClipboardInternal {
        param([string]$Text)
        try {
            if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
                $Text | Set-Clipboard
            } else {
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.Clipboard]::SetText($Text)
            }
            Write-Host "已复制到剪贴板" -ForegroundColor Green
        } catch {
            Write-Warning "无法复制到剪贴板，请手动复制。"
        }
    }

    # 基础路径配置（可根据需要改为从配置文件或环境变量读取）
    $aomRoot = "D:\Code\aom"
    $buildExe = Join-Path $aomRoot "KingAutomate\Build\Build\Build.exe"
    $liteLicenseExe = Join-Path $aomRoot "KingAutomate\Licenses\LiteLicense\LiteLicense.exe"
    $rpaLicenseExe = Join-Path $aomRoot "Tools\LicensesMake\LicensesMake.exe"

    switch ($action) {
        "build-lite" {
            # 点源外部脚本（假设与主脚本在同一目录）
            $buildScriptPath = Join-Path $PSScriptRoot "build_lite.ps1"
            if (Test-Path $buildScriptPath) {
                . $buildScriptPath   # 点源，将函数加载到当前作用域
                Invoke-BuildLite     # 调用函数
            } else {
                Write-Error "找不到 build-lite 脚本: $buildScriptPath"
            }
        }

        "clean-image" {
            $cleanScriptPath = Join-Path $PSScriptRoot "clean-image.ps1"
            if (Test-Path $cleanScriptPath) {
                . $cleanScriptPath          # 点源加载函数
                Invoke-CleanImage -Path $path   # 调用函数，传入参数
            } else {
                Write-Error "找不到 clean-image 脚本: $cleanScriptPath"
            }
        }

        "license-lite" {
            $licenseLiteScriptPath = Join-Path $PSScriptRoot "license-lite.ps1"
            if (Test-Path $licenseLiteScriptPath) {
                . $licenseLiteScriptPath                     # 点源加载函数
                Invoke-LicenseLite -Root:$root -ExePath $liteLicenseExe
            } else {
                Write-Error "找不到 license-lite 脚本: $licenseLiteScriptPath"
            }
        }

        "license-rpa" {
            $licenseRpaScriptPath = Join-Path $PSScriptRoot "license-rpa.ps1"
            if (Test-Path $licenseRpaScriptPath) {
                . $licenseRpaScriptPath                     # 点源加载函数
                Invoke-LicenseRpa -ExePath $rpaLicenseExe   # 调用函数，传入路径
            } else {
                Write-Error "找不到 license-rpa 脚本: $licenseRpaScriptPath"
            }
        }

        "set_lite_alias" {
            # 当输入 tool_ set_lite_alias 时，将调起 set_lite_alias.py
            $pythonScript = Join-Path $PSScriptRoot "set_lite_alias.py"
            if (Test-Path $pythonScript) {
                python $pythonScript
            } else {
                Write-Error "找不到 set_lite_alias.py 脚本: $pythonScript"
            }
        }

        default {
            Write-Host "使用方法:" -ForegroundColor Blue
            Write-Host "  build-lite                     # 打包 KRPA Lite" -ForegroundColor Yellow
            Write-Host "  clean-image [路径]             # 清理指定路径下md文档中没有被引用的图片资源" -ForegroundColor Yellow
            Write-Host "                                 # 默认路径为当前目录" -ForegroundColor Yellow
            Write-Host "  license-lite [-root]           # 打开 Lite 授权工具，-root 时传递 'kingauto' 参数（密码仍为普通密码）" -ForegroundColor Yellow
            Write-Host "  license-rpa                    # 打开 RPA 授权工具" -ForegroundColor Yellow
            Write-Host "  setLiteAlias                   # 设置 lite 内置函数的别名" -ForegroundColor Yellow
        }
    }
}