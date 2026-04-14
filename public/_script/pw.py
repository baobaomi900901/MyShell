#!/usr/bin/env python3
# public/_script/pw.py

import sys
import json
import os

# 尝试导入 colorama 以获得跨平台颜色支持，没有则使用原始 ANSI 码
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
    from questionary import Style as QStyle
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False

CONFIG_TEMPLATE = '''{
  "lite-root": {
    "password": "123",
    "description": "lite 服务器 root 密码"
  }
}'''


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


def interactive_selection(data):
    """交互式选择菜单（仅在无参数时调用）"""
    # 收集有密码的项
    choices = []
    key_to_password = {}
    max_key_len = max(len(key) for key in data.keys()) if data else 0

    for key, value in data.items():
        password = value.get("password")
        if password is None:
            continue
        key_to_password[key] = password
        desc = value.get("description", "")
        display_text = f"{key:<{max_key_len}}  # {desc}".rstrip()
        choices.append(display_text)

    if not choices:
        print(f"{RED}❌ 配置文件中没有可用的密码项。{RESET}")
        sys.exit(1)

    if not QUESTIONARY_AVAILABLE:
        print(f"{RED}❌ 交互模式需要安装 questionary: pip install questionary{RESET}")
        sys.exit(1)

    custom_style = QStyle([
        ('qmark', 'fg:#5F819D bold'),
        ('question', 'bold'),
        ('instruction', 'fg:#808080'),
        ('pointer', 'fg:#FF8C00 bold'),
        ('highlighted', 'fg:#FF8C00 bold'),
    ])

    selected = questionary.select(
        "请选择要复制的密码:",
        choices=choices,
        instruction="(按 ↑/↓ 选择，回车确认，Ctrl+C 退出)",
        style=custom_style
    ).ask()

    if selected is None:
        sys.exit(0)

    selected_key = selected.split()[0]
    return key_to_password.get(selected_key)


def main():
    if len(sys.argv) < 3:
        print(f"{RED}❌ 错误：参数不足，需要 config_path 和 out_file{RESET}")
        sys.exit(1)

    config_path = sys.argv[1]
    out_file = sys.argv[2]
    query = sys.argv[3] if len(sys.argv) > 3 else None

    data = load_config(config_path)
    password = None

    # 情况1：提供了查询参数 -> 直接匹配，不进入交互菜单
    if query and query.strip():
        key_candidate = query  # 密码配置的键名通常不含特殊字符，保持原样即可
        if key_candidate in data:
            password = data[key_candidate].get("password")
            if password is not None:
                print(f"{GREEN}✔ 已匹配密码项: {key_candidate}{RESET}")
            else:
                print(f"{RED}❌ 配置项 '{key_candidate}' 中没有 password 字段{RESET}")
                sys.exit(1)
        else:
            available = ', '.join(data.keys())
            print(f"{RED}❌ 未找到配置项: {query}{RESET}")
            print(f"{YELLOW}可用的键名: {available}{RESET}")
            sys.exit(1)
    else:
        # 情况2：无查询参数 -> 交互选择
        password = interactive_selection(data)
        if password is None:
            sys.exit(0)

    # 写入临时文件
    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(password)
    except Exception as e:
        print(f"{RED}❌ 写入临时文件失败: {e}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()