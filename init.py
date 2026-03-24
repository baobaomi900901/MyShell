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
    # ========== Windows 分支（按新需求实现） ==========
    import winreg

    # 1. 安装必要的 Python 库（questionary 和 keyboard）
    print("检查并安装必要的 Python 库...")
    try:
        import questionary
        import keyboard
    except ImportError:
        print("正在安装 questionary 和 keyboard ...")
        subprocess.run([sys.executable, "-m", "pip", "install", "questionary", "keyboard"], check=True)
        import questionary
        import keyboard

    # 获取用户主目录（USERPROFILE 环境变量）
    userprofile = os.environ.get('USERPROFILE')
    if not userprofile:
        userprofile = os.path.expanduser("~")
    print(f"用户主目录: {userprofile}")

    # 期望的 MYSHELL 路径：%USERPROFILE%\Documents\WindowsPowerShell\MyShell
    expected_myshell = os.path.join(userprofile, "Documents", "WindowsPowerShell", "MyShell")
    print(f"期望的 MYSHELL 路径: {expected_myshell}")

    # 定义读取用户环境变量的函数（从注册表）
    def get_user_environment_variable(name):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
            value, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return value
        except FileNotFoundError:
            return None

    # 2. 处理环境变量 MYSHELL
    env_var_name = "MYSHELL"
    current_reg_value = get_user_environment_variable(env_var_name)

    # 比较当前值与期望值（标准化路径，忽略大小写和末尾反斜杠）
    def normalize_path(p):
        return os.path.normpath(p).lower()

    need_update = False
    if current_reg_value is None:
        print(f"环境变量 {env_var_name} 不存在。")
        need_update = True
    else:
        if normalize_path(current_reg_value) != normalize_path(expected_myshell):
            print(f"当前 MYSHELL 值为: {current_reg_value}")
            print(f"期望值为: {expected_myshell}")
            need_update = True
        else:
            print("环境变量 MYSHELL 已正确设置。")

    if need_update:
        # 询问用户是否覆盖
        answer = questionary.confirm(
            f"当前 MYSHELL 值不是 {expected_myshell}，是否覆盖？"
        ).ask()
        if answer:
            try:
                subprocess.run(
                    ["setx", env_var_name, expected_myshell],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"环境变量 {env_var_name} 已更新为: {expected_myshell}")
                # 更新当前进程环境变量
                os.environ[env_var_name] = expected_myshell
            except subprocess.CalledProcessError as e:
                print(f"设置环境变量失败: {e.stderr}")
                sys.exit(1)
        else:
            print(f"本库必须基于 MYSHELL={expected_myshell}，终止进程。")
            sys.exit(1)

    # 3. 处理 PowerShell 配置文件
    # 构建 PowerShell 配置文件路径
    ps_folder = os.path.join(userprofile, "Documents", "WindowsPowerShell")
    profile_file = os.path.join(ps_folder, "Microsoft.PowerShell_profile.ps1")
    os.makedirs(ps_folder, exist_ok=True)

    # 定义要检查的核心代码块（包含递归加载和 Import-Module PSReadLine）
    core_block = r"""$functionsDir = "$PSScriptRoot\MyShell\windows"
if (Test-Path $functionsDir) {
    Get-ChildItem -Path $functionsDir -Recurse -Filter *.ps1 -File | ForEach-Object {
        . $_.FullName
    }
}
Import-Module PSReadLine"""

    # 读取现有内容（如果文件不存在则视为空）
    if os.path.exists(profile_file):
        with open(profile_file, 'r', encoding='utf-8-sig') as f:
            existing_content = f.read()
    else:
        existing_content = ""

    # 检查代码块是否已存在
    if block_exists_in_file(existing_content, core_block):
        print("已在 Microsoft.PowerShell_profile.ps1 文件中写入 shell 递归循环。")
    else:
        # 追加代码块（添加换行）
        with open(profile_file, 'a', encoding='utf-8-sig') as f:
            f.write("\n" + core_block + "\n")
        print("init 已帮你在 Microsoft.PowerShell_profile.ps1 文件中写入 shell 递归循环。")

    # 4. 判断 reloadsh 方法是否存在
    # 在新 PowerShell 进程中加载配置文件并检查命令是否存在
    check_cmd = [
        "powershell", "-NoProfile", "-Command",
        f". '{profile_file}'; if (Get-Command reloadsh -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}"
    ]
    try:
        subprocess.run(check_cmd, check=True, capture_output=True, text=True)
        reloadsh_exists = True
        print("检测到 reloadsh 命令存在。")
    except subprocess.CalledProcessError:
        reloadsh_exists = False
        print("\033[93m未找到 reloadsh 命令，请先在终端执行 . $PROFILE\033[0m")
        sys.exit(1)  # 终止进程，不继续执行后续

    # 5. 如果 reloadsh 存在，执行原有逻辑（自动打开新窗口并安装依赖）
    # 创建自定义脚本目录（用于存放自定义函数）
    myshell_windows = os.path.join(ps_folder, "MyShell", "windows")
    os.makedirs(myshell_windows, exist_ok=True)
    print(f"自定义脚本目录已确保存在: {myshell_windows}")

    # 自动打开新窗口执行 . $PROFILE 和 reloadsh（并设置 UTF-8 编码）
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
    # ========== macOS 分支（保持之前的修改） ==========
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