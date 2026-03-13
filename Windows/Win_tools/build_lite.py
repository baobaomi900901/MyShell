# .\Windows\Win_tools\build_lite.py
# 包含 build-lite 子命令的具体实现，被 tool_ 函数调用

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KRPA Lite 自动化构建脚本（正式版远程版本号自动递增，格式优化）
执行步骤：
1. cd 到 D:\Code\aom
2. git reset --hard HEAD (使用 utf-8 编码)
3. git pull --rebase (使用 utf-8 编码)
4. 清空 KingAutomate\web 文件夹
5. 执行 now_ 命令，获取时间戳（只取第一行）
6. 询问构建类型：
   - 测试：生成 时间戳|分支_#_哈希 并复制
   - 正式发版：从远程获取 newversion，自动递增后生成 递增版本|分支_#_哈希 并复制
7. 运行 Build.exe（直接交还终端，用户手动交互）
"""

import os
import sys
import subprocess
import time
import shutil
import urllib.request
import configparser
import re
import ctypes
from pathlib import Path
import questionary

# 配置路径
AOM_PATH = r"D:\Code\aom"
BUILD_EXE = r"D:\Code\aom\KingAutomate\Build\Build\Build.exe"
WEB_DIR = r"D:\Code\aom\KingAutomate\web"
VERSION_INI_URL = "http://k-rpa-lite.kingsware.cn:50351/krpalite/package/LiteVersion.ini"


def run_command(cmd, cwd=None, check=True, encoding='gbk', timeout=None):
    """运行命令并返回是否成功（使用 subprocess.run）"""
    print(f"执行命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding=encoding,
            errors='replace',
            timeout=timeout
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)

        if check and result.returncode != 0:
            print(f"命令执行失败，返回码: {result.returncode}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"命令执行超时 (>{timeout}秒)")
        return False
    except Exception as e:
        print(f"执行命令异常: {e}")
        return False


def run_now_command():
    """执行 now_ 命令，返回第一行作为时间戳（如 '20260312-17:12'），失败返回 None"""
    print("正在执行 now_ 命令...")
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'now_'],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='replace'
        )
        if result.returncode == 0:
            lines = result.stdout.strip().splitlines()
            timestamp = lines[0].strip() if lines else ""
            print(f"now_ 输出: {timestamp}")
            return timestamp
        else:
            print(f"now_ 执行失败，返回码: {result.returncode}")
            return None
    except Exception as e:
        print(f"now_ 执行异常: {e}")
        return None


def clean_web_directory():
    """清空 KingAutomate\web 文件夹"""
    print(f"\n正在清空 web 目录: {WEB_DIR}")
    if not os.path.exists(WEB_DIR):
        os.makedirs(WEB_DIR, exist_ok=True)
        print("web 目录已创建（原本不存在）")
        return True

    try:
        for item in os.listdir(WEB_DIR):
            item_path = os.path.join(WEB_DIR, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
                print(f"  删除文件: {item}")
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"  删除目录: {item}")
        print("web 目录已清空")
        return True
    except Exception as e:
        print(f"清空 web 目录失败: {e}")
        return False


def ask_build_type():
    """询问构建类型：测试或正式发版，返回字符串 '测试' 或 '正式发版'"""
    answer = questionary.select(
        "请选择构建类型：",
        choices=["测试", "正式发版"]
    ).ask()
    return answer


def get_git_info():
    """获取当前 Git 分支名称和短 commit 哈希值（默认7位），返回 (branch, short_hash)"""
    try:
        # 获取分支名称（使用 utf-8 编码）
        branch_result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=AOM_PATH
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # 获取短 commit 哈希（默认7位，Git 会自动加长以避免歧义）
        hash_result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=AOM_PATH
        )
        short_hash = hash_result.stdout.strip() if hash_result.returncode == 0 else "unknown"

        return branch, short_hash
    except Exception as e:
        print(f"获取 Git 信息失败: {e}")
        return "unknown", "unknown"


def fetch_newversion_from_url(url):
    """
    从指定 URL 下载 LiteVersion.ini，解析出 newversion 的值
    返回 newversion 字符串，失败返回 None
    """
    print(f"正在从远程获取版本信息: {url}")
    try:
        response = urllib.request.urlopen(url, timeout=10)
        content = response.read()
        # 尝试多种编码解析
        for enc in ['utf-8', 'gbk', 'gb2312']:
            try:
                decoded = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            decoded = content.decode('utf-8', errors='ignore')

        config = configparser.ConfigParser()
        config.read_string(decoded)
        newversion = config.get('Main', 'newversion', fallback=None)
        if newversion:
            return newversion.strip()
        else:
            print("未找到 [Main] 下的 newversion 字段")
            return None
    except Exception as e:
        print(f"获取或解析远程版本失败: {e}")
        return None


def increment_version(version):
    """
    根据当前版本号生成下一个版本号，格式为四段数字（如 2.1.1.17）。
    规则：
    - 如果版本号包含 '-beta' 后跟数字（如 '2.1.1-beta16'），则转换为 '2.1.1.17'（beta数字+1）。
    - 否则按点号分割：
        - 如果是三段数字（如 '2.1.1'），则在末尾添加 '.1' 得到 '2.1.1.1'。
        - 如果是四段数字（如 '2.1.1.1'），则将最后一段加1，如 '2.1.1.2'。
        - 如果超过四段，只保留前四段并递增第四段。
    - 如果无法解析，尝试原逻辑作为后备，并打印警告。
    """
    version = version.strip()
    
    # 1. 处理 -beta 格式：X.Y.Z-betaN
    beta_match = re.search(r'^(\d+\.\d+\.\d+)-beta(\d+)$', version)
    if beta_match:
        base = beta_match.group(1)        # 如 '2.1.1'
        beta_num = int(beta_match.group(2))  # 如 16
        new_version = f"{base}.{beta_num + 1}"
        print(f"检测到 -beta 格式，转换后版本: {new_version}")
        return new_version

    # 2. 处理普通点分数字
    parts = version.split('.')
    # 检查是否所有部分都是数字（允许前三段+第四段数字）
    if all(p.isdigit() for p in parts):
        if len(parts) == 3:
            # 三段，补 .1
            new_version = f"{version}.1"
            print(f"三段数字，补第四段为 1: {new_version}")
            return new_version
        elif len(parts) >= 4:
            # 至少四段，取前四段，递增最后一段
            major, minor, build, revision = parts[0], parts[1], parts[2], parts[3]
            new_revision = int(revision) + 1
            new_version = f"{major}.{minor}.{build}.{new_revision}"
            print(f"四段数字，递增第四段: {new_version}")
            return new_version
        else:
            # 不足三段，无法处理，警告并原样返回
            print(f"警告: 版本号 '{version}' 格式异常（不足三段），将原样返回。")
            return version
    else:
        # 包含非数字，尝试原逻辑作为后备
        print(f"警告: 版本号 '{version}' 包含非数字，尝试原递增逻辑。")
        # 原逻辑：匹配 -beta 后数字（但上面已处理，这里仅保留原逻辑的通用部分）
        beta_match_old = re.search(r'(.*-beta)(\d+)$', version)
        if beta_match_old:
            prefix = beta_match_old.group(1)
            num = int(beta_match_old.group(2))
            new_num = num + 1
            return f"{prefix}{new_num}"
        parts = version.split('.')
        if parts and parts[-1].isdigit():
            last_num = int(parts[-1])
            parts[-1] = str(last_num + 1)
            return '.'.join(parts)
        # 实在无法处理，返回原值
        return version


def run_build_exe():
    """
    直接运行 Build.exe，将终端交还给用户手动交互。
    运行前临时将控制台代码页设为 GBK (936) 以解决中文乱码，运行后恢复。
    工作目录设为 AOM_PATH（与 PowerShell 脚本一致），不捕获输出，不自动输入。
    """
    if not os.path.exists(BUILD_EXE):
        print(f"错误: 找不到 Build.exe，路径: {BUILD_EXE}")
        return False

    print("正在运行 Build.exe...")
    print("（终端已交给 Build.exe，请手动完成交互，完成后脚本将继续）")
    work_dir = AOM_PATH

    # 保存当前控制台输出代码页，并临时设为 GBK (936)
    old_cp = None
    try:
        kernel32 = ctypes.windll.kernel32
        old_cp = kernel32.GetConsoleOutputCP()
        # 设置为简体中文 GBK
        kernel32.SetConsoleOutputCP(936)
    except Exception as e:
        print(f"警告: 无法设置控制台代码页，输出可能仍为乱码: {e}")

    try:
        result = subprocess.run([BUILD_EXE], cwd=work_dir)
    finally:
        # 恢复原代码页
        if old_cp is not None:
            try:
                kernel32.SetConsoleOutputCP(old_cp)
            except Exception:
                pass

    if result.returncode == 0:
        print("\nBuild.exe 执行成功！")
        return True
    else:
        print(f"\nBuild.exe 执行失败，返回码: {result.returncode}")
        return False


def main():
    print("=" * 60)
    print("开始执行 KRPA Lite 构建流程（正式版远程版本号自动递增，格式优化）")
    print("=" * 60)

    start_time = time.time()

    # 1. 切换到 aom 目录
    print("\n[1/6] 正在切换到 aom 目录...")
    try:
        os.chdir(AOM_PATH)
        print(f"已切换到: {AOM_PATH}")
    except Exception as e:
        print(f"切换目录失败: {e}")
        return 1

    # 2. git reset --hard HEAD（使用 utf-8 编码）
    print("\n[2/6] git reset --hard HEAD...")
    if not run_command(['git', 'reset', '--hard', 'HEAD'], encoding='utf-8'):
        return 1

    # 3. git pull --rebase（使用 utf-8 编码）
    print("\n[3/6] git pull --rebase...")
    if not run_command(['git', 'pull', '--rebase'], encoding='utf-8'):
        return 1

    # 4. 清空 web 目录
    print("\n[4/6] 清空 KingAutomate\\web 目录...")
    if not clean_web_directory():
        return 1

    # 5. 执行 now_ 命令并获取时间戳（仅用于测试时作为默认值）
    print("\n[5/6] 执行 now_ 命令...")
    timestamp = run_now_command()
    if timestamp is None:
        print("警告: 无法获取时间戳，但将继续构建")
        timestamp = "未知时间"

    # 6. 询问构建类型
    build_type = ask_build_type()
    print(f"你选择了: {build_type}")

    # 7. 根据类型生成版本标识符
    branch, commit_hash = get_git_info()

    if build_type == "测试":
        version_string = f"{timestamp}|{branch}_#_{commit_hash}"
        print("\n" + "=" * 40)
        print("生成的版本标识符（测试）:")
        print(version_string)
        print("=" * 40)
    else:  # 正式发版
        remote_version = fetch_newversion_from_url(VERSION_INI_URL)
        if remote_version:
            incremented_version = increment_version(remote_version)
            print(f"原始版本: {remote_version}，递增后: {incremented_version}")
            version_string = f"{incremented_version}|{branch}_#_{commit_hash}"
            print("\n" + "=" * 40)
            print("生成的版本标识符（正式版）:")
            print(version_string)
            print("=" * 40)
        else:
            print("\n无法从远程获取版本号。")
            fallback = input(f"请手动输入版本号（直接回车使用 {timestamp}）: ").strip()
            if fallback:
                version_string = f"{fallback}|{branch}_#_{commit_hash}"
            else:
                version_string = f"{timestamp}|{branch}_#_{commit_hash}"
            print(f"使用版本号: {version_string}")

    # 复制到剪贴板
    try:
        import pyperclip
        pyperclip.copy(version_string)
        print("✅ 版本标识符已复制到剪贴板，可直接粘贴。")
    except ImportError:
        print("⚠️ 未安装 pyperclip，无法自动复制。请手动复制上面的版本标识符。")
        print("   安装命令: pip install pyperclip")
    except Exception as e:
        print(f"⚠️ 复制到剪贴板失败: {e}")

    # 8. 运行 Build.exe，完全交给用户交互
    print("\n[6/6] 运行 Build.exe...")
    if not run_build_exe():
        return 1

    elapsed = time.time() - start_time
    print(f"\n" + "=" * 60)
    print(f"构建完成！总耗时: {elapsed:.2f} 秒")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())