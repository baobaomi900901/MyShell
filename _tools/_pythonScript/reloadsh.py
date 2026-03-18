#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import re
import argparse
import ast
import sys
from pathlib import Path

try:
    import keyboard
except ImportError:
    print("缺少 keyboard 模块，请执行 pip install keyboard / pip3 install keyboard")
    sys.exit(10)

try:
    import questionary
except ImportError:
    print("缺少 questionary 模块，请执行 pip install questionary / pip3 install questionary")
    sys.exit(10)

# ----------------------------------------------------------------------
# 函数扫描：根据文件类型提取函数名和描述
# ----------------------------------------------------------------------
def find_functions_in_file(filepath):
    """
    根据文件扩展名选择合适的函数提取方式。
    返回函数信息列表，每个元素为 {"name": 函数名, "description": 描述, "file": 文件路径}
    """
    ext = filepath.suffix.lower()
    if ext == '.ps1':
        return find_functions_in_ps1(filepath)
    elif ext == '.zsh':
        return find_functions_in_zsh(filepath)
    else:
        # 不支持的文件类型，返回空列表
        return []

def find_functions_in_ps1(filepath):
    """从 PowerShell 脚本中提取函数"""
    functions = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # 匹配 function 定义行，支持包含连字符的函数名（如 Invoke-CleanImage）
        pattern = r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_-]*)\s*'
        for i, line in enumerate(lines):
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                if func_name.startswith('_'):
                    continue
                # 在函数定义后最多5行内查找 "# 用途:"
                desc = ""
                for j in range(i+1, min(i+5, len(lines))):
                    stripped = lines[j].lstrip()
                    if stripped.startswith("# 用途:"):
                        desc = stripped[len("# 用途:"):].strip()
                        break
                functions.append({
                    "name": func_name,
                    "description": desc,
                    "file": str(filepath)
                })
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    return functions

def find_functions_in_zsh(filepath):
    """从 zsh 脚本中提取函数"""
    functions = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # 匹配两种常见函数定义格式：
        # 1. function name { ... }
        # 2. name() { ... }
        # 注意：函数名允许包含字母、数字、下划线、连字符，但不能以数字开头
        pattern_func_keyword = r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_-]*)\s*'
        pattern_parentheses = r'^\s*([a-zA-Z_][a-zA-Z0-9_-]*)\s*\(\s*\)\s*'

        for i, line in enumerate(lines):
            # 尝试匹配 function 关键字形式
            match = re.search(pattern_func_keyword, line)
            if not match:
                # 尝试匹配 name() 形式
                match = re.search(pattern_parentheses, line)
            if match:
                func_name = match.group(1)
                if func_name.startswith('_'):
                    continue
                # 在函数定义后最多5行内查找 "# 用途:"
                desc = ""
                for j in range(i+1, min(i+5, len(lines))):
                    stripped = lines[j].lstrip()
                    if stripped.startswith("# 用途:"):
                        desc = stripped[len("# 用途:"):].strip()
                        break
                functions.append({
                    "name": func_name,
                    "description": desc,
                    "file": str(filepath)
                })
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    return functions

# ----------------------------------------------------------------------
# 第三方包扫描：分析项目内所有 .py 文件的 import 语句
# ----------------------------------------------------------------------
def get_third_party_packages(root_dir, exclude_packages=None):
    """
    扫描 root_dir 下所有 .py 文件，收集第三方包名。
    exclude_packages: 列表，需要排除的包名（映射后的真实包名，如 'pywin32'）。
    返回去重排序后的列表。
    """
    if exclude_packages is None:
        exclude_packages = []

    PACKAGE_ALIASES = {
        'win32gui': 'pywin32',
        'win32api': 'pywin32',
        'win32con': 'pywin32',
        'win32file': 'pywin32',
        'win32process': 'pywin32',
        'win32com': 'pywin32',
    }

    packages = set()
    # 获取标准库模块名
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
            # 使用 utf-8-sig 自动移除 BOM
            with open(py_file, 'r', encoding='utf-8-sig') as f:
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

    # 应用别名映射
    mapped_packages = set()
    for pkg in packages:
        mapped = PACKAGE_ALIASES.get(pkg, pkg)
        mapped_packages.add(mapped)

    # 排除手动指定的包
    mapped_packages = mapped_packages - set(exclude_packages)

    return sorted(mapped_packages)

# ----------------------------------------------------------------------
# 终端类型检测与按键模拟
# ----------------------------------------------------------------------
def detect_terminal():
    """检测终端类型（基于环境变量 TERM_PROGRAM）"""
    if os.environ.get('TERM_PROGRAM') == 'vscode':
        return "vscode"
    else:
        return "windows"

def send_combo(keys):
    """按下并释放组合键"""
    for key in keys:
        keyboard.press(key)
    time.sleep(0.05)
    for key in reversed(keys):
        keyboard.release(key)

def send_vscode_combo():
    """Ctrl+Shift+` （VS Code 新建终端）"""
    send_combo(['ctrl', 'shift', '`'])

def send_windows_combo():
    """Ctrl+Shift+t （Windows 恢复已关闭标签页）"""
    send_combo(['ctrl', 'shift', 't'])

def countdown(seconds):
    """倒计时打印"""
    for i in range(seconds, 0, -1):
        print(f"窗口将在 {i} 秒后关闭...", flush=True)
        time.sleep(1)

# ----------------------------------------------------------------------
# 主程序
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='Reloadsh helper')
    parser.add_argument('--system-dir', required=True, help='Path to system directory containing script files')
    parser.add_argument('--json-file', required=True, help='Path to function_tracker.json')
    parser.add_argument('--system-type', required=True, choices=['windows', 'mac'], help='Type of system: windows or mac')
    parser.add_argument('--public-script-dir', required=False, help='Path to public script directory')
    args = parser.parse_args()

    system_dir = Path(args.system_dir)
    json_file = Path(args.json_file)
    system_type = args.system_type
    public_script_dir = args.public_script_dir

    # 根据系统类型确定要扫描的脚本文件扩展名
    if system_type == 'windows':
        script_extensions = ['.ps1']
    elif system_type == 'mac':
        script_extensions = ['.zsh']
    else:
        # 理论上不会执行到这里，因为 argparse 限制了 choices
        print(f"错误: 不支持的 system_type: {system_type}", file=sys.stderr)
        sys.exit(1)

    # 构建要扫描的目录列表
    scan_dirs = [system_dir]
    if public_script_dir:
        public_dir_path = Path(public_script_dir)
        if public_dir_path.exists() and public_dir_path.is_dir():
            scan_dirs.append(public_dir_path)
        else:
            print(f"警告: 提供的公共脚本目录不存在或不是目录: {public_script_dir}", file=sys.stderr)

    # 读取旧数据（函数名、排除列表等）
    old_function_names = []
    old_data = {}                     # 保存完整的旧 JSON 数据
    ignore_packages = []               # 排除包名列表，默认为空
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                old_data = data        # 保存完整数据
                # 提取函数名（兼容新旧格式）
                if "function" in data:
                    old_function_names = list(data["function"].keys())
                elif "functionName" in data:
                    old_function_names = data["functionName"]
                # 提取排除包名列表（键名为 pythoPackageIgnore）
                ignore_packages = data.get("pythoPackageIgnore", [])
                if not isinstance(ignore_packages, list):
                    ignore_packages = []
        except Exception as e:
            print(f"⚠️  Warning: Could not read existing {json_file} (will be overwritten): {e}", file=sys.stderr)

    # ------------------------------------------------------------------
    # 扫描所有指定目录下的脚本文件，获取新函数信息
    # ------------------------------------------------------------------
    new_function_infos = []
    for scan_dir in scan_dirs:
        for ext in script_extensions:
            script_files = sorted(scan_dir.rglob(f'*{ext}'))
            for script_file in script_files:
                new_function_infos.extend(find_functions_in_file(script_file))

    # 去重（同名函数保留首次扫描到的描述和文件）
    unique_functions = {}
    for info in new_function_infos:
        name = info["name"]
        if name not in unique_functions:
            unique_functions[name] = {
                "description": info["description"],
                "file": info["file"]
            }

    # 构建新函数列表（按名称排序）
    new_function_names = sorted(unique_functions.keys())
    new_functions = [{"name": name, "description": unique_functions[name]["description"]} for name in new_function_names]

    # 计算添加/删除（仅基于函数名）
    old_set = set(old_function_names)
    new_set = set(new_function_names)
    added = sorted(list(new_set - old_set))
    removed = sorted(list(old_set - new_set))

    # ------------------------------------------------------------------
    # 扫描第三方包：合并所有扫描目录下的 Python 包（无论系统类型，都扫描 .py 文件）
    # ------------------------------------------------------------------
    all_packages = set()
    for scan_dir in scan_dirs:
        try:
            dir_packages = get_third_party_packages(scan_dir, exclude_packages=ignore_packages)
            all_packages.update(dir_packages)
        except Exception as e:
            print(f"Error scanning Python packages in {scan_dir}: {e}", file=sys.stderr)
    third_party_packages = sorted(all_packages)

    # 构建新 JSON 数据：基于旧数据，更新函数和包列表，保留其他字段（如 pythoPackageIgnore）
    function_dict = {info["name"]: {"description": info["description"]} for info in new_functions}
    json_data = dict(old_data)          # 复制旧数据
    json_data["function"] = function_dict
    json_data["pythonPackage"] = third_party_packages

    # 写入 JSON 文件
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 彩色输出结果
    # ------------------------------------------------------------------
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    RESET = '\033[0m'

    print(f"{GREEN}reloadsh{RESET}")
    print(f"{CYAN}📊 已生效方法: {len(old_function_names)}{RESET}")
    print(f"{CYAN}📊 准备加载方法: {len(new_function_names)}{RESET}")

    if added:
        print(f"{GREEN}🆕 新增方法 ({len(added)}):{RESET}")
        for func in added:
            file_path = unique_functions[func]["file"]
            print(f"{GREEN}   ✅ {func} ({file_path}){RESET}")
    else:
        print(f"{GREEN}✅ 没有新增方法{RESET}")

    if removed:
        print(f"{RED}🗑️  删除方法 ({len(removed)}):{RESET}")
        for func in removed:
            print(f"{RED}   ❌ {func}{RESET}")
    else:
        print(f"{GREEN}✅ 没有删除方法{RESET}")

    print(f"{CYAN}✅ 已重新加载所有函数文件{RESET}")
    print(f"{GREEN}✅ reload完成！{RESET}")

    # ------------------------------------------------------------------
    # 根据系统类型执行不同的后续操作
    # ------------------------------------------------------------------
    if system_type == 'windows':
        # Windows：询问是否重启终端
        answer = questionary.select(
            "PowerShell 不支持热更新，是否需要重新打开终端窗口：",
            choices=["Yes", "No"]
        ).ask()

        if answer == "No":
            print("已取消。")
            sys.exit(0)  # 退出码 0：不关闭窗口

        # 用户选择 Yes
        print("\n准备关闭当前窗口...")
        countdown(3)  # 倒计时3秒

        # 检测终端类型并发送组合键
        terminal_type = detect_terminal()
        print(f"检测到当前终端窗口类型：{terminal_type}")

        if terminal_type == "vscode":
            print("即将发送 Ctrl+Shift+` 到 VS Code，请确保焦点在 VS Code 窗口...")
            time.sleep(2)
            send_vscode_combo()
            print("组合键已发送。")
        else:  # windows
            print("即将发送 Ctrl+Shift+t 到 Windows（恢复已关闭标签页），请确保焦点在浏览器或资源管理器...")
            time.sleep(2)
            send_windows_combo()
            print("组合键已发送。")

        # 退出码 1：通知 PowerShell 关闭窗口
        sys.exit(1)

    elif system_type == 'mac':
        # macOS：提示用户手动执行 source
        print(f"\n{GREEN}✅ 配置已更新。请执行以下命令以应用更改：{RESET}")
        print(f"{CYAN}   source ~/.zshrc{RESET}")
        sys.exit(0)  # 正常退出

if __name__ == "__main__":
    main()