cd_() {
    if [ "$1" = "MyShell" ]; then
        cd /Users/mobytang/MyShell
    elif [ "$1" = "sb8" ]; then
        cd /Users/mobytang/Documents/金智维/Code/storybook8
    elif [ "$1" = "kswux" ]; then
        cd /Users/mobytang/Documents/金智维/Code/storybook8/kswux
    elif [ "$1" = "kswux-docs" ]; then
        cd /Users/mobytang/Documents/金智维/Code/storybook8/kswux/docs
    elif [ "$1" = "lite-docs" ]; then
        cd /Users/mobytang/Documents/金智维/Code/k-mate-docs
    else    
        echo "用法:"
        echo "  cd_ MyShell     # cd 到 MyShell 目录"
        echo "  cd_ sb8         # cd 到 Storybook8 目录"
        echo "  cd_ kswux       # cd 到 KSWUX 目录"
        echo "  cd_ kswux-docs  # cd 到 KSWUX 文档目录"
        echo "  cd_ lite-docs   # cd 到 lite-docs 目录"
    fi
}

# 定义 cd_ 的补全函数
_cd_completion() {
    local -a options=(
        "MyShell:cd to MyShell"
        "sb8:cd to Storybook8"
        "kswux:cd to KSWUX"
        "kswux-docs:cd to KSWUX docs"
        "lite-docs:cd to lite-docs"
    )
    _describe 'cd_ options' options
}
# 将补全函数关联到 cd_ 命令
compdef _cd_completion cd_