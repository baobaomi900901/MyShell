# MyShell\Windows\win_password_fun.ps1

function pw_ {
    param (
        [Parameter(Position = 0)]
        [string]$action
    )

    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\password.json"
    
    if (-not (Test-Path $configFile)) {
        Write-Host "Error: Password config file not found" -ForegroundColor Red
        Write-Host "Please create: $configFile" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Example config file content:" -ForegroundColor Cyan
        return
    }
    
    # Read config
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
    } catch {
        Write-Host "Error: Config file format error" -ForegroundColor Red
        return
    }
    
    # Show help
    if (-not $action) {
        Write-Host "可选项:" -ForegroundColor Green
        
        $hasItems = $false
        $config.PSObject.Properties | ForEach-Object {
            $key = $_.Name
            $item = $_.Value
            if ($item.password -and $item.password -ne $null) {
                $hasItems = $true
                Write-Host "  $key" -ForegroundColor Yellow -NoNewline
                Write-Host " - $($item.description)"
            }
        }
        
        if (-not $hasItems) {
            Write-Host "  (No password items configured)" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "示例:" -ForegroundColor Cyan
        Write-Host "  pw_ lite-root     # 复制密码到剪切板" -ForegroundColor White
        
        return  # Just show help, don't copy anything
    }
    
    # Get password item
    if (-not $config.$action) {
        Write-Host "Error: Password item '$action' not found" -ForegroundColor Red
        Write-Host "Use 'pw_' to view all available password items" -ForegroundColor Yellow
        return
    }
    
    $item = $config.$action
    $password = $item.password
    $description = $item.description
    
    if (-not $password -or $password -eq $null) {
        Write-Host "Error: Password item '$action' has no password configured" -ForegroundColor Red
        return
    }
    
    # Copy password to clipboard
    $copied = $false
    $errorMsg = ""
    
    # Method 1: Use Set-Clipboard (built-in to Windows PowerShell 5.1+)
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
        try {
            Set-Clipboard -Value $password -ErrorAction Stop
            $copied = $true
        } catch {
            $errorMsg = "Set-Clipboard failed: $_"
        }
    }
    
    # Method 2: If Set-Clipboard is not available or failed, use .NET method
    if (-not $copied) {
        try {
            Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
            [System.Windows.Forms.Clipboard]::SetText($password)
            $copied = $true
        } catch {
            $errorMsg = "$errorMsg`n.NET Clipboard failed: $_"
        }
    }
    
    if ($copied) {
        Write-Host "✓ 复制 '$action' 密码到剪切板" -ForegroundColor Green
        Write-Host "说明: $description" -ForegroundColor Cyan
    } else {
        Write-Host "Error: Failed to copy to clipboard" -ForegroundColor Red
        Write-Host "Description: $description" -ForegroundColor Cyan
        Write-Host "Password: $password" -ForegroundColor Gray
        Write-Host "Warning: Password displayed on screen, ensure no one is watching" -ForegroundColor Red
        if ($errorMsg) {
            Write-Host "Error details: $errorMsg" -ForegroundColor DarkRed
        }
    }
}

# Tab completion
Register-ArgumentCompleter -CommandName pw_ -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $configFile = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\MyShell\config\password.json"
    
    if (-not (Test-Path $configFile)) {
        return
    }
    
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
        
        # Get all available password items
        $completionItems = $config.PSObject.Properties | Where-Object {
            $_.Value.password -and $_.Value.password -ne $null
        } | ForEach-Object {
            $key = $_.Name
            $description = $_.Value.description
            
            # Create completion item
            [System.Management.Automation.CompletionResult]::new(
                $key,                    # Completion text
                $key,                    # List text
                'ParameterValue',        # Result type
                $description             # Tooltip
            )
        }
        
        # Filter completion items based on current input
        $completionItems | Where-Object {
            $_.CompletionText -like "$wordToComplete*"
        }
        
    } catch {
        # If parsing fails, return empty result
        return
    }
}