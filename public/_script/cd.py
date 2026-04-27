#!/usr/bin/env python3
# public/_script/cd.py

import sys
import os
from common import (
    RED, GREEN, YELLOW, RESET,
    get_system_type, load_json_config, interactive_select, write_temp_file
)

CONFIG_TEMPLATE = '''{
    "MyShell": {
        "win": "C:\\\\Users\\\\YourUsername\\\\Documents\\\\WindowsPowerShell\\\\MyShell",
        "mac": "/Users/YourUsername/MyShell",
        "description": "MyShell 配置目录"
    }
}'''


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
        # 直接匹配
        key_candidate = query.replace('-', '_')
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
            available = ', '.join(data.keys())
            print(f"{RED}❌ 未找到配置项: {query}{RESET}")
            print(f"{YELLOW}可用的键名: {available}{RESET}")
            sys.exit(1)
    else:
        # 交互选择
        valid_targets = get_valid_targets(data, os_type)
        if not valid_targets:
            print(f"{RED}❌ 当前系统下没有可用的目录配置。{RESET}")
            sys.exit(1)

        # 构建 items: (key, display_text, value)
        max_key_len = max(len(key) for key in valid_targets.keys())
        items = []
        for key, path in valid_targets.items():
            desc = data.get(key, {}).get("description", "")
            display_text = f"{key:<{max_key_len}}  # {desc}".rstrip()
            items.append((key, display_text, path))

        selected_key, target_path = interactive_select(
            "请选择你要跳转的目录:",
            items,
            instruction="(按 ↑/↓ 选择，回车确认，Ctrl+C 退出)"
        )
        if target_path is None:
            print(f"{YELLOW}已取消操作。{RESET}")
            sys.exit(0)

    write_temp_file(out_file, target_path)


if __name__ == "__main__":
    main()