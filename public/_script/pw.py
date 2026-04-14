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
    YELLOW = Fore.YELLOW
    DARK_GRAY = Fore.LIGHTBLACK_EX
    RESET = Style.RESET_ALL
except ImportError:
    # 回退到 ANSI 转义码
    RED = '\033[91m'
    YELLOW = '\033[93m'
    DARK_GRAY = '\033[90m'
    RESET = '\033[0m'

try:
    import questionary
    from questionary import Style as QStyle
except ImportError:
    sys.stderr.write("请先安装 questionary：pip install questionary\n")
    sys.exit(1)

CONFIG_TEMPLATE = '''{
  "lite-root": {
    "password": "123",
    "description": "lite 服务器 root 密码"
  }
}'''


def main():
    if len(sys.argv) < 3:
        print(f"{RED}❌ 错误：参数不足{RESET}")
        sys.exit(1)
    
    config_path = sys.argv[1]
    out_file = sys.argv[2]
    
    if not os.path.exists(config_path):
        print(f"{RED}❌ 配置文件不存在: {config_path}{RESET}")
        print(f"{YELLOW}   请手动创建该文件，模板如下:{RESET}")
        print(f"{DARK_GRAY}{CONFIG_TEMPLATE}{RESET}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except Exception as e:
        print(f"{RED}❌ JSON 解析失败: {e}{RESET}")
        sys.exit(1)

    max_key_len = max(len(key) for key in data.keys())
    choices = []
    key_to_password = {}

    for key, value in data.items():
        password = value.get("password")
        if password is None:
            continue
        desc = value.get("description", "")
        display_text = f"{key:<{max_key_len}}  # {desc}".rstrip()
        choices.append(display_text)
        key_to_password[key] = password

    if not choices:
        print(f"{RED}❌ 配置文件中没有可用的密码项。{RESET}")
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
    password = key_to_password.get(selected_key)

    if not password:
        print(f"{RED}❌ 内部错误：无法获取密码{RESET}")
        sys.exit(1)

    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(password)
    except Exception as e:
        print(f"{RED}❌ 写入临时文件失败: {e}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()