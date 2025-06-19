#pnpm
pd() {
    pnpm run dev
}

pdoc() {
    pnpm run docs:dev
}

pa() {
    pnpm add "$@"
}

pi() {
    pnpm install "$@"
}