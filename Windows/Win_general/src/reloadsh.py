import os
import time
import json
import re
import argparse
import ast
import sys
import questionary
from pathlib import Path

try:
    import keyboard
except ImportError:
    print("错误：需要 'keyboard' 库来模拟按键。请执行 'pip install keyboard' 安装。", file=sys.stderr)
    sys.exit(1)

# 查找文件中的方法
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

# 获取第三方软件包
def get_third_party_packages(root_dir):
    """
    Scan all .py files under root_dir, collect third-party package names.
    Returns sorted list of unique package names, with known aliases mapped.
    """
    PACKAGE_ALIASES = {
        'win32gui': 'pywin32',
        'win32api': 'pywin32',
        'win32con': 'pywin32',
        'win32file': 'pywin32',
        'win32process': 'pywin32',
        'win32com': 'pywin32',
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

    mapped_packages = set()
    for pkg in packages:
        mapped = PACKAGE_ALIASES.get(pkg, pkg)
        mapped_packages.add(mapped)

    return sorted(mapped_packages)

# 检测终端
def detect_terminal():
    """检测终端类型（基于环境变量 TERM_PROGRAM）"""
    if os.environ.get('TERM_PROGRAM') == 'vscode':
        return "vscode"
    else:
        return "windows"

# 发送组合键
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

def main():
    parser = argparse.ArgumentParser(description='Reloadsh helper')
    parser.add_argument('--windows-dir', required=True, help='Path to Windows directory containing *.ps1 files')
    parser.add_argument('--json-file', required=True, help='Path to function_tracker.json')
    args = parser.parse_args()

    windows_dir = Path(args.windows_dir)
    json_file = Path(args.json_file)

    # 阅读老的方法数据
    old_functions = []
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                old_functions = data.get('functionName', [])
        except Exception as e:
            print(f"⚠️  Warning: Could not read existing {json_file} (will be overwritten): {e}", file=sys.stderr)

    # 递归扫描所有 *.ps1文件
    ps_files = sorted(windows_dir.rglob('*.ps1'))
    new_functions = []
    for ps_file in ps_files:
        new_functions.extend(find_functions_in_file(ps_file))
    new_functions = sorted(list(dict.fromkeys(new_functions)))

    # 计算添加/删除
    old_set = set(old_functions)
    new_set = set(new_functions)
    added = sorted(list(new_set - old_set))
    removed = sorted(list(old_set - new_set))

    # 扫描所有.py文件收集第三方包
    try:
        third_party_packages = get_third_party_packages(windows_dir)
    except Exception as e:
        print(f"Error scanning Python packages: {e}", file=sys.stderr)
        third_party_packages = []

    # 更新 JSON 文件
    json_data = {
        'functionName': new_functions,
        'pythonPackage': third_party_packages
    }
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # 在终端中打印结果（带颜色）
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    RESET = '\033[0m'

    print(f"{GREEN}reloadsh{RESET}")
    print(f"{CYAN}📊 已生效方法: {len(old_functions)}{RESET}")
    print(f"{CYAN}📊 准备加载方法: {len(new_functions)}{RESET}")

    if added:
        print(f"{GREEN}🆕 新增方法 ({len(added)}):{RESET}")
        for func in added:
            print(f"{GREEN}   ✅ {func}{RESET}")
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

    answer = questionary.select(
        "PowerShell 不支持热更新，是否需要重新打开终端窗口：",
        choices=["Yes", "No"]
    ).ask()

    if answer == "No":
        print("已取消。")
        sys.exit(0)  # 退出码 0：不关闭窗口

    # 用户选择 Yes
    print("\n准备关闭当前窗口...")
    countdown(3)

    terminal_type = detect_terminal()
    print(f"检测到当前终端窗口类型：{terminal_type}")

    if terminal_type == "vscode":
        print("即将发送 Ctrl+Shift+` 到 VS Code，请确保焦点在 VS Code 窗口...")
        time.sleep(1)
        send_vscode_combo()
        print("组合键已发送。")
    else:
        print("即将发送 Ctrl+Shift+t 到 Windows（恢复已关闭标签页），请确保焦点在浏览器或资源管理器...")
        time.sleep(1)
        send_windows_combo()
        print("组合键已发送。")

    sys.exit(1)  # 退出码 1：通知 PowerShell 关闭窗口

if __name__ == "__main__":
    main()