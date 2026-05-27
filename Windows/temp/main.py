#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""接收坐标参数，在屏幕上绘制紫色矩形。

用法:
    python sketch.py "{x: 1995, y: 579, w: 108, h: 44}"
"""

import json
import re
import sys
import tkinter as tk


def parse_args(raw: str) -> dict:
    """解析类似 '{x: 1995, y: 579, w: 108, h: 44}' 的字符串为字典。"""
    # 先尝试标准 JSON
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 处理非标准 JSON（键无引号、单引号等）
    # 标准化：键加双引号，单引号换双引号
    s = raw.strip()
    s = s.replace("'", '"')
    # 为无引号的键添加双引号
    s = re.sub(r'(?<!\w)([a-zA-Z_]\w*)(?=\s*:)', r'"\1"', s)
    return json.loads(s)


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python sketch.py '{x: 1995, y: 579, w: 108, h: 44}'")
        sys.exit(1)

    params = parse_args(sys.argv[1])
    x = int(float(params.get("x", 0)))
    y = int(float(params.get("y", 0)))
    w = int(float(params.get("w", 100)))
    h = int(float(params.get("h", 50)))

    root = tk.Tk()
    root.title("sketch")
    root.geometry(f"{w}x{h}+{x}+{y}")
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.5)
    root.overrideredirect(True)

    # 紫色矩形填满窗口
    canvas = tk.Canvas(root, width=w, height=h, highlightthickness=0, bg="purple")
    canvas.pack()

    print(f"已绘制矩形: x={x}, y={y}, w={w}, h={h}。5秒后自动销毁。")
    root.after(5000, root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
