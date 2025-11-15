code_() {
    case "$1" in
    lang-cn)
        code ~/Documents/金智维/Code/aom/KingAutomate/Res/chinese.json
        echo "打开 CN 语言包"
        ;;
    lang-en)
        code ~/Documents/金智维/Code/aom/KingAutomate/Res/english.json
        echo "打开 EN 语言包"
        ;;
    Error-message)
        code ~/Documents/金智维/Code/aom/VueCodeBase/vue-king-automate/public/js/errorPatterns.js
        echo "打开 错误信息"
        ;;
    Alias)
        code ~/Documents/金智维/Code/aom/KingAutomate/Res/FunctionSetting.json
        echo "打开 函数别名与设置"
        ;;
    *)
        echo -e "${c_b}使用方法:${c_x}"
        echo -e "${c_y}  code_ lang-cn       # 打开 CN 语言包${c_x}"
        echo -e "${c_y}  code_ lang-en       # 打开 EN 语言包${c_x}"
        echo -e "${c_y}  code_ Error-message # 打开 错误信息${c_x}"
        echo -e "${c_y}  code_ Alias         # 打开 函数别名与设置${c_x}"
        ;;
    esac
}

# 定义 cd_ 的补全函数
_code_completion() {
    local -a options=(
        'lang-cn:打开 CN 语言包'
        'lang-en:打开 EN 语言包'
        'Error-message:打开 错误信息'
        'Alias:打开 函数别名与设置'
    )
    _describe 'code_ options' options
}
# 将补全函数关联到 cd_ 命令
compdef _code_completion code_