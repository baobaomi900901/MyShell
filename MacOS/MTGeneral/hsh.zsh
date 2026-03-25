# 定义 hsh 函数
hsh() {
  # 用途: 查找内置方法的描述，并按文件分组显示（单函数文件不分组）
  local json_file="${MYSHELL}/config/private/function_tracker.json"

  # 检查文件是否存在
  if [[ ! -f "$json_file" ]]; then
    echo "错误：文件 $json_file 不存在" >&2
    return 1
  fi

  # 检查是否安装了 jq
  if ! command -v jq >/dev/null 2>&1; then
    echo "错误：需要 jq 命令来解析 JSON，请安装 jq" >&2
    return 1
  fi

  # 使用 jq 提取函数名、描述和文件路径（兼容新旧格式）
  local entries=("${(@f)$(jq -r '
    .function | to_entries[] |
    if .value | type == "object" then
      if .value.description != "" then
        "\(.key)\t\(.value.description)\t\(.value.file // "")"
      else empty end
    else
      if .value != "" then
        "\(.key)\t\(.value)\t"
      else empty end
    end
  ' "$json_file")}")

  if [[ ${#entries} -eq 0 ]]; then
    echo "没有找到有描述的函数。"
    return 0
  fi

  # 数据结构
  typeset -A file_funcs      # 文件 -> 该文件下的所有函数名（空格分隔）
  typeset -A func_desc       # 函数名 -> 描述
  local max_len=0

  # 解析所有条目
  local entry name desc file
  for entry in "${entries[@]}"; do
    name="${entry%%$'\t'*}"
    local rest="${entry#*$'\t'}"
    desc="${rest%%$'\t'*}"
    file="${rest#*$'\t'}"

    # 无文件信息的归为顶层组 __top__
    if [[ -z "$file" ]]; then
      file="__top__"
    fi

    # 存储描述
    func_desc[$name]="$desc"

    # 将函数名追加到对应文件的列表中
    if [[ -n "${file_funcs[$file]}" ]]; then
      file_funcs[$file]="${file_funcs[$file]} $name"
    else
      file_funcs[$file]="$name"
    fi

    # 更新最大函数名长度
    if [[ ${#name} -gt $max_len ]]; then
      max_len=${#name}
    fi
  done

  # 颜色定义
  local color_name=$'\e[32m'   # 绿色（函数名）
  local color_desc=$'\e[34m'    # 蓝色（描述）
  local color_file=$'\e[33m'    # 黄色（文件名分组）
  local reset=$'\e[0m'

  echo "内置方法:"

  # ------------------------------------------------------------------
  # 收集顶层函数（__top__ 组 + 单函数文件中的函数）
  # ------------------------------------------------------------------
  local top_names=()
  # 存储多函数文件的分组信息
  typeset -A multi_funcs

  # 处理 __top__ 组
  if [[ -n "${file_funcs[__top__]}" ]]; then
    top_names+=(${=file_funcs[__top__]})
  fi

  # 处理其他文件
  for file in ${(k)file_funcs:#__top__}; do
    local names=(${=file_funcs[$file]})
    if (( ${#names} == 1 )); then
      # 单函数文件：加入顶层列表
      top_names+=("$names[1]")
    else
      # 多函数文件：保留分组信息
      multi_funcs[$file]="${file_funcs[$file]}"
    fi
  done

  # 对顶层函数排序
  top_names=(${(on)top_names})

  # 输出顶层函数
  for name in "${top_names[@]}"; do
    printf "  %s%-*s%s  # %s%s%s\n" \
           "$color_name" $max_len "$name" "$reset" \
           "$color_desc" "${func_desc[$name]}" "$reset"
  done

  # ------------------------------------------------------------------
  # 输出多函数文件分组（按文件名排序）
  # ------------------------------------------------------------------
  local group_files=(${(on)${(k)multi_funcs}})
  for file in "${group_files[@]}"; do
    # 提取纯文件名（不含路径）
    local filename="${file##*/}"
    printf "  %s%s:%s\n" "$color_file" "$filename" "$reset"

    # 获取该文件下的函数名列表并排序
    local names=(${(on)${=multi_funcs[$file]}})
    for name in "${names[@]}"; do
      printf "    %s%-*s%s  # %s%s%s\n" \
             "$color_name" $max_len "$name" "$reset" \
             "$color_desc" "${func_desc[$name]}" "$reset"
    done
  done
}