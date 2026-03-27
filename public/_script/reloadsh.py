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
from typing import List, Dict, Set, Tuple, Optional, Any

try:
    import questionary
except ImportError:
    print("缺少 questionary 模块，请执行 pip install questionary")
    sys.exit(10)


try:
    import keyboard
except ImportError:
    print("缺少 keyboard 模块，请执行 pip install keyboard")
    sys.exit(10)

# ----------------------------------------------------------------------
# 常量定义
# ----------------------------------------------------------------------
JSON_FIELD_FUNCTION = "function"
JSON_FIELD_FUNCTION_NAME = "functionName"          # 兼容旧格式
JSON_FIELD_PYTHON_PACKAGE = "pip_package"
JSON_FIELD_PIP_IGNORE = "pip_ignore"
JSON_FIELD_PIP_ALIASES = "pip_aliases"

DESC_MARKER = "# 用途:"
MAX_DESC_LINES = 5

# ----------------------------------------------------------------------
# 全局缓存：标准库模块集合（只计算一次）
# ----------------------------------------------------------------------
_STDLIB_MODULES: Optional[Set[str]] = None

def _get_stdlib_modules() -> Set[str]:
    """获取 Python 标准库模块名集合（带缓存）"""
    global _STDLIB_MODULES
    if _STDLIB_MODULES is not None:
        return _STDLIB_MODULES

    try:
        if hasattr(sys, 'stdlib_module_names'):
            _STDLIB_MODULES = set(sys.stdlib_module_names)
        else:
            import pkgutil
            _STDLIB_MODULES = {module.name for module in pkgutil.iter_modules()}
    except Exception as e:
        print(f"⚠️  Warning: Could not determine standard library modules: {e}", file=sys.stderr)
        _STDLIB_MODULES = set()
    return _STDLIB_MODULES

# ----------------------------------------------------------------------
# 函数扫描：公共提取逻辑
# ----------------------------------------------------------------------
def _extract_functions_from_lines(
    lines: List[str],
    name_patterns: List[str],
    desc_marker: str = DESC_MARKER,
    max_desc_lines: int = MAX_DESC_LINES
) -> List[Dict[str, str]]:
    """
    从行列表中提取函数信息。
    name_patterns: 函数名匹配的正则表达式列表。
    返回函数信息列表，每个元素为 {"name": 函数名, "description": 描述, "file": 文件路径}
    """
    functions = []
    for i, line in enumerate(lines):
        for pattern in name_patterns:
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                if func_name.startswith('_'):
                    continue
                # 查找描述
                desc = ""
                for j in range(i+1, min(i+max_desc_lines, len(lines))):
                    stripped = lines[j].lstrip()
                    if stripped.startswith(desc_marker):
                        desc = stripped[len(desc_marker):].strip()
                        break
                functions.append({
                    "name": func_name,
                    "description": desc,
                    "file": ""   # 调用者填充
                })
                break  # 匹配到后跳出内层模式循环
    return functions

def find_functions_in_ps1(filepath: Path) -> List[Dict[str, str]]:
    """从 PowerShell 脚本中提取函数"""
    functions = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        pattern = r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_-]*)\s*'
        extracted = _extract_functions_from_lines(lines, [pattern])
        for func in extracted:
            func["file"] = str(filepath)
        functions.extend(extracted)
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    return functions

def find_functions_in_zsh(filepath: Path) -> List[Dict[str, str]]:
    """从 zsh 脚本中提取函数"""
    functions = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        patterns = [
            r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_-]*)\s*',
            r'^\s*([a-zA-Z_][a-zA-Z0-9_-]*)\s*\(\s*\)\s*'
        ]
        extracted = _extract_functions_from_lines(lines, patterns)
        for func in extracted:
            func["file"] = str(filepath)
        functions.extend(extracted)
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    return functions

def find_functions_in_file(filepath: Path) -> List[Dict[str, str]]:
    """根据扩展名选择提取函数"""
    ext = filepath.suffix.lower()
    if ext == '.ps1':
        return find_functions_in_ps1(filepath)
    elif ext == '.zsh':
        return find_functions_in_zsh(filepath)
    else:
        return []

# ----------------------------------------------------------------------
# 第三方包扫描
# ----------------------------------------------------------------------
def get_third_party_packages(
    root_dir: Path,
    exclude_packages: Optional[List[str]] = None,
    alias_map: Optional[Dict[str, str]] = None
) -> List[str]:
    """
    扫描 root_dir 下所有 .py 文件，收集第三方包名。
    exclude_packages: 需要排除的包名（映射后的真实包名）。
    alias_map: 别名到真实包名的映射字典。
    返回去重排序后的列表。
    """
    if exclude_packages is None:
        exclude_packages = []
    if alias_map is None:
        alias_map = {}

    stdlib_modules = _get_stdlib_modules()
    packages: Set[str] = set()

    for py_file in Path(root_dir).rglob('*.py'):
        try:
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
    mapped_packages: Set[str] = set()
    for pkg in packages:
        mapped = alias_map.get(pkg, pkg)
        mapped_packages.add(mapped)

    # 排除指定包
    mapped_packages -= set(exclude_packages)

    return sorted(mapped_packages)

# ----------------------------------------------------------------------
# 配置文件加载
# ----------------------------------------------------------------------
def load_pip_config() -> Tuple[List[str], Dict[str, List[str]]]:
    """
    加载 ${MYSHELL}/config/public/reloadsh_pip.json 配置文件。
    返回 (pip_ignore, pip_aliases) 元组。
    如果环境变量未设置或文件读取失败，返回空列表和空字典。
    """
    ignore_list: List[str] = []
    aliases: Dict[str, List[str]] = {}

    myshell = os.environ.get('MYSHELL')
    if not myshell:
        print("⚠️  环境变量 MYSHELL 未设置，无法加载 pip 配置文件", file=sys.stderr)
        return ignore_list, aliases

    config_path = Path(myshell) / 'config' / 'public' / 'reloadsh_pip.json'
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            ignore_list = config.get(JSON_FIELD_PIP_IGNORE, [])
            if not isinstance(ignore_list, list):
                ignore_list = []
            aliases = config.get(JSON_FIELD_PIP_ALIASES, {})
            if not isinstance(aliases, dict):
                aliases = {}
            print(f"✅ 已加载 pip 配置: {config_path}", file=sys.stderr)
        else:
            print(f"⚠️  pip 配置文件不存在: {config_path}，使用默认配置（无忽略包、无别名）", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  读取 pip 配置文件失败: {e}，使用默认配置（无忽略包、无别名）", file=sys.stderr)

    return ignore_list, aliases

# ----------------------------------------------------------------------
# 终端类型检测与按键模拟
# ----------------------------------------------------------------------
def detect_terminal() -> str:
    """检测终端类型（基于环境变量 TERM_PROGRAM）"""
    return "vscode" if os.environ.get('TERM_PROGRAM') == 'vscode' else "windows"

def send_combo(keys: List[str]) -> None:
    """按下并释放组合键"""
    for key in keys:
        keyboard.press(key)
    time.sleep(0.05)
    for key in reversed(keys):
        keyboard.release(key)

def send_vscode_combo() -> None:
    """Ctrl+Shift+` （VS Code 新建终端）"""
    send_combo(['ctrl', 'shift', '`'])

def send_windows_combo() -> None:
    """Ctrl+Shift+t （Windows 恢复已关闭标签页）"""
    send_combo(['ctrl', 'shift', 't'])

# ----------------------------------------------------------------------
# 主程序
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description='Reloadsh helper')
    parser.add_argument('--system-dir', required=True, help='Path to system directory containing script files')
    parser.add_argument('--json-file', required=True, help='Path to function_tracker.json')
    parser.add_argument('--system-type', required=True, choices=['windows', 'mac'], help='Type of system: windows or mac')
    parser.add_argument('--public-script-dir', required=False, help='Path to public script directory')
    parser.add_argument('--no-restart', action='store_true', help='Skip restart prompt on Windows (do not reopen terminal)')
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

    # 加载 pip 配置（忽略列表和别名映射）
    pip_ignore, pip_aliases = load_pip_config()

    # 将别名配置转换为 {别名: 真实包名} 映射
    alias_map: Dict[str, str] = {}
    for real_pkg, aliases in pip_aliases.items():
        for alias in aliases:
            alias_map[alias] = real_pkg

    # 读取旧数据（函数名等）
    old_function_names: List[str] = []
    old_data: Dict[str, Any] = {}
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                old_data = data
                # 提取函数名（兼容新旧格式）
                if JSON_FIELD_FUNCTION in data:
                    old_function_names = list(data[JSON_FIELD_FUNCTION].keys())
                elif JSON_FIELD_FUNCTION_NAME in data:
                    old_function_names = data[JSON_FIELD_FUNCTION_NAME]
        except Exception as e:
            print(f"⚠️  Warning: Could not read existing {json_file} (will be overwritten): {e}", file=sys.stderr)

    # 扫描所有指定目录下的脚本文件，获取新函数信息
    new_function_infos: List[Dict[str, str]] = []
    for scan_dir in scan_dirs:
        for ext in script_extensions:
            script_files = sorted(scan_dir.rglob(f'*{ext}'))
            for script_file in script_files:
                new_function_infos.extend(find_functions_in_file(script_file))

    # 去重（同名函数保留首次扫描到的描述和文件）
    unique_functions: Dict[str, Dict[str, str]] = {}
    for info in new_function_infos:
        name = info["name"]
        if name not in unique_functions:
            unique_functions[name] = {
                "description": info["description"],
                "file": info["file"]
            }

    # 构建新函数列表（按名称排序）
    new_function_names = sorted(unique_functions.keys())
    new_functions = [
        {
            "name": name,
            "description": info["description"],
            "file": info["file"]
        }
        for name, info in sorted(unique_functions.items())
    ]

    # 计算添加/删除（仅基于函数名）
    old_set = set(old_function_names)
    new_set = set(new_function_names)
    added = sorted(new_set - old_set)
    removed = sorted(old_set - new_set)

    # 扫描第三方包：合并所有扫描目录下的 Python 包（无论系统类型，都扫描 .py 文件）
    all_packages: Set[str] = set()
    for scan_dir in scan_dirs:
        try:
            dir_packages = get_third_party_packages(
                scan_dir,
                exclude_packages=pip_ignore,
                alias_map=alias_map
            )
            all_packages.update(dir_packages)
        except Exception as e:
            print(f"Error scanning Python packages in {scan_dir}: {e}", file=sys.stderr)
    third_party_packages = sorted(all_packages)

    # 构建新 JSON 数据
    function_dict = {
        info["name"]: {
            "description": info["description"],
            "file": info["file"]
        }
        for info in new_functions
    }
    json_data = dict(old_data)          # 复制旧数据，保留其他字段
    json_data[JSON_FIELD_FUNCTION] = function_dict
    json_data[JSON_FIELD_PYTHON_PACKAGE] = third_party_packages
    # 注意：不再写入旧的 pythoPackageIgnore 字段

    # 写入 JSON 文件
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # 彩色输出结果
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

    # 根据系统类型执行不同的后续操作
    if system_type == 'windows':
        if args.no_restart:
            print("已跳过终端重启询问（--no-restart 指定）。")
            sys.exit(0)

        try:
            answer = questionary.select(
                "PowerShell 不支持热更新，是否需要重新打开终端窗口：",
                choices=["Yes", "No"]
            ).ask()
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)

        if answer == "No":
            print("已取消。")
            sys.exit(0)

        print("\n准备关闭当前窗口...")
        terminal_type = detect_terminal()
        print(f"检测到当前终端窗口类型：{terminal_type}")

        if terminal_type == "vscode":
            print("即将发送 Ctrl+Shift+` 到 VS Code，请确保焦点在 VS Code 窗口...")
            time.sleep(2)
            send_vscode_combo()
            print("组合键已发送。")
        else:
            print("即将发送 Ctrl+Shift+t 到 Windows（恢复已关闭标签页），请确保焦点在浏览器或资源管理器...")
            time.sleep(2)
            send_windows_combo()
            print("组合键已发送。")

        sys.exit(1)

    elif system_type == 'mac':
        if (added or removed) and 'RELOADSH_REMOVED_FILE' in os.environ:
            removed_file = os.environ['RELOADSH_REMOVED_FILE']
            try:
                with open(removed_file, 'w', encoding='utf-8') as f:
                    for func in removed:
                        f.write(func + '\n')
                sys.exit(42)
            except Exception as e:
                print(f"{RED}❌ 写入删除函数列表到文件失败: {e}{RESET}", file=sys.stderr)
                sys.exit(1)
        print(f"\n{GREEN}✅ 如未更新请执行：source ~/.zshrc{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()