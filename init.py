# .\init.py
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

if current_system == System.WINDOWS:
    # Windows 分支：获取用户名和 Documents 文件夹路径
    username = getpass.getuser()
    print(f"当前用户: {username}")
    docs_folder = os.path.expanduser("~\\Documents")
    print(f"Documents 文件夹: {docs_folder}")

    # 构建 PowerShell 配置文件路径
    ps_folder = os.path.join(docs_folder, "WindowsPowerShell")
    profile_file = os.path.join(ps_folder, "Microsoft.PowerShell_profile.ps1")

    # 创建 MyShell\windows 目录（用于存放自定义脚本）
    myshell_windows = os.path.join(docs_folder, "WindowsPowerShell", "MyShell", "windows")
    if not os.path.exists(myshell_windows):
        os.makedirs(myshell_windows)
        print(f"创建自定义脚本目录: {myshell_windows}")
    else:
        print(f"自定义脚本目录已存在: {myshell_windows}")

    # 定义要检查的核心代码块（不含注释，使用原始字符串避免转义警告）
    core_block = r"""$functionsDir = "$PSScriptRoot\MyShell\windows"
if (Test-Path $functionsDir) {
    Get-ChildItem -Path $functionsDir -Recurse -Filter *.ps1 -File | ForEach-Object {
        . $_.FullName
    }
}"""

    # 定义包含注释的完整内容（使用 format 避免 f-string 中的大括号冲突）
    full_content = "# {}\n{}".format(profile_file, core_block)

    # 确保目录存在
    if not os.path.exists(ps_folder):
        os.makedirs(ps_folder)
        print(f"创建目录: {ps_folder}")

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

    # 等待 JSON 文件生成并安装 Python 依赖
    json_file = os.path.join(docs_folder, "WindowsPowerShell", "MyShell", "Windows", "function_tracker.json")
    max_attempts = 5
    for attempt in range(max_attempts):
        if os.path.exists(json_file):
            print("找到 function_tracker.json，开始安装 Python 依赖...")
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                packages = data.get('pythonPackage', [])
                if packages:
                    print(f"需要安装的包: {packages}")
                    for pkg in packages:
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
            break
        else:
            if attempt < max_attempts - 1:
                print(f"等待 JSON 文件生成 ({attempt+1}/{max_attempts-1})...")
                time.sleep(1)
            else:
                print("未找到 function_tracker.json，请确保已执行 reloadsh 后手动安装依赖。")

elif current_system == System.MACOS:
    # macOS 分支：初始化 shell 配置文件（以 zsh 为例）
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

    # 创建 MyShell/macos 目录（用于存放自定义脚本）
    myshell_macos = os.path.join(home, "Documents", "WindowsPowerShell", "MyShell", "macos")
    if not os.path.exists(myshell_macos):
        os.makedirs(myshell_macos)
        print(f"创建自定义脚本目录: {myshell_macos}")
    else:
        print(f"自定义脚本目录已存在: {myshell_macos}")

    # 定义要检查的核心代码块（用于加载自定义脚本）
    core_block = f"""# Load custom shell scripts from MyShell/macos
if [ -d "{myshell_macos}" ]; then
    for file in "{myshell_macos}"/*.sh; do
        if [ -f "$file" ]; then
            source "$file"
        fi
    done
fi"""

    # 处理配置文件
    if not os.path.exists(profile_file):
        with open(profile_file, 'w', encoding='utf-8') as f:
            f.write(core_block + "\n")
        print(f"已创建配置文件: {profile_file}")
    else:
        with open(profile_file, 'r', encoding='utf-8') as f:
            content = f.read()
        if block_exists_in_file(content, core_block):
            print("配置文件中已包含所需代码块，无需修改。")
        else:
            with open(profile_file, 'a', encoding='utf-8') as f:
                f.write("\n" + core_block + "\n")
            print("已向配置文件追加所需代码块。")

    # 提示用户手动 source 配置文件或重启终端
    print("\n配置已更新。请执行以下命令使配置立即生效：")
    print(f"source {profile_file}")
    print("或者直接打开新的终端窗口。")

else:
    print("其他操作系统，暂无自动配置。")