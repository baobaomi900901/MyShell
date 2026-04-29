#pnpm

p() {
    # 用途: 执行 pnpm
    pnpm "$@"
}

pd() {
    # 用途: 执行 pnpm run dev
    pnpm run dev
}

pdoc() {
    # 用途: 执行 pnpm run docs:dev
    pnpm run docs:dev
}

pa() {
    # 用途: 执行 pnpm add
    pnpm add "$@"
}

pi() {
    # 用途: 执行 pnpm install
    pnpm install "$@"
}

pb() {
    # 用途: 执行 pnpm build
    pnpm build
}