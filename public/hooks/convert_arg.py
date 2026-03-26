# .\public\hooks\convert_arg.py
import ast

def convert_arg(value):
    """
    尝试将字符串转换为合适的 Python 类型：
    1. 如果是 "True" 或 "False"（不区分大小写），转换为 bool
    2. 尝试用 ast.literal_eval 安全解析 Python 字面量（列表、字典等）
    3. 如果能转换为整数，则返回 int
    4. 如果能转换为浮点数，则返回 float
    5. 否则返回原字符串
    """
    lower_val = value.lower()
    if lower_val == "true":
        return True
    if lower_val == "false":
        return False

    # 尝试用 ast.literal_eval 解析 Python 字面量
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        pass

    # 尝试整数
    try:
        return int(value)
    except ValueError:
        pass

    # 尝试浮点数
    try:
        return float(value)
    except ValueError:
        pass

    # 默认返回字符串
    return value