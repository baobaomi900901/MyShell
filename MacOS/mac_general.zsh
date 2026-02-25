# ~/Users/mobytang/MyShell/MacOS/mac_general.zsh
hsh() {
    echo -e "${c_b}内置地方法:${c_x}"
    echo -e "${c_y}  setsh         # vscode 打开 自定义shell ( MyShell ) 配置文件${c_x}"
    echo -e "${c_y}  reloadsh      # 重载自定义shell配置文件${c_x}"
    echo -e "${c_grey}  remove_sh     # 🚫 [已弃用] 删除别名或函数, 请使用 reloadsh${c_x}"
    echo -e "${c_y}  type_         # 查看 cd_ 方法是否存在${c_x}"
    echo -e "${c_b}  master_         # 允许允许运行任何来源的应用${c_x}"
    echo -e "${c_y}  cd_           # 切换到指定目录${c_x}"
    echo -e "${c_y}  code_         # 打开 vscode 并切换到指定目录${c_x}"
    echo -e "${c_y}  myip_         # 获取本机IP地址${c_x}"
    echo -e "${c_y}  new_          # 创建文件夹或文件 "
    echo -e "${c_b}git相关操作:${c_x}"
    echo -e "${c_y}  gs            # git status${c_x}"
    echo -e "${c_y}  gcmt          # git commit -m${c_x}"
    echo -e "${c_y}  ga            # git add${c_x}"
    echo -e "${c_y}  gpr           # git pull${c_x}"
    echo -e "${c_y}  gpo           # git push${c_x}"
    echo -e "${c_y}  greset        # git reset --hard${c_x}"
}

# 重载自定义shell配置文件
reloadsh() {
    echo "reloadsh"

    # 定义一些变量:
    # 缓存存储的文件地址, 需要读取 json 文件 中的 functionName 数组内容
    local json_file="/Users/mobytang/MyShell/MacOS/function_tracker.json"
    # 老的函数名称
    local old_func_names=()
    # 新的函数名称
    local new_func_names=()
    # 本次增加的方法名称
    local new_add_func_names=()
    # 本次删除的方法名称
    local new_del_func_names=()

    # 步骤一, 读取 json_file 中的 functionName 数组内容, 并存储到 old_func_names 数组中
    if [[ -f "$json_file" ]]; then
        echo "📖 方法统计来源于: $json_file"
        while IFS= read -r func_name; do
            if [[ -n "$func_name" ]]; then
                old_func_names+=("$func_name")
            fi
        done < <(jq -r '.functionName[]?' "$json_file" 2>/dev/null)
        echo "📋 旧的方法数量: ${#old_func_names[@]}"
    else
        echo "📝 No existing function tracker found"
    fi

    # 步骤二, 循环获取 ~/MyShell/MacOS/*.zsh 文件中的方法名称, 并存储到 new_func_names 数组中
    echo "📁 方法来源于: ~/MyShell/MacOS/*.zsh:"
    local func_count=0
    
    for func_file in ~/MyShell/MacOS/*.zsh; do
        if [[ -f "$func_file" ]]; then
            # echo "🔍 Scanning: $(basename "$func_file")"
            
            while IFS= read -r func_name; do
                if [[ ! "$func_name" =~ ^_ ]] && [[ -n "$func_name" ]]; then
                    # echo "   ✅ Function: $func_name"
                    new_func_names+=("$func_name")
                    ((func_count++))
                fi
            done < <(grep -E '^[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\(\)' "$func_file" | sed -E 's/^[[:space:]]*([a-zA-Z_][a-zA-Z0-9_]*)[[:space:]]*\(\).*/\1/')
        fi
    done
    
    echo "📊 新方法数量: $func_count"

    # 步骤三, 对比 old_func_names 数组和 new_func_names 数组, 计算出本次增加和删除的方法名称
    echo "🔍 对比方法清单变更..."
    
    # 查找新增的函数
    for func in "${new_func_names[@]}"; do
        if [[ ! " ${old_func_names[@]} " =~ " ${func} " ]]; then
            new_add_func_names+=("$func")
        fi
    done
    
    # 查找删除的函数
    for func in "${old_func_names[@]}"; do
        if [[ ! " ${new_func_names[@]} " =~ " ${func} " ]]; then
            new_del_func_names+=("$func")
        fi
    done

    # 步骤四, 打印出本次增加和删除的方法名称
    if [[ ${#new_add_func_names[@]} -gt 0 ]]; then
        echo "🆕 Newly added functions (${#new_add_func_names[@]}):"
        printf "   ✅ %s\n" "${new_add_func_names[@]}"
    else
        echo "✅ 没有添加方法"
    fi
    
    if [[ ${#new_del_func_names[@]} -gt 0 ]]; then
        echo "🗑️  Deleted functions (${#new_del_func_names[@]}):"
        printf "   ❌ %s\n" "${new_del_func_names[@]}"
    else
        echo "✅ 没有删除方法"
    fi

    # 步骤五, 遍历 new_del_func_names 中的方法名称, 并执行 unalias 和 unset -f 命令删除方法
    if [[ ${#new_del_func_names[@]} -gt 0 ]]; then
        echo "🧹 Cleaning up deleted functions..."
        for func in "${new_del_func_names[@]}"; do
            echo "   🧹 Removing: $func"
            # 删除别名
            unalias "$func" 2>/dev/null || true
            # 删除函数
            unset -f "$func" 2>/dev/null || true
        done
        echo "✅ Cleanup completed"
    fi

    # 更新 JSON 文件
    echo "💾 更新清单 JSON 文件..."
    jq -n --argjson names "$(printf '%s\n' "${new_func_names[@]}" | jq -R . | jq -s .)" '{
        functionName: $names
    }' > "$json_file"
    
    if [[ $? -eq 0 ]]; then
        echo "✅ 更新清单成功"
    else
        echo "❌ 更新清单失败"
    fi

    # 重新加载配置
    echo "🔄 重新加载配置..."
    source ~/.zshrc
    echo "✅ 重新加载完成!"
}

# 打开 vscode 并切换到指定目录
setsh() { 
    code ~/MyShell 
    }

# 允许运行任何来源的应用
master_() { 
    sudo spctl --master-disable 
    }


# 删除指定 alias 的函数
remove_sh() {
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
    if [ $# -eq 0 ]; then
        echo "用法: type_ <name1>"
        echo "查看是否有指定名称的函数或别名."
        return 1
    fi
    type "$@"
}

# 现在的时间
now_() {
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