# .\Windows\Win_tools\license-rpa.ps1
# 打开 RPA 授权工具，并复制密码到剪贴板

function Invoke-LicenseRpa {
    <#
    .SYNOPSIS
        打开 RPA 授权工具，并复制密码到剪贴板
    .PARAMETER ExePath
        LicensesMake.exe 的完整路径，若不提供则使用默认路径 D:\Code\aom\Tools\LicensesMake\LicensesMake.exe
    #>
    [CmdletBinding()]
    param(
        [string]$ExePath
    )

    try {
        # 如果未提供 ExePath，使用默认路径（基于约定）
        if (-not $ExePath) {
            $aomRoot = "D:\Code\aom"
            $ExePath = Join-Path $aomRoot "Tools\LicensesMake\LicensesMake.exe"
        }

        if (-not (Test-Path $ExePath)) {
            throw "文件不存在: $ExePath"
        }

        & $ExePath
        if ($LASTEXITCODE -ne 0) {
            throw "RPALicense 执行失败，退出代码: $LASTEXITCODE"
        }

        $password = "kingswarekcaom"
        Copy-LicenseRpaToClipboard -Text $password
        Write-Host "已打开 RPALicense，密码: $password" -ForegroundColor Green
    }
    catch {
        Write-Error $_
    }
}

# 内部辅助函数：复制文本到剪贴板
function Copy-LicenseRpaToClipboard {
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
    $exePath = $null
    if ($args.Count -gt 0) {
        $exePath = $args[0]
    }
    Invoke-LicenseRpa -ExePath $exePath
}