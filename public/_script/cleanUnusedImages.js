/*
 *  项目名称: cleanUnusedImages
 *  用途: 过滤 .md中 未使用的图片资源
 *  作者: RengarTang
 *  创建时间: 2020/6/8 10:00
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import readline from 'readline';

// 获取当前目录
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 配置选项
const config = {
  scanExtensions: ['.md', '.html', '.htm'], // 扫描的文件扩展名
  imageExtensions: ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'], // 图片扩展名
  excludeDirs: ['node_modules', '.git', 'dist', 'build'], // 排除的目录
  verbose: true // 详细日志
};

// 创建readline接口
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// 主函数
async function main() {
  try {
    logHeader();

    // 获取命令行参数
    const targetPath = process.argv[2] || __dirname;
    console.log(`📁 扫描目录: ${path.resolve(targetPath)}`);

    const { allFiles, allImages } = await scanProject(targetPath);
    const usedImages = await findUsedImages(allFiles);
    const unusedImages = findUnusedImages(allImages, usedImages);

    if (unusedImages.length === 0) {
      console.log('🎉 没有发现未使用的图片资源!');
      process.exit(0);
    }

    await reportResults(unusedImages, targetPath);

    const shouldDelete = await askConfirmation(`确定要删除 ${unusedImages.length} 个未使用的图片文件吗? (y/n)`);
    if (shouldDelete) {
      await deleteUnusedImages(unusedImages, targetPath);
    }
  } catch (error) {
    console.error('❌ 发生错误:', error.message);
    process.exit(1);
  } finally {
    rl.close();
  }
}

// 扫描项目获取所有文件和图片
async function scanProject(rootDir) {
  console.log('🔍 扫描项目文件中...');

  const allFiles = [];
  const allImages = [];

  async function scanDir(dir) {
    const entries = await fs.readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        if (!config.excludeDirs.includes(entry.name)) {
          await scanDir(fullPath);
        }
      } else {
        const ext = path.extname(entry.name).toLowerCase();

        if (config.scanExtensions.includes(ext)) {
          allFiles.push(fullPath);
        } else if (config.imageExtensions.includes(ext)) {
          allImages.push(fullPath);
        }
      }
    }
  }

  await scanDir(rootDir);

  if (config.verbose) {
    console.log(`📂 找到 ${allFiles.length} 个可扫描文件`);
    console.log(`🖼️  找到 ${allImages.length} 个图片文件`);
  }

  return { allFiles, allImages };
}

// 查找被引用的图片
async function findUsedImages(filePaths) {
  console.log('🔎 查找被引用的图片...');
  const usedImages = new Set();

  for (const filePath of filePaths) {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const imageRefs = findImageReferences(content);

      for (const ref of imageRefs) {
        // 解析相对路径为绝对路径
        const resolvedPath = path.normalize(path.join(path.dirname(filePath), ref));
        usedImages.add(resolvedPath);
      }
    } catch (error) {
      console.warn(`⚠️ 无法读取文件 ${filePath}: ${error.message}`);
    }
  }

  if (config.verbose) {
    console.log(`🔗 找到 ${usedImages.size} 个被引用的图片`);
  }

  return usedImages;
}

// 查找图片引用(支持Markdown和HTML)
function findImageReferences(content) {
  const patterns = [
    /!\[.*?\]\((.*?)\)/g, // Markdown图片
    /<img[^>]+src=["'](.*?)["']/g, // HTML img标签
    /background(?:-image)?\s*:\s*url\(["']?(.*?)["']?\)/g // CSS背景图片
  ];

  const matches = [];

  patterns.forEach((pattern) => {
    let match;
    while ((match = pattern.exec(content)) !== null) {
      // 移除查询参数和哈希
      const cleanPath = match[1].split(/[?#]/)[0];
      if (cleanPath && !cleanPath.startsWith('http')) {
        matches.push(cleanPath);
      }
    }
  });

  return matches;
}

// 找出未使用的图片
function findUnusedImages(allImages, usedImages) {
  return allImages.filter((img) => {
    // 规范化路径比较
    const normalizedImg = path.normalize(img);
    return !Array.from(usedImages).some((used) => path.normalize(used) === normalizedImg);
  });
}

// 报告结果
async function reportResults(unusedImages, basePath) {
  console.log(`\n❌ 发现 ${unusedImages.length} 个未使用的图片文件:`);

  if (config.verbose) {
    unusedImages.forEach((img, index) => {
      const relativePath = path.relative(basePath, img);
      console.log(`  ${index + 1}. ${relativePath}`);
    });
  }

  const totalSize = await calculateTotalSize(unusedImages);
  console.log(`\n📊 总大小: ${formatFileSize(totalSize)}`);
}

// 计算文件总大小
async function calculateTotalSize(filePaths) {
  let total = 0;

  for (const filePath of filePaths) {
    try {
      const stats = await fs.stat(filePath);
      total += stats.size;
    } catch (error) {
      console.warn(`⚠️ 无法获取文件大小 ${filePath}: ${error.message}`);
    }
  }

  return total;
}

// 删除未使用的图片
async function deleteUnusedImages(unusedImages, basePath) {
  console.log('\n🗑️ 开始删除未使用的图片...');
  let successCount = 0;
  let failCount = 0;

  for (const img of unusedImages) {
    try {
      await fs.unlink(img);
      if (config.verbose) {
        const relativePath = path.relative(basePath, img);
        console.log(`  ✅ 已删除: ${relativePath}`);
      }
      successCount++;
    } catch (error) {
      console.warn(`  ❌ 删除失败 ${img}: ${error.message}`);
      failCount++;
    }
  }

  console.log(`\n删除完成: ${successCount} 成功, ${failCount} 失败`);
}

// 辅助函数: 询问确认
function askConfirmation(question) {
  return new Promise((resolve) => {
    rl.question(question + ' ', (answer) => {
      resolve(answer.toLowerCase() === 'y');
    });
  });
}

// 辅助函数: 格式化文件大小
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]);
}

// 辅助函数: 打印头部信息
function logHeader() {
  console.log('\n🖼️ 图片资源清理工具');
  console.log('----------------------------');
  console.log(`扫描扩展名: ${config.scanExtensions.join(', ')}`);
  console.log(`图片扩展名: ${config.imageExtensions.join(', ')}`);
  console.log(`排除目录: ${config.excludeDirs.join(', ')}`);
  console.log('----------------------------\n');
}

// 启动主函数
main();
