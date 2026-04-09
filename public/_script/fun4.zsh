#!/usr/bin/env zsh
# fun3.zsh - 示例 zsh 脚本
# public/_script/fun4.zsh

fun4() {
  # 打印接收到的参数
  echo "参数: $@"
  echo "参数: $@[1]"
  echo "参数: $@[2]"
  echo "参数: $@[3]"

  # 返回退出码 123
  return 123
}
