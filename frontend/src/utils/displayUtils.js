/**
 * 显示工具函数
 * 用于统一处理各种显示相关的逻辑
 */

/**
 * 格式化显示文本，处理null/undefined/空值
 * @param {any} value - 要显示的值
 * @param {string} defaultText - 默认显示文本
 * @returns {string} 格式化后的显示文本
 */
export const formatDisplayText = (value, defaultText = '暂无') => {
  if (value === null || value === undefined || value === '' || value === 'null') {
    return defaultText;
  }
  return String(value).trim();
};

/**
 * 格式化联系电话显示
 * @param {string} phone - 电话号码
 * @returns {string} 格式化后的电话号码或默认文本
 */
export const formatPhoneDisplay = (phone) => {
  return formatDisplayText(phone, '暂无联系电话');
};

/**
 * 检查值是否为空（包括null、undefined、空字符串、'null'字符串）
 * @param {any} value - 要检查的值
 * @returns {boolean} 是否为空
 */
export const isEmpty = (value) => {
  return value === null || value === undefined || value === '' || value === 'null';
};

/**
 * 安全地获取表单字段值，将null转换为空字符串
 * @param {any} value - 原始值
 * @returns {string} 安全的字符串值
 */
export const safeFormValue = (value) => {
  if (isEmpty(value)) {
    return '';
  }
  return String(value);
};

/**
 * 格式化价格显示
 * @param {string} propertyType - 房屋类型 ('rent' 或 'sale')
 * @param {number} price - 价格
 * @returns {string} 格式化后的价格
 */
export const formatPrice = (propertyType, price) => {
  if (!price) return '价格面议';
  
  if (propertyType === 'rent') {
    return `${price} 元/月`;
  } else {
    return `${price} 万元`;
  }
};

/**
 * 格式化面积显示
 * @param {number} area - 面积
 * @returns {string} 格式化后的面积
 */
export const formatArea = (area) => {
  if (!area) return '';
  return `${area}㎡`;
};
