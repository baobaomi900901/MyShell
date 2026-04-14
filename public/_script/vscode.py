#!/usr/bin/env python3
# public/_script/vscode.py

import sys
import json
import os
import platform

# 颜色支持（与 pw.py 保持一致）
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    DARK_GRAY = Fore.LIGHTBLACK_EX
    RESET = Style.RESET_ALL
except ImportError:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    DARK_GRAY = '\033[90m'
    RESET = '\033[0m'

try:
    import questionary
    from questionary import Style
except ImportError:
    sys.stderr.write("请先安装 questionary：pip install questionary\n")
    sys.exit(1)

# 配置文件模板
CONFIG_TEMPLATE = '''{
  "ShIndex": {
    "win": "C:\\\\Users\\\\mobytang\\\\Documents\\\\WindowsPowerShell\\\\Microsoft.PowerShell_profile.ps1",
    "mac": "/Users/mobytang/.zshrc",
    "description": "打开 sh 入口文件"
  },
  "Documents": {
    "win": "C:\\\\Users\\\\mobytang\\\\Documents",
    "description": "Documents"
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

    system = platform.system()
    os_type = "win" if system == "Windows" else ("mac" if system == "Darwin" else "unknown")

    # 格式化菜单：只显示当前系统有配置的项目
    max_key_len = max(len(key) for key in data.keys())
    choices = []
    valid_targets = {}  # 记录 key -> 实际路径的映射

    for key, value in data.items():
        raw_path = value.get(os_type)
        if not raw_path:
            continue   # 当前系统无配置，跳过
        expanded = os.path.expanduser(raw_path)
        # 不检查路径是否存在，因为可能是尚未创建的文件夹，但 code 命令仍可打开
        valid_targets[key] = expanded
        desc = value.get("description", "")
        display_text = f"{key:<{max_key_len}}  # {desc}".rstrip()
        choices.append(display_text)

    if not choices:
        print(f"{RED}❌ 当前系统 ({os_type}) 下没有可用的项目配置。{RESET}")
        sys.exit(1)

    custom_style = Style([
        ('qmark', 'fg:#5F819D bold'),
        ('question', 'bold'),
        ('instruction', 'fg:#808080'),
        ('pointer', 'fg:#FF8C00 bold'),
        ('highlighted', 'fg:#FF8C00 bold'),
    ])

    selected = questionary.select(
        "请选择要用 VS Code 打开的项目:",
        choices=choices,
        instruction="(按 ↑/↓ 选择，回车确认，Ctrl+C 退出)",
        style=custom_style
    ).ask()

    if selected is None:
        sys.exit(0)  # 用户取消

    selected_key = selected.split()[0]
    target_path = valid_targets.get(selected_key)

    if not target_path:
        print(f"{RED}❌ 内部错误：无法获取路径{RESET}")
        sys.exit(1)

    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(target_path)
    except Exception as e:
        print(f"{RED}❌ 写入临时文件失败: {e}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()