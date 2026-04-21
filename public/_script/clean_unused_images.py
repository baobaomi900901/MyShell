#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clean_unused_images — 过滤 .md / .html / .htm 中未被引用的图片资源。
逻辑与 cleanUnusedImages.js 对齐；依赖仅标准库。

用法:
    python clean_unused_images.py [扫描目录]
    未传目录时默认为「当前工作目录」（即你在终端里 cd 到的目录，与 _tool 从何处调用无关）。
"""

from __future__ import annotations

import math
import os
import re
import sys
from pathlib import Path

CONFIG = {
    "scan_extensions": {".md", ".html", ".htm"},
    "image_extensions": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"},
    "exclude_dirs": {"node_modules", ".git", "dist", "build"},
    "verbose": True,
}

# 与 JS 版一致的正则
RE_MD_IMG = re.compile(r"!\[.*?\]\((.*?)\)")
RE_HTML_IMG = re.compile(r'<img[^>]+src=["\'](.*?)["\']', re.IGNORECASE)
RE_CSS_BG = re.compile(
    r"background(?:-image)?\s*:\s*url\([\"']?(.*?)[\"']?\)",
    re.IGNORECASE,
)


def _strip_md_angle_brackets(url: str) -> str:
    """Markdown 中 ![](<path with spaces>) 会包一层尖括号，需去掉再拼路径。"""
    s = url.strip()
    if len(s) >= 2 and s[0] == "<" and s[-1] == ">":
        return s[1:-1].strip()
    return s


def log_header() -> None:
    print("\n🖼️ 图片资源清理工具 (Python)")
    print("----------------------------")
    print(f"扫描扩展名: {', '.join(sorted(CONFIG['scan_extensions']))}")
    print(f"图片扩展名: {', '.join(sorted(CONFIG['image_extensions']))}")
    print(f"排除目录: {', '.join(sorted(CONFIG['exclude_dirs']))}")
    print("----------------------------\n")


def scan_project(root_dir: Path) -> tuple[list[Path], list[Path]]:
    print("🔍 扫描项目文件中...")
    all_files: list[Path] = []
    all_images: list[Path] = []

    def scan_dir(d: Path) -> None:
        try:
            for entry in sorted(d.iterdir(), key=lambda p: p.name.lower()):
                if entry.is_dir():
                    if entry.name not in CONFIG["exclude_dirs"]:
                        scan_dir(entry)
                else:
                    ext = entry.suffix.lower()
                    if ext in CONFIG["scan_extensions"]:
                        all_files.append(entry)
                    elif ext in CONFIG["image_extensions"]:
                        all_images.append(entry)
        except PermissionError as e:
            print(f"⚠️ 跳过目录（无权限）: {d} — {e}", file=sys.stderr)

    scan_dir(root_dir.resolve())

    if CONFIG["verbose"]:
        print(f"📂 找到 {len(all_files)} 个可扫描文件")
        print(f"🖼️  找到 {len(all_images)} 个图片文件")

    return all_files, all_images


def find_image_references(content: str) -> list[str]:
    matches: list[str] = []
    for pattern in (RE_MD_IMG, RE_HTML_IMG, RE_CSS_BG):
        for m in pattern.finditer(content):
            raw = m.group(1) if m.lastindex else ""
            if not raw:
                continue
            clean = re.split(r"[?#]", raw, maxsplit=1)[0]
            clean = _strip_md_angle_brackets(clean)
            if clean and not clean.lower().startswith("http"):
                matches.append(clean)
    return matches


def find_used_images(file_paths: list[Path]) -> set[str]:
    print("🔎 查找被引用的图片...")
    used: set[str] = set()

    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"⚠️ 无法读取文件 {file_path}: {e}")
            continue

        for ref in find_image_references(content):
            resolved = os.path.normpath(os.path.join(str(file_path.parent), ref))
            used.add(resolved)

    if CONFIG["verbose"]:
        print(f"🔗 找到 {len(used)} 个被引用的图片路径")

    return used


def find_unused_images(all_images: list[Path], used_images: set[str]) -> list[Path]:
    """未使用图片：规范化后与已引用集合比对（与 JS 版一致）。"""
    used_list = [os.path.normpath(p) for p in used_images]

    def is_used(img: Path) -> bool:
        normalized = os.path.normpath(str(img))
        if any(os.path.normpath(u) == normalized for u in used_list):
            return True
        # Windows：盘符大小写等
        return any(os.path.normcase(os.path.normpath(u)) == os.path.normcase(normalized) for u in used_list)

    return [img for img in all_images if not is_used(img)]


def format_file_size(num_bytes: int) -> str:
    if num_bytes == 0:
        return "0 Bytes"
    k = 1024.0
    sizes = ["Bytes", "KB", "MB", "GB"]
    i = int(math.floor(math.log(num_bytes) / math.log(k)))
    i = min(i, len(sizes) - 1)
    return f"{(num_bytes / math.pow(k, i)):.2f} {sizes[i]}"


def calculate_total_size(paths: list[Path]) -> int:
    total = 0
    for p in paths:
        try:
            total += p.stat().st_size
        except OSError as e:
            print(f"⚠️ 无法获取文件大小 {p}: {e}")
    return total


def report_results(unused: list[Path], base_path: Path) -> None:
    print(f"\n❌ 发现 {len(unused)} 个未使用的图片文件:")
    if CONFIG["verbose"]:
        for i, img in enumerate(unused, 1):
            try:
                rel = os.path.relpath(str(img), str(base_path))
            except ValueError:
                rel = str(img)
            print(f"  {i}. {rel}")
    total = calculate_total_size(unused)
    print(f"\n📊 总大小: {format_file_size(total)}")


def delete_unused_images(unused: list[Path], base_path: Path) -> None:
    print("\n🗑️ 开始删除未使用的图片...")
    ok, fail = 0, 0
    for img in unused:
        try:
            img.unlink()
            if CONFIG["verbose"]:
                try:
                    rel = os.path.relpath(str(img), str(base_path))
                except ValueError:
                    rel = str(img)
                print(f"  ✅ 已删除: {rel}")
            ok += 1
        except OSError as e:
            print(f"  ❌ 删除失败 {img}: {e}")
            fail += 1
    print(f"\n删除完成: {ok} 成功, {fail} 失败")


def ask_confirmation(question: str) -> bool:
    ans = input(question + " ").strip().lower()
    return ans == "y"


def main() -> int:
    log_header()
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()

    if not target.is_dir():
        print(f"❌ 不是目录: {target}", file=sys.stderr)
        return 1

    print(f"📁 扫描目录: {target}")

    try:
        all_files, all_images = scan_project(target)
        used = find_used_images(all_files)
        unused = find_unused_images(all_images, used)

        if not unused:
            print("🎉 没有发现未使用的图片资源!")
            return 0

        report_results(unused, target)

        if ask_confirmation(f"确定要删除 {len(unused)} 个未使用的图片文件吗? (y/N)"):
            delete_unused_images(unused, target)
        return 0
    except KeyboardInterrupt:
        print("\n已取消。", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ 发生错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
