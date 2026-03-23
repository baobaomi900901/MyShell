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
   - 正式发版：从远程获取 newversion，自动递增后让用户选择版本号（自动或自定义），并询问是否打包setup
7. 更新 KingAutomate\krpalite.dproj 中的 ProductVersion（仅正式版）
8. 运行 Build.exe（直接交还终端，用户手动交互）
9. Build.exe 执行完毕后，如果选择了打包，则运行 build_lite_setup.py "K-RPA Lite"
10. 切换到 aom 目录，放弃所有更改并清理未跟踪文件
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
from datetime import datetime
from pathlib import Path
import questionary

# 配置路径（请根据实际项目位置修改）
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
    """生成当前时间戳，格式如 '20260313-20:39'，直接返回字符串"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H:%M")
    print(f"当前时间戳: {timestamp}")
    return timestamp


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


def is_valid_version(text):
    """
    验证输入的版本号是否符合格式：四段数字，每段为非负整数。
    返回 True 或错误消息。
    """
    text = text.strip()
    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', text):
        return "版本号必须为四段数字，格式如 1.2.3.4"
    # 可选：检查每段是否为非负整数（正则已保证是数字，但可额外检查是否包含前导零？不强制）
    # 如果需要更严格（如不允许前导零且数字>0），可以添加如下检查：
    # parts = text.split('.')
    # for part in parts:
    #     if part != '0' and part.startswith('0'):
    #         return "版本号的每段数字不能有前导零（除非为0）"
    # 但通常不强制，所以只检查格式
    return True


def update_dproj_version(new_version):
    """
    更新 KingAutomate\krpalite.dproj 文件中的 ProductVersion。
    使用正则表达式在 VerInfo_Keys 中查找 ProductVersion=旧值 并替换为新值。
    保持原文件格式不变，不引入命名空间前缀。
    返回 True 表示成功，False 表示失败。
    """
    dproj_path = os.path.join(AOM_PATH, "KingAutomate", "krpalite.dproj")
    if not os.path.exists(dproj_path):
        print(f"错误: 找不到 dproj 文件: {dproj_path}")
        return False

    # 备份原文件
    backup_path = dproj_path + ".bak"
    try:
        shutil.copy2(dproj_path, backup_path)
        print(f"已备份原文件到: {backup_path}")
    except Exception as e:
        print(f"备份文件失败: {e}")
        return False

    try:
        # 读取文件内容
        with open(dproj_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 定义正则表达式模式，匹配 VerInfo_Keys 中的 ProductVersion=xxx;
        # 模式说明：ProductVersion= 后跟任意非分号字符，直到遇到分号
        pattern = r'(ProductVersion=)[^;]*;'

        # 替换为新版本号
        new_content, count = re.subn(pattern, rf'\g<1>{new_version};', content)

        if count == 0:
            print("错误: 未找到 ProductVersion 字段")
            return False

        # 写回文件
        with open(dproj_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ 已更新 {dproj_path} 中的 ProductVersion 为 {new_version}")
        return True

    except Exception as e:
        print(f"更新 dproj 文件失败: {e}")
        # 尝试恢复备份
        try:
            shutil.copy2(backup_path, dproj_path)
            print("已从备份恢复原文件。")
        except:
            pass
        return False


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


def clean_workspace_after_build():
    """
    构建完成后清理工作区：
    1. 切换到 AOM_PATH 目录
    2. 执行 git reset --hard HEAD 放弃所有更改
    3. 执行 git clean -fd 删除所有未跟踪文件
    直接使用 Python 调用 git，使用 utf-8 编码以确保中文正确显示。
    """
    print("\n正在清理工作区（放弃所有更改并删除未跟踪文件）...")
    try:
        # 确保当前目录是 AOM_PATH
        os.chdir(AOM_PATH)

        # 执行 git reset --hard HEAD
        print("执行: git reset --hard HEAD")
        reset_result = subprocess.run(
            ['git', 'reset', '--hard', 'HEAD'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if reset_result.returncode == 0:
            if reset_result.stdout:
                print(reset_result.stdout)
            if reset_result.stderr:
                print("错误输出:", reset_result.stderr)
        else:
            print(f"git reset 失败，返回码: {reset_result.returncode}")
            if reset_result.stderr:
                print(reset_result.stderr)

        # 执行 git clean -fd
        print("执行: git clean -fd")
        clean_result = subprocess.run(
            ['git', 'clean', '-fd'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if clean_result.returncode == 0:
            if clean_result.stdout:
                print(clean_result.stdout)
            else:
                print("没有未跟踪文件需要清理。")
        else:
            print(f"git clean 失败，返回码: {clean_result.returncode}")
            if clean_result.stderr:
                print(clean_result.stderr)

    except Exception as e:
        print(f"清理时发生异常: {e}")


def main():
    print("=" * 60)
    print("开始执行 KRPA Lite 构建流程（正式版远程版本号自动递增，格式优化）")
    print("=" * 60)

    start_time = time.time()

    # 1. 切换到 aom 目录
    print("\n[1/7] 正在切换到 aom 目录...")
    try:
        os.chdir(AOM_PATH)
        print(f"已切换到: {AOM_PATH}")
    except Exception as e:
        print(f"切换目录失败: {e}")
        return 1

    # 2. git reset --hard HEAD（使用 utf-8 编码）
    print("\n[2/7] git reset --hard HEAD...")
    if not run_command(['git', 'reset', '--hard', 'HEAD'], encoding='utf-8'):
        return 1

    # 3. git pull --rebase（使用 utf-8 编码）
    print("\n[3/7] git pull --rebase...")
    if not run_command(['git', 'pull', '--rebase'], encoding='utf-8'):
        return 1

    # 4. 清空 web 目录
    print("\n[4/7] 清空 KingAutomate\\web 目录...")
    if not clean_web_directory():
        return 1

    # 5. 执行 now_ 命令并获取时间戳（仅用于测试时作为默认值）
    print("\n[5/7] 执行 now_ 命令...")
    timestamp = run_now_command()
    if timestamp is None:
        print("警告: 无法获取时间戳，但将继续构建")
        timestamp = "未知时间"

    # 6. 询问构建类型
    build_type = ask_build_type()
    print(f"你选择了: {build_type}")

    # 7. 根据类型生成版本标识符
    branch, commit_hash = get_git_info()
    need_pack = False  # 记录是否需要打包

    if build_type == "测试":
        version_string = f"{timestamp}|{branch}_#_{commit_hash}"
        print("\n" + "=" * 40)
        print("生成的版本标识符（测试）:")
        print(version_string)
        print("=" * 40)
        version_number = timestamp  # 测试版不需要更新 dproj
    else:  # 正式发版
        remote_version = fetch_newversion_from_url(VERSION_INI_URL)
        if remote_version:
            incremented_version = increment_version(remote_version)
            print(f"原始版本: {remote_version}，递增后: {incremented_version}")

            # 让用户选择使用自动生成的版本号还是自定义
            choice = questionary.select(
                "请选择版本号：",
                choices=[incremented_version, "自定义"]
            ).ask()

            if choice == "自定义":
                while True:
                    custom_version = questionary.text(
                        "请输入版本号 (格式: n.n.n.n，每个n为非负整数):",
                        validate=is_valid_version
                    ).ask()
                    if custom_version is None:
                        # 用户可能取消了（例如按了 Ctrl+C），则回退到自动生成
                        print("取消自定义输入，将使用自动生成的版本号。")
                        version_number = incremented_version
                        break
                    else:
                        version_number = custom_version
                        break
            else:
                version_number = incremented_version

            # 询问是否打包setup
            pack_choice = questionary.select(
                "是否打包setup？",
                choices=["否", "是"]
            ).ask()
            need_pack = (pack_choice == "是")
            if need_pack:
                print("你选择了需要打包setup，将在构建完成后执行打包脚本。")
            else:
                print("你选择了不打包setup")

            version_string = f"{version_number}|{branch}_#_{commit_hash}"
            print("\n" + "=" * 40)
            print("生成的版本标识符（正式版）:")
            print(version_string)
            print("=" * 40)
        else:
            print("\n无法从远程获取版本号。")
            fallback = input(f"请手动输入版本号（直接回车使用 {timestamp}）: ").strip()
            if fallback:
                version_number = fallback
                version_string = f"{fallback}|{branch}_#_{commit_hash}"
            else:
                version_number = timestamp
                version_string = f"{timestamp}|{branch}_#_{commit_hash}"
            print(f"使用版本号: {version_string}")

    # 统一复制版本标识符到剪贴板（测试和正式均执行）
    try:
        import pyperclip
        pyperclip.copy(version_string)
        print("✅ 版本标识符已复制到剪贴板，可直接粘贴。")
    except ImportError:
        print("⚠️ 未安装 pyperclip，无法自动复制。请手动复制上面的版本标识符。")
        print("   安装命令: pip install pyperclip")
    except Exception as e:
        print(f"⚠️ 复制到剪贴板失败: {e}")

    # 如果是正式版，还需要更新 dproj 文件
    if build_type == "正式发版":
        print("\n[6/7] 更新 krpalite.dproj 中的 ProductVersion...")
        if not update_dproj_version(version_number):
            print("错误: 更新 dproj 文件失败，终止构建。")
            return 1

    # 8. 运行 Build.exe，完全交给用户交互（步骤编号根据正式版调整）
    if build_type == "测试":
        print("\n[6/7] 运行 Build.exe...")
    else:
        print("\n[7/7] 运行 Build.exe...")

    build_success = run_build_exe()

    # 如果构建成功且用户选择了打包，则运行打包脚本（继承终端以实现交互）
    if build_success and need_pack:
        print("\n开始执行打包脚本 build_lite_setup.py ...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        setup_script = os.path.join(script_dir, "build_lite_setup.py")
        if not os.path.exists(setup_script):
            print(f"错误：找不到打包脚本 {setup_script}")
        else:
            try:
                # 修改点：移除了 capture_output，直接继承父进程的终端
                result = subprocess.run(
                    [sys.executable, setup_script, "K-RPA Lite"],
                    cwd=AOM_PATH
                )
                if result.returncode == 0:
                    print("✅ 打包脚本执行成功")
                else:
                    print(f"❌ 打包脚本执行失败，返回码: {result.returncode}")
            except Exception as e:
                print(f"运行打包脚本时发生异常: {e}")

    # 9. 构建完成后清理工作区（无论成功与否）
    clean_workspace_after_build()

    if not build_success:
        return 1

    elapsed = time.time() - start_time
    print(f"\n" + "=" * 60)
    print(f"构建完成！总耗时: {elapsed:.2f} 秒")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())