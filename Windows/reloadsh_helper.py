# .\Windows\Win_tools\reloadsh_helper.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper script for reloadsh PowerShell function.
Now recursively scans all .ps1 files under windows_dir.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

def find_functions_in_file(filepath):
    """Scan a PowerShell script file and return list of function names."""
    functions = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        # Match lines like: function function_name {
        pattern = r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{'
        for line in content.splitlines():
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                if not func_name.startswith('_'):
                    functions.append(func_name)
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    return functions

def main():
    parser = argparse.ArgumentParser(description='Reloadsh helper')
    parser.add_argument('--windows-dir', required=True, help='Path to Windows directory containing *.ps1 files')
    parser.add_argument('--json-file', required=True, help='Path to function_tracker.json')
    args = parser.parse_args()

    windows_dir = Path(args.windows_dir)
    json_file = Path(args.json_file)

    # Read old function list
    old_functions = []
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                old_functions = data.get('functionName', [])
        except Exception as e:
            print(f"Error reading {json_file}: {e}", file=sys.stderr)
            sys.exit(1)

    # Recursively scan all *.ps1 files under windows_dir
    ps_files = sorted(windows_dir.rglob('*.ps1'))
    new_functions = []
    for ps_file in ps_files:
        new_functions.extend(find_functions_in_file(ps_file))
    new_functions = sorted(list(dict.fromkeys(new_functions)))  # deduplicate and sort

    # Compute added/removed
    old_set = set(old_functions)
    new_set = set(new_functions)
    added = sorted(list(new_set - old_set))
    removed = sorted(list(old_set - new_set))

    # Update JSON file
    json_data = {'functionName': new_functions}
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # Generate PowerShell commands
    ps_commands = []

    # Header
    ps_commands.append('Write-Host "reloadsh" -ForegroundColor Green')
    ps_commands.append(f'Write-Host "📊 已生效方法: {len(old_functions)}" -ForegroundColor Cyan')
    ps_commands.append(f'Write-Host "📊 准备加载方法: {len(new_functions)}" -ForegroundColor Cyan')

    # Added functions
    if added:
        ps_commands.append(f'Write-Host "🆕 新增方法 ({len(added)}):" -ForegroundColor Green')
        for func in added:
            ps_commands.append(f'Write-Host "   ✅ {func}" -ForegroundColor Green')
    else:
        ps_commands.append('Write-Host "✅ 没有新增方法" -ForegroundColor Green')

    # Removed functions
    if removed:
        ps_commands.append(f'Write-Host "🗑️  删除方法 ({len(removed)}):" -ForegroundColor Red')
        for func in removed:
            ps_commands.append(f'Write-Host "   ❌ {func}" -ForegroundColor Red')
        ps_commands.append('Write-Host "🧹 清理已删除函数..." -ForegroundColor Yellow')
        for func in removed:
            ps_commands.append(f'Remove-Item "function:{func}" -ErrorAction SilentlyContinue')
            ps_commands.append(f'Write-Host "   🧹 移除: {func}" -ForegroundColor Yellow')
        ps_commands.append('Write-Host "✅ 清理完成" -ForegroundColor Green')
    else:
        ps_commands.append('Write-Host "✅ 没有删除方法" -ForegroundColor Green')

    # Reload all .ps1 files (now including subdirectories)
    ps_commands.append('Write-Host "🔄 重新加载函数文件..." -ForegroundColor Cyan')
    for ps_file in ps_files:
        quoted = str(ps_file.resolve()).replace("'", "''")
        ps_commands.append(f'. "{quoted}"')
    ps_commands.append('Write-Host "✅ 已重新加载所有函数文件" -ForegroundColor Green')

    # Profile reminder
    ps_commands.append('Write-Host "ℹ️ 如需更新别名或其他profile内容，请手动执行: . `$PROFILE" -ForegroundColor Yellow')
    ps_commands.append('Set-Clipboard -Value ". `$PROFILE"')
    ps_commands.append('Write-Host "📋 命令已复制到剪贴板" -ForegroundColor Cyan')
    ps_commands.append('Write-Host "✅ reload完成！" -ForegroundColor Green')

    # Output the whole script block
    print("\n".join(ps_commands))

if __name__ == "__main__":
    main()