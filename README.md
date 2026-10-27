# MyShell

个人 Shell 脚本工具集，用于在 **macOS（Zsh）** 和 **Windows（PowerShell）** 中管理常用命令、目录快捷跳转、VS Code 项目入口和开发工具。

项目采用「平台 Shell 函数 + 公共 Python 脚本 + JSON 配置」的结构：Shell 负责操作当前终端，Python 负责交互菜单及共享逻辑，JSON 保存个人路径和工具配置。两端的命令并非完全一致；Linux 暂无自动初始化支持。

## 主要功能

- **命令索引**：`hsh` 按文件分组展示函数及用途，`reloadsh` 更新索引并处理脚本变更。
- **快捷入口**：`cd_` 跳转到配置目录，`code_` 用 VS Code 打开配置目标，`pw_` 将配置中的密码复制到剪贴板。
- **开发命令**：Git、pnpm、Python 等常用操作的快捷函数；Windows 另提供交互式分支切换和 UI 自动化工具。
- **工具集合**：通过 JSON 配置调用图片清理脚本；Windows 还包含 KRPA Lite 打包、授权等个人工作工具。
- **可扩展模板**：`MT_Tmpl` 提供命令分发、参数透传、交互菜单及 Tab 补全入口。

## 环境要求

| 环境 / 工具 | 用途 |
| --- | --- |
| macOS + Zsh / Windows + PowerShell | 加载对应平台的 Shell 函数；初始化脚本会配置 Windows PowerShell 和 PowerShell 7 的当前用户全宿主配置文件 |
| Python 3 | 运行初始化程序和公共脚本；建议使用 3.10 或更高版本，macOS 使用 `python3`，Windows 使用 `python` |
| pip | 安装 Python 依赖 |
| Git | 克隆仓库及使用 Git 快捷命令 |
| jq（macOS） | `hsh` 解析命令索引 |
| VS Code 的 `code` 命令（可选） | 使用 `code_` 等编辑器入口 |
| Node.js / pnpm（可选） | 执行 JavaScript 脚本及 pnpm 快捷命令 |

`init.py` 会按需安装 `questionary`，Windows 还会安装 `keyboard`。更新命令索引后，它会尝试安装当前平台及公共目录中扫描到的第三方 Python 包。个别工作工具仍需要本机应用、资源文件和个人路径配置。

## 快速开始

### 1. 获取项目

```sh
git clone https://github.com/baobaomi900901/MyShell.git
cd MyShell
```

仓库可以下载到任意目录。运行初始化程序时，若项目不在推荐目录，它会询问是否移动整个项目；直接回车或输入 `N` 会保留当前位置并继续安装。推荐目录为 macOS 的 `~/MyShell`，以及 Windows 的 `~/Documents/WindowsPowerShell/MyShell`。目标目录已存在时不会覆盖；若选择移动，请在初始化后切换到新目录。Windows 若因原终端占用旧目录而无法删除它，程序会完成新目录的配置并提示关闭原终端后手动清理旧目录。

### 2. 初始化 Shell

**macOS：**

```zsh
python3 init.py
source ~/.zshrc
hsh
```

**Windows：**

```powershell
python .\init.py
```

请使用可正常运行 `pip` 的 Python 执行初始化。`uv run init.py` 可能选用 uv 托管的 Python，依赖安装会报 `externally-managed-environment`；遇到该错误时可改用上述 `python .\init.py`。

初始化完成后，重新打开 PowerShell 终端，再执行：

```powershell
hsh
```

macOS 初始化程序会在新的 Zsh 子进程中执行 `reloadsh` 和 `hsh`，确认索引可用。随后在当前终端执行 `source ~/.zshrc`，让新函数在当前会话生效。

初始化程序会进行以下操作：

1. 校验项目文件，确认目录位置；只有明确输入 `y` 才移动项目，目标已存在时停止移动。
2. 创建 `config/private/`，为 `~/.zshrc` 或已安装 PowerShell 的 `$PROFILE.CurrentUserAllHosts` 写入带标记的加载块，并跳过 `Expired` 目录。重复运行会更新已有加载块；首次修改现有配置时保存 `.myshell.bak` 备份。
3. macOS 执行 `reloadsh`、安装扫描到的 Python 依赖并检查 `hsh`；Windows 执行 `reloadsh --no-restart`、安装依赖，然后提示重新打开终端执行 `hsh`。

macOS 需要预先安装 `jq`。初始化失败会返回非零退出码及原因；例如 Python 依赖无法安装时，可根据提示处理后重新运行 `init.py`。

### 3. 配置个人入口（可选）

`init.py` 会自动创建 `config/private/` 并生成 `function_tracker.json`。使用 `cd_`、`code_`、`pw_` 前，可在**初始化后的项目目录**中将模板复制到 `config/private/`。

**macOS：**

```zsh
cp -n config/Template/config/*.json config/private/
```

**Windows：**

```powershell
Get-ChildItem .\config\Template\config\*.json | ForEach-Object {
    $target = Join-Path .\config\private $_.Name
    if (-not (Test-Path $target)) {
        Copy-Item $_.FullName $target
    }
}
```

复制后，按下文的配置说明修改路径和密码。模板中的个人路径及示例值需要自行替换；`function_tracker.json` 会由 `reloadsh` 更新。

### 手动加载（可选）

若希望自行维护 Shell 配置，可使用下面的加载块，并将仓库路径替换为实际路径。

**macOS：在 `~/.zshrc` 中添加：**

```zsh
export MYSHELL="$HOME/MyShell"

# 脚本中的 compdef 依赖 Zsh 补全系统。
# 如果现有配置已初始化补全，可省略下面两行。
autoload -Uz compinit
compinit

setopt extended_glob
for func_file in "$MYSHELL"/MacOS/**/*.zsh(N); do
  if [[ "$func_file" == *"/Expired/"* ]]; then
    continue
  fi
  source "$func_file"
done
```

随后执行 `source ~/.zshrc`、`reloadsh` 和 `hsh`。

**Windows：在 `$PROFILE` 对应的文件中添加：**

```powershell
$env:MYSHELL = 'C:\path\to\MyShell'
$functionsDir = Join-Path $env:MYSHELL 'Windows'
if (Test-Path $functionsDir) {
    Get-ChildItem -Path $functionsDir -Recurse -Filter *.ps1 -File |
        Where-Object { $_.FullName -notmatch '\\Expired\\' } |
        ForEach-Object { . $_.FullName }
}
Import-Module PSReadLine
```

随后执行 `. $PROFILE`、`reloadsh --no-restart` 和 `hsh`。手动加载方式需要自行安装 Python 依赖，例如 `questionary`；Windows 的终端快捷键操作还需要 `keyboard`。

## 配置说明

### 配置文件位置

| 文件 | 作用 |
| --- | --- |
| `config/private/path.json` | `cd_` 的目录快捷入口 |
| `config/private/path_code.json` | `code_` 的 VS Code 入口 |
| `config/private/password.json` | `pw_` 的密码项 |
| `config/private/function_tracker.json` | `reloadsh` 生成的函数索引、文件来源和 `pip_package` 依赖列表 |
| `config/public/reloadsh_pip.json` | 依赖扫描的忽略项（`pip_ignore`）及导入名映射（`pip_aliases`） |
| 平台工具目录中的 `config.json` | 工具子命令、脚本路径和描述 |

`config/private/` 下的文件已被 `.gitignore` 忽略。`password.json` 是明文配置，`pw_` 会将内容复制到系统剪贴板；请使用自己的本地值，避免将真实密码写入受版本控制的模板或文档。

### 目录与 VS Code 入口

`path.json` 和 `path_code.json` 使用相同结构：

```json
{
  "my_project": {
    "win": "D:\\Projects\\my-project",
    "mac": "~/Projects/my-project",
    "description": "我的项目"
  }
}
```

- `win` 和 `mac` 分别对应 Windows 与 macOS；不适用的平台可设为 `null` 或省略。
- 路径支持 `~` 展开；Windows JSON 路径中的反斜杠需要写成 `\\`。
- `cd_` 的目标应为已存在的目录；`code_` 可以配置文件或目录。
- 有参数时按键名查找，`my-project` 会转换为 `my_project`；无参数时进入交互选择。

```sh
cd_ my-project
code_ my-project
```

### 密码项

```json
{
  "demo-account": {
    "password": "replace-with-your-local-value",
    "description": "示例账号"
  }
}
```

执行 `pw_ demo-account` 可直接复制对应密码；执行 `pw_` 可交互选择。密码项按原始键名匹配，不进行连字符与下划线转换。

## 常用命令

| 命令 | 功能 | 平台 |
| --- | --- | --- |
| `hsh` | 查看带用途描述的函数索引 | macOS / Windows |
| `reloadsh` | 更新函数索引；macOS 重新加载 `.zshrc`，Windows 提供终端重启交互 | macOS / Windows |
| `reloadsh --no-restart` | 更新索引并跳过终端重启交互 | Windows |
| `type_` | 查询命令或函数是否存在 | macOS / Windows |
| `now_` | 显示当前时间并复制到剪贴板 | macOS / Windows |
| `new_` / `del_` | 创建 / 删除文件或目录；macOS 强制创建用 `-f`，Windows 用 `-Force` | macOS / Windows |
| `myip_` | 查看并复制本机 IP 地址 | macOS |
| `master_` | 调用 macOS 系统命令调整应用来源限制 | macOS |
| `cd_ [配置键名]` | 跳转到配置目录 | macOS / Windows |
| `code_ [配置键名]` | 用 VS Code 打开配置目标 | macOS / Windows |
| `pw_ [配置键名]` | 复制配置密码 | macOS / Windows |
| `ga [文件...]` | `git add`；无参数时执行 `git add .` | macOS / Windows |
| `gs` / `gcmt "消息"` | 查看 Git 状态 / 提交改动 | macOS / Windows |
| `gpr` / `gpo` | `git pull --rebase` / 推送；macOS 用 `git push origin`，Windows 用 `git push` | macOS / Windows |
| `gsuk` / `gspop` | `git stash -u -k` / `git stash pop` | macOS / Windows |
| `grecmt` / `glocal` | 软重置最新提交 / 查看相对 `origin/develop` 的本地提交 | macOS / Windows |
| `greset` | 交互式 Git 重置操作 | macOS / Windows |
| `gswitch [分支]` | 无参数时选择本地或远端分支，有参数时执行 `git switch` | macOS / Windows |
| `py_star` / `py_end` | 激活当前目录的 `.venv` / 退出当前虚拟环境 | macOS / Windows |
| `op_ [路径...]` | 在 Finder、资源管理器或默认程序中打开路径；无参数时打开当前目录 | macOS / Windows |
| `pd` / `pdoc` / `pa` / `pi` | pnpm 开发、文档开发、添加依赖、安装依赖 | macOS / Windows |
| `tool_` | 工具集入口，无参数时交互选择子命令 | macOS / Windows |
| `tmpl_` | 模板命令集入口 | macOS / Windows |
| `game_` | 游戏存档备份工具 | macOS / Windows |

Windows 的 `reloadsh` 更新函数索引后可请求打开新终端。脚本会观察启动进程最多 3 秒，检查退出码和异常输出；启动失败会显示诊断并保留当前终端。打开请求发出后，还需确认新终端已正常打开才会关闭旧终端，默认保留；取消或按 Ctrl+C 也会保留。Tabby 的 `uncaughtException` 等异常即使伴随退出码 0，也按启动失败处理，普通弃用警告不会阻止后续确认。可用 `reloadsh --no-restart` 跳过这些交互，再手动打开新标签页或执行 `. $PROFILE` 重新加载配置。

完整命令列表以本机执行 `reloadsh` 后的 `hsh` 输出为准。`greset all` 会执行 `git reset --hard HEAD`，丢弃已跟踪文件的未提交改动；执行前应确认要保留的内容。

macOS 原有的 `_type`、`_now`、`_new`、`_del`、`_master`、`_myip`、`_tool` 保留为兼容别名；新文档和函数索引使用统一后的名称。

Git 简写命令由共用 Python 脚本执行，Zsh 与 PowerShell 只保留同名终端入口、补全及虚拟环境激活所需的 shell 操作。交互式 `gswitch` 会区分本地和远端分支。选择远端分支时，若已有同名本地分支则切换到它，否则创建跟踪分支。菜单使用本地已有的远端引用，需要最新列表时先执行 `git fetch`。

## 扩展脚本与工具

### 添加普通 Shell 函数

1. 在对应平台目录中新增 `.zsh` 或 `.ps1` 文件，避免放入 `Expired/`。
2. 定义函数，并在函数内添加 `# 用途: 描述` 注释，便于 `reloadsh` 提取说明。
3. 执行 `reloadsh`，再用 `hsh` 检查索引。Windows 下需重新加载配置或打开新终端，使新增函数生效。

### 使用命令集模板

复制对应平台的 `MT_Tmpl/` 目录，修改入口文件中的 `tmpl` 命名及补全绑定，避免与原模板发生冲突。入口文件分别为 `index.zsh` 和 `index.ps1`。

在 `config.json` 中定义子命令，例如：

```json
{
  "hello": {
    "script_path": "@MYSHELL/public/_script/fun1.py",
    "description": "运行示例脚本",
    "ignore_exit_code": false
  }
}
```

| 字段 | 说明 |
| --- | --- |
| 配置键名 | 子命令名称，例如 `hello` |
| `script_path` | 脚本路径；支持相对入口目录的路径和 `@MYSHELL` 前缀 |
| `description` | 菜单及补全中的说明 |
| `ignore_exit_code` | 为 `true` 时忽略脚本的非零退出码，默认不忽略 |

保留原模板名称时，可执行 `tmpl_ hello`；额外参数会传给目标脚本，无参数时显示交互菜单。Python 和 JavaScript 脚本分别通过 Python 与 Node.js 运行；Shell 脚本使用对应平台的执行方式。macOS 非可执行的 `.zsh` 示例可参考 `src/fun3.zsh`，定义与子命令同名的函数。

## 项目结构

```text
MyShell/
├── MacOS/
│   ├── MT_General/        # 通用命令、Git、pnpm、补全及配置入口
│   ├── MT_dev/            # Python、agent 等开发入口
│   ├── MT_Tmpl/           # Zsh 命令集模板
│   ├── MT_Tool/           # macOS 工具集
│   └── Expired/           # 历史脚本，加载时跳过
├── Windows/
│   ├── MT_General/        # 通用命令、Git 及配置入口
│   ├── MT_Dev/            # Python、pnpm、agent 和 UI 自动化
│   ├── MT_Tmpl/           # PowerShell 命令集模板
│   ├── MT_Tool/           # 打包、授权等工作工具
│   ├── temp/             # 临时脚本及历史记录
│   └── Expired/           # 历史脚本，加载时跳过
├── public/
│   ├── _script/           # 公共 Python 逻辑、脚本示例及测试
│   ├── hooks/             # 参数转换辅助模块
│   ├── typeOf/            # 参数类型转换辅助模块
│   ├── lite_setup/        # Windows 打包相关资源
│   └── package.json       # 声明 JavaScript 使用 ES Module
├── config/
│   ├── Template/config/   # 本地配置模板
│   ├── private/           # 本地配置，需自行创建，不纳入版本控制
│   └── public/            # 公共配置
├── docs/superpowers/      # 部分功能的设计与实施记录
├── assets/                # 文档图片资源
├── init.py                # 跨平台初始化入口
└── README.md
```

## 常见问题

| 问题 | 排查方式 |
| --- | --- |
| 提示 `MYSHELL` 未设置 | macOS 用 `echo "$MYSHELL"`，Windows 用 `$env:MYSHELL` 检查；重新加载配置或重开终端 |
| `hsh` 找不到索引 | 执行 `reloadsh`；初始化程序会自动创建 `config/private/` |
| macOS 提示缺少 `jq` | 安装 `jq`，再执行 `hsh` |
| macOS 提示找不到 `compdef` | 在加载脚本前初始化补全系统：`autoload -Uz compinit`，然后执行 `compinit` |
| 路径菜单为空或目标不存在 | 检查当前平台的 `win` / `mac` 字段，并将模板路径改为本机实际路径 |
| `code_` 找不到 `code` | 将 VS Code 的命令行入口加入 `PATH` |
| Python 依赖安装失败 | 使用实际运行脚本的解释器执行 `python3 -m pip install 包名` 或 `python -m pip install 包名`；虚拟环境需在使用命令时保持激活 |
| Windows 无法加载 `.ps1` | 检查 PowerShell 报错、当前 `$PROFILE` 和执行策略；受组织策略管理时按所在环境要求处理 |

## 开发验证

公共 Python 辅助逻辑的现有单元测试可在仓库根目录执行：

```sh
python3 -m unittest discover -s public/_script -p 'test_*.py'
```

Windows 下将 `python3` 替换为 `python`。这些测试覆盖部分交互菜单、分支列表与终端辅助逻辑；平台集成和依赖本机应用的工作工具仍需在对应环境中验证。
