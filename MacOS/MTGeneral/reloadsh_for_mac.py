#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
import argparse
from pathlib import Path

# ----------------------------------------------------------------------
# 函数扫描：从 .zsh 脚本中提取函数名（忽略以下划线开头的）
# ----------------------------------------------------------------------
def find_functions_in_zsh(filepath):
    """
    扫描 .zsh 文件，返回函数信息列表。
    每个元素为字典：{"name": 函数名, "description": ""}
    描述字段留空（可自行扩展注释提取）。
    """
    functions = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # 匹配函数定义行： name() {  或 name () {
        # 函数名只能包含字母、数字、下划线，且不能以数字开头
        pattern = r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)\s*\{'
        for i, line in enumerate(lines):
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                # 忽略以下划线开头的函数
                if func_name.startswith('_'):
                    continue
                # 描述字段留空，如需提取注释可在此扩展
                functions.append({"name": func_name, "description": ""})
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    return functions

# ----------------------------------------------------------------------
# 主程序
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='reloadsh for macOS (Zsh function tracker)')
    parser.add_argument('--zsh-dir', required=True, help='Path to directory containing *.zsh files')
    parser.add_argument('--json-file', required=True, help='Path to function_tracker.json')
    args = parser.parse_args()

    zsh_dir = Path(args.zsh_dir)
    json_file = Path(args.json_file)

    # 读取旧数据（函数名列表）
    old_function_names = []
    old_data = {}  # 保存完整的旧 JSON 数据
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                old_data = data
                # 兼容两种格式：{"function": {"name": {"description": ...}}} 或 {"functionName": [...]}
                if "function" in data:
                    old_function_names = list(data["function"].keys())
                elif "functionName" in data:
                    old_function_names = data["functionName"]
        except Exception as e:
            print(f"⚠️ Warning: Could not read existing {json_file} (will be overwritten): {e}", file=sys.stderr)

    # 递归扫描所有 *.zsh 文件，获取新函数信息
    zsh_files = sorted(zsh_dir.rglob('*.zsh'))
    new_function_infos = []
    for zsh_file in zsh_files:
        new_function_infos.extend(find_functions_in_zsh(zsh_file))

    # 去重（同名函数保留首次扫描到的描述）
    unique_functions = {}
    for info in new_function_infos:
        name = info["name"]
        if name not in unique_functions:
            unique_functions[name] = info["description"]

    # 构建新函数列表（按名称排序）
    new_function_names = sorted(unique_functions.keys())
    new_functions = [{"name": name, "description": unique_functions[name]} for name in new_function_names]

    # 计算添加/删除
    old_set = set(old_function_names)
    new_set = set(new_function_names)
    added = sorted(list(new_set - old_set))
    removed = sorted(list(old_set - new_set))

    # 构建新 JSON 数据：保留旧数据中的其他字段（如 pythonPackage），更新 function 字典
    function_dict = {info["name"]: {"description": info["description"]} for info in new_functions}
    json_data = dict(old_data)  # 复制旧数据
    json_data["function"] = function_dict
    # 可选：移除 pythonPackage 字段或保留为空列表（原 Windows 版本有该字段，这里为了兼容可置空）
    json_data["pythonPackage"] = json_data.get("pythonPackage", [])

    # 写入 JSON 文件
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 彩色输出结果（兼容 macOS 终端）
    # ------------------------------------------------------------------
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    RESET = '\033[0m'

    print(f"{GREEN}reloadsh for macOS{RESET}")
    print(f"{CYAN}📊 之前记录的函数数: {len(old_function_names)}{RESET}")
    print(f"{CYAN}📊 当前扫描到的函数数: {len(new_function_names)}{RESET}")

    if added:
        print(f"{GREEN}🆕 新增函数 ({len(added)}):{RESET}")
        for func in added:
            print(f"{GREEN}   ✅ {func}{RESET}")
    else:
        print(f"{GREEN}✅ 没有新增函数{RESET}")

    if removed:
        print(f"{RED}🗑️  删除函数 ({len(removed)}):{RESET}")
        for func in removed:
            print(f"{RED}   ❌ {func}{RESET}")
    else:
        print(f"{GREEN}✅ 没有删除函数{RESET}")

    print(f"{CYAN}✅ 已重新加载所有函数文件{RESET}")
    print(f"{GREEN}✅ 函数列表已更新到 {json_file}{RESET}")

    # ------------------------------------------------------------------
    # 提示用户手动 source（因为 Python 无法重新加载当前 shell）
    # ------------------------------------------------------------------
    print("\n💡 提示：请执行以下命令使更改在当前 shell 中生效：")
    print("   source ~/.zshrc")
    print("如果已将函数定义放在其他文件中，请确保它们已被 .zshrc 引用。")

    sys.exit(0)

if __name__ == "__main__":
    main()