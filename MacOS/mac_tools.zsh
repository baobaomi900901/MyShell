tool_() {
    case "$1" in
    clean-image)
        # 获取当前工作目录
        local current_dir="$PWD"
        # echo -e "命令执行路径: ${c_g}$current_dir${c_x}"

        # 获取脚本绝对路径（完全兼容zsh的方案）
        local script_file="${functions_source[$0]:-${(%):-%x}}"
        if [[ "$script_file" == */* ]]; then
            script_file="$(cd "${script_file%/*}" && pwd)/${script_file##*/}"
        else
            script_file="$(pwd)/$script_file"
        fi
        local script_path="${script_file%/*}"
        # echo -e "脚本所在路径: ${c_g}$script_path${c_x}"

        # 定位清理脚本
        local tools_js_path="$script_path/../_tools/cleanUnusedImages.js"
        tools_js_path="$(cd "${tools_js_path%/*}" && pwd)/${tools_js_path##*/}"
        if [[ ! -f "$tools_js_path" ]]; then
            echo -e "${c_r}错误: 清理脚本不存在于 $tools_js_path${c_x}"
            return 1
        fi
        # echo -e "找到清理脚本: ${c_g}$tools_js_path${c_x}"

        # 检查Node.js环境
        if ! command -v node &> /dev/null; then
            echo -e "${c_r}错误: Node.js未安装${c_x}"
            echo -e "请通过以下方式安装:"
            echo -e "  • 官方下载: https://nodejs.org/"
            echo -e "  • 使用Homebrew: ${c_y}brew install node${c_x}"
            return 1
        fi

        # 检查Node.js版本
        local node_version=$(node -v)
        echo -e "检测到Node.js版本: ${c_g}${node_version#v}${c_x}"

        # 确定目标目录（安全方式）
        local target_dir
        if [[ -n "$2" ]]; then
            if [[ "$2" == /* ]]; then
                target_dir="$2"
            else
                target_dir="$current_dir/$2"
            fi
            
            if ! target_dir=$(cd "$target_dir" && pwd 2>/dev/null); then
                echo -e "${c_r}错误: 目标目录不存在 - $2${c_x}"
                return 1
            fi
        else
            target_dir="$current_dir"
        fi
        echo -e "执行目录: ${c_g}$target_dir${c_x}"

        # 执行清理脚本
        echo -e "${c_y}正在扫描未使用的图片...${c_x}"
        if grep -q '^import\|^export default' "$tools_js_path"; then
            # ES模块模式
            if [[ "$tools_js_path" != *.mjs ]]; then
                echo -e "${c_y}提示: 建议将脚本重命名为.mjs扩展名或添加package.json配置${c_x}"
            fi
            if ! node "$tools_js_path" "$target_dir"; then
                echo -e "${c_r}错误: 清理脚本执行失败${c_x}"
                echo -e "${c_y}解决方案:"
                echo -e "1. 将脚本重命名为 cleanUnusedImages.mjs"
                echo -e "2. 或在 _tools 目录添加 package.json 包含: {\"type\": \"module\"}${c_x}"
                return 1
            fi
        else
            # CommonJS模式
            if ! node "$tools_js_path" "$target_dir"; then
                echo -e "${c_r}错误: 清理脚本执行失败${c_x}"
                return 1
            fi
        fi

        echo -e "${c_g}✓ 清理完成${c_x}"
        ;;
    *)
        echo -e "${c_b}使用方法:${c_x}"
        echo -e "  ${c_y}tool_ clean-image [目录]${c_x}"
        echo -e "  目录参数可选，默认为当前目录"
        ;;
    esac
}