# ========== code_ 函数 ==========
# 功能：根据配置文件快速在 VS Code 中打开项目
# 依赖：$MYSHELL 环境变量指向 MyShell 根目录
#       Python3 脚本位于 $MYSHELL/public/_script/vscode_open.py
#       配置文件位于 $MYSHELL/config/private/path_code.json

code_() {
    # 用途: vscode 打开指定文件
    local name="$1"
    local script="${MYSHELL}/public/_script/vscode_open.py"
    local output exit_code

    # 检查 Python 脚本是否存在
    if [[ ! -f "$script" ]]; then
        print -P "%F{red}❌ Python 脚本不存在: $script%f"
        return 1
    fi

    # 调用 Python3 脚本，捕获输出和退出码
    output=$(python3 "$script" "$name" 2>&1)
    exit_code=$?

    # 根据退出码处理
    if [[ $exit_code -eq 0 ]]; then
        # 成功：如果输出以 "code " 开头则执行，否则直接显示
        if [[ "$output" =~ ^code\  ]]; then
            eval "$output"
        else
            print "$output"
        fi
    else
        # 失败：红色显示错误信息
        print -P "%F{red}${output}%f"
    fi
    print ""  # 空行分隔
}

# ========== 补全配置 ==========
# 补全函数：读取 path_code.json，生成“名称:描述”列表
_code_completion() {
    local json_file="${MYSHELL}/config/private/path_code.json"
    local -a suggestions

    # 如果 JSON 文件不存在，直接返回
    [[ -f "$json_file" ]] || return 1

    # 使用 Python3 解析 JSON，输出每行 "名称:描述"
    suggestions=(${(f)"$(python3 -c "
import sys, json
try:
    with open('$json_file', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
except:
    sys.exit(1)
for key, val in data.items():
    if val.get('win') or val.get('mac'):   # 至少在一个系统上有路径
        name = key.replace('_', '-')
        desc = val.get('description', '').replace('\n', ' ')
        print(f'{name}:{desc}')
")"})

    # 将列表提供给 _describe 进行补全（自动过滤已输入部分）
    _describe -t 'code projects' 'VS Code project' suggestions
}

# 注册补全函数到命令 code_
compdef _code_completion code_
