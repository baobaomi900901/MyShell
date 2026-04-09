// MTHooks/src/fun2.js
function bbm(...params) {
  console.log(params);
  return 123; // 此值将作为退出码
}

// 获取命令行参数（跳过前两个：node 路径和脚本路径）
const args = process.argv.slice(2);

// 执行函数并获取退出码
const exitCode = bbm(...args);

// 将退出码传递给 Node.js 进程
process.exit(exitCode);
