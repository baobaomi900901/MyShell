# .\Windows\win_pnpm.ps1
# pnpm 的快捷指令

function pd { pnpm run dev }
function pdoc { pnpm run docs:dev }
function pa { pnpm add }
function pi { pnpm install }
function open { explorer $args }