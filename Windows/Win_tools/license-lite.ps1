# .\Windows\Win_tools\license-lite.ps1
# 打开 Lite 授权工具，并可选择传递特殊参数

function Invoke-LicenseLite {
    <#
    .SYNOPSIS
        打开 Lite 授权工具，并复制密码到剪贴板
    .PARAMETER Root
        若指定，则传递 "kingauto" 参数启动程序（需验证密码文件中的 lite-forever 密码）
    .PARAMETER ExePath
        LiteLicense.exe 的完整路径，若不提供则使用默认路径 D:\Code\aom\KingAutomate\Licenses\LiteLicense\LiteLicense.exe
    #>
    [CmdletBinding()]
    param(
        [switch]$Root,
        [string]$ExePath
    )

    try {
        # 如果未提供 ExePath，使用默认路径（基于约定）
        if (-not $ExePath) {
            $aomRoot = "D:\Code\aom"
            $ExePath = Join-Path $aomRoot "KingAutomate\Licenses\LiteLicense\LiteLicense.exe"
        }

        if (-not (Test-Path $ExePath)) {
            throw "文件不存在: $ExePath"
        }

        if ($Root) {
            # 使用相对路径定位密码文件
            $passwordFile = Join-Path $PSScriptRoot "../../config/password.json"
            # 尝试解析为绝对路径（如果文件存在）
            $resolvedPath = Resolve-Path $passwordFile -ErrorAction SilentlyContinue
            if ($resolvedPath) {
                $passwordFile = $resolvedPath.Path
            } else {
                Write-Host "错误: 密码文件不存在，尝试路径: $passwordFile" -ForegroundColor Red
                Write-Host "请确保文件位于 MyShell/config/password.json" -ForegroundColor Yellow
                return
            }

            if (-not (Test-Path $passwordFile)) {
                Write-Host "错误: 密码文件不存在 - $passwordFile" -ForegroundColor Red
                Write-Host "请创建该文件并添加 'lite-forever' 密码后再使用 -Root 参数。" -ForegroundColor Yellow
                return
            }
            try {
                $passwordConfig = Get-Content $passwordFile -Raw | ConvertFrom-Json
            } catch {
                throw "密码文件格式错误，请检查 JSON 语法。"
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
            # 密码验证通过，启动程序并传递参数
            & $ExePath "kingauto"
            if ($LASTEXITCODE -ne 0) {
                throw "LiteLicense 执行失败，退出代码: $LASTEXITCODE"
            }
        } else {
            & $ExePath
            if ($LASTEXITCODE -ne 0) {
                throw "LiteLicense 执行失败，退出代码: $LASTEXITCODE"
            }
        }

        # 无论是否带 -Root，复制到剪贴板的密码都是 kingautomate
        $password = "kingautomate"
        Copy-LicenseToClipboard -Text $password
        Write-Host "已打开 LiteLicense，密码: $password" -ForegroundColor Green
    }
    catch {
        Write-Error $_
    }
}

# 内部辅助函数：复制文本到剪贴板
function Copy-LicenseToClipboard {
    param([string]$Text)
    try {
        if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
            $Text | Set-Clipboard
        } else {
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.Clipboard]::SetText($Text)
        }
        Write-Host "密码已复制到剪贴板" -ForegroundColor Green
    } catch {
        Write-Warning "无法复制到剪贴板，请手动复制密码: $Text"
    }
}

# 如果脚本被直接执行，则调用函数（方便单独测试）
if ($MyInvocation.InvocationName -ne '.') {
    $rootParam = $false
    $exePath = $null
    # 简单解析参数：若第一个参数是 "-root" 或 "/root"，则设置 $rootParam 为 true，并可能还有第二个参数作为路径
    if ($args.Count -gt 0) {
        if ($args[0] -match '^-root$|^/root$') {
            $rootParam = $true
            if ($args.Count -gt 1) {
                $exePath = $args[1]
            }
        } else {
            $exePath = $args[0]
        }
    }
    Invoke-LicenseLite -Root:$rootParam -ExePath $exePath
}