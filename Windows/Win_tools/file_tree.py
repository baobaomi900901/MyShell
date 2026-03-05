# .\Windows\Win_tools\file_tree.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
读取剪贴板文本，可混合已有树形符号（如 └─）和空格缩进，自动识别层级，
生成统一格式的树形结构：根直接输出，子节点使用 '├'/'└' + 与层级相同数量的 '─' + 空格，
每级缩进2个空格，并正确区分兄弟节点的先后关系。
结果自动复制回剪贴板。
"""

import sys
import re

# 剪贴板模块
try:
    import pyperclip
    def get_clipboard(): return pyperclip.paste()
    def set_clipboard(text): pyperclip.copy(text)
except ImportError:
    try:
        import tkinter as tk
        def get_clipboard():
            root = tk.Tk()
            root.withdraw()
            try:
                return root.clipboard_get()
            except tk.TclError:
                return ""
            finally:
                root.destroy()
        def set_clipboard(text):
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
    except ImportError:
        print("错误: 需要 pyperclip 或 tkinter 模块来访问剪贴板。")
        sys.exit(1)

# 匹配树形符号的正则：行首为 ├ 或 └，后跟一串 ─，可选的尾随空格
TREE_SYMBOL_PATTERN = re.compile(r'^[├└][─]+ ?')

def detect_indent_unit(lines):
    """检测纯空格行的最小正缩进空格数，若无则返回默认值2"""
    spaces_list = []
    for line in lines:
        # 排除符号行，只考虑纯空格行（无符号）
        if not TREE_SYMBOL_PATTERN.match(line.lstrip(' ')):
            leading_spaces = len(line) - len(line.lstrip(' '))
            if leading_spaces > 0:
                spaces_list.append(leading_spaces)
    return min(spaces_list) if spaces_list else 2

def parse_line(line, unit):
    """
    解析一行，返回 (层级, 显示文本)
    如果行有树形符号，层级由符号中 '─' 的数量决定；
    否则，层级由前导空格数 // unit 决定。
    """
    stripped = line.lstrip(' ')
    match = TREE_SYMBOL_PATTERN.match(stripped)
    if match:
        # 符号行
        symbol = match.group()
        level = symbol.count('─')
        content = stripped[len(symbol):].lstrip()
    else:
        # 纯空格行
        leading_spaces = len(line) - len(stripped)
        level = leading_spaces // unit
        content = stripped
    # 解析注释 #
    if '#' in content:
        idx = content.index('#')
        name = content[:idx].strip()
        comment = '#' + content[idx+1:].lstrip()
        display = f"{name} {comment}"
    else:
        display = content.strip()
    return level, display

def build_tree(lines):
    """生成树形文本"""
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return []
    unit = detect_indent_unit(non_empty)
    parsed = [parse_line(line, unit) for line in non_empty]

    result = []
    n = len(parsed)
    for i, (level, text) in enumerate(parsed):
        # 判断当前节点是否有后续同级兄弟
        has_next_sibling = False
        for j in range(i+1, n):
            if parsed[j][0] <= level:
                if parsed[j][0] == level:
                    has_next_sibling = True
                break
        if level == 0:
            result.append(text)
        else:
            indent = '  ' * (level - 1)
            symbol_char = '├' if has_next_sibling else '└'
            symbol = symbol_char + '─' * level + ' '
            result.append(indent + symbol + text)
    return result

def main():
    raw = get_clipboard()
    if not raw:
        print("剪贴板为空")
        return
    lines = raw.splitlines()
    tree = build_tree(lines)
    output = "\n".join(tree)
    print(output)
    set_clipboard(output)
    print("\n结果已复制到剪贴板")

if __name__ == "__main__":
    main()