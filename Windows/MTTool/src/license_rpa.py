import os
import json
import subprocess
import time
import logging
import uiautomation as auto

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_process_running(process_name):
    """检查进程是否运行"""
    try:
        output = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {process_name}"', shell=True, text=True)
        return process_name.lower() in output.lower()
    except subprocess.CalledProcessError:
        return False

def read_password_from_json():
    """从环境变量 MYSHELL/config/password.json 读取 rpa.password"""
    myshell = os.environ.get('MYSHELL')
    if not myshell:
        logging.error("环境变量 MYSHELL 未设置")
        return None

    json_path = os.path.join(myshell, 'config', 'password.json')
    if not os.path.exists(json_path):
        logging.error(f"密码文件不存在: {json_path}")
        return None

    try:
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        password = data.get('rpa', {}).get('password')
        if not password:
            logging.error("JSON 文件中未找到 rpa.password 字段")
            return None
        return password
    except Exception as e:
        logging.error(f"读取文件时发生错误: {e}")
        return None

def set_control_text(control, text):
    """设置控件文本，优先使用 ValuePattern，失败则回退到 SendKeys"""
    try:
        value_pattern = control.GetValuePattern()
        value_pattern.SetValue(text)
        logging.info(f"已通过 ValuePattern 设置文本: {text}")
        return True
    except Exception as e:
        logging.warning(f"ValuePattern 失败: {e}，尝试 SendKeys")
        try:
            control.SendKeys(text)
            logging.info(f"已通过 SendKeys 设置文本: {text}")
            return True
        except Exception as e2:
            logging.error(f"SendKeys 失败: {e2}")
            return False

def get_password_edit(window):
    """获取窗口中的密码输入框（IsPassword=True 的 TEdit）"""
    # 尝试获取所有 TEdit 控件，最多等待5秒，确保控件加载
    for attempt in range(3):
        # 获取窗口下的所有子控件（不限深度）
        all_controls = window.GetChildren()
        t_edits = [ctrl for ctrl in all_controls
                   if ctrl.ControlType == auto.ControlType.EditControl and ctrl.ClassName == 'TEdit']
        
        # 筛选出 IsPassword=True 的
        password_edits = [edit for edit in t_edits if edit.IsPassword]
        
        if password_edits:
            # 理论上只有一个，如果有多个则取最后一个（或可根据其他特征筛选）
            if len(password_edits) > 1:
                logging.warning(f"找到 {len(password_edits)} 个 IsPassword=True 的 TEdit，将使用最后一个")
                for i, edit in enumerate(password_edits):
                    logging.info(f"  密码框 {i+1}: AutomationId={edit.AutomationId}, BoundingRect={edit.BoundingRectangle}")
            return password_edits[-1]  # 返回最后一个（或根据需要选择）
        
        # 如果未找到，等待并重试
        if attempt < 2:
            logging.info(f"未找到密码框，等待 1 秒后重试 ({attempt+1}/3)")
            time.sleep(1)
    return None

def launch_and_fill_fields(exe_path, password):
    """启动程序（若未运行），等待窗口，依次输入 K-RPA 和密码"""
    if not os.path.exists(exe_path):
        logging.error(f"可执行文件不存在: {exe_path}")
        return

    process_name = os.path.basename(exe_path)
    if is_process_running(process_name):
        logging.info(f"进程 {process_name} 已在运行，不再重复启动。")
    else:
        logging.info(f"正在以普通用户权限启动 {exe_path} ...")
        try:
            # 使用 cmd /c start 降权启动，避免继承管理员权限
            subprocess.Popen(f'cmd /c start "" "{exe_path}"', shell=True)
        except Exception as e:
            logging.error(f"启动程序失败: {e}")
            return

    # 等待窗口出现
    logging.info("等待窗口 '授权制作' 出现...")
    window = auto.WindowControl(Name='授权制作', searchDepth=1, waitTime=15)
    if not window.Exists(maxSearchSeconds=15):
        logging.error("未找到目标窗口 '授权制作'")
        return

    window.SetFocus()
    time.sleep(1)  # 等待窗口完全激活

    # ========== 1. 输入 K-RPA ==========
    logging.info("定位普通编辑框 (AutomationId='1001')...")
    edit_normal = window.EditControl(AutomationId='1001')
    if not edit_normal.Exists(maxSearchSeconds=5):
        logging.error("未找到 AutomationId='1001' 的编辑框，无法输入 K-RPA")
    else:
        set_control_text(edit_normal, "K-RPA")

    # ========== 2. 输入密码 ==========
    logging.info("定位密码输入框（通过 IsPassword=True 筛选）...")
    password_edit = get_password_edit(window)
    if not password_edit:
        logging.error("未找到密码输入框")
        return

    logging.info(f"找到密码框，AutomationId={password_edit.AutomationId}")
    password_edit.SetFocus()
    time.sleep(0.5)
    set_control_text(password_edit, password)
    logging.info("密码已填入。")

def main():
    password = read_password_from_json()
    if not password:
        logging.error("无法获取密码，脚本退出。")
        return

    exe_path = r"D:\Code\aom\Tools\LicensesMake\LicensesMake.exe"
    launch_and_fill_fields(exe_path, password)

if __name__ == "__main__":
    main()