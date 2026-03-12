# .\Windows\Win_general\reloadsh.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper script for reloadsh PowerShell function.
Recursively scans all .ps1 files under windows_dir, tracks functions,
and also scans all .py files to collect third-party package dependencies.
"""

import os
import sys
import json
import re
import argparse
import ast
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


def get_third_party_packages(root_dir):
    """
    Scan all .py files under root_dir, collect third-party package names.
    Returns sorted list of unique package names.
    """
    packages = set()
    # Get standard library modules
    try:
        if hasattr(sys, 'stdlib_module_names'):
            stdlib_modules = sys.stdlib_module_names
        else:
            # Fallback for older Python: use pkgutil to list top-level modules
            import pkgutil
            stdlib_modules = {module.name for module in pkgutil.iter_modules()}
    except Exception as e:
        print(f"Warning: Could not determine standard library modules: {e}", file=sys.stderr)
        stdlib_modules = set()  # Fallback to empty set, may include third-party

    for py_file in Path(root_dir).rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=py_file)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        if module_name not in stdlib_modules:
                            packages.add(module_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and not node.module.startswith('.'):
                        module_name = node.module.split('.')[0]
                        if module_name not in stdlib_modules:
                            packages.add(module_name)
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {py_file}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error processing {py_file}: {e}", file=sys.stderr)

    return sorted(packages)


def main():
    parser = argparse.ArgumentParser(description='Reloadsh helper')
    parser.add_argument('--windows-dir', required=True, help='Path to Windows directory containing *.ps1 files')
    parser.add_argument('--json-file', required=True, help='Path to function_tracker.json')
    args = parser.parse_args()

    windows_dir = Path(args.windows_dir)
    json_file = Path(args.json_file)

    # Read old function list (if JSON exists and is valid)
    old_functions = []
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                old_functions = data.get('functionName', [])
        except Exception as e:
            print(f"⚠️  Warning: Could not read existing {json_file} (will be overwritten): {e}", file=sys.stderr)
            # Continue with empty old_functions, file will be recreated later

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

    # Scan all .py files to collect third-party packages (with error handling)
    try:
        third_party_packages = get_third_party_packages(windows_dir)
    except Exception as e:
        print(f"Error scanning Python packages: {e}", file=sys.stderr)
        third_party_packages = []

    # Update JSON file with both function list and package list (always write new)
    json_data = {
        'functionName': new_functions,
        'pythonPackage': third_party_packages
    }
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
        for func in removed:
            ps_commands.append(f'Remove-Item "function:{func}" -ErrorAction SilentlyContinue')
        ps_commands.append('Write-Host "✅ 清理完成" -ForegroundColor Green')
    else:
        ps_commands.append('Write-Host "✅ 没有删除方法" -ForegroundColor Green')

    # Reload all .ps1 files (including subdirectories)
    ps_commands.append('Write-Host "🔄 重新加载函数文件..." -ForegroundColor Cyan')
    for ps_file in ps_files:
        quoted = str(ps_file.resolve()).replace("'", "''")
        ps_commands.append(f'. "{quoted}"')
    ps_commands.append('Write-Host "✅ 已重新加载所有函数文件" -ForegroundColor Green')

    # Profile reminder
    ps_commands.append('Write-Host "✅ reload完成！" -ForegroundColor Green')

    # Output the whole script block
    print("\n".join(ps_commands))


if __name__ == "__main__":
    main()