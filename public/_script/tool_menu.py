#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""无参数时由 _tool 调用：从 MTTool config.json 列出命令，交互选择后写入临时文件（一行命令名）。"""

import json
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from common import RED, RESET, interactive_select, write_temp_file  # noqa: E402


def main() -> None:
    if len(sys.argv) < 3:
        print(f"{RED}用法: tool_menu.py <config.json> <out_file>{RESET}", file=sys.stderr)
        sys.exit(2)

    config_path = os.path.abspath(sys.argv[1])
    out_file = sys.argv[2]

    if not os.path.isfile(config_path):
        print(f"{RED}配置文件不存在: {config_path}{RESET}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if not isinstance(data, dict) or not data:
        print(f"{RED}配置为空或格式错误{RESET}", file=sys.stderr)
        sys.exit(1)

    names = sorted(data.keys(), key=str.lower)
    max_len = max(len(n) for n in names)
    items = []
    for name in names:
        entry = data.get(name) or {}
        desc = ""
        if isinstance(entry, dict):
            desc = (entry.get("description") or "").replace("\r\n", " ").replace("\n", " ")
        display = f"{name:<{max_len}}  # {desc}".rstrip()
        items.append((name, display, name))

    _key, value = interactive_select("请选择工具命令:", items)
    if value is None:
        write_temp_file(out_file, "")
        return
    write_temp_file(out_file, str(value).strip())


if __name__ == "__main__":
    main()
