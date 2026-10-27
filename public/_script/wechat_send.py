# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
r"""微信发送消息：激活 → Ctrl+F → 输入联系人 → 回车 → 发送文本。

用法：
  uv run wechat_send.py "任务已完成请查看"
  uv run wechat_send.py "测试" --dry-run
  uv run wechat_send.py "上线完成" --contact 猫叔叔 --strict   # 额外读会话气泡复核（慢约 3 秒）

做法与校验：
  1. 激活唯一微信主窗口（Weixin.exe / 标题“微信”）。
  2. Ctrl+F 打开搜索，清空后输入联系人，回车进入会话。
  3. 用本目录 `wechat_element` 元素库中的“聊天输入行”定位输入框（SDK 直读，约 0.4 秒），
     校验输入框名称属于该联系人，防止误发。
  4. 输入消息后回读输入框内容，必须与待发文本完全一致。
  5. 回车发送后再次回读，确认输入框已清空；--strict 时再读一次会话气泡复核。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

SDK_SOURCE = Path(r"D:\code\desktop\sdk\src")
if not (SDK_SOURCE / "uiautoma" / "__init__.py").is_file():
    raise RuntimeError(f"SDK 不存在：{SDK_SOURCE}")
sys.path.insert(0, str(SDK_SOURCE))

import uiautoma  # noqa: E402
from uiautoma import win32  # noqa: E402

TEST_DIR = Path(__file__).resolve().parent
LIBRARY_DIR = TEST_DIR / "wechat_element"
LIBRARY_FALLBACKS = (
    TEST_DIR / "wechat_element",
    Path(r"D:\code\元素库\CLI测试\tools\wechat_element"),
)


def default_library() -> Path:
    for candidate in LIBRARY_FALLBACKS:
        if (candidate / "package.json").is_file():
            return candidate
    return LIBRARY_DIR
DEFAULT_CLI = Path(r"D:\code\desktop\cli\target\x86_64-pc-windows-msvc\release\uia.exe")
PROCESS = "Weixin.exe"
TITLE = "微信"
EDIT_TYPE = 50004


class Bot:
    def __init__(self, library: Path, cli: Path, dry_run: bool, strict: bool,
                 screenshot_dir: Path | None):
        self.library = library
        self.cli = cli
        self.dry_run = dry_run
        self.strict = strict
        self.screenshot_dir = screenshot_dir

    # ---------- 基础 ----------
    def window(self):
        matched = []
        for window in win32.get_list(process_name=PROCESS, timeout=5):
            detail = window.get_detail()
            if (detail.get("process_name", "").casefold() == PROCESS.casefold()
                    and detail.get("title") == TITLE):
                matched.append(window)
        if len(matched) != 1:
            raise RuntimeError(f"预期唯一的微信主窗口，实际 {len(matched)} 个")
        return matched[0]

    def chat_input(self, window, contact: str):
        """定位“聊天输入行”下的 Edit，并校验它属于该联系人。"""
        row = window.find("聊天输入行", timeout=2)
        children = row.children()
        if len(children) != 1:
            raise RuntimeError(f"聊天输入行子节点数异常：{len(children)}")
        edit = children[0]
        attributes = edit.get_all_attributes()
        name = attributes.get("Name") or ""
        if attributes.get("ControlType") != EDIT_TYPE:
            raise RuntimeError(f"聊天输入行下不是输入框：{attributes.get('ControlType')!r}")
        if not name.startswith(contact):
            raise RuntimeError(f"当前会话不是“{contact}”，而是 {name!r}，已中止")
        return edit, name

    def wait_input(self, window, contact: str, timeout: float):
        deadline = time.monotonic() + timeout
        last_error = None
        while True:
            try:
                return self.chat_input(window, contact)
            except Exception as error:  # noqa: BLE001 - 会话打开期间允许暂时找不到
                last_error = error
            if time.monotonic() >= deadline:
                raise RuntimeError(f"未进入与“{contact}”的会话：{last_error}")
            time.sleep(0.25)

    def wait_value(self, window, contact: str, expected: str, timeout: float, label: str):
        deadline = time.monotonic() + timeout
        while True:
            edit, _ = self.chat_input(window, contact)
            value = edit.get_value()
            if value == expected:
                return
            if time.monotonic() >= deadline:
                raise RuntimeError(f"{label} 超时：当前输入框内容 {value!r}")
            time.sleep(0.2)

    def screenshot(self, window, label: str):
        if not self.screenshot_dir:
            return
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(self.cli), "screenshot", "win",
                        "--hwnd", str(window.get_detail()["handle"]),
                        "--out", str(self.screenshot_dir / f"{label}.png"), "--format", "json"],
                       capture_output=True, text=True, timeout=120)

    def strict_bubble(self, window, hwnd: int, message: str):
        """可选的慢校验：CLI 观察会话气泡（约 3 秒）。"""
        process = subprocess.run(
            [str(self.cli), "observe", "win", "tree", "--hwnd", str(hwnd),
             "--max-depth", "20", "--max-nodes", "4000", "--budget-ms", "8000",
             "--format", "json"], capture_output=True, text=True, encoding="utf-8", timeout=120)
        payload = json.loads(process.stdout or "{}")
        if process.returncode != 0 or not payload.get("ok"):
            raise RuntimeError(f"CLI 观察失败：{payload.get('error')!r}")
        nodes: list[dict] = []

        def walk(node):
            nodes.append(node)
            for child in node.get("children") or []:
                walk(child)

        walk(payload["data"]["root"])
        bubbles = [n for n in nodes if n.get("control_type") == "ListItem"
                   and isinstance(n.get("name"), str) and message in n["name"]]
        if not bubbles:
            raise RuntimeError("会话中未找到刚发送的消息气泡")
        print(f"[strict] 气泡记录：{bubbles[0]['name'].splitlines()[:2]}", flush=True)

    # ---------- 主流程 ----------
    def run(self, contact: str, message: str) -> int:
        uiautoma.open(str(self.library))
        window = self.window()
        window.activate()
        if not window.is_active():
            raise RuntimeError("微信窗口未置于前台")
        hwnd = int(window.get_detail()["handle"])
        print(f"[1/4] 已激活微信窗口：HWND {hwnd}", flush=True)

        win32.send_keys("^f", delay_after=0.35)
        # 若微信未把焦点交给搜索框（例如刚才停留在搜索结果页），点一下左上角搜索框再输入
        rect = window.get_detail()["rect"]
        win32.mouse_move(rect["x"] + 150, rect["y"] + 57, move_speed="instant", delay_after=0.1)
        win32.mouse_click(delay_after=0.25)
        win32.send_keys("^a", send_key_delay=15)
        win32.send_keys(contact, send_key_delay=25, delay_after=0.7)
        win32.send_keys("{ENTER}", delay_after=0.5)

        edit, target_name = self.wait_input(window, contact, 5)
        print(f"[2/4] 已进入会话：{target_name!r}", flush=True)

        win32.send_keys(message, send_key_delay=25, delay_after=0.1)
        self.wait_value(window, contact, message, 2, "回读输入框内容")
        print(f"[3/4] 已输入并回读消息：{message!r}", flush=True)

        if self.dry_run:
            win32.send_keys("^a", send_key_delay=15)
            win32.send_keys("{BACKSPACE}", send_key_delay=15, delay_after=0.2)
            self.wait_value(window, contact, "", 2, "清空输入框")
            self.screenshot(window, "dry-run")
            print("[dry-run] 已清空输入框，未发送", flush=True)
            return 0

        win32.send_keys("{ENTER}", delay_after=0.3)
        self.wait_value(window, contact, "", 3, "发送后输入框清空")
        print(f"[4/4] 已发送并确认输入框清空：{message!r}", flush=True)

        if self.strict:
            self.strict_bubble(window, hwnd, message)

        self.screenshot(window, "after-send")
        print(f"[完成] 已发送到 {target_name!r}：{message!r}", flush=True)
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="微信发送消息（激活 → 搜索联系人 → 回车 → 发送）")
    parser.add_argument("message", nargs="?", help="要发送的文本（位置参数）")
    parser.add_argument("--contact", default="猫叔叔", help="联系人名称（默认：猫叔叔）")
    parser.add_argument("--message", "--content", dest="message_option", metavar="TEXT",
                        help="要发送的文本（--message / --content / 位置参数 三选一）")
    parser.add_argument("--dry-run", action="store_true", help="只输入不发送，结束前清空输入框")
    parser.add_argument("--strict", action="store_true", help="发送后再读会话气泡复核（慢约 3 秒）")
    parser.add_argument("--library", type=Path, default=default_library(), help="元素库目录")
    parser.add_argument("--cli", type=Path, default=DEFAULT_CLI, help="uia.exe 路径（仅 --strict 用）")
    parser.add_argument("--screenshot-dir", type=Path, default=None, help="保存截图")
    args = parser.parse_args()
    message = args.message_option if args.message_option is not None else args.message
    if message is None or not message.strip():
        parser.error('必须提供消息内容：wechat_send.py "内容" 或 --message "内容"')
    if not (args.library / "package.json").is_file():
        raise RuntimeError(f"元素库不存在：{args.library}")
    bot = Bot(args.library, args.cli, args.dry_run, args.strict, args.screenshot_dir)
    try:
        return bot.run(args.contact, message)
    except Exception as error:  # noqa: BLE001
        print(f"[失败] {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
