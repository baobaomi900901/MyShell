# .\Windows\Win_general\cd.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python script for cd_ function.
Reads path.json and either shows help (with colored directory names) or outputs Set-Location command.
"""

import os
import sys
import json
from pathlib import Path

# ANSI color codes
YELLOW = '\033[93m'
RESET = '\033[0m'

def get_config_path():
    """Return the path to config/path.json."""
    user_profile = os.environ.get('USERPROFILE', '')
    if not user_profile:
        user_profile = str(Path.home())
    return Path(user_profile) / "Documents" / "WindowsPowerShell" / "MyShell" / "config" / "path.json"

def load_config(config_path):
    """Load and return the JSON config. Print error and return None on failure."""
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}", file=sys.stderr)
        return None

def show_help(config):
    """Print available directories with colored names and aligned columns."""
    lines = []
    lines.append("快速目录跳转")
    lines.append("用法: cd_ <名称>")
    lines.append("")
    lines.append("可用目录:")

    # Collect directory names to determine max width
    names = []
    for key, value in config.items():
        if value.get('win') is not None:
            display_name = key.replace('_', '-')
            names.append(display_name)
    max_len = max(len(name) for name in names) if names else 0

    # Generate lines with colored names
    for key, value in config.items():
        if value.get('win') is not None:
            display_name = key.replace('_', '-')
            description = value.get('description', '')
            # Yellow name, padded to max_len, then description
            line = f"  {YELLOW}{display_name:<{max_len}}{RESET} - {description}"
            lines.append(line)
    return "\n".join(lines)

def main():
    if len(sys.argv) < 2 or not sys.argv[1]:
        # No argument -> show help
        config_path = get_config_path()
        if not config_path.exists():
            print(f"❌ 配置文件不存在\n请手动创建: {config_path}")
            sys.exit(1)
        config = load_config(config_path)
        if config is None:
            sys.exit(1)
        print(show_help(config))
        return

    action = sys.argv[1]
    internal_action = action.replace('-', '_')

    config_path = get_config_path()
    if not config_path.exists():
        print(f"❌ 配置文件不存在\n请手动创建: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    if config is None:
        sys.exit(1)

    if internal_action not in config:
        print(f"❌ 目录 '{action}' 不存在")
        sys.exit(1)

    item = config[internal_action]
    target_path = item.get('win')
    if target_path is None:
        print(f"❌ 目录 '{action}' 在 Windows 上未配置")
        sys.exit(1)

    path_obj = Path(target_path)
    if not path_obj.exists():
        print(f"❌ 目录不存在 - {target_path}")
        sys.exit(1)
    if not path_obj.is_dir():
        print(f"❌ 路径不是目录 - {target_path}")
        if path_obj.is_file():
            print("提示: 该路径是一个文件，若要运行工具请使用 'tool_ license-lite' 或 'tool_ license-rpa'")
        sys.exit(1)

    safe_path = str(target_path).replace("'", "''")
    print(f"Set-Location '{safe_path}'")

if __name__ == "__main__":
    main()