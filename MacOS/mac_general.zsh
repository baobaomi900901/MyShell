reloadsh() { source ~/.zshrc }
setsh() { code ~/MyShell }
upapp() { sudo spctl --master-disable }


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

hsh() {
    echo -e "${c_b}内置地方法:${c_x}"
    echo -e "${c_y}  setsh         # vscode 打开 自定义shell ( MyShell ) 配置文件${c_x}"
    echo -e "${c_y}  remove_sh     # 删除别名或函数${c_x}"
    echo -e "${c_y}  type          # 查看 cd_ 方法是否存在${c_x}"
    echo -e "${c_y}  cd_           # 切换到指定目录${c_x}"
    echo -e "${c_y}  code_         # 打开 vscode 并切换到指定目录${c_x}"
    echo -e "${c_b}git相关操作:${c_x}"
    echo -e "${c_y}  gs            # git status${c_x}"
    echo -e "${c_y}  gcmt          # git commit -m${c_x}"
    echo -e "${c_y}  ga            # git add${c_x}"
    echo -e "${c_y}  gpr           # git pull${c_x}"
    echo -e "${c_y}  gpo           # git push${c_x}"
    echo -e "${c_y}  greset        # git reset --hard${c_x}"
}