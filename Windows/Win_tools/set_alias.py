# .\Windows\Win_tools\set_alias.ps1

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import re
import shlex
import os

# 文件路径常量
CHINESE_LANGUAGE_PATH = r"D:\Code\aom\KingAutomate\Res\chinese.json"
FUNCTION_ALIAS_PATH = r"D:\Code\aom\KingAutomate\Res\FunctionSetting.json"

def load_chinese_map():
    try:
        with open(CHINESE_LANGUAGE_PATH, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        return {value: key for key, value in data.items()}
    except Exception as e:
        print(f"加载中文语言包失败: {e}")
        return {}

def load_function_settings():
    try:
        with open(FUNCTION_ALIAS_PATH, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载函数别名配置失败: {e}")
        return {}

def save_function_settings(settings):
    try:
        os.makedirs(os.path.dirname(FUNCTION_ALIAS_PATH), exist_ok=True)
        with open(FUNCTION_ALIAS_PATH, 'w', encoding='utf-8-sig') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存函数别名配置失败: {e}")
        return False

def remove_version_suffix(key):
    return re.sub(r'V\d+$', '', key) if key else key

def convert_to_rpa_alias(cleaned_key):
    if not cleaned_key:
        return None
    return 'RPA' + cleaned_key.replace('.', '')

def normalize_alias(alias_str):
    return alias_str.strip().lower()

def split_alias_arg(alias_arg):
    arg = alias_arg.strip()
    if not arg:
        return []
    if ',' in arg:
        return [normalize_alias(p) for p in arg.split(',') if p.strip()]
    return [normalize_alias(arg)]

def main():
    chinese_to_key = load_chinese_map()
    if not chinese_to_key:
        print("警告：中文语言包加载失败或为空，查询功能不可用")

    function_settings = load_function_settings()
    if function_settings is None:
        function_settings = {}

    print("Lite Alias 设置模式已启动，输入 wq 退出")
    print("可用命令：")
    print("  <中文文本> view                     # 查询对应的原始键名、RPA别名及已配置的别名列表")
    print("  <中文文本> add <别名列表>            # 添加别名（多个别名用逗号分隔，支持引号包裹含空格的别名）")
    print("  <中文文本> rm <别名列表>             # 删除指定的别名（多个别名用逗号分隔）")
    print("  <中文文本> rm -f                     # 强制删除整个 RPA 别名条目（包括其所有别名）")

    while True:
        try:
            raw_cmd = input(">>> ").strip()
            if not raw_cmd:
                continue
            # 退出指令：支持 wq 或 :wq（兼容旧习惯）
            if raw_cmd.lower() in ("wq", ":wq"):
                print("退出设置模式")
                break

            tokens = shlex.split(raw_cmd)
            if len(tokens) < 2:
                print("命令格式错误，请参考帮助信息")
                continue

            query = tokens[0]
            command = tokens[1].lower()

            if command == "view":
                if len(tokens) != 2:
                    print("用法: <中文文本> view")
                    continue
                raw_key = chinese_to_key.get(query)
                if not raw_key:
                    print(f"未找到中文 '{query}' 对应的键名")
                    continue
                cleaned_key = remove_version_suffix(raw_key)
                rpa_alias = convert_to_rpa_alias(cleaned_key)
                print(f"原始键名: {raw_key}")
                print(f"RPA 别名: {rpa_alias}")
                if function_settings and rpa_alias in function_settings:
                    entry = function_settings[rpa_alias]
                    alias_data = entry.get("alias", [])
                    name_data = entry.get("name")
                    if name_data:
                        print(f"中文名称: {name_data}")
                    if alias_data:
                        print(f"别名列表: {alias_data}")
                    else:
                        print("别名列表: 空（配置中 alias 字段不存在或为空）")
                else:
                    print("别名列表: 未配置（FunctionSetting.json 中无此键）")

            elif command == "add":
                if len(tokens) < 3:
                    print("用法: <中文文本> add <别名列表>")
                    continue
                alias_arg = tokens[2]
                raw_key = chinese_to_key.get(query)
                if not raw_key:
                    print(f"未找到中文 '{query}' 对应的键名")
                    continue
                cleaned_key = remove_version_suffix(raw_key)
                rpa_alias = convert_to_rpa_alias(cleaned_key)

                if rpa_alias not in function_settings:
                    function_settings[rpa_alias] = {"alias": [], "name": query}
                elif "alias" not in function_settings[rpa_alias]:
                    function_settings[rpa_alias]["alias"] = []

                current_aliases = [normalize_alias(a) for a in function_settings[rpa_alias]["alias"]]
                new_aliases = split_alias_arg(alias_arg)
                added, existed = [], []
                for alias in new_aliases:
                    if alias in current_aliases:
                        existed.append(alias)
                    else:
                        function_settings[rpa_alias]["alias"].append(alias)
                        added.append(alias)

                if added or existed:
                    if save_function_settings(function_settings):
                        if added:
                            print(f"已添加别名: {', '.join(added)}")
                        if existed:
                            print(f"别名已存在: {', '.join(existed)}")
                        print(f"当前别名列表: {function_settings[rpa_alias]['alias']}")
                    else:
                        print("保存失败，请检查权限或磁盘空间")
                else:
                    print("没有需要添加的别名")

            elif command == "rm":
                # 处理 rm -f 强制删除整个条目
                if len(tokens) == 3 and tokens[2] == "-f":
                    raw_key = chinese_to_key.get(query)
                    if not raw_key:
                        print(f"未找到中文 '{query}' 对应的键名")
                        continue
                    cleaned_key = remove_version_suffix(raw_key)
                    rpa_alias = convert_to_rpa_alias(cleaned_key)
                    if rpa_alias not in function_settings:
                        print(f"RPA 别名 '{rpa_alias}' 在配置中不存在，无法删除")
                        continue
                    confirm = input(f"确定要删除整个 RPA 别名条目 '{rpa_alias}' 吗？(y/N): ").strip().lower()
                    if confirm != 'y':
                        print("已取消删除")
                        continue
                    del function_settings[rpa_alias]
                    if save_function_settings(function_settings):
                        print(f"已删除整个 RPA 别名条目: {rpa_alias}")
                    else:
                        print("保存失败，请检查权限或磁盘空间")
                    continue

                # 原有的删除指定别名逻辑
                if len(tokens) < 3:
                    print("用法: <中文文本> rm <别名列表>  或  <中文文本> rm -f")
                    continue
                alias_arg = tokens[2]
                raw_key = chinese_to_key.get(query)
                if not raw_key:
                    print(f"未找到中文 '{query}' 对应的键名")
                    continue
                cleaned_key = remove_version_suffix(raw_key)
                rpa_alias = convert_to_rpa_alias(cleaned_key)
                if rpa_alias not in function_settings:
                    print(f"RPA 别名 '{rpa_alias}' 在配置中不存在，无别名可删")
                    continue
                if "alias" not in function_settings[rpa_alias]:
                    function_settings[rpa_alias]["alias"] = []
                to_delete = split_alias_arg(alias_arg)
                if not to_delete:
                    print("没有指定要删除的别名")
                    continue
                current_list = function_settings[rpa_alias]["alias"]
                delete_set = set(to_delete)
                new_list, removed = [], []
                for alias in current_list:
                    norm = normalize_alias(alias)
                    if norm in delete_set:
                        delete_set.remove(norm)
                        removed.append(norm)
                    else:
                        new_list.append(alias)
                not_found = list(delete_set)
                function_settings[rpa_alias]["alias"] = new_list
                if removed or not_found:
                    if save_function_settings(function_settings):
                        if removed:
                            print(f"已删除别名: {', '.join(removed)}")
                        if not_found:
                            print(f"别名不存在: {', '.join(not_found)}")
                        print(f"当前别名列表: {function_settings[rpa_alias]['alias']}")
                    else:
                        print("保存失败，请检查权限或磁盘空间")
                else:
                    print("没有需要删除的别名")
            else:
                print(f"未知命令: {command}")

        except (KeyboardInterrupt, EOFError):
            print("\n退出设置模式")
            break
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()