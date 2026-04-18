import platform
import getpass
import os
import subprocess
import json
import sys
import time
import shlex
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

# 本仓库根目录（init.py 所在目录）：MYSHELL 与 function_tracker 均以此为准
myshell_root = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
config_json = os.path.join(myshell_root, "config", "private", "function_tracker.json")

# ----------------------------------------------------------------------
# Windows 分支
# ----------------------------------------------------------------------
if current_system == System.WINDOWS:
    import winreg

    # 1. 安装必要的 Python 库（仅 Windows 需要 keyboard 模拟快捷键）
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
    print(f"MyShell 根目录（将写入 MYSHELL）: {myshell_root}")

    def get_user_environment_variable(name):
        """从注册表读取用户环境变量"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
            value, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return value
        except (FileNotFoundError, OSError):
            return None

    # 2. 处理环境变量 MYSHELL（与当前 init.py 所在仓库一致）
    env_var_name = "MYSHELL"
    current_reg_value = get_user_environment_variable(env_var_name)

    def normalize_path(p):
        return os.path.normpath(p).lower()

    need_update = False
    if current_reg_value is None:
        print(f"环境变量 {env_var_name} 不存在。")
        need_update = True
    else:
        if normalize_path(current_reg_value) != normalize_path(myshell_root):
            print(f"当前 MYSHELL 值为: {current_reg_value}")
            print(f"期望值为: {myshell_root}")
            need_update = True
        else:
            print("环境变量 MYSHELL 已正确设置。")

    if need_update:
        answer = questionary.confirm(
            f"当前 MYSHELL 值不是 {myshell_root}，是否覆盖？"
        ).ask()
        if answer is True:
            try:
                subprocess.run(
                    ["setx", env_var_name, myshell_root],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"环境变量 {env_var_name} 已更新为: {myshell_root}")
                os.environ[env_var_name] = myshell_root
            except subprocess.CalledProcessError as e:
                print(f"设置环境变量失败: {e.stderr}")
                sys.exit(1)
        elif answer is False:
            print(f"本库必须基于 MYSHELL={myshell_root}，终止进程。")
            sys.exit(1)
        else:
            print("已取消（未修改环境变量），终止进程。")
            sys.exit(1)

    os.environ[env_var_name] = myshell_root

    # 3. 处理 PowerShell 配置文件（Windows PowerShell 5 与 PowerShell 7）
    profiles = [
        os.path.join(userprofile, "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1"),
        os.path.join(userprofile, "Documents", "PowerShell", "Microsoft.PowerShell_profile.ps1"),
    ]

    core_block = r"""$functionsDir = Join-Path $env:MYSHELL "windows"
if ($env:MYSHELL -and (Test-Path $functionsDir)) {
    Get-ChildItem -Path $functionsDir -Recurse -Filter *.ps1 -File |
        Where-Object { $_.FullName -notmatch '\\Expired\\' } |
        ForEach-Object {
            . $_.FullName
        }
}
Import-Module PSReadLine"""

    def ps_escape_single(path: str) -> str:
        return path.replace("'", "''")

    for profile_path in profiles:
        os.makedirs(os.path.dirname(profile_path), exist_ok=True)
        if os.path.exists(profile_path):
            with open(profile_path, 'r', encoding='utf-8-sig') as f:
                existing_content = f.read()
        else:
            existing_content = ""
        if block_exists_in_file(existing_content, core_block):
            print(f"已存在 MyShell 加载块: {profile_path}")
        else:
            with open(profile_path, 'a', encoding='utf-8-sig') as f:
                f.write("\n" + core_block + "\n")
            print(f"init 已写入 shell 加载块: {profile_path}")

    profile_shell_pairs = [
        (profiles[0], "powershell"),
        (profiles[1], "pwsh"),
    ]
    profile_file = None
    shell_for_profile = None
    for profile_path, exe in profile_shell_pairs:
        if not os.path.exists(profile_path):
            continue
        q = ps_escape_single(os.path.normpath(profile_path))
        check_cmd = [
            exe, "-NoProfile", "-Command",
            f". '{q}'; if (Get-Command reloadsh -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}"
        ]
        try:
            subprocess.run(check_cmd, check=True, capture_output=True, text=True)
            profile_file = profile_path
            shell_for_profile = exe
            print(f"检测到 reloadsh（使用 {exe} 加载: {profile_path}）。")
            break
        except FileNotFoundError:
            print(f"未安装或找不到 {exe}，跳过配置文件: {profile_path}")
        except subprocess.CalledProcessError:
            continue

    if not profile_file or not shell_for_profile:
        print("\033[93m未找到 reloadsh 命令，请确认 MYSHELL 已生效后执行: . $PROFILE（或重启终端）\033[0m")
        sys.exit(1)

    # 5. 如果 reloadsh 存在，先执行 reloadsh --no-restart（刷新函数列表）
    print("正在执行 reloadsh --no-restart 以刷新函数列表...")
    try:
        q = ps_escape_single(os.path.normpath(profile_file))
        subprocess.run(
            [shell_for_profile, "-NoProfile", "-Command", f". '{q}'; reloadsh --no-restart"],
            check=True
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
    print("powershell 不支持热更新, 即将帮你打开新的终端窗口")
    print(f"检测到当前终端窗口类型：{terminal_type}，正在打开新终端...")

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
    print(f"MyShell 根目录（将写入 MYSHELL）: {myshell_root}")

    # 1. 安装 questionary（keyboard 仅 Windows 需要）
    print("检查并安装必要的 Python 库...")
    try:
        import questionary
    except ImportError:
        print("正在安装 questionary ...")
        subprocess.run([sys.executable, "-m", "pip", "install", "questionary"], check=True)
        import questionary

    # 2. 确定配置文件路径（.zshrc）
    profile_file = os.path.join(home, ".zshrc")
    print(f"目标配置文件: {profile_file}")

    if not os.path.exists(profile_file):
        open(profile_file, 'w', encoding='utf-8').close()
        print(f"已创建空配置文件: {profile_file}")

    with open(profile_file, 'r', encoding='utf-8') as f:
        content = f.read()

    env_line_pattern = "export MYSHELL="
    desired_env = f"export MYSHELL={shlex.quote(myshell_root)}"
    lines = content.splitlines()
    env_index = None
    existing_env = None
    for i, line in enumerate(lines):
        if line.startswith(env_line_pattern):
            env_index = i
            existing_env = line.strip()
            break

    expected_abs = os.path.normpath(myshell_root)

    if env_index is not None:
        value_part = existing_env[len(env_line_pattern):].strip()
        if (value_part.startswith('"') and value_part.endswith('"')) or \
           (value_part.startswith("'") and value_part.endswith("'")):
            value_part = value_part[1:-1]
        if value_part.startswith("${HOME}"):
            value_part = value_part.replace("${HOME}", home)
        elif value_part.startswith("$HOME"):
            value_part = value_part.replace("$HOME", home)
        elif value_part.startswith('~'):
            value_part = os.path.expanduser(value_part)
        actual_abs = os.path.normpath(value_part)
        if actual_abs != expected_abs:
            print(f"当前 MYSHELL 设置为: {existing_env}")
            answer = questionary.confirm(
                f"当前 MYSHELL 值不是 {desired_env}，是否覆盖？"
            ).ask()
            if answer is True:
                lines[env_index] = desired_env
                with open(profile_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(lines) + "\n")
                print("已更新 MYSHELL 环境变量。")
            elif answer is False:
                print(f"本库必须基于 MYSHELL 指向当前仓库（{myshell_root}），终止进程。")
                sys.exit(1)
            else:
                print("已取消（未修改环境变量），终止进程。")
                sys.exit(1)
        else:
            print("MYSHELL 环境变量已正确设置。")
    else:
        with open(profile_file, 'a', encoding='utf-8') as f:
            f.write("\n" + desired_env + "\n")
        print("已添加 MYSHELL 环境变量到配置文件。")

    os.environ["MYSHELL"] = myshell_root

    with open(profile_file, 'r', encoding='utf-8') as f:
        content = f.read()

    loop_block_legacy = """for func_file in ~/MyShell/MacOS/**/*.zsh(N); do
  # 如果路径中包含 /Expired/ 则跳过
  if [[ "$func_file" == *"/Expired/"* ]]; then
    continue
  fi
  source "$func_file"
done
zstyle ':completion:*' menu select=1"""

    loop_block = """setopt extended_glob
for func_file in "$MYSHELL"/MacOS/**/*.zsh(N); do
  if [[ "$func_file" == *"/Expired/"* ]]; then
    continue
  fi
  source "$func_file"
done
zstyle ':completion:*' menu select=1"""

    legacy_home_myshell = os.path.normpath(os.path.join(home, "MyShell"))
    has_modern = block_exists_in_file(content, loop_block)
    has_legacy = block_exists_in_file(content, loop_block_legacy)

    if has_modern:
        print("已在 .zshrc 中配置基于 $MYSHELL 的加载循环。")
    elif has_legacy and legacy_home_myshell == myshell_root:
        print("已在 .zshrc 中写入 shell 递归循环（与 ~/MyShell 布局一致）。")
    elif has_legacy:
        print(
            "检测到旧的 ~/MyShell 加载块，但当前仓库不在 ~/MyShell；"
            "请编辑 .zshrc 删除旧的 for 循环后重新运行 init。"
        )
        sys.exit(1)
    else:
        with open(profile_file, 'a', encoding='utf-8') as f:
            f.write("\n" + loop_block + "\n")
        print("init 已帮你在 .zshrc 文件中写入 shell 递归循环。")

    q_prof = shlex.quote(profile_file)
    try:
        subprocess.run(
            ["zsh", "-c", f"source {q_prof} && type reloadsh >/dev/null 2>&1"],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError:
        print("\033[93m未找到 reloadsh 命令，请先在终端执行 source ~/.zshrc\033[0m")
        sys.exit(1)

    try:
        subprocess.run(["zsh", "-c", f"source {q_prof} && reloadsh"], check=True)
        print("已执行 reloadsh 命令。")
    except subprocess.CalledProcessError as e:
        print(f"reloadsh 执行失败，退出码: {e.returncode}")
        sys.exit(1)

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

# ----------------------------------------------------------------------
# 其他操作系统分支
# ----------------------------------------------------------------------
else:
    print("其他操作系统，暂无自动配置。")
