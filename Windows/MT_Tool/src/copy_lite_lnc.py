import os
import subprocess

def create_license_link():
    target = r"C:\K-RPALite\K-RPA Lite.lnc"
    link = os.path.join(os.getcwd(), "K-RPA Lite.lnc")
    
    if not os.path.exists(target):
        print(f"❌ 授权文件不存在：{target}")
        return
    
    if os.path.exists(link):
        os.remove(link)
        print(f"已删除旧的同名文件")
    
    cmd = f'mklink "{link}" "{target}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
    
    if result.returncode == 0:
        print(f"✅ 链接创建成功：{link}")
    else:
        print(f"❌ 创建失败：{result.stderr}")

if __name__ == "__main__":
    create_license_link()