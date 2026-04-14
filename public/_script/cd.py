#!/usr/bin/env python3
# public/_script/cd.py

import sys
import json
import os
import platform

# 颜色支持
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    DARK_GRAY = Fore.LIGHTBLACK_EX
    RESET = Style.RESET_ALL
except ImportError:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    DARK_GRAY = '\033[90m'
    RESET = '\033[0m'

# questionary 仅在交互模式下需要
try:
    import questionary
    from questionary import Style
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False

CONFIG_TEMPLATE = '''{
    "MyShell": {
        "win": "C:\\\\Users\\\\YourUsername\\\\Documents\\\\WindowsPowerShell\\\\MyShell",
        "mac": "/Users/YourUsername/MyShell",
        "description": "MyShell 配置目录"
    }
}'''


def get_system_type():
    system = platform.system()
    if system == "Windows":
        return "win"
    elif system == "Darwin":
        return "mac"
    else:
        return "unknown"


def load_config(config_path):
    if not os.path.exists(config_path):
        print(f"{RED}❌ 配置文件不存在: {config_path}{RESET}")
        print(f"{YELLOW}   请手动创建该文件，模板如下:{RESET}")
        print(f"{DARK_GRAY}{CONFIG_TEMPLATE}{RESET}")
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"{RED}❌ JSON 解析失败: {e}{RESET}")
        sys.exit(1)


def get_valid_targets(data, os_type):
    """返回 { key: expanded_path } 字典，仅包含当前系统存在且路径有效的项"""
    valid = {}
    for key, value in data.items():
        raw_path = value.get(os_type)
        if not raw_path:
            continue
        expanded = os.path.expanduser(raw_path)
        if os.path.exists(expanded):
            valid[key] = expanded
    return valid


def interactive_selection(data, valid_targets):
    """交互式选择菜单（仅当无参数时调用）"""
    if not valid_targets:
        print(f"{RED}❌ 当前系统下没有可用的目录配置。{RESET}")
        sys.exit(1)

    if not QUESTIONARY_AVAILABLE:
        print(f"{RED}❌ 交互模式需要安装 questionary: pip install questionary{RESET}")
        sys.exit(1)

    max_key_len = max(len(key) for key in valid_targets.keys())
    choices = []
    for key, path in valid_targets.items():
        desc = data.get(key, {}).get("description", "")
        display_text = f"{key:<{max_key_len}}  # {desc}".rstrip()
        choices.append(display_text)

    custom_style = Style([
        ('qmark', 'fg:#5F819D bold'),
        ('question', 'bold'),
        ('instruction', 'fg:#808080'),
        ('pointer', 'fg:#FF8C00 bold'),
        ('highlighted', 'fg:#FF8C00 bold'),
    ])

    selected = questionary.select(
        "请选择你要跳转的目录:",
        choices=choices,
        instruction="(按 ↑/↓ 选择，回车确认，Ctrl+C 退出)",
        style=custom_style
    ).ask()

    if selected is None:
        sys.exit(0)

    selected_key = selected.split()[0]
    return valid_targets.get(selected_key)


def main():
    if len(sys.argv) < 3:
        print(f"{RED}❌ 错误：参数不足，需要 config_path 和 out_file{RESET}")
        sys.exit(1)

    config_path = sys.argv[1]
    out_file = sys.argv[2]
    query = sys.argv[3] if len(sys.argv) > 3 else None

    data = load_config(config_path)
    os_type = get_system_type()
    if os_type == "unknown":
        print(f"{RED}❌ 不支持的操作系统{RESET}")
        sys.exit(1)

    target_path = None

    # 情况1：提供了查询参数 -> 直接匹配，不进入交互菜单
    if query and query.strip():
        # 将查询中的短横线替换为下划线，以匹配配置中的键名
        key_candidate = query.replace('-', '_')
        # 获取当前系统下该键对应的路径（不要求路径存在性？但最好检查）
        if key_candidate in data:
            raw_path = data[key_candidate].get(os_type)
            if raw_path:
                expanded = os.path.expanduser(raw_path)
                if os.path.exists(expanded):
                    target_path = expanded
                    print(f"{GREEN}✔ 跳转到: {key_candidate} -> {target_path}{RESET}")
                else:
                    print(f"{RED}❌ 路径不存在: {expanded}{RESET}")
                    sys.exit(1)
            else:
                print(f"{RED}❌ 配置项 '{key_candidate}' 在当前系统 ({os_type}) 下没有定义路径{RESET}")
                sys.exit(1)
        else:
            # 提供模糊提示：列出所有可用的键名
            available = ', '.join(data.keys())
            print(f"{RED}❌ 未找到配置项: {query}{RESET}")
            print(f"{YELLOW}可用的键名: {available}{RESET}")
            sys.exit(1)
    else:
        # 情况2：无查询参数 -> 交互选择
        valid_targets = get_valid_targets(data, os_type)
        target_path = interactive_selection(data, valid_targets)
        if target_path is None:
            sys.exit(0)

    # 写入临时文件
    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(target_path)
    except Exception as e:
        print(f"{RED}❌ 写入临时文件失败: {e}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()