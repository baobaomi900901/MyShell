# gswitch 工作树导航设计

## 目标

无参 `gswitch` 菜单同时呈现普通本地分支、已检出的工作树和远端追踪分支。选择普通本地分支时切换分支；选择工作树时进入该工作树目录。

## 菜单分类

- `[本地] <branch>`：存在于当前仓库、且未被任何工作树检出的本地分支。
- `[工作树] <branch>  # <path>`：已被工作树检出的本地分支。此项替代同一分支的 `[本地]` 项，避免重复。
- `[工作树] (detached)  # <path>`：处于 detached HEAD 的工作树。
- `[远端] <remote>/<branch>`：已获取的远端追踪分支；忽略 `<remote>/HEAD`。

当前目录所属的工作树也显示为 `[工作树]`。不会在打开菜单时运行 `git fetch`。

## 选择行为

Python 菜单通过临时文件写入来源和目标，字段以制表符分隔。

- `local<TAB><branch>`：PowerShell 执行 `git switch <branch>`。
- `worktree<TAB><path>`：PowerShell 用 `Set-Location -LiteralPath <path>` 进入目标工作树。
- `remote<TAB><remote>/<branch>`：若有同名本地分支则切换它，否则执行 `git switch --track <remote>/<branch>`。

工作树路径不存在或无法进入时显示错误并保留当前目录。带参数的 `gswitch <branch>` 与参数补全不改变。

## 数据与验证

Python 使用 `git worktree list --porcelain` 解析工作树路径、分支引用和 detached HEAD 状态；不依赖目录命名约定。

测试覆盖工作树条目替代本地条目、detached 工作树、临时文件载荷与 `Set-Location` 路由。集成测试在临时 Git 工作树中验证选择工作树后当前目录变为目标路径。
