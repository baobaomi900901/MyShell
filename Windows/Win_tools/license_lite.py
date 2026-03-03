# .\Windows\Win_tools\license_lite.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
license_lite_auto.py - 启动Lite授权工具并自动完成机器标识、授权期限输入，生成授权码。

用法：
    python license_lite_auto.py [--root] MACHINE_ID

选项：
    --root      以 root 模式启动（传递 kingauto 参数）
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
from datetime import datetime
from pathlib import Path

import win32gui
import uiautomation as auto
import pyperclip

# ========== 配置区域 ==========
DEFAULT_EXE_RELATIVE = Path("KingAutomate/Licenses/LiteLicense/LiteLicense.exe")
PROJECT_ROOT_ENV_VAR = "AOM_ROOT"          # 可选环境变量，用于覆盖项目根目录
DEFAULT_PROJECT_ROOT = r"D:\Code\aom"      # 默认项目根目录
WINDOW_TITLE = "K-RPA Lite授权"             # 窗口标题
PASSWORD = "kingautomate"                   # 授权密码
MAX_WAIT_SECONDS = 15                        # 等待窗口出现的最大时间（秒）
# =============================

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
        button = window.ButtonControl(Name='生成')
        if not button.Exists():
            button = None
    except:
        pass

    if not button:
        # 方法2：遍历查找 Name='生成' 的按钮
        try:
            for ctrl in window.GetChildren():
                if ctrl.ControlType == auto.ControlType.ButtonControl and ctrl.Name == '生成':
                    button = ctrl
                    break
        except:
            pass

    if not button:
        print("❌ 未能找到'生成'按钮")
        return False

    print("✅ 找到'生成'按钮，尝试点击...")
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

    # 查找 ClassName='TMemo' 的编辑框
    for ctrl in all_controls:
        if ctrl.ControlType == auto.ControlType.EditControl:
            try:
                class_name = ctrl.GetPropertyValue(auto.PropertyId.ClassNameProperty)
                if class_name == 'TMemo':
                    memo_ctrl = ctrl
                    break
            except:
                continue

    if not memo_ctrl:
        print("❌ 未找到授权码结果框（ClassName=TMemo）")
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

def main():
    parser = argparse.ArgumentParser(description="自动完成Lite授权工具的机器标识、授权期限输入和授权码生成")
    parser.add_argument("--root", action="store_true", help="以 root 模式启动（传递 kingauto 参数）")
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

        print(f"启动 LiteLicense.exe{' (Root模式)' if args.root else ''}...")
        if args.root:
            subprocess.Popen([str(exe_path), "kingauto"])
        else:
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

    # 定位机器标识框：ClassName='TEdit', IsPassword=False, IsReadOnly=False，且 HelpText 为空
    machine_ctrl = None
    for eb in edit_boxes:
        if (eb['class_name'] == 'TEdit' 
                and eb['is_password'] is False 
                and eb['is_readonly'] is False 
                and (eb['help_text'] is None or eb['help_text'] == '')):
            machine_ctrl = eb['control']
            print(f"\n✅ 找到机器标识框，索引 {eb['index']}")
            break

    # 定位授权期限框：ClassName='TEdit', HelpText 包含 "正确日期格式"
    expiry_ctrl = None
    for eb in edit_boxes:
        if eb['class_name'] == 'TEdit' and '正确日期格式' in eb['help_text']:
            expiry_ctrl = eb['control']
            print(f"✅ 找到授权期限框，索引 {eb['index']} (HelpText: {eb['help_text']})")
            break

    # 定位密码框：ClassName='TEdit', IsPassword=True
    password_ctrl = None
    for eb in edit_boxes:
        if eb['class_name'] == 'TEdit' and eb['is_password'] is True:
            password_ctrl = eb['control']
            print(f"✅ 找到授权密码框，索引 {eb['index']}")
            break

    # 备用方案（基于索引，仅当上述逻辑失败时）
    if not machine_ctrl:
        candidates = [eb for eb in edit_boxes if eb['class_name'] == 'TEdit' and eb['is_readonly'] is False and eb['is_password'] is False]
        if candidates:
            machine_ctrl = candidates[0]['control']
            print(f"\n⚠️ 使用备用方案，选择第一个可编辑TEdit作为机器标识框，索引 {candidates[0]['index']}")
    if not expiry_ctrl:
        # 如果没找到，可能是HelpText获取不到，尝试根据位置（假设是第一个可编辑TEdit）？但更可靠的是根据HelpText，这里暂时不设自动备用，而是报错。
        # 为了兼容性，可以尝试查找 HelpText 非空且包含日期的
        candidates = [eb for eb in edit_boxes if eb['class_name'] == 'TEdit' and '日期' in eb['help_text']]
        if candidates:
            expiry_ctrl = candidates[0]['control']
            print(f"⚠️ 使用备用方案，根据'日期'关键词找到授权期限框，索引 {candidates[0]['index']}")
        else:
            # 最后一个备选：假设索引 0 是授权期限（根据之前UI，第一个是授权期限，索引0）
            if len(edit_boxes) > 0 and edit_boxes[0]['class_name'] == 'TEdit':
                expiry_ctrl = edit_boxes[0]['control']
                print(f"⚠️ 使用备用方案，假设索引0为授权期限框")
    if not password_ctrl:
        candidates = [eb for eb in edit_boxes if eb['class_name'] == 'TEdit' and eb['is_password'] is True]
        if candidates:
            password_ctrl = candidates[0]['control']
            print(f"⚠️ 使用备用方案，选择第一个密码TEdit作为授权密码框，索引 {candidates[0]['index']}")

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