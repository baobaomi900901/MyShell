// .\Windows\Hooks\src\fun2.js
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import readline from 'readline';
import convertArg from '../../../public/hooks/convertArg.js'; // 相对路径导入

// 获取命令行参数（前两个是 node 路径和脚本路径，跳过）
const args = process.argv.slice(2);

console.error('fun2');
console.log('接收到的参数（自动转换类型后）:');
args.forEach((arg, index) => {
  const converted = convertArg(arg);
  console.log(`参数${index + 1}:`, converted, `(类型: ${typeof converted})`);
  // 如果是对象或数组，额外打印其实际类型
  if (converted && typeof converted === 'object') {
    console.log(`      具体类型: ${Array.isArray(converted) ? 'array' : 'object'}`);
  }
});
