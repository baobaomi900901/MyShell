#!/usr/bin/env python3
# public/_script/vscode.py

import sys
import os
from common import (
    RED, GREEN, YELLOW, RESET,
    get_system_type, load_json_config, interactive_select, write_temp_file
)

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


def get_valid_targets(data, os_type):
    """返回 { key: expanded_path } 字典，仅包含当前系统下定义了路径的项（不检查存在性）"""
    valid = {}
    for key, value in data.items():
        raw_path = value.get(os_type)
        if not raw_path:
            continue
        expanded = os.path.expanduser(raw_path)
        valid[key] = expanded
    return valid


def main():
    if len(sys.argv) < 3:
        print(f"{RED}❌ 错误：参数不足，需要 config_path 和 out_file{RESET}")
        sys.exit(1)

    config_path = sys.argv[1]
    out_file = sys.argv[2]
    query = sys.argv[3] if len(sys.argv) > 3 else None

    data = load_json_config(config_path, CONFIG_TEMPLATE)
    os_type = get_system_type()
    if os_type == "unknown":
        print(f"{RED}❌ 不支持的操作系统{RESET}")
        sys.exit(1)

    target_path = None

    if query and query.strip():
        key_candidate = query.replace('-', '_')
        if key_candidate in data:
            raw_path = data[key_candidate].get(os_type)
            if raw_path:
                expanded = os.path.expanduser(raw_path)
                if os.path.exists(expanded):
                    target_path = expanded
                    print(f"{GREEN}✔ 将用 VS Code 打开: {key_candidate} -> {target_path}{RESET}")
                else:
                    print(f"{RED}❌ 路径不存在: {expanded}{RESET}")
                    sys.exit(1)
            else:
                print(f"{RED}❌ 配置项 '{key_candidate}' 在当前系统 ({os_type}) 下没有定义路径{RESET}")
                sys.exit(1)
        else:
            available = ', '.join(data.keys())
            print(f"{RED}❌ 未找到配置项: {query}{RESET}")
            print(f"{YELLOW}可用的键名: {available}{RESET}")
            sys.exit(1)
    else:
        valid_targets = get_valid_targets(data, os_type)
        if not valid_targets:
            print(f"{RED}❌ 当前系统下没有可用的项目配置。{RESET}")
            sys.exit(1)

        max_key_len = max(len(key) for key in valid_targets.keys())
        items = []
        for key, path in valid_targets.items():
            desc = data.get(key, {}).get("description", "")
            display_text = f"{key:<{max_key_len}}  # {desc}".rstrip()
            items.append((key, display_text, path))

        selected_key, target_path = interactive_select(
            "请选择要用 VS Code 打开的项目:",
            items,
            instruction="(按 ↑/↓ 选择，回车确认，Ctrl+C 退出)"
        )
        if target_path is None:
            print(f"{YELLOW}已取消打开项目。{RESET}")
            sys.exit(1)

    write_temp_file(out_file, target_path)


if __name__ == "__main__":
    main()