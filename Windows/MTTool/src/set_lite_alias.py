# .\Windows\Win_tools\set_lite_alias.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import re
import shlex
import os
import ast
import subprocess

# 文件路径常量
CHINESE_LANGUAGE_PATH = r"D:\Code\aom\KingAutomate\Res\chinese.json"
FUNCTION_ALIAS_PATH = r"D:\Code\aom\KingAutomate\Res\FunctionSetting.json"
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'temp', 'alias_change_record.txt')
REPO_ROOT = r"D:\Code\aom"
TARGET_FILE = r"KingAutomate\Res\FunctionSetting.json"

# 全局缓存：存储待添加的联想关系
# 结构: { source_rpa_alias: [(target_rpa_alias, target_cn), ...] }
pending_relevance = {}

def load_chinese_map():
    try:
        with open(CHINESE_LANGUAGE_PATH, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        chinese_to_keys = {}
        for key, chinese in data.items():
            if chinese not in chinese_to_keys:
                chinese_to_keys[chinese] = []
            chinese_to_keys[chinese].append(key)
        return chinese_to_keys
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

def compact_json_arrays(json_str):
    """
    将 JSON 字符串中的所有数组（[...]）压缩为单行。
    注意：假设数组内没有嵌套数组，且字符串值中不包含未转义的方括号。
    """
    pattern = r'\[\s*(.*?)\s*\]'

    def replacer(match):
        inner = match.group(1)
        inner = re.sub(r'\n\s+', ' ', inner)
        inner = inner.strip()
        return f'[{inner}]'

    return re.sub(pattern, replacer, json_str, flags=re.DOTALL)

def save_function_settings(settings):
    try:
        os.makedirs(os.path.dirname(FUNCTION_ALIAS_PATH), exist_ok=True)
        json_str = json.dumps(settings, indent=2, ensure_ascii=False)
        json_str = compact_json_arrays(json_str)
        with open(FUNCTION_ALIAS_PATH, 'w', encoding='utf-8') as f:
            f.write(json_str)
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

def load_net_state():
    net_add = {}
    net_remove = {}
    alias_info = {}
    if not os.path.exists(LOG_PATH):
        return net_add, net_remove, alias_info
    try:
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        section = None
        for line in lines:
            line = line.rstrip('\n')
            if line.startswith('# 新增'):
                section = 'add'
                continue
            elif line.startswith('# 删除'):
                section = 'remove'
                continue
            elif line.startswith('#') or not line.strip():
                continue
            if section in ('add', 'remove'):
                match = re.match(r'\[(.+?)\]_别名:\s*(.+)', line)
                if not match:
                    continue
                info_part = match.group(1)
                list_part = match.group(2)
                try:
                    alias_list = ast.literal_eval(list_part)
                    if not isinstance(alias_list, list):
                        continue
                    if '|' in info_part:
                        chinese = info_part.split('|', 1)[0].strip()
                        raw_key = info_part.split('|', 1)[1].strip()
                    else:
                        chinese = info_part
                        raw_key = info_part
                    cleaned = remove_version_suffix(raw_key)
                    rpa_alias = convert_to_rpa_alias(cleaned)
                    alias_info[rpa_alias] = (chinese, raw_key)
                    if section == 'add':
                        net_add[rpa_alias] = set(alias_list)
                    else:
                        net_remove[rpa_alias] = set(alias_list)
                except:
                    continue
    except Exception as e:
        print(f"读取日志失败: {e}")
    return net_add, net_remove, alias_info

def apply_pending_relevance():
    """将缓存的联想关系应用到 function_settings 中，并清空缓存"""
    global pending_relevance
    if not pending_relevance:
        return

    for source_rpa, links in pending_relevance.items():
        if source_rpa not in function_settings:
            # 如果源条目不存在，跳过（理论上不应该发生，但安全起见）
            continue

        entry = function_settings[source_rpa]
        # 获取现有列表
        relevance_list = entry.get("relevance", [])
        relevance_cn_list = entry.get("relevance_cn", [])

        # 去重合并
        for target_rpa, target_cn in links:
            if target_rpa not in relevance_list:
                relevance_list.append(target_rpa)
                relevance_cn_list.append(target_cn)

        entry["relevance"] = relevance_list
        entry["relevance_cn"] = relevance_cn_list

    # 清空缓存
    pending_relevance.clear()

def remove_from_pending_relevance(source_rpa, target_cn):
    """从 pending_relevance 缓存中移除指定源和目标联想关系（如果有）"""
    global pending_relevance
    if source_rpa not in pending_relevance:
        return
    # 过滤掉匹配 target_cn 的项
    new_links = [(rpa, cn) for (rpa, cn) in pending_relevance[source_rpa] if cn != target_cn]
    if new_links:
        pending_relevance[source_rpa] = new_links
    else:
        del pending_relevance[source_rpa]

def main():
    global function_settings  # 声明为全局，以便在 apply_pending_relevance 中访问
    chinese_to_keys = load_chinese_map()
    if not chinese_to_keys:
        print("警告：中文语言包加载失败或为空，查询功能不可用")

    function_settings = load_function_settings()
    if function_settings is None:
        function_settings = {}

    net_add, net_remove, alias_info = load_net_state()

    def write_final_log():
        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, 'w', encoding='utf-8') as f:
                f.write("# rpalite:lite函数别名变更\n")
                f.write("\n")
                f.write("# 新增\n")
                for rpa_alias in sorted(net_add.keys()):
                    if rpa_alias not in alias_info:
                        continue
                    chinese, raw_key = alias_info[rpa_alias]
                    alias_list = sorted(net_add[rpa_alias])
                    line = f"[{chinese} | {raw_key}]_别名: {json.dumps(alias_list, ensure_ascii=False)}"
                    f.write(line + '\n')
                if net_add:
                    f.write("\n")
                f.write("# 删除\n")
                for rpa_alias in sorted(net_remove.keys()):
                    if rpa_alias not in alias_info:
                        continue
                    chinese, raw_key = alias_info[rpa_alias]
                    alias_list = sorted(net_remove[rpa_alias])
                    line = f"[{chinese} | {raw_key}]_别名: {json.dumps(alias_list, ensure_ascii=False)}"
                    f.write(line + '\n')
        except Exception as e:
            print(f"写入日志失败: {e}")

    print("Lite Alias 设置模式已启动，输入 wq 退出")
    print("可用命令：")
    print("  <中文文本> view                     # 查询对应的原始键名、RPA别名及已配置的别名列表")
    print("  <中文文本> add <别名列表>            # 添加别名（多个别名用逗号分隔，支持引号包裹含空格的别名）")
    print("  <中文文本> rm <别名列表>             # 删除指定的别名（多个别名用逗号分隔）")
    print("  <中文文本> rm -f                     # 强制删除整个 RPA 别名条目（包括其所有别名）")
    print("  <中文文本> add2 <联想中文列表>       # 为函数添加联想关系（多个联想中文用逗号分隔，缓存，退出时保存）")
    print("  <中文文本> rm2 <联想中文列表>        # 删除指定的联想关系（多个联想中文用逗号分隔，立即生效）")
    print("  <中文文本> rm2 -f                    # 删除指定函数的所有联想关系")
    print("  push                                 # 提交 FunctionSetting.json，并使用日志内容作为 commit message")

    while True:
        try:
            raw_cmd = input(">>> ").strip()
            if not raw_cmd:
                continue
            if raw_cmd.lower() in ("wq", ":wq"):
                # 应用缓存的联想关系并保存
                apply_pending_relevance()
                save_function_settings(function_settings)
                write_final_log()
                print("退出设置模式")
                break

            if raw_cmd.lower() == "push":
                # 先应用缓存的联想关系并保存，确保所有修改都被提交
                apply_pending_relevance()
                save_function_settings(function_settings)
                write_final_log()

                if not os.path.exists(LOG_PATH):
                    print("日志文件不存在，无法提交")
                    continue
                with open(LOG_PATH, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                print("\n=== 提交信息 ===")
                print(log_content)
                print("=================")
                confirm = input("确认提交以上变更？(y/N): ").strip().lower()
                if confirm != 'y':
                    print("提交已取消")
                    continue

                stash_created = False
                try:
                    os.chdir(REPO_ROOT)

                    # 2. git add 目标文件
                    add_result = subprocess.run(["git", "add", TARGET_FILE], capture_output=True, text=True, encoding='utf-8')
                    if add_result.returncode != 0:
                        print(f"git add 失败: {add_result.stderr}")
                        continue

                    # 3. 检查目标文件是否有变化（暂存区是否有内容）
                    diff_cached = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
                    if diff_cached.returncode == 0:
                        print("FunctionSetting.json 没有变化，无需提交")
                        subprocess.run(["git", "reset", TARGET_FILE])
                        continue

                    # 4. git stash -u -k 暂存其他更改（保留暂存区的目标文件）
                    stash_result = subprocess.run(["git", "stash", "push", "-u", "-k"], capture_output=True, text=True, encoding='utf-8')
                    stash_created = (stash_result.returncode == 0 and "No local changes to save" not in stash_result.stdout)

                    # 5. git commit
                    commit_result = subprocess.run(["git", "commit", "-F", LOG_PATH], capture_output=True, text=True, encoding='utf-8')
                    if commit_result.returncode != 0:
                        print("提交失败:", commit_result.stderr)
                        if stash_created:
                            subprocess.run(["git", "stash", "pop"], capture_output=True)
                        subprocess.run(["git", "reset", TARGET_FILE])
                        continue

                    print("提交成功:", commit_result.stdout)

                    # 6. 提交成功后清空净变更状态并重置日志
                    net_add.clear()
                    net_remove.clear()
                    write_final_log()
                    print("日志已清空，准备下一次累积")

                    # 7. git pull --rebase
                    pull_result = subprocess.run(["git", "pull", "--rebase"], capture_output=True, text=True, encoding='utf-8')
                    if pull_result.returncode != 0:
                        print("git pull --rebase 失败，请手动解决冲突。")
                        if pull_result.stderr:
                            print(pull_result.stderr)
                        print("由于 pull 失败，请手动处理冲突后执行 git push，然后执行 git stash pop 恢复工作区。")
                        continue

                    # 8. git push
                    push_result = subprocess.run(["git", "push"], capture_output=True, text=True, encoding='utf-8')
                    if push_result.returncode == 0:
                        print("推送成功:", push_result.stdout)
                    else:
                        print("推送失败:", push_result.stderr)
                        print("请手动处理推送问题，然后执行 git stash pop 恢复工作区。")
                        continue

                    # 9. git stash pop 恢复工作区
                    if stash_created:
                        pop_result = subprocess.run(["git", "stash", "pop"], capture_output=True, text=True, encoding='utf-8')
                        if pop_result.returncode == 0:
                            print("工作区已恢复")
                        else:
                            print("恢复 stash 失败，请手动解决冲突。")
                            if pop_result.stderr:
                                print(pop_result.stderr)

                except Exception as e:
                    print(f"执行 git 操作出错: {e}")
                    subprocess.run(["git", "reset", TARGET_FILE], stderr=subprocess.DEVNULL)
                    if stash_created:
                        subprocess.run(["git", "stash", "pop"], stderr=subprocess.DEVNULL)
                continue

            tokens = shlex.split(raw_cmd)
            if len(tokens) < 2:
                print("命令格式错误，请参考帮助信息")
                continue

            query = tokens[0]
            command = tokens[1].lower()
            raw_keys = chinese_to_keys.get(query, [])
            if not raw_keys:
                print(f"未找到中文 '{query}' 对应的键名")
                continue

            if len(raw_keys) > 1:
                print(f"提示：中文 '{query}' 对应多个键名: {', '.join(raw_keys)}")

            if command == "view":
                if len(tokens) != 2:
                    print("用法: <中文文本> view")
                    continue
                for raw_key in raw_keys:
                    cleaned_key = remove_version_suffix(raw_key)
                    rpa_alias = convert_to_rpa_alias(cleaned_key)
                    if rpa_alias not in alias_info:
                        alias_info[rpa_alias] = (query, raw_key)

                    print(f"\n原始键名: {raw_key}")
                    print(f"RPA 别名: {rpa_alias}")
                    if function_settings and rpa_alias in function_settings:
                        entry = function_settings[rpa_alias]
                        alias_data = entry.get("alias", [])
                        name_data = entry.get("name")
                        relevance_data = entry.get("relevance_cn")  # 显示中文联想
                        if name_data:
                            print(f"中文名称: {name_data}")
                        if alias_data:
                            print(f"别名列表: {alias_data}")
                        else:
                            print("别名列表: 空")
                        if relevance_data:
                            print(f"函数联想列表: {relevance_data}")
                    else:
                        print("别名列表: 未配置")
                continue

            elif command == "add":
                if len(tokens) < 3:
                    print("用法: <中文文本> add <别名列表>")
                    continue
                alias_arg = tokens[2]
                new_aliases = split_alias_arg(alias_arg)
                if not new_aliases:
                    print("没有指定要添加的别名")
                    continue

                for raw_key in raw_keys:
                    cleaned_key = remove_version_suffix(raw_key)
                    rpa_alias = convert_to_rpa_alias(cleaned_key)
                    if rpa_alias not in alias_info:
                        alias_info[rpa_alias] = (query, raw_key)

                    if rpa_alias not in function_settings:
                        function_settings[rpa_alias] = {"alias": [], "name": query}
                    elif "alias" not in function_settings[rpa_alias]:
                        function_settings[rpa_alias]["alias"] = []

                    current_aliases = [normalize_alias(a) for a in function_settings[rpa_alias]["alias"]]
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
                                print(f"[{raw_key}] 已添加别名: {', '.join(added)}")
                                added_set = set(added)
                                if rpa_alias not in net_add:
                                    net_add[rpa_alias] = set()
                                net_add[rpa_alias].update(added_set)
                                if rpa_alias in net_remove:
                                    net_remove[rpa_alias] -= added_set
                                    if not net_remove[rpa_alias]:
                                        del net_remove[rpa_alias]
                            if existed:
                                print(f"[{raw_key}] 别名已存在: {', '.join(existed)}")
                            print(f"[{raw_key}] 当前别名列表: {function_settings[rpa_alias]['alias']}")
                        else:
                            print(f"[{raw_key}] 保存失败")
                    else:
                        print(f"[{raw_key}] 没有需要添加的别名")
                continue

            elif command == "rm":
                if len(tokens) == 3 and tokens[2] == "-f":
                    if len(raw_keys) > 1:
                        confirm_all = input(f"中文 '{query}' 对应多个键名，是否删除所有对应的整个条目？(y/N): ").strip().lower()
                        if confirm_all != 'y':
                            print("已取消删除")
                            continue
                    for raw_key in raw_keys:
                        cleaned_key = remove_version_suffix(raw_key)
                        rpa_alias = convert_to_rpa_alias(cleaned_key)
                        if rpa_alias not in alias_info:
                            alias_info[rpa_alias] = (query, raw_key)

                        if rpa_alias not in function_settings:
                            print(f"[{raw_key}] RPA 别名 '{rpa_alias}' 在配置中不存在，无法删除")
                            continue
                        old_aliases = function_settings[rpa_alias].get("alias", [])
                        if len(raw_keys) == 1:
                            confirm = input(f"确定要删除整个 RPA 别名条目 '{rpa_alias}' 吗？(y/N): ").strip().lower()
                            if confirm != 'y':
                                print(f"[{raw_key}] 已取消删除")
                                continue
                        del function_settings[rpa_alias]
                        if save_function_settings(function_settings):
                            print(f"[{raw_key}] 已删除整个 RPA 别名条目: {rpa_alias}")
                            # 同时清除该条目在 pending_relevance 中的缓存
                            if rpa_alias in pending_relevance:
                                del pending_relevance[rpa_alias]
                            for alias in old_aliases:
                                norm_alias = normalize_alias(alias)
                                if rpa_alias in net_add and norm_alias in net_add[rpa_alias]:
                                    net_add[rpa_alias].discard(norm_alias)
                                    if not net_add[rpa_alias]:
                                        del net_add[rpa_alias]
                                else:
                                    if rpa_alias not in net_remove:
                                        net_remove[rpa_alias] = set()
                                    net_remove[rpa_alias].add(norm_alias)
                        else:
                            print(f"[{raw_key}] 保存失败")
                    continue

                if len(tokens) < 3:
                    print("用法: <中文文本> rm <别名列表>  或  <中文文本> rm -f")
                    continue
                alias_arg = tokens[2]
                to_delete = split_alias_arg(alias_arg)
                if not to_delete:
                    print("没有指定要删除的别名")
                    continue

                for raw_key in raw_keys:
                    cleaned_key = remove_version_suffix(raw_key)
                    rpa_alias = convert_to_rpa_alias(cleaned_key)
                    if rpa_alias not in alias_info:
                        alias_info[rpa_alias] = (query, raw_key)

                    if rpa_alias not in function_settings:
                        print(f"[{raw_key}] RPA 别名 '{rpa_alias}' 在配置中不存在，无别名可删")
                        continue
                    if "alias" not in function_settings[rpa_alias]:
                        function_settings[rpa_alias]["alias"] = []

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
                                print(f"[{raw_key}] 已删除别名: {', '.join(removed)}")
                                for norm_alias in removed:
                                    if rpa_alias in net_add and norm_alias in net_add[rpa_alias]:
                                        net_add[rpa_alias].discard(norm_alias)
                                        if not net_add[rpa_alias]:
                                            del net_add[rpa_alias]
                                    else:
                                        if rpa_alias not in net_remove:
                                            net_remove[rpa_alias] = set()
                                        net_remove[rpa_alias].add(norm_alias)
                            if not_found:
                                print(f"[{raw_key}] 别名不存在: {', '.join(not_found)}")
                            print(f"[{raw_key}] 当前别名列表: {function_settings[rpa_alias]['alias']}")
                        else:
                            print(f"[{raw_key}] 保存失败")
                    else:
                        print(f"[{raw_key}] 没有需要删除的别名")
                continue

            elif command == "add2":
                if len(tokens) < 3:
                    print("用法: <中文文本> add2 <联想中文列表>")
                    continue
                # 支持逗号分隔多个联想中文
                target_cns = [t.strip() for t in tokens[2].split(',') if t.strip()]
                if not target_cns:
                    print("没有指定联想中文")
                    continue

                success_targets = []
                failed_targets = []

                for target_cn in target_cns:
                    # 获取联想目标对应的原始键名列表
                    target_raw_keys = chinese_to_keys.get(target_cn, [])
                    if not target_raw_keys:
                        failed_targets.append(target_cn)
                        print(f"警告：未找到中文 '{target_cn}' 对应的键名，跳过")
                        continue

                    # 转换为 RPA 别名（去重）
                    target_rpa_aliases = []
                    for raw_key in target_raw_keys:
                        cleaned = remove_version_suffix(raw_key)
                        rpa_alias = convert_to_rpa_alias(cleaned)
                        if rpa_alias and rpa_alias not in target_rpa_aliases:
                            target_rpa_aliases.append(rpa_alias)

                    # 对于每个源中文（query）对应的每个原始键名，添加联想关系
                    for raw_key in raw_keys:
                        cleaned = remove_version_suffix(raw_key)
                        source_rpa = convert_to_rpa_alias(cleaned)
                        if not source_rpa:
                            continue
                        # 确保源条目在 function_settings 中存在（至少要有 name）
                        if source_rpa not in function_settings:
                            function_settings[source_rpa] = {"alias": [], "name": query}
                        # 将联想关系添加到 pending_relevance 缓存中（去重）
                        if source_rpa not in pending_relevance:
                            pending_relevance[source_rpa] = []
                        # 添加不存在的
                        for target_rpa in target_rpa_aliases:
                            if not any(item[0] == target_rpa for item in pending_relevance[source_rpa]):
                                pending_relevance[source_rpa].append((target_rpa, target_cn))
                    success_targets.append(target_cn)

                # 输出汇总信息
                if success_targets:
                    print(f"已缓存联想关系：{query} -> {', '.join(success_targets)}")
                if failed_targets:
                    print(f"未找到的目标：{', '.join(failed_targets)}")
                continue

            elif command == "rm2":
                # 处理强制删除所有联想关系
                if len(tokens) == 3 and tokens[2] == "-f":
                    # 确认操作
                    if len(raw_keys) > 1:
                        confirm_all = input(f"中文 '{query}' 对应多个键名，是否删除所有这些函数的所有联想关系？(y/N): ").strip().lower()
                        if confirm_all != 'y':
                            print("已取消删除")
                            continue
                    # 对每个源键名执行清空
                    deleted_any = False
                    for raw_key in raw_keys:
                        cleaned_key = remove_version_suffix(raw_key)
                        source_rpa = convert_to_rpa_alias(cleaned_key)
                        if not source_rpa:
                            continue
                        if source_rpa not in function_settings:
                            print(f"[{raw_key}] 未在配置中找到，跳过")
                            continue
                        entry = function_settings[source_rpa]
                        # 如果已有 relevance 字段，清空
                        if "relevance" in entry or "relevance_cn" in entry:
                            entry["relevance"] = []
                            entry["relevance_cn"] = []
                            deleted_any = True
                        # 同时清理 pending_relevance 缓存中的该条目
                        if source_rpa in pending_relevance:
                            del pending_relevance[source_rpa]
                    if deleted_any:
                        if save_function_settings(function_settings):
                            print(f"已删除函数 {query} 的所有联想关系")
                        else:
                            print("保存失败")
                    else:
                        print(f"函数 {query} 没有联想关系可删除")
                    continue

                # 原有 rm2 逻辑：删除指定的联想中文列表
                if len(tokens) < 3:
                    print("用法: <中文文本> rm2 <联想中文列表>  或  <中文文本> rm2 -f")
                    continue
                # 支持逗号分隔多个联想中文
                target_cns = [t.strip() for t in tokens[2].split(',') if t.strip()]
                if not target_cns:
                    print("没有指定要删除的联想中文")
                    continue

                # 记录删除结果
                removed_targets = []   # 成功删除的目标
                not_found_targets = [] # 未在配置中找到的目标
                errors = []            # 其他错误

                # 对每个源键名（可能多个）进行删除操作
                for raw_key in raw_keys:
                    cleaned_key = remove_version_suffix(raw_key)
                    source_rpa = convert_to_rpa_alias(cleaned_key)
                    if not source_rpa:
                        continue
                    if source_rpa not in function_settings:
                        # 源条目不存在，所有目标都视为未找到
                        not_found_targets.extend(target_cns)
                        continue

                    entry = function_settings[source_rpa]
                    relevance_list = entry.get("relevance", [])
                    relevance_cn_list = entry.get("relevance_cn", [])

                    # 对于每个目标中文，从列表中删除
                    for target_cn in target_cns:
                        # 查找匹配的索引（可能有多个，但通常只有一个，且应只删一个）
                        indices_to_remove = [i for i, cn in enumerate(relevance_cn_list) if cn == target_cn]
                        if not indices_to_remove:
                            not_found_targets.append(target_cn)
                            continue

                        # 删除所有匹配项（如果有重复，全部删除）
                        for idx in reversed(indices_to_remove):
                            del relevance_list[idx]
                            del relevance_cn_list[idx]

                        # 更新条目
                        entry["relevance"] = relevance_list
                        entry["relevance_cn"] = relevance_cn_list

                        # 从 pending_relevance 缓存中也删除对应项
                        remove_from_pending_relevance(source_rpa, target_cn)

                        if target_cn not in removed_targets:
                            removed_targets.append(target_cn)

                # 如果成功删除任何内容，保存文件
                if removed_targets:
                    if save_function_settings(function_settings):
                        print(f"已删除联想关系：{query} -> {', '.join(removed_targets)}")
                    else:
                        errors.append("保存失败")
                # 输出未找到的信息（去重）
                if not_found_targets:
                    unique_not_found = sorted(set(not_found_targets))
                    print(f"未找到的联想关系：{', '.join(unique_not_found)}")
                if errors:
                    for err in errors:
                        print(err)
                continue

            else:
                print(f"未知命令: {command}")

        except (KeyboardInterrupt, EOFError):
            print("\n退出设置模式")
            break
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()