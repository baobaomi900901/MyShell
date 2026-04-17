#!/usr/bin/env python3
# public/_script/pw.py

import sys
from common import (
    RED, GREEN, YELLOW, RESET,
    load_json_config, interactive_select, write_temp_file
)

CONFIG_TEMPLATE = '''{
  "lite-root": {
    "password": "123",
    "description": "lite 服务器 root 密码"
  }
}'''


def get_valid_entries(data):
    """返回 { key: password } 字典，仅包含有 password 字段的项"""
    valid = {}
    for key, value in data.items():
        password = value.get("password")
        if password is not None:
            valid[key] = password
    return valid


def main():
    if len(sys.argv) < 3:
        print(f"{RED}❌ 错误：参数不足，需要 config_path 和 out_file{RESET}")
        sys.exit(1)

    config_path = sys.argv[1]
    out_file = sys.argv[2]
    query = sys.argv[3] if len(sys.argv) > 3 else None

    data = load_json_config(config_path, CONFIG_TEMPLATE)
    password = None

    if query and query.strip():
        key_candidate = query
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
        valid_entries = get_valid_entries(data)
        if not valid_entries:
            print(f"{RED}❌ 配置文件中没有可用的密码项。{RESET}")
            sys.exit(1)

        max_key_len = max(len(key) for key in valid_entries.keys())
        items = []
        for key, pwd in valid_entries.items():
            desc = data.get(key, {}).get("description", "")
            display_text = f"{key:<{max_key_len}}  # {desc}".rstrip()
            items.append((key, display_text, pwd))

        selected_key, password = interactive_select(
            "请选择要复制的密码:",
            items,
            instruction="(按 ↑/↓ 选择，回车确认，Ctrl+C 退出)"
        )
        if password is None:
            print(f"{YELLOW}已取消密码复制。{RESET}")
            sys.exit(1)

    write_temp_file(out_file, password)


if __name__ == "__main__":
    main()