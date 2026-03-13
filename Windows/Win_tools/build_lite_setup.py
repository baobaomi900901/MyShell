# .\Windows\Win_tools\build_lite_setup.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

def main():
    # 获取命令行参数（第一个参数）
    if len(sys.argv) < 2:
        print("错误：请提供一个参数。")
        sys.exit(1)
    param = sys.argv[1]
    print(f"传入的参数: {param}")

    # 获取环境变量 MYSHELL_tools
    env_path = os.environ.get('MYSHELL_tools')
    if not env_path:
        print("环境变量 MYSHELL_tools 未设置。")
        sys.exit(1)

    # 构造目标文件路径
    target_exe = os.path.join(env_path, 'lite_setup', 'k-setup.exe')
    print(f"查找路径: {target_exe}")

    # 检查文件是否存在
    if os.path.isfile(target_exe):
        print("✅ 找到 k-setup.exe")
        # 这里可以添加后续处理，例如执行该程序并传入参数
        # subprocess.run([target_exe, param])
    else:
        print("❌ 未找到 k-setup.exe")

if __name__ == "__main__":
    main()