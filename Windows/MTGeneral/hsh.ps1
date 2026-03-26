function hsh {
    # 用途: 查看所有内置方法及其描述。
    <#
    .SYNOPSIS
        列出所有内置方法及其描述，按文件分组显示。
    .DESCRIPTION
        从 function_tracker.json 中读取函数名称、描述和所属文件。
        单函数文件中的函数直接显示在顶层（黄色），多函数文件先显示文件名（蓝色），再缩进显示其内部函数（黄色）。
    #>

    # 检查环境变量
    if (-not $env:myshell) {
        Write-Error "环境变量 'myshell' 未设置，无法定位 function_tracker.json。"
        return
    }

    $jsonPath = Join-Path $env:myshell "config\private\function_tracker.json"
    
    if (-not (Test-Path $jsonPath)) {
        Write-Error "找不到 function_tracker.json，预期路径：$jsonPath"
        return
    }

    try {
        $content = Get-Content $jsonPath -Raw -Encoding UTF8
        if ($content.Length -gt 0 -and $content[0] -eq [char]0xFEFF) {
            $content = $content.Substring(1)
        }
        $json = $content | ConvertFrom-Json
    } catch {
        Write-Error "无法解析 JSON 文件：$_"
        Write-Host "文件内容预览（前200字符）：" -ForegroundColor Yellow
        Write-Host $content.Substring(0, [Math]::Min(200, $content.Length))
        return
    }

    if (-not $json.function) {
        Write-Host "没有找到内置方法。" -ForegroundColor Yellow
        return
    }

    # 数据结构
    $fileFuncs = @{}
    $funcDesc = @{}
    $maxLen = 0

    foreach ($prop in $json.function.PSObject.Properties) {
        $name = $prop.Name
        $value = $prop.Value

        $desc = ""
        $file = ""
        if ($value -is [string]) {
            $desc = $value
        } else {
            $desc = $value.description
            $file = $value.file
        }

        if ([string]::IsNullOrWhiteSpace($desc)) {
            continue
        }

        if ([string]::IsNullOrWhiteSpace($file)) {
            $file = "__top__"
        }

        $funcDesc[$name] = $desc

        if (-not $fileFuncs.ContainsKey($file)) {
            $fileFuncs[$file] = @()
        }
        $fileFuncs[$file] += $name

        if ($name.Length -gt $maxLen) {
            $maxLen = $name.Length
        }
    }

    if ($funcDesc.Count -eq 0) {
        Write-Host "没有找到带有描述的内置方法。" -ForegroundColor Yellow
        return
    }

    Write-Host ""
    Write-Host "内置方法:"

    # 收集顶层函数（__top__ 组 + 单函数文件）
    $topNames = @()
    if ($fileFuncs.ContainsKey("__top__")) {
        $topNames += $fileFuncs["__top__"]
    }

    $multiFileFuncs = @{}
    foreach ($file in $fileFuncs.Keys | Where-Object { $_ -ne "__top__" }) {
        $names = $fileFuncs[$file]
        if ($names.Count -eq 1) {
            $topNames += $names[0]
        } else {
            $multiFileFuncs[$file] = $names
        }
    }

    $topNames = $topNames | Sort-Object

    # 输出顶层函数（整行黄色）
    foreach ($name in $topNames) {
        $desc = $funcDesc[$name]
        $line = "  " + $name.PadRight($maxLen + 2) + "# " + $desc
        Write-Host $line -ForegroundColor Yellow
    }

    # 输出多函数文件分组
    $sortedFiles = $multiFileFuncs.Keys | Sort-Object
    foreach ($file in $sortedFiles) {
        $filename = Split-Path $file -Leaf
        Write-Host ("  " + $filename + ":") -ForegroundColor Blue

        $names = $multiFileFuncs[$file] | Sort-Object
        foreach ($name in $names) {
            $desc = $funcDesc[$name]
            $line = "    " + $name.PadRight($maxLen + 2) + "# " + $desc
            Write-Host $line -ForegroundColor Yellow
        }
    }

    Write-Host ""
}