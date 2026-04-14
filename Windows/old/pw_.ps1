# # .\Windows\MTPW\index.ps1
# # 查询密码到剪切板（无乱码版）

# function pw_ {
#     <#
#     .SYNOPSIS
#     快速查找并复制密码到剪贴板
#     .DESCRIPTION
#     从 JSON 配置文件中读取密码项，支持 Tab 补全。
#     .PARAMETER action
#     密码项的名称（如 lite-root）
#     .EXAMPLE
#     pw_ lite-root
#     复制 lite-root 的密码到剪贴板
#     #>
#     param (
#         [Parameter(Position = 0)]
#         [string]$action
#     )
    
#     # ---------- 编码修复：确保控制台使用 UTF-8 ----------
#     # 仅在 Windows 旧终端下尝试设置代码页为 UTF-8
#     if ($env:WT_SESSION -eq $null) {
#         try {
#             # 设置输出编码为 UTF-8
#             [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
#             $null = & chcp 65001 2>$null
#         } catch {
#             # 忽略错误（某些环境可能不允许修改）
#         }
#     }
    
#     # 定义安全输出函数（避免乱码）
#     function Write-SafeHost($message, $color = $null) {
#         if ($color) {
#             Write-Host $message -ForegroundColor $color
#         } else {
#             Write-Host $message
#         }
#     }
    
#     $configFile = Join-Path $env:MYSHELL "config\private\password.json"
#     if (-not (Test-Path $configFile)) {
#         Write-SafeHost "" 
#         Write-SafeHost "❌ 配置文件不存在: $configFile" -color Red
#         Write-SafeHost "请手动创建该文件，模板如下：" -color Yellow
#         Write-SafeHost @'
# {
#   "lite-root": {
#     "password": "12345678",
#     "description": "lite 服务器 root 密码"
#   }
# }
# '@ -color DarkGray
#         Write-SafeHost ""
#         return
#     }
    
#     # 读取配置文件（指定 UTF-8 编码）
#     try {
#         $raw = Get-Content -Path $configFile -Raw -Encoding UTF8
#         $config = $raw | ConvertFrom-Json
#     } catch {
#         Write-SafeHost "错误: 配置文件格式错误或编码不正确，请确保文件为 UTF-8 无 BOM 格式" -color Red
#         return
#     }
    
#     # 无参数：显示帮助（中文）
#     if (-not $action) {
#         Write-SafeHost "可选项:" -color Green
        
#         $hasItems = $false
#         $config.PSObject.Properties | ForEach-Object {
#             $key = $_.Name
#             $item = $_.Value
#             if ($item.password -and $item.password -ne $null) {
#                 $hasItems = $true
#                 Write-Host "  $key" -ForegroundColor Yellow -NoNewline
#                 Write-Host " - $($item.description)"
#             }
#         }
        
#         if (-not $hasItems) {
#             Write-SafeHost "  (未配置任何密码项)" -color Gray
#         }
        
#         Write-SafeHost ""
#         Write-SafeHost "示例:" -color Cyan
#         Write-SafeHost "  pw_ lite-root     # 复制密码到剪切板" -color White
        
#         return
#     }
    
#     # 查找密码项
#     if (-not $config.$action) {
#         Write-SafeHost "错误: 密码项 '$action' 不存在" -color Red
#         Write-SafeHost "使用 'pw_' 查看所有可用密码项" -color Yellow
#         return
#     }
    
#     $item = $config.$action
#     $password = $item.password
#     $description = $item.description
    
#     if (-not $password -or $password -eq $null) {
#         Write-SafeHost "错误: 密码项 '$action' 未配置密码" -color Red
#         return
#     }
    
#     # 复制到剪贴板
#     $copied = $false
#     $errorMsg = ""
    
#     # 方法1: 使用 Set-Clipboard (Windows PowerShell 5.1+)
#     if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
#         try {
#             Set-Clipboard -Value $password -ErrorAction Stop
#             $copied = $true
#         } catch {
#             $errorMsg = "Set-Clipboard 失败: $_"
#         }
#     }
    
#     # 方法2: 使用 .NET 剪贴板
#     if (-not $copied) {
#         try {
#             Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
#             [System.Windows.Forms.Clipboard]::SetText($password)
#             $copied = $true
#         } catch {
#             $errorMsg = "$errorMsg`n.NET 剪贴板失败: $_"
#         }
#     }
    
#     if ($copied) {
#         Write-SafeHost "✓ 复制 '$action' 密码到剪贴板" -color Green
#         Write-SafeHost "说明: $description" -color Cyan
#     } else {
#         Write-SafeHost "错误: 复制到剪贴板失败" -color Red
#         Write-SafeHost "说明: $description" -color Cyan
#         Write-SafeHost "密码原文: $password" -color Gray
#         Write-SafeHost "警告: 密码已显示在屏幕上，请注意隐私安全" -color Red
#         if ($errorMsg) {
#             Write-SafeHost "详细错误: $errorMsg" -color DarkRed
#         }
#     }
# }

# # Tab 补全（保持原有逻辑，但确保配置文件读取编码正确）
# Register-ArgumentCompleter -CommandName pw_ -ScriptBlock {
#     param($wordToComplete, $commandAst, $cursorPosition)
    
#     $configFile = Join-Path $env:MYSHELL "config\private\password.json"
    
#     if (-not (Test-Path $configFile)) {
#         return
#     }
    
#     try {
#         # 指定 UTF8 编码读取
#         $raw = Get-Content -Path $configFile -Raw -Encoding UTF8
#         $config = $raw | ConvertFrom-Json
        
#         $completionItems = $config.PSObject.Properties | Where-Object {
#             $_.Value.password -and $_.Value.password -ne $null
#         } | ForEach-Object {
#             $key = $_.Name
#             $description = $_.Value.description
            
#             [System.Management.Automation.CompletionResult]::new(
#                 $key,
#                 $key,
#                 'ParameterValue',
#                 $description
#             )
#         }
        
#         $completionItems | Where-Object {
#             $_.CompletionText -like "$wordToComplete*"
#         }
#     } catch {
#         return
#     }
# }