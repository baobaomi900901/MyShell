updatesh() { source ~/.zshrc }
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