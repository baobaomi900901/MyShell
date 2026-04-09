# .\Windows\Win_tools\license_lite.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
license_lite.py - 启动Lite授权工具并自动完成机器标识、授权期限输入，生成授权码。

用法：
    python license_lite.py [--root] MACHINE_ID

选项：
    --root      以 root 模式启动，启动参数从 ../../config/private/password.json 的 lite-forever.password 读取
    MACHINE_ID  机器标识字符串

交互：
    脚本会提示输入授权期限（格式 YYYY-MM-DD），校验通过后继续。
    如果目标窗口已存在，则直接使用现有窗口，不再重复启动程序。
"""

import os
import sys
import time
import argparse
import subprocess
import re
import json
from datetime import datetime
from pathlib import Path

import win32gui
import uiautomation as auto
import pyperclip

# ==================== 配置区域（请根据UI特征修改） ====================
# 窗口标题
WINDOW_TITLE = "K-RPA Lite授权"

# 授权密码（填入密码框的字符串）
PASSWORD = "kingautomate"

# 等待窗口出现的最长时间（秒）
MAX_WAIT_SECONDS = 15

# ----- 控件定位特征（修改这些以匹配实际UI） -----
# 机器标识框
MACHINE_CLASS = "TEdit"
MACHINE_IS_PASSWORD = False
MACHINE_IS_READONLY = False
MACHINE_HELP_TEXT = ""                 # 帮助文本为空

# 授权期限框
EXPIRY_CLASS = "TEdit"
EXPIRY_HELP_TEXT_KEYWORD = "正确日期格式"   # 帮助文本包含的关键词

# 授权密码框
PASSWORD_CLASS = "TEdit"
PASSWORD_IS_PASSWORD = True

# 授权码结果框
RESULT_CLASS = "TMemo"

# 生成按钮
GENERATE_BUTTON_NAME = "生成"

# ----- 备用定位（当上述条件匹配失败时使用）-----
# 是否启用备用方案（基于索引或关键词）
ENABLE_FALLBACK = True
# 备用方案中假设的索引（例如：授权期限框可能是第一个TEdit）
FALLBACK_EXPIRY_INDEX = 0
# 备用方案中根据“日期”关键词搜索
FALLBACK_EXPIRY_KEYWORD = "日期"

# ----- 可执行文件路径 -----
DEFAULT_EXE_RELATIVE = Path("KingAutomate/Licenses/LiteLicense/LiteLicense.exe")
PROJECT_ROOT_ENV_VAR = "AOM_ROOT"          # 可选环境变量，用于覆盖项目根目录
DEFAULT_PROJECT_ROOT = r"D:\Code\aom"      # 默认项目根目录
# ============================================================

def find_window_handle(title):
    """根据窗口标题查找窗口句柄（精确匹配）"""
    def enum_callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) == title:
            hwnds.append(hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows(enum_callback, hwnds)
    return hwnds[0] if hwnds else None

def get_edit_boxes_info(window):
    """获取窗口中所有编辑框的属性列表"""
    all_controls = window.GetChildren()
    edit_boxes = []
    for ctrl in all_controls:
        if ctrl.ControlType == auto.ControlType.EditControl:
            try:
                is_password = ctrl.GetPropertyValue(auto.PropertyId.IsPasswordProperty)
            except:
                is_password = 'N/A'
            try:
                class_name = ctrl.GetPropertyValue(auto.PropertyId.ClassNameProperty)
            except:
                class_name = 'N/A'
            automation_id = ctrl.AutomationId
            bounding_rect = ctrl.BoundingRectangle

            is_readonly = 'N/A'
            try:
                value_pattern = ctrl.GetValuePattern()
                is_readonly = value_pattern.IsReadOnly
            except:
                try:
                    is_readonly = ctrl.GetPropertyValue(auto.PropertyId.IsReadOnlyProperty)
                except:
                    pass

            help_text = ''
            try:
                help_text = ctrl.GetPropertyValue(auto.PropertyId.HelpTextProperty)
            except:
                pass

            edit_boxes.append({
                'control': ctrl,
                'index': len(edit_boxes),
                'is_password': is_password,
                'class_name': class_name,
                'automation_id': automation_id,
                'rect': bounding_rect,
                'is_readonly': is_readonly,
                'help_text': help_text
            })
    return edit_boxes

def input_to_control(ctrl, text, description):
    """向控件输入文本，尝试多种方法"""
    print(f"向 {description} 输入文本...")
    ctrl.SetFocus()
    time.sleep(0.2)

    # 尝试 ValuePattern.SetValue
    try:
        value_pattern = ctrl.GetValuePattern()
        value_pattern.SetValue(text)
        print(f"  ✅ 通过 ValuePattern 成功输入")
        return True
    except Exception as e:
        print(f"  ValuePattern 输入失败: {e}")

    # 尝试 SendKeys
    try:
        ctrl.SendKeys(text)
        print(f"  ✅ 通过 SendKeys 成功输入")
        return True
    except Exception as e:
        print(f"  SendKeys 输入失败: {e}")

    # 尝试 Click + SendKeys
    try:
        ctrl.Click()
        time.sleep(0.2)
        ctrl.SendKeys(text)
        print(f"  ✅ 通过 Click+SendKeys 成功输入")
        return True
    except Exception as e:
        print(f"  Click+SendKeys 输入失败: {e}")

    print(f"  ❌ 所有输入方法均失败")
    return False

def click_generate_button(window):
    """点击'生成'按钮，尝试多种方法"""
    print("\n正在查找'生成'按钮...")
    button = None

    # 方法1：通过 Name 定位
    try:
        button = window.ButtonControl(Name=GENERATE_BUTTON_NAME)
        if not button.Exists():
            button = None
    except:
        pass

    if not button:
        # 方法2：遍历查找 Name='生成' 的按钮
        try:
            for ctrl in window.GetChildren():
                if ctrl.ControlType == auto.ControlType.ButtonControl and ctrl.Name == GENERATE_BUTTON_NAME:
                    button = ctrl
                    break
        except:
            pass

    if not button:
        print(f"❌ 未能找到'{GENERATE_BUTTON_NAME}'按钮")
        return False

    print(f"✅ 找到'{GENERATE_BUTTON_NAME}'按钮，尝试点击...")
    button.SetFocus()
    time.sleep(0.3)

    # 点击尝试顺序
    try:
        button.Invoke()
        print("   ✅ 通过 InvokePattern 点击成功")
        return True
    except Exception as e:
        print(f"   InvokePattern 失败: {e}")

    try:
        legacy = button.GetLegacyIAccessiblePattern()
        if legacy:
            legacy.DoDefaultAction()
            print("   ✅ 通过 LegacyIAccessible.DoDefaultAction 点击成功")
            return True
    except Exception as e:
        print(f"   LegacyIAccessible 失败: {e}")

    try:
        rect = button.BoundingRectangle
        if rect:
            x = (rect.left + rect.right) // 2
            y = (rect.top + rect.bottom) // 2
            auto.Click(x, y)
            print(f"   ✅ 通过模拟鼠标点击 ({x}, {y}) 成功")
            return True
    except Exception as e:
        print(f"   模拟鼠标点击失败: {e}")

    try:
        button.SendKeys('{Space}')
        print("   ✅ 通过发送空格键点击成功")
        return True
    except Exception as e:
        print(f"   发送空格键失败: {e}")

    print("❌ 所有点击方法均失败")
    return False

def copy_authorization_code_to_clipboard(window):
    """将授权码结果（ClassName=TMemo）复制到剪贴板"""
    print("\n正在获取授权码结果...")
    all_controls = window.GetChildren()
    memo_ctrl = None

    # 查找 ClassName=RESULT_CLASS 的编辑框
    for ctrl in all_controls:
        if ctrl.ControlType == auto.ControlType.EditControl:
            try:
                class_name = ctrl.GetPropertyValue(auto.PropertyId.ClassNameProperty)
                if class_name == RESULT_CLASS:
                    memo_ctrl = ctrl
                    break
            except:
                continue

    if not memo_ctrl:
        print(f"❌ 未找到授权码结果框（ClassName={RESULT_CLASS}）")
        return False

    try:
        value_pattern = memo_ctrl.GetValuePattern()
        code_text = value_pattern.Value
        if code_text:
            pyperclip.copy(code_text)
            print(f"✅ 已复制授权码到剪贴板，内容长度: {len(code_text)} 字符")
            print(f"   前50字符: {code_text[:50]}{'...' if len(code_text)>50 else ''}")
            return True
        else:
            print("⚠️ 授权码内容为空，可能尚未生成")
            return False
    except Exception as e:
        print(f"获取授权码失败: {e}")
        return False

def get_default_exe_path():
    """获取默认的 LiteLicense.exe 路径（支持环境变量覆盖）"""
    project_root = os.environ.get(PROJECT_ROOT_ENV_VAR, DEFAULT_PROJECT_ROOT)
    exe_path = Path(project_root) / DEFAULT_EXE_RELATIVE
    return exe_path

def wait_for_window(title, max_seconds=MAX_WAIT_SECONDS):
    """等待窗口出现，返回窗口句柄或None"""
    print(f"等待窗口 '{title}' 出现...")
    for i in range(int(max_seconds * 2)):  # 每0.5秒检查一次
        hwnd = find_window_handle(title)
        if hwnd:
            print(f"✅ 窗口已出现 (句柄: {hwnd})")
            return hwnd
        time.sleep(0.5)
    print(f"❌ 等待窗口超时 ({max_seconds}秒)")
    return None

def validate_date(date_str):
    """验证日期格式是否为 YYYY-MM-DD 且为有效日期"""
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def resolve_password_file(script_path):
    """根据脚本路径解析密码文件位置：脚本所在目录/../../config/private/password.json"""
    base = script_path.parent
    password_file = (base / "../../config/private/password.json").resolve()
    return password_file

def get_root_startup_param(password_file):
    """从密码文件中读取 lite-forever.password 作为 root 模式启动参数"""
    if not password_file.exists():
        print(f"错误: 密码文件不存在: {password_file}", file=sys.stderr)
        print("请确保文件位于 config/private/password.json 并包含 'lite-forever' 密码。", file=sys.stderr)
        return None
    try:
        with open(password_file, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: 密码文件格式错误，不是有效的 JSON: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"错误: 读取密码文件失败: {e}", file=sys.stderr)
        return None

    lite_forever = config.get('lite-forever')
    if not lite_forever or not isinstance(lite_forever, dict):
        print("错误: 密码文件中未找到 'lite-forever' 对象。", file=sys.stderr)
        return None
    param = lite_forever.get('password')
    if not param or not isinstance(param, str):
        print("错误: 'lite-forever' 中缺少有效的 'password' 字段。", file=sys.stderr)
        return None
    return param

def main():
    parser = argparse.ArgumentParser(description="自动完成Lite授权工具的机器标识、授权期限输入和授权码生成")
    parser.add_argument("--root", action="store_true", help="以 root 模式启动（启动参数从配置文件读取）")
    parser.add_argument("machine_id", help="机器标识字符串")
    args = parser.parse_args()

    # 交互式获取授权期限日期
    print("请输入授权期限（格式 YYYY-MM-DD）：")
    while True:
        expiry_date = input("> ").strip()
        if validate_date(expiry_date):
            break
        else:
            print("日期格式错误或无效，请重新输入（例如 2025-12-31）：")

    # 先检查窗口是否已存在
    hwnd = find_window_handle(WINDOW_TITLE)
    if hwnd:
        print(f"✅ 已存在窗口 '{WINDOW_TITLE}'，直接使用现有窗口。")
    else:
        exe_path = get_default_exe_path()
        if not exe_path.exists():
            print(f"错误: 程序文件不存在: {exe_path}", file=sys.stderr)
            sys.exit(1)

        # 根据 root 参数决定启动参数
        if args.root:
            # 读取启动参数从密码文件
            script_path = Path(__file__).resolve()
            password_file = resolve_password_file(script_path)
            startup_param = get_root_startup_param(password_file)
            if startup_param is None:
                print("无法获取 root 启动参数，退出。", file=sys.stderr)
                sys.exit(1)
            print(f"启动 LiteLicense.exe (Root模式)，参数: {startup_param}")
            subprocess.Popen([str(exe_path), startup_param])
        else:
            print("启动 LiteLicense.exe...")
            subprocess.Popen([str(exe_path)])

        # 等待窗口出现
        hwnd = wait_for_window(WINDOW_TITLE)
        if not hwnd:
            print("无法找到授权窗口，退出。", file=sys.stderr)
            sys.exit(1)

    window = auto.ControlFromHandle(hwnd)
    window.SetFocus()
    time.sleep(0.5)

    edit_boxes = get_edit_boxes_info(window)
    print("\n当前窗口中所有编辑框：")
    for eb in edit_boxes:
        print(f"  索引 {eb['index']}: ClassName={eb['class_name']}, IsPassword={eb['is_password']}, IsReadOnly={eb['is_readonly']}, HelpText='{eb['help_text']}', AutomationId={eb['automation_id']}")

    # 定位机器标识框：使用配置的特征
    machine_ctrl = None
    for eb in edit_boxes:
        if (eb['class_name'] == MACHINE_CLASS 
                and eb['is_password'] is MACHINE_IS_PASSWORD 
                and eb['is_readonly'] is MACHINE_IS_READONLY 
                and (eb['help_text'] is None or eb['help_text'] == MACHINE_HELP_TEXT)):
            machine_ctrl = eb['control']
            print(f"\n✅ 找到机器标识框，索引 {eb['index']}")
            break

    # 定位授权期限框：使用配置的关键词
    expiry_ctrl = None
    for eb in edit_boxes:
        if eb['class_name'] == EXPIRY_CLASS and EXPIRY_HELP_TEXT_KEYWORD in eb['help_text']:
            expiry_ctrl = eb['control']
            print(f"✅ 找到授权期限框，索引 {eb['index']} (HelpText: {eb['help_text']})")
            break

    # 定位密码框：使用配置的特征
    password_ctrl = None
    for eb in edit_boxes:
        if eb['class_name'] == PASSWORD_CLASS and eb['is_password'] is PASSWORD_IS_PASSWORD:
            password_ctrl = eb['control']
            print(f"✅ 找到授权密码框，索引 {eb['index']}")
            break

    # 备用方案（如果 ENABLE_FALLBACK 为 True）
    if ENABLE_FALLBACK:
        if not machine_ctrl:
            candidates = [eb for eb in edit_boxes if eb['class_name'] == MACHINE_CLASS and eb['is_readonly'] is False and eb['is_password'] is False]
            if candidates:
                machine_ctrl = candidates[0]['control']
                print(f"\n⚠️ 使用备用方案，选择第一个可编辑{MACHINE_CLASS}作为机器标识框，索引 {candidates[0]['index']}")
        if not expiry_ctrl:
            # 尝试根据备用关键词搜索
            candidates = [eb for eb in edit_boxes if eb['class_name'] == EXPIRY_CLASS and FALLBACK_EXPIRY_KEYWORD in eb['help_text']]
            if candidates:
                expiry_ctrl = candidates[0]['control']
                print(f"⚠️ 使用备用方案，根据'{FALLBACK_EXPIRY_KEYWORD}'关键词找到授权期限框，索引 {candidates[0]['index']}")
            else:
                # 假设索引 FALLBACK_EXPIRY_INDEX 是授权期限框
                if len(edit_boxes) > FALLBACK_EXPIRY_INDEX and edit_boxes[FALLBACK_EXPIRY_INDEX]['class_name'] == EXPIRY_CLASS:
                    expiry_ctrl = edit_boxes[FALLBACK_EXPIRY_INDEX]['control']
                    print(f"⚠️ 使用备用方案，假设索引{FALLBACK_EXPIRY_INDEX}为授权期限框")
        if not password_ctrl:
            candidates = [eb for eb in edit_boxes if eb['class_name'] == PASSWORD_CLASS and eb['is_password'] is True]
            if candidates:
                password_ctrl = candidates[0]['control']
                print(f"⚠️ 使用备用方案，选择第一个密码{PASSWORD_CLASS}作为授权密码框，索引 {candidates[0]['index']}")

    if not machine_ctrl:
        print("❌ 无法定位机器标识框")
        sys.exit(1)
    if not expiry_ctrl:
        print("❌ 无法定位授权期限框")
        sys.exit(1)
    if not password_ctrl:
        print("❌ 无法定位授权密码框")
        sys.exit(1)

    # 输入机器标识
    input_to_control(machine_ctrl, args.machine_id, "机器标识框")
    # 输入授权期限
    input_to_control(expiry_ctrl, expiry_date, "授权期限框")
    # 输入授权密码
    input_to_control(password_ctrl, PASSWORD, "授权密码框")

    # 点击生成按钮
    click_success = click_generate_button(window)
    if not click_success:
        print("点击生成按钮失败，可能无法生成授权码。")

    print("\n等待授权码生成...")
    time.sleep(2)  # 可根据实际情况调整或改为检测结果框变化

    # 复制授权码到剪贴板
    copy_authorization_code_to_clipboard(window)

    print("\n✅ 所有操作完成。")

if __name__ == "__main__":
    main()