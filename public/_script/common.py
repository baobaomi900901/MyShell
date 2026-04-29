#!/usr/bin/env python3
# public/_script/common.py

import sys
import os
import platform
import json

# Windows 控制台可能是 GBK，遇到 “❌/✔” 等字符会炸；这里统一把 stdout/stderr 设为 utf-8 并容错替换。
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 颜色支持
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    DARK_GRAY = Fore.LIGHTBLACK_EX
    RESET = Style.RESET_ALL
except ImportError:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    DARK_GRAY = '\033[90m'
    RESET = '\033[0m'

# questionary 可选
try:
    import questionary
    from questionary import Style as QStyle
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False


def get_system_type():
    """返回 'win', 'mac' 或 'unknown'"""
    system = platform.system()
    if system == "Windows":
        return "win"
    elif system == "Darwin":
        return "mac"
    else:
        return "unknown"


def load_json_config(config_path, template=""):
    """通用 JSON 配置加载，失败时打印模板并退出"""
    if not os.path.exists(config_path):
        print(f"{RED}❌ 配置文件不存在: {config_path}{RESET}")
        if template:
            print(f"{YELLOW}   请手动创建该文件，模板如下:{RESET}")
            print(f"{DARK_GRAY}{template}{RESET}")
        sys.exit(1)

    try:
        # 二进制读入后去掉 UTF-8 BOM，避免部分环境下 utf-8-sig 仍报 Unexpected UTF-8 BOM
        with open(config_path, 'rb') as f:
            raw = f.read()
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        text = raw.decode('utf-8')
        return json.loads(text)
    except Exception as e:
        print(f"{RED}❌ JSON 解析失败: {e}{RESET}")
        sys.exit(1)


def generate_back_line(max_len, arrow=" 🔙 "):
    """生成与最长选项等宽的分隔线，箭头居中"""
    if max_len <= len(arrow):
        return arrow
    total_len = max_len
    arrow_len = len(arrow)
    side_len = (total_len - arrow_len) // 2
    # 右侧多补一点保证总长度足够（+6 为经验值，可保留原视觉效果）
    back_line = '-' * side_len + arrow + '-' * (total_len - side_len - arrow_len + 6)
    return back_line


def interactive_select(title, items, instruction="(按 ↑/↓ 选择，回车确认，Ctrl+C 退出)"):
    """
    通用交互式选择菜单。
    items: list of tuple (key, display_text, value) 或 (key, display_text, value)
           其中 display_text 是已经格式化的字符串（包含对齐和描述）。
           也可以只传 key 和 value，内部自动生成 display_text，但那样需要额外传 max_key_len 和描述字典。
    为了简化，我们要求调用者自行构建 display_text，这样更灵活。
    返回: (selected_key, selected_value) 或 (None, None) 表示取消。
    """
    if not items:
        print(f"{RED}❌ 没有可用的选项。{RESET}")
        sys.exit(1)

    if not QUESTIONARY_AVAILABLE:
        print(f"{RED}❌ 交互模式需要安装 questionary: pip install questionary{RESET}")
        sys.exit(1)

    # 构建 choices 列表（显示文本）
    choices = [item[1] for item in items]   # display_text
    # 计算最长选项长度（用于生成分隔线）
    max_option_len = max(len(display) for _, display, _ in items) if items else 0
    back_line = generate_back_line(max_option_len)
    choices.append(back_line)

    custom_style = QStyle([
        ('qmark', 'fg:#5F819D bold'),
        ('question', 'bold'),
        ('instruction', 'fg:#808080'),
        ('pointer', 'fg:#FF8C00 bold'),
        ('highlighted', 'fg:#FF8C00 bold'),
    ])

    selected = questionary.select(
        title,
        choices=choices,
        instruction=instruction,
        style=custom_style
    ).ask()

    if selected is None:
        sys.exit(0)
    if selected == back_line:
        return None, None   # 用户取消

    # 根据选中的显示文本找到对应的 key 和 value
    for key, display, value in items:
        if display == selected:
            return key, value

    # 理论上不会到这里
    return None, None


def write_temp_file(out_file, content):
    """将内容写入临时文件"""
    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"{RED}❌ 写入临时文件失败: {e}{RESET}")
        sys.exit(1)