# .\Windows\Win_tools\lite_alias.ps1
# 将输入字符串转换为 RPA 别名 JSON 片段，并复制到剪贴板

function Invoke-LiteAlias {
    <#
    .SYNOPSIS
        将字符串转换为 RPA 别名格式，生成适合嵌入 JSON 的片段并复制到剪贴板
    .PARAMETER InputString
        要转换的原始字符串，例如 "Data.ExtractContentFromTextV4"
    .EXAMPLE
        Invoke-LiteAlias -InputString "Data.ExtractContentFromTextV4"
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$InputString
    )

    try {
        # 转换规则：
        # 1. 添加前缀 "RPA"
        # 2. 去掉所有点（.）
        # 3. 去掉最后的版本号（V后跟数字，不区分大小写，如 V4、v12 等，支持小数点如 V4.1）

        # 去掉点号
        $noDots = $InputString -replace '\.', ''

        # 去掉末尾的版本号（支持 V4、V4.1、v2.0 等）
        $noVersion = $noDots -replace '[Vv]\d+(\.\d+)*$', ''

        # 添加前缀
        $aliasKey = "RPA" + $noVersion

        # 动态生成 JSON 片段
        $jsonObject = @{
            $aliasKey = @{
                alias = @()
            }
        }
        # 转换为带缩进的 JSON 字符串（8 空格缩进，与原输出一致）
        $jsonFragment = ($jsonObject | ConvertTo-Json -Depth 2) -replace '(?m)^', (' ' * 8)

        Write-Host "`n输出JSON的格式:" -ForegroundColor Cyan
        Write-Host $jsonFragment -ForegroundColor Green

        # 复制到剪贴板（内部辅助函数）
        Copy-LiteAliasToClipboard -Text $jsonFragment
    }
    catch {
        Write-Error $_
    }
}

# 内部辅助函数：复制文本到剪贴板
function Copy-LiteAliasToClipboard {
    param([string]$Text)
    try {
        if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
            $Text | Set-Clipboard
        } else {
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.Clipboard]::SetText($Text)
        }
        Write-Host "嵌入格式已复制到剪贴板" -ForegroundColor Green
    } catch {
        Write-Warning "无法复制到剪贴板，请手动复制。"
    }
}

# 如果脚本被直接执行，则调用函数（方便单独测试）
if ($MyInvocation.InvocationName -ne '.') {
    if ($args.Count -gt 0) {
        Invoke-LiteAlias -InputString $args[0]
    } else {
        Write-Host "请提供要转换的字符串，例如: .\lite_alias.ps1 Data.ExtractContentFromTextV4" -ForegroundColor Yellow
    }
}