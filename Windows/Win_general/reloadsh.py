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
import io
from pathlib import Path

# 强制 stdout 使用 UTF-8 编码（适配终端代码页 65001）
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def safe_print(text):
    """
    安全打印，自动适配控制台编码（备用，防止强制 UTF-8 失败）
    """
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        safe_text = text.encode(encoding, errors='replace').decode(encoding)
        print(safe_text)

def find_functions_in_file(filepath):
    """Scan a PowerShell script file and return list of function names."""
    functions = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
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
    Returns sorted list of unique package names, with known aliases mapped.
    """
    # 已知的模块名 -> 实际安装包名映射（例如 win32gui 属于 pywin32 包）
    PACKAGE_ALIASES = {
        'win32gui': 'pywin32',
        'win32api': 'pywin32',
        'win32con': 'pywin32',
        'win32file': 'pywin32',
        'win32process': 'pywin32',
        'win32com': 'pywin32',
        # 如有其他需要映射的模块，可继续添加
    }

    packages = set()
    # Get standard library modules
    try:
        if hasattr(sys, 'stdlib_module_names'):
            stdlib_modules = sys.stdlib_module_names
        else:
            import pkgutil
            stdlib_modules = {module.name for module in pkgutil.iter_modules()}
    except Exception as e:
        print(f"Warning: Could not determine standard library modules: {e}", file=sys.stderr)
        stdlib_modules = set()

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

    # 应用别名映射：将识别出的模块名替换为实际安装包名
    mapped_packages = set()
    for pkg in packages:
        mapped = PACKAGE_ALIASES.get(pkg, pkg)
        mapped_packages.add(mapped)

    return sorted(mapped_packages)

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
            print(f"⚠️  Warning: Could not read existing {json_file} (will be overwritten): {e}", file=sys.stderr)

    # Recursively scan all *.ps1 files
    ps_files = sorted(windows_dir.rglob('*.ps1'))
    new_functions = []
    for ps_file in ps_files:
        new_functions.extend(find_functions_in_file(ps_file))
    new_functions = sorted(list(dict.fromkeys(new_functions)))

    # Compute added/removed
    old_set = set(old_functions)
    new_set = set(new_functions)
    added = sorted(list(new_set - old_set))
    removed = sorted(list(old_set - new_set))

    # Scan all .py files to collect third-party packages
    try:
        third_party_packages = get_third_party_packages(windows_dir)
    except Exception as e:
        print(f"Error scanning Python packages: {e}", file=sys.stderr)
        third_party_packages = []

    # Update JSON file
    json_data = {
        'functionName': new_functions,
        'pythonPackage': third_party_packages
    }
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # Generate PowerShell commands
    ps_commands = []

    ps_commands.append('Write-Host "reloadsh" -ForegroundColor Green')
    ps_commands.append(f'Write-Host "📊 已生效方法: {len(old_functions)}" -ForegroundColor Cyan')
    ps_commands.append(f'Write-Host "📊 准备加载方法: {len(new_functions)}" -ForegroundColor Cyan')

    if added:
        ps_commands.append(f'Write-Host "🆕 新增方法 ({len(added)}):" -ForegroundColor Green')
        for func in added:
            ps_commands.append(f'Write-Host "   ✅ {func}" -ForegroundColor Green')
    else:
        ps_commands.append('Write-Host "✅ 没有新增方法" -ForegroundColor Green')

    if removed:
        ps_commands.append(f'Write-Host "🗑️  删除方法 ({len(removed)}):" -ForegroundColor Red')
        for func in removed:
            ps_commands.append(f'Write-Host "   ❌ {func}" -ForegroundColor Red')
        for func in removed:
            ps_commands.append(f'Remove-Item "function:{func}" -ErrorAction SilentlyContinue')
        ps_commands.append('Write-Host "✅ 清理完成" -ForegroundColor Green')
    else:
        ps_commands.append('Write-Host "✅ 没有删除方法" -ForegroundColor Green')

    ps_commands.append('Write-Host "🔄 重新加载函数文件..." -ForegroundColor Cyan')
    for ps_file in ps_files:
        quoted = str(ps_file.resolve()).replace("'", "''")
        ps_commands.append(f'. "{quoted}"')
    ps_commands.append('Write-Host "✅ 已重新加载所有函数文件" -ForegroundColor Green')

    ps_commands.append('Write-Host "✅ reload完成！" -ForegroundColor Green')
    ps_commands.append('Write-Host "✅ 请重新开启终端窗口, powershell 不支持新添加的函数热更新!!!" -ForegroundColor Green')

    # Output using safe_print (但强制 UTF-8 后直接 print 也行，保留 safe_print 作为保险)
    for line in ps_commands:
        safe_print(line)


if __name__ == "__main__":
    main()