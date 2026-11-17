#!/usr/bin/env python3
"""Order private configuration entries for menus and shell completion."""

from __future__ import annotations

import json
import sys


def sorted_config_keys(data: dict, keys=None) -> list[str]:
    """Integer index first (ascending), then unindexed; ties use the key name."""
    def sort_key(name: str):
        entry = data.get(name)
        index = entry.get("index") if isinstance(entry, dict) else None
        if isinstance(index, int) and not isinstance(index, bool):
            return (0, index, name.casefold(), name)
        return (1, 0, name.casefold(), name)

    return sorted(data if keys is None else keys, key=sort_key)


def completion_rows(data: dict, kind: str) -> list[dict[str, str]]:
    rows = []
    for key in sorted_config_keys(data):
        entry = data[key]
        if not isinstance(entry, dict):
            continue
        if kind == "path" and not (entry.get("win") or entry.get("mac")):
            continue
        if kind == "password" and entry.get("password") is None:
            continue
        name = key.replace("_", "-") if kind == "path" else key
        description = str(entry.get("description") or "").replace("\r", " ").replace("\n", " ")
        rows.append({"name": name, "description": description})
    return rows


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 3 or argv[1] not in {"path", "password"} or argv[2] not in {"zsh", "json"}:
        print("用法: config_entries.py <配置文件> <path|password> <zsh|json>", file=sys.stderr)
        return 2
    try:
        with open(argv[0], encoding="utf-8-sig") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError("配置根节点必须是对象")
        rows = completion_rows(data, argv[1])
    except (OSError, ValueError) as exc:
        print(f"读取配置失败: {exc}", file=sys.stderr)
        return 1
    if argv[2] == "json":
        # ASCII JSON survives Windows PowerShell's native-process pipe decoding.
        print(json.dumps(rows, ensure_ascii=True))
    else:
        for row in rows:
            print(f'{row["name"]}:{row["description"]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
