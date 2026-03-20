import sys
from pathlib import Path

current_file = Path(__file__).resolve()

# 自动向上找到包含 public 的根目录
project_root = current_file
while project_root != project_root.parent:
    if (project_root / "public").exists():
        break
    project_root = project_root.parent
else:
    print("❌ 未找到 public 目录")
    sys.exit(1)

tools_dir = project_root / "public"
typeOf_dir = tools_dir / "typeOf"

# 将 typeOf 目录加入 sys.path
if str(typeOf_dir) not in sys.path:
    sys.path.insert(0, str(typeOf_dir))

try:
    from convert_arg import convert_arg
except ImportError as e:
    print(f"❌ 无法导入 convert_arg 模块: {e}")
    sys.exit(1)

def main():
    print("fun1 !")
    print("接收到的参数（自动转换类型后）:")
    for i, arg in enumerate(sys.argv[1:], start=1):
        converted = convert_arg(arg)
        print(f"参数{i}: {converted} (类型: {type(converted).__name__})")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())