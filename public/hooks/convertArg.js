// .\public\hooks\convertArg.js
/**
 * 尝试将字符串转换为合适的 JavaScript 类型（保留 "true"/"false" 为字符串）
 * @param {string} value - 原始字符串参数
 * @returns {any} 转换后的值
 */
function convertArg(value) {
  // 不再自动将 "true"/"false" 转换为布尔值，保持为字符串

  // 尝试转换为数字（整数或浮点数）
  if (/^-?\d+$/.test(value)) {
    return parseInt(value, 10);
  }
  if (/^-?\d*\.\d+$/.test(value)) {
    return parseFloat(value);
  }

  // 尝试解析 JSON（支持双引号格式）
  try {
    return JSON.parse(value);
  } catch {
    // 忽略错误，继续尝试其他方法
  }

  // 尝试将单引号替换为双引号后解析 JSON（适配 Python 风格字面量）
  try {
    const jsonCompatible = value.replace(/'/g, '"');
    return JSON.parse(jsonCompatible);
  } catch {
    // 忽略错误
  }

  // 默认返回原字符串
  return value;
}

export default convertArg;
