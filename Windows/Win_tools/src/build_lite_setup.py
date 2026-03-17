# .\Windows\Win_tools\build_lite_setup.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess

def get_file_version(filepath):
    """通过 PowerShell 获取文件的产品版本号，失败返回 None"""
    try:
        cmd = ['powershell', '-Command', f'(Get-Item "{filepath}").VersionInfo.ProductVersion']
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode == 0:
            version = result.stdout.strip()
            return version if version else None
        else:
            return None
    except Exception:
        return None

def clean_temp_folder():
    """结束可能占用文件的进程并删除临时文件夹 ONEFIL~1"""
    ps_script = """
    # 结束可能锁定的进程
    taskkill /F /IM ISCC.exe 2>$null
    taskkill /F /IM islzma64.exe 2>$null
    taskkill /F /IM ISPP.exe 2>$null
    Start-Sleep -Seconds 1
    # 删除临时文件夹
    Remove-Item -Path "C:\\Users\\mobytang\\AppData\\Local\\Temp\\ONEFIL~1" -Recurse -Force -ErrorAction Stop
    """
    try:
        result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print("已清理临时文件夹缓存。")
        else:
            print(f"清理临时文件夹失败（可能已不存在或无权限）: {result.stderr}")
    except Exception as e:
        print(f"清理临时文件夹时出错: {e}")

def main():
    # 获取命令行参数（第一个参数）
    if len(sys.argv) < 2:
        print("错误：请提供一个参数。")
        sys.exit(1)
    param = sys.argv[1]
    print(f"传入的参数: {param}")

    # 在桌面上查找指定名称的 exe 文件
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    exe_name = f"{param}.exe"
    exe_path = os.path.join(desktop, exe_name)
    
    product_version = None
    if os.path.isfile(exe_path):
        print(f"✅ 在桌面找到: {exe_path}")
        # 读取产品版本号
        product_version = get_file_version(exe_path)
        if product_version:
            print(f"产品版本号: {product_version}")
        else:
            print("无法读取产品版本号")
            sys.exit(1)
    else:
        print(f"❌ 在桌面未找到: {exe_name}")
        sys.exit(1)

    # 获取环境变量 MYSHELL
    env_path = os.environ.get('MYSHELL')
    if not env_path:
        print("环境变量 MYSHELL 未设置。")
        sys.exit(1)

    # 构造目标文件路径
    target_exe = os.path.join(env_path, '_tools', 'lite_setup', 'k-setup.exe')
    print(f"查找路径: {target_exe}")

    # 检查文件是否存在
    if os.path.isfile(target_exe):
        print("✅ 找到 k-setup.exe")
        
        # 清理上一次可能的临时缓存
        clean_temp_folder()

        # 构建参数：--version <产品版本号>
        cmd_args = [target_exe, '--version', product_version]
        print(f"执行命令: {' '.join(cmd_args)}")
        try:
            result = subprocess.run(cmd_args)
            print(f"\nk-setup.exe 执行完成，返回码: {result.returncode}")
        except Exception as e:
            print(f"运行 k-setup.exe 时出错: {e}")
            sys.exit(1)
    else:
        print("❌ 未找到 k-setup.exe")
        sys.exit(1)

if __name__ == "__main__":
    main()