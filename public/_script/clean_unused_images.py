#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clean_unused_images — 过滤 .md / .html / .htm 中未被引用的图片资源。
逻辑与 cleanUnusedImages.js 对齐；依赖仅标准库。

用法:
    python clean_unused_images.py [扫描目录]
    未传目录时默认为「当前工作目录」（即你在终端里 cd 到的目录，与 tool_ 从何处调用无关）。
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
    "exclude_dirs": {"node_modules", ".git", "dist", "build", ".obsidian"},
    "verbose": True,
}

# 标准 Markdown / HTML / CSS
RE_MD_IMG = re.compile(r"!\[.*?\]\((.*?)\)")
RE_HTML_IMG = re.compile(r'<img[^>]+src=["\'](.*?)["\']', re.IGNORECASE)
RE_CSS_BG = re.compile(
    r"background(?:-image)?\s*:\s*url\([\"']?(.*?)[\"']?\)",
    re.IGNORECASE,
)
# Obsidian embed：![[path]]、![[path|100]]、![[path#heading|alias]]
RE_OBSIDIAN_EMBED = re.compile(r"!\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")


def _strip_md_angle_brackets(url: str) -> str:
    """Markdown 中 ![](<path with spaces>) 会包一层尖括号，需去掉再拼路径。"""
    s = url.strip()
    if len(s) >= 2 and s[0] == "<" and s[-1] == ">":
        return s[1:-1].strip()
    return s


def _is_image_ref(ref: str) -> bool:
    """引用目标是否像图片路径（用于 Obsidian 按文件名匹配时过滤非图片笔记链接）。"""
    return Path(ref).suffix.lower() in CONFIG["image_extensions"]


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

    # Obsidian wikilink / embed（路径段已排除 | 与 #）
    for m in RE_OBSIDIAN_EMBED.finditer(content):
        clean = m.group(1).strip()
        if clean and not clean.lower().startswith("http"):
            matches.append(clean)

    return matches


def find_used_images(
    file_paths: list[Path], root_dir: Path
) -> tuple[set[str], set[str]]:
    """返回 (规范化绝对路径集合, 文件名小写集合)。

    Obsidian 解析顺序近似：
    1. 相对当前笔记目录
    2. 相对库根目录
    3. 仅文件名时在库内按唯一名查找 → 用 basename 保守标记为已用
    """
    print("🔎 查找被引用的图片...")
    used_paths: set[str] = set()
    used_names: set[str] = set()
    root = str(root_dir.resolve())

    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"⚠️ 无法读取文件 {file_path}: {e}")
            continue

        parent = str(file_path.parent)
        for ref in find_image_references(content):
            used_paths.add(os.path.normpath(os.path.join(parent, ref)))
            used_paths.add(os.path.normpath(os.path.join(root, ref)))
            if _is_image_ref(ref):
                used_names.add(Path(ref).name.lower())

    if CONFIG["verbose"]:
        print(f"🔗 找到 {len(used_paths)} 个被引用路径候选, {len(used_names)} 个文件名")

    return used_paths, used_names


def find_unused_images(
    all_images: list[Path], used_paths: set[str], used_names: set[str]
) -> list[Path]:
    """未使用图片：路径命中或（Obsidian）文件名命中均视为已引用。"""
    used_norm = {os.path.normpath(p) for p in used_paths}
    used_normcase = {os.path.normcase(p) for p in used_norm}

    def is_used(img: Path) -> bool:
        normalized = os.path.normpath(str(img))
        if normalized in used_norm:
            return True
        if os.path.normcase(normalized) in used_normcase:
            return True
        # Obsidian：![[foo.png]] 可跨目录按文件名解析
        return img.name.lower() in used_names

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
        used_paths, used_names = find_used_images(all_files, target)
        unused = find_unused_images(all_images, used_paths, used_names)

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
