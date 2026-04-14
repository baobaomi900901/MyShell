import platform
import getpass
import os
import subprocess
import json
import sys
import time
from enum import Enum

# ----------------------------------------------------------------------
# 辅助函数
# ----------------------------------------------------------------------
def normalize_lines(text):
    """将文本按行分割，并去除每行的首尾空白"""
    return [line.strip() for line in text.splitlines()]

def block_exists_in_file(file_content, block_content):
    """检查 block_content 是否以行序列的形式存在于 file_content 中（忽略每行的首尾空白）"""
    file_lines = normalize_lines(file_content)
    block_lines = normalize_lines(block_content)
    len_block = len(block_lines)
    for i in range(len(file_lines) - len_block + 1):
        if file_lines[i:i+len_block] == block_lines:
            return True
    return False

class System(Enum):
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

# 获取当前脚本所在目录（用于定位 config/private/function_tracker.json）
script_dir = os.path.dirname(os.path.abspath(__file__))
config_json = os.path.join(script_dir, "config", "private", "function_tracker.json")

# ----------------------------------------------------------------------
# Windows 分支
# ----------------------------------------------------------------------
if current_system == System.WINDOWS:
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

    def get_user_environment_variable(name):
        """从注册表读取用户环境变量"""
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
    ps_folder = os.path.join(userprofile, "Documents", "WindowsPowerShell")
    profile_file = os.path.join(ps_folder, "Microsoft.PowerShell_profile.ps1")
    os.makedirs(ps_folder, exist_ok=True)

    core_block = r"""$functionsDir = "$HOME\Documents\WindowsPowerShell\MyShell\windows"
if (Test-Path $functionsDir) {
    Get-ChildItem -Path $functionsDir -Recurse -Filter *.ps1 -File |
        Where-Object { $_.FullName -notmatch '\\Expired\\' } |
        ForEach-Object {
            . $_.FullName
        }
}
Import-Module PSReadLine"""

    if os.path.exists(profile_file):
        with open(profile_file, 'r', encoding='utf-8-sig') as f:
            existing_content = f.read()
    else:
        existing_content = ""

    if block_exists_in_file(existing_content, core_block):
        print("已在 Microsoft.PowerShell_profile.ps1 文件中写入 shell 递归循环。")
    else:
        with open(profile_file, 'a', encoding='utf-8-sig') as f:
            f.write("\n" + core_block + "\n")
        print("init 已帮你在 Microsoft.PowerShell_profile.ps1 文件中写入 shell 递归循环。")

    # 4. 判断 reloadsh 方法是否存在
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
        sys.exit(1)

    # 5. 如果 reloadsh 存在，先执行 reloadsh --no-restart（刷新函数列表）
    print("正在执行 reloadsh --no-restart 以刷新函数列表...")
    try:
        # 不捕获输出，直接显示到控制台，避免编码问题
        subprocess.run(
            ["powershell", "-Command",
             f". '{profile_file}'; reloadsh --no-restart"],
            check=True  # 不设置 capture_output 和 text
        )
        print("reloadsh 执行完毕。")
    except subprocess.CalledProcessError as e:
        print(f"reloadsh 执行失败，退出码: {e.returncode}")

    # 6. 安装 Python 依赖（从 function_tracker.json）
    if os.path.exists(config_json):
        print("找到 function_tracker.json，开始检查 Python 依赖...")
        try:
            with open(config_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            packages = data.get('pip_package', [])
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

    # 7. 通过模拟按键打开新终端（参考 reloadsh.py 的实现）
    def send_combo(keys):
        for key in keys:
            keyboard.press(key)
        time.sleep(0.05)
        for key in reversed(keys):
            keyboard.release(key)

    def send_vscode_combo():
        send_combo(['ctrl', 'shift', '`'])

    def send_windows_combo():
        send_combo(['ctrl', 'shift', 't'])

    def detect_terminal():
        if os.environ.get('TERM_PROGRAM') == 'vscode':
            return "vscode"
        else:
            return "windows"

    terminal_type = detect_terminal()
    print(f"powershell 不支持热更新, 即将帮你打开新的终端窗口")
    print(f"检测到当前终端窗口类型：{terminal_type}，正在打开新终端...")

    # 倒计时 3 秒
    def countdown(seconds):
        for i in range(seconds, 0, -1):
            print(f"  窗口将在 {i} 秒后打开...", flush=True)
            time.sleep(1)

    countdown(3)

    if terminal_type == "vscode":
        send_vscode_combo()
        print("组合键 Ctrl+Shift+` 已发送，VS Code 将打开新终端。")
    else:
        send_windows_combo()
        print("组合键 Ctrl+Shift+t 已发送，Windows 终端将恢复已关闭标签页。")

    print("\033[91m请自行关闭当前终端窗口!\033[0m")

# ----------------------------------------------------------------------
# macOS 分支
# ----------------------------------------------------------------------
elif current_system == System.MACOS:
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

    # 处理环境变量 MYSHELL
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
  # 如果路径中包含 /Expired/ 则跳过
  if [[ "$func_file" == *"/Expired/"* ]]; then
    continue
  fi
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
    except subprocess.CalledProcessError:
        print("\033[93m未找到 reloadsh 命令，请先在终端执行 source ~/.zshrc\033[0m")

    # 5. 安装 Python 依赖（从 function_tracker.json）
    myshell_env = os.environ.get('MYSHELL')
    if myshell_env:
        config_json_mac = os.path.join(myshell_env, "config", "private", "function_tracker.json")
    else:
        config_json_mac = os.path.join(home, "MyShell", "config", "private", "function_tracker.json")

    if os.path.exists(config_json_mac):
        print("找到 function_tracker.json，开始检查 Python 依赖...")
        try:
            with open(config_json_mac, 'r', encoding='utf-8') as f:
                data = json.load(f)
            packages = data.get('pip_package', [])
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

# ----------------------------------------------------------------------
# 其他操作系统分支
# ----------------------------------------------------------------------
else:
    print("其他操作系统，暂无自动配置。")