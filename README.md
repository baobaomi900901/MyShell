## 说明

这是 私人的 shell 脚本仓库，里面包含了一些常用的 shell 脚本。
分为 mac 和 windows 两个目录，分别存放 mac 和 windows 下的脚本。

## 如何使用

### mac

1. 克隆仓库到 home 目录:
   - 在终端中执行 'cd ~'
2. 在 .zshrc 中添加以下内容
   ```shell
   for func_file in ~/MyShell/MacOS/**/*.zsh(N); do
   # 如果路径中包含 /Expired/ 则跳过
   if [[ "$func_file" == *"/Expired/"* ]]; then
      continue
   fi
   source "$func_file"
   done
   ```
3. 在终端中运行, 使配置生效 ( 此命令用于 reload 脚本)
   ```shell
   source ~/.zshrc
   ```
4. 终端运行, 查看相关指令
   ```shell
   hsh
   ```

### windows

1.  找到这个目录 C:\Users\Admin\Documents\WindowsPowerShell
2.  把 MyShell 放在这里目录下
    ![alt text](assets/README/image.png)

3.  在 Microsoft.PowerShell_profile.ps1 中添加以下内容

```shell
   # C:\Users\{用户名}\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1

   $functionsDir = "$HOME\Documents\WindowsPowerShell\MyShell\windows"
   if (Test-Path $functionsDir) {
      Get-ChildItem -Path $functionsDir -Recurse -Filter *.ps1 -File |
         Where-Object { $_.FullName -notmatch '\\Expired\\' } |
         ForEach-Object {
               . $_.FullName
         }
   }
```

4.  终端运行命令, 使配置生效 ( 此命令用于 reload 脚本)

```shell
. $PROFILE
```

5.  终端运行, 查看相关指令

```shell
hsh
```

### 关于 tmpl

MTTmpl 这是一个模板文件夹(有 mac 和 windows 两种), 内置一个入口文件 index.zhs/index.ps1,
一个配置文件 config.json.

使用时请复制整个文件夹, 在 index.zhs/ index.ps1 中, 找到所有 tmpl, 修改成你想要执行的方法名称就可以使用.

![alt text](assets/README/image-1.png)

![alt text](assets/README/image-2.png)

## 文件结构说明

```
MyShell
├── assets                        # markdown 图片资源
├── config                        # 配置文件
│   ├── private                   # 私有配置, 影响cd_ code_ pw_, 格式参考 Template
│   └── public                     # 公共配置, 影响所有脚本
├── Templates                     # private 配置模板
├── MacOS                         # mac 脚本
├── public                        # 公共脚本
│   ├── _script                   # 公共脚本
│   ├── lite_setup                # 公司打包工具
│   └── hooks                     # hooks
├── temp                          # 临时缓存文件
├── Windows                       # windows 脚本
├── .gitignore                    # git 忽略文件
├── init.py                       # 初始化工具
└── README.md                     # 说明文档
```
