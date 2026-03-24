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
    # ========== Windows 分支（保持不变） ==========
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
    # ========== macOS 分支（修正版） ==========
    username = getpass.getuser()
    print(f"当前用户: {username}")
    home = os.path.expanduser("~")
    print(f"Home 目录: {home}")

    # 1. 安装 questionary 和 keyboard 库
    print("检查并安装必要的 Python 库...")
    try:
        import questionary
        import keyboard
    except ImportError:
        print("正在安装 questionary 和 keyboard ...")
        subprocess.run([sys.executable, "-m", "pip", "install", "questionary", "keyboard"], check=True)
        import questionary
        import keyboard

    # 2. 确定配置文件路径（.zshrc）
    profile_file = os.path.join(home, ".zshrc")
    print(f"目标配置文件: {profile_file}")

    # 确保配置文件存在
    if not os.path.exists(profile_file):
        open(profile_file, 'w').close()
        print(f"已创建空配置文件: {profile_file}")

    # 读取现有内容
    with open(profile_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 2. 处理环境变量 MYSHELL
    env_line_pattern = "export MYSHELL="
    desired_env = 'export MYSHELL="$HOME/MyShell"'
    lines = content.splitlines()
    env_index = None
    existing_env = None
    for i, line in enumerate(lines):
        if line.startswith(env_line_pattern):
            env_index = i
            existing_env = line.strip()
            break

    # 期望的绝对路径
    expected_abs = os.path.join(home, "MyShell")

    if env_index is not None:
        # 提取值部分
        value_part = existing_env[len(env_line_pattern):].strip()
        # 去除引号
        if (value_part.startswith('"') and value_part.endswith('"')) or \
           (value_part.startswith("'") and value_part.endswith("'")):
            value_part = value_part[1:-1]
        # 展开 $HOME 和 ~
        if value_part.startswith('$HOME'):
            value_part = value_part.replace('$HOME', home)
        elif value_part.startswith('~'):
            value_part = os.path.expanduser(value_part)
        actual_abs = os.path.normpath(value_part)
        if actual_abs != expected_abs:
            print(f"当前 MYSHELL 设置为: {existing_env}")
            answer = questionary.confirm(f"当前 MYSHELL 值不是 {desired_env}，是否覆盖？").ask()
            if answer:
                lines[env_index] = desired_env
                with open(profile_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(lines) + "\n")
                print("已更新 MYSHELL 环境变量。")
            else:
                print("本库必须基于 export MYSHELL=\"$HOME/MyShell\"，终止进程。")
                sys.exit(1)
        else:
            print("MYSHELL 环境变量已正确设置。")
    else:
        # 不存在，直接追加
        with open(profile_file, 'a', encoding='utf-8') as f:
            f.write("\n" + desired_env + "\n")
        print("已添加 MYSHELL 环境变量到配置文件。")

    # 重新读取文件内容（因为可能被修改过）
    with open(profile_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 3. 判断并添加 shell 递归循环块
    loop_block = """for func_file in ~/MyShell/MacOS/**/*.zsh(N); do
  source "$func_file"
done
zstyle ':completion:*' menu select=1"""
    if block_exists_in_file(content, loop_block):
        print("已在 .zshrc 文件中写入 shell 递归循环。")
    else:
        with open(profile_file, 'a', encoding='utf-8') as f:
            f.write("\n" + loop_block + "\n")
        print("init 已帮你在 .zshrc 文件中写入 shell 递归循环。")

    # 4. 判断 reloadsh 方法并执行
    check_cmd = ["zsh", "-c", f"source {profile_file} && type reloadsh >/dev/null 2>&1"]
    try:
        subprocess.run(check_cmd, check=True, capture_output=True)
        # 存在，执行 reloadsh
        subprocess.run(["zsh", "-c", f"source {profile_file} && reloadsh"])
        print("已执行 reloadsh 命令。")

        # 5. reloadsh 成功后，安装 pythonPackage 中的包
        # 构建 config.json 路径：优先使用 MYSHELL 环境变量，若不存在则使用 ~/MyShell
        myshell_env = os.environ.get('MYSHELL')
        if myshell_env:
            config_json_mac = os.path.join(myshell_env, "config", "function_tracker.json")
        else:
            config_json_mac = os.path.join(home, "MyShell", "config", "function_tracker.json")

        if os.path.exists(config_json_mac):
            print("找到 function_tracker.json，开始检查 Python 依赖...")
            try:
                with open(config_json_mac, 'r', encoding='utf-8') as f:
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
            print(f"未找到配置文件 {config_json_mac}，跳过 Python 依赖安装。")

    except subprocess.CalledProcessError:
        # 黄色提示，已去除句号
        print("\033[93m未找到 reloadsh 命令，请先在终端执行 source ~/.zshrc\033[0m")
        
else:
    print("其他操作系统，暂无自动配置。")