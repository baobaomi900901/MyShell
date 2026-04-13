import sys
import os
import json
import platform
import msvcrt

def clear_and_home():
    """使用 ANSI 转义序列清屏并将光标移到左上角 (1,1)"""
    # 清屏 + 光标归位，在支持 ANSI 的终端（Windows 10+、PowerShell）中可靠工作
    sys.stderr.write("\033[2J\033[H")
    sys.stderr.flush()

def read_key():
    """返回按键字符或特殊键名 ('up', 'down', 'enter', 'q', 'w')"""
    key = msvcrt.getch()
    if key == b'\xe0':          # 方向键前缀
        key2 = msvcrt.getch()
        if key2 == b'H':
            return 'up'
        elif key2 == b'P':
            return 'down'
        elif key2 == b'M':
            return 'enter'
        else:
            return None
    elif key == b'\r':
        return 'enter'
    elif key == b'q':
        return 'q'
    elif key == b'w':
        return 'w'
    else:
        return None

def show_menu(items, current_index):
    """显示菜单（每次都完整重绘）"""
    clear_and_home()
    # 所有输出都重定向到 stderr，避免干扰 stdout
    print("\n请使用上下方向键选择项目，按回车切换目录，按 w 然后 q 退出：\n", file=sys.stderr)
    for i, (key, desc, path) in enumerate(items):
        prefix = "→ " if i == current_index else "  "
        line = f"{prefix}{key} - {desc} ({path})"
        if i == current_index:
            # 高亮当前选中行（逆视频）
            print(f"\033[7m{line}\033[0m", file=sys.stderr)
        else:
            print(line, file=sys.stderr)
    print("\n提示：上下键移动，回车选择，连续按 w 和 q 退出", file=sys.stderr)
    sys.stderr.flush()

def main():
    if len(sys.argv) < 2:
        print("错误：未提供配置文件路径", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"配置文件不存在: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    is_windows = platform.system().lower() == "windows"
    items = []
    for key, value in config.items():
        path = value.get("win") if is_windows else value.get("mac")
        if path is None:
            continue
        if path.startswith("~"):
            path = os.path.expanduser(path)
        description = value.get("description", "")
        items.append((key, description, path))

    if not items:
        print("没有可用的路径", file=sys.stderr)
        sys.exit(1)

    current_index = 0
    w_pressed = False          # 标记 w 是否已被按下

    while True:
        show_menu(items, current_index)
        key = read_key()

        if key == 'up':
            current_index = (current_index - 1) % len(items)
            w_pressed = False
        elif key == 'down':
            current_index = (current_index + 1) % len(items)
            w_pressed = False
        elif key == 'enter':
            selected_path = items[current_index][2]
            # 只输出路径到 stdout，供父进程使用
            print(selected_path)
            break
        elif key == 'w':
            if not w_pressed:
                w_pressed = True
                # 提示信息输出到 stderr，不影响 stdout
                print("\n再按 q 确认退出...", file=sys.stderr)
            # 如果已经按过 w，再次按 w 不做任何事
        elif key == 'q':
            if w_pressed:
                # w 之后按 q，退出
                print("", file=sys.stdout)   # 输出空行，避免破坏 shell 提示符
                break
            else:
                # 单独的 q 键也允许退出（符合直觉）
                print("", file=sys.stdout)
                break
        else:
            w_pressed = False

if __name__ == "__main__":
    main()