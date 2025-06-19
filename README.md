## 说明

这是 私人的 shell 脚本仓库，里面包含了一些常用的 shell 脚本。
分为 mac 和 windows 两个目录，分别存放 mac 和 windows 下的脚本。

## 如何使用

### mac

1. 克隆仓库到 home 目录:
   - 在终端中执行 'cd ~'
2. 在 .zshrc 中添加以下内容
   ```shell
   for func_file in ~/MyShell/mac/*.zsh; do
      source "$func_file"
   done
   ```
