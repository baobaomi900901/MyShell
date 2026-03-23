#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
import getpass
import os
import subprocess
import json
import sys
import time
from enum import Enum

def normalize_lines(text):
    """将文本按行分割，并去除每行的首尾空白"""
    return [line.strip() for line in text.splitlines()]

def block_exists_in_file(file_content, block_content):
    """
    检查 block_content 是否以行序列的形式存在于 file_content 中
    （忽略每行的首尾空白）
    """
    file_lines = normalize_lines(file_content)
    block_lines = normalize_lines(block_content)
    len_block = len(block_lines)
    for i in range(len(file_lines) - len_block + 1):
        if file_lines[i:i+len_block] == block_lines:
            return True
    return False

class System(Enum):
    """操作系统类型枚举"""
    WINDOWS = "Windows"
    MACOS = "MacOS"
    OTHER = "Other"

# 获取当前系统对应的枚举成员
system_name = platform.system()
if system_name == "Windows":
    current_system = System.WINDOWS
elif system_name == "Darwin":
    current_system = System.MACOS
else:
    current_system = System.OTHER

print(current_system.value)

# 获取当前脚本所在目录（用于定位 config/function_tracker.json）
script_dir = os.path.dirname(os.path.abspath(__file__))
config_json = os.path.join(script_dir, "config", "function_tracker.json")

if current_system == System.WINDOWS:
    # ========== Windows 分支 ==========
    import winreg

    def get_user_environment_variable(name):
        """从 HKEY_CURRENT_USER\Environment 读取用户环境变量，不存在则返回 None"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
            value, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return value
        except FileNotFoundError:
            return None

    username = getpass.getuser()
    print(f"当前用户: {username}")
    docs_folder = os.path.expanduser("~\\Documents")
    print(f"Documents 文件夹: {docs_folder}")

    # 构建 PowerShell 配置文件路径
    ps_folder = os.path.join(docs_folder, "WindowsPowerShell")
    profile_file = os.path.join(ps_folder, "Microsoft.PowerShell_profile.ps1")

    # 创建 MyShell\windows 目录（用于存放自定义脚本）
    myshell_windows = os.path.join(docs_folder, "WindowsPowerShell", "MyShell", "windows")
    os.makedirs(myshell_windows, exist_ok=True)
    print(f"自定义脚本目录已确保存在: {myshell_windows}")

    # ====== 设置环境变量 MYSHELL（指向 MyShell 根目录）======
    myshell_root = os.path.join(docs_folder, "WindowsPowerShell", "MyShell")
    env_var_name = "MYSHELL"
    desired_value = myshell_root

    current_reg_value = get_user_environment_variable(env_var_name)
    if current_reg_value != desired_value:
        try:
            subprocess.run(
                ["setx", env_var_name, desired_value],
                check=True,
                capture_output=True,
                text=True
            )
            if current_reg_value is None:
                print(f"环境变量 {env_var_name} 已创建: {desired_value}")
            else:
                print(f"环境变量 {env_var_name} 已从 '{current_reg_value}' 更新为 '{desired_value}'")
            # 更新当前进程的环境变量，以便后续操作可能用到
            os.environ[env_var_name] = desired_value
        except subprocess.CalledProcessError as e:
            print(f"设置环境变量失败: {e.stderr}")
    else:
        print(f"环境变量 {env_var_name} 已正确设置，无需修改。")

    # 定义要检查的核心代码块（不含注释）
    core_block = r"""$functionsDir = "$PSScriptRoot\MyShell\windows"
if (Test-Path $functionsDir) {
    Get-ChildItem -Path $functionsDir -Recurse -Filter *.ps1 -File | ForEach-Object {
        . $_.FullName
    }
}"""

    full_content = "# {}\n{}".format(profile_file, core_block)

    # 确保目录存在
    os.makedirs(ps_folder, exist_ok=True)

    # 处理配置文件
    if not os.path.exists(profile_file):
        with open(profile_file, 'w', encoding='utf-8-sig') as f:
            f.write(full_content)
        print(f"已创建配置文件: {profile_file}")
    else:
        with open(profile_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        if block_exists_in_file(content, core_block):
            print("配置文件中已包含所需代码块，无需修改。")
        else:
            with open(profile_file, 'a', encoding='utf-8-sig') as f:
                f.write("\n" + full_content)
            print("已向配置文件追加所需代码块。")

    # 自动打开新窗口执行 . $PROFILE 和 reloadsh
    print("正在新窗口中执行 . $PROFILE 和 reloadsh（已设置 UTF-8 编码）...")
    subprocess.run(
        ["start", "powershell", "-NoExit", "-Command",
         "chcp 65001 > $null; $OutputEncoding = [console]::OutputEncoding = [System.Text.Encoding]::UTF8; $env:PYTHONIOENCODING='utf-8'; . $PROFILE; reloadsh"],
        shell=True
    )

    # 检查 config/function_tracker.json 并安装 Python 依赖
    if os.path.exists(config_json):
        print("找到 function_tracker.json，开始检查 Python 依赖...")
        try:
            with open(config_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            packages = data.get('pythonPackage', [])
            if packages:
                print(f"需要检查的包: {packages}")
                for pkg in packages:
                    print(f"检查 {pkg}...")
                    check_result = subprocess.run(
                        [sys.executable, "-m", "pip", "show", pkg],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    if check_result.returncode == 0:
                        print(f"✅ {pkg} 已安装，跳过。")
                        continue

                    print(f"正在安装 {pkg}...")
                    result = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", pkg])
                    if result.returncode == 0:
                        print(f"✅ {pkg} 安装成功。")
                    else:
                        print(f"❌ {pkg} 安装失败，请手动执行: pip install {pkg}")
            else:
                print("没有需要安装的 Python 包。")
        except Exception as e:
            print(f"安装 Python 包时出错: {e}")
    else:
        print(f"未找到配置文件 {config_json}，跳过 Python 依赖安装。")

elif current_system == System.MACOS:
    # ========== macOS 分支 ==========
    username = getpass.getuser()
    print(f"当前用户: {username}")
    home = os.path.expanduser("~")
    print(f"Home 目录: {home}")

    # 检测默认 shell
    shell = os.environ.get('SHELL', '')
    if 'zsh' in shell:
        profile_file = os.path.join(home, ".zshrc")
        shell_name = "zsh"
    elif 'bash' in shell:
        profile_file = os.path.join(home, ".bash_profile")
        shell_name = "bash"
    else:
        profile_file = os.path.join(home, ".profile")
        shell_name = "sh"

    print(f"检测到默认 Shell: {shell_name}，配置文件: {profile_file}")

    # 自定义脚本目录：~/MyShell/MacOS
    myshell_root = os.path.join(home, "MyShell")
    myshell_macos = os.path.join(myshell_root, "MacOS")
    os.makedirs(myshell_macos, exist_ok=True)
    print(f"自定义脚本目录已确保存在: {myshell_macos}")

    # 定义三段要添加的文本块
    blocks = [
        # 块1: 环境变量 MYSHELL
        f'export MYSHELL="$HOME/MyShell"',
        # 块2: 递归加载 ~/MyShell/MacOS 下的所有 .zsh 文件
        """for func_file in ~/MyShell/MacOS/**/*.zsh(N); do
  source "$func_file"
done""",
        # 块3: zstyle 补全菜单
        "zstyle ':completion:*' menu select=1"
    ]

    # 读取现有配置文件内容（如果存在）
    if os.path.exists(profile_file):
        with open(profile_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    else:
        existing_content = ""

    # 分别检查每个块是否存在，缺失则追加
    for block in blocks:
        if block_exists_in_file(existing_content, block):
            print(f"配置文件已包含所需代码块:\n{block}\n")
        else:
            # 追加块（添加换行分隔）
            with open(profile_file, 'a', encoding='utf-8') as f:
                f.write("\n" + block + "\n")
            print(f"已向配置文件追加代码块:\n{block}\n")

    # 如果配置文件原本不存在，需要确保写入后生效
    if not os.path.exists(profile_file):
        print(f"已创建配置文件: {profile_file}")

    # 检查 config/function_tracker.json 并安装 Python 依赖
    if os.path.exists(config_json):
        print("找到 function_tracker.json，开始检查 Python 依赖...")
        try:
            with open(config_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            packages = data.get('pythonPackage', [])
            if packages:
                print(f"需要检查的包: {packages}")
                for pkg in packages:
                    print(f"检查 {pkg}...")
                    check_result = subprocess.run(
                        [sys.executable, "-m", "pip", "show", pkg],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    if check_result.returncode == 0:
                        print(f"✅ {pkg} 已安装，跳过。")
                        continue

                    print(f"正在安装 {pkg}...")
                    result = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", pkg])
                    if result.returncode == 0:
                        print(f"✅ {pkg} 安装成功。")
                    else:
                        print(f"❌ {pkg} 安装失败，请手动执行: pip install {pkg}")
            else:
                print("没有需要安装的 Python 包。")
        except Exception as e:
            print(f"安装 Python 包时出错: {e}")
    else:
        print(f"未找到配置文件 {config_json}，跳过 Python 依赖安装。")

    # 提示用户手动 source 配置文件或重启终端
    print("\n配置已更新。请执行以下命令使配置立即生效：")
    print(f"source {profile_file}")
    print("或者直接打开新的终端窗口。")

else:
    print("其他操作系统，暂无自动配置。")