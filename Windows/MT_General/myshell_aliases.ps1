# 与 macOS 侧命名对齐：下划线前缀别名，转发到 cd_/pw_/code_/game_/tmpl_
# 需在对应主函数定义之后加载（通常由 reloadsh / profile 顺序保证）。

function _cd { cd_ @args }
function _pw { pw_ @args }
function _code { code_ @args }
function _game { game_ @args }
# _tmpl 在 Windows/MT_Tmpl/index.ps1 末尾定义（须晚于 tmpl_ 加载）
