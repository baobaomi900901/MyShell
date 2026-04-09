# 打开 vscode 并切换到指定目录
setsh() {
    # 用途: vscode 打开sh脚本项目 
    code ~/MyShell 
    }

# 允许运行任何来源的应用
master_() { 
    # 用途: 允许运行任何来源的应用
    sudo spctl --master-disable 
    }


# 删除指定 alias 的函数
remove_sh() {
    # 用途: 删除指定 alias 或 shell 函数
    if [ $# -eq 0 ]; then
        echo "用法: remove_alias <name1> <name2>..."
        echo "删除别名或shell函数."
        return 1
    fi

    for name in "$@"; do
        # 尝试 unalias（如果是别名）
        unalias "$name" 2>/dev/null
        
        # 尝试 unset -f（如果是函数）
        unset -f "$name" 2>/dev/null

        # 检查是否仍然存在（既不是别名也不是函数）
        if ! type "$name" >/dev/null 2>&1; then
            echo "✅ '$name' 被删除（别名或函数）"
        else
            echo "❌ '$name' 既不是别名也不是函数，或者不能删除"
        fi
    done
}

# 检测方法是否存在
type_() {
    # 用途: 检测方法是否存在
    if [ $# -eq 0 ]; then
        echo "用法: type_ <name1>"
        echo "查看是否有指定名称的函数或别名."
        return 1
    fi
    type "$@"
}

# 现在的时间
now_() {
    # 用途: 显示当前时间
    # 获取当前日期时间，格式：20251117-10:10
    local current_time=$(date "+%Y%m%d-%H:%M")
    echo -e "${c_g}$current_time${c_x}"
    
    # 可选：复制到剪贴板（macOS）
    if command -v pbcopy &> /dev/null; then
        echo -n "$current_time" | pbcopy
        echo -e "${c_y}✅ 时间已复制到剪贴板${c_x}"
    fi
}

# 本机ip地址
myip_() {
    # 用途: 显示本机IP地址
    # 尝试多个常见的网络接口
    local interfaces=("en0" "en1" "en2" "eth0")
    local ip_address=""
  
    for interface in "${interfaces[@]}"; do
        ip_address=$(ifconfig $interface 2>/dev/null | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')
        if [ -n "$ip_address" ]; then
        break
        fi
    done
  
    # 如果还是没找到，尝试其他方法
    if [ -z "$ip_address" ]; then
        ip_address=$(ipconfig getifaddr en0 2>/dev/null)
    fi
    
    if [ -z "$ip_address" ]; then
        echo "无法获取IP地址"
        return 1
    fi
  
    # 复制到剪贴板（不带换行符）
    printf "%s" "$ip_address" | pbcopy
    
    echo "✅ IP地址已复制到剪贴板: $ip_address"
}

# 创建文件或文件夹的便捷函数
new_() {
    # 用途: 创建文件或文件夹
    local force_overwrite=false
    local name

    # 解析 -f 选项
    if [ "$1" = "-f" ]; then
        force_overwrite=true
        shift
    fi

    # 检查是否提供了名称
    if [ -z "$1" ]; then
        echo -e "${c_y}用法: new_ [-f] < 名称 / 路径 / .* >${c_x}"
        echo -e "${c_y}  -f: 强制创建，覆盖已存在的文件${c_x}"
        return 1
    fi

    name="$1"

    # 处理已存在的情况
    if [ -e "$name" ]; then
        if [ "$force_overwrite" = false ]; then
            if [ -f "$name" ]; then
                echo -e "${c_m}📄 文件已存在: $name${c_x}"
                echo -e "${c_y}使用 'new_ -f $name' 可以强制覆盖${c_x}"
            elif [ -d "$name" ]; then
                echo -e "${c_m}📁 文件夹已存在: $name${c_x}"
            else
                echo -e "${c_m}⚠️  路径已存在: $name${c_x}"
            fi
            return 1
        else
            # 强制模式下，如果是文件则删除后重新创建
            if [ -f "$name" ]; then
                rm "$name"
                echo -e "${c_y}⚠️  已删除现有文件: $name${c_x}"
            fi
            # 如果是目录，保持原样（不删除目录）
        fi
    fi

    # 确保父目录存在
    local dir_path=$(dirname "$name")
    if [ ! -d "$dir_path" ] && [ "$dir_path" != "." ]; then
        mkdir -p "$dir_path"
    fi

    # 判断是创建文件还是文件夹
    local base_name=$(basename "$name")
    if [[ "$base_name" == *.* ]]; then
        # 名称中包含点（例如 file.txt 或 .hidden），创建文件
        touch "$name"
        echo -e "${c_g}📄 已创建文件: $name${c_x}"
    else
        # 名称中没有点，创建文件夹
        mkdir -p "$name"
        echo -e "${c_g}📁 已创建文件夹: $name${c_x}"
    fi
}

cl() {
    # 用途: 清空终端信息
    clear
}

py() {
    # 用途: 执行 python3
    python3 "$@"
}



# 公共函数

# 路径解析函数
# 用法：resolve_path <路径> [基准目录]
# 基准目录默认为当前工作目录，用于解析相对路径（./ 或 ../ 开头）
resolve_path() {
    local path="$1"
    local base_dir="${2:-$PWD}"
    local resolved

    # 处理 @MYSHELL 前缀
    if [[ "$path" == "@MYSHELL"* ]]; then
        local myshell="${MYSHELL:-$base_dir/..}"
        resolved="${myshell}/${path#@MYSHELL}"
        resolved="${resolved:a}"
        echo "$resolved"
        return 0
    fi

    # 处理相对路径（以 ./ 或 ../ 开头）
    if [[ "$path" == "./"* ]] || [[ "$path" == "../"* ]]; then
        resolved="${base_dir}/${path}"
        resolved="${resolved:a}"
        echo "$resolved"
        return 0
    fi

    # 处理 ~ 扩展
    if [[ "$path" == "~"* ]]; then
        resolved="${path:a}"
        echo "$resolved"
        return 0
    fi

    # 绝对路径或其它，转换为绝对路径
    echo "${path:a}"
    return 0
}