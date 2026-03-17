# .\Windows\win_pnpm.ps1
# pnpm 的快捷指令

function pd { 
  # 用途: 执行 "pnpm run dev"
  pnpm run dev 
}
function pdoc { 
  # 用途: 执行 "pnpm run docs:dev"
  pnpm run docs:dev 
}
function pa { 
  # 用途: 执行 "pnpm add"
  pnpm add 
}
function pi { 
  # 用途: 执行 "pnpm install"
  pnpm install 
}