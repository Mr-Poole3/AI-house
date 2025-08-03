// 常量定义

// 房屋类型
export const PROPERTY_TYPES = {
  RENT: 'rent',
  SALE: 'sale'
};

// 房屋类型标签
export const PROPERTY_TYPE_LABELS = {
  [PROPERTY_TYPES.RENT]: '租房',
  [PROPERTY_TYPES.SALE]: '售房'
};

// 价格范围
export const PRICE_RANGES = {
  RENT: {
    MIN: 500,
    MAX: 20000
  },
  SALE: {
    MIN: 30,
    MAX: 2000
  }
};

// 支持的图片格式
export const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png'];

// 文件大小限制 (10MB)
export const MAX_FILE_SIZE = 10 * 1024 * 1024;