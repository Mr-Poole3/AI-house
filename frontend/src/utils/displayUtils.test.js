/**
 * 显示工具函数测试
 */
import { 
  formatDisplayText, 
  formatPhoneDisplay, 
  isEmpty, 
  safeFormValue,
  formatPrice,
  formatArea 
} from './displayUtils';

describe('displayUtils', () => {
  describe('formatDisplayText', () => {
    test('应该处理null值', () => {
      expect(formatDisplayText(null)).toBe('暂无');
      expect(formatDisplayText(null, '无数据')).toBe('无数据');
    });

    test('应该处理undefined值', () => {
      expect(formatDisplayText(undefined)).toBe('暂无');
      expect(formatDisplayText(undefined, '无数据')).toBe('无数据');
    });

    test('应该处理空字符串', () => {
      expect(formatDisplayText('')).toBe('暂无');
      expect(formatDisplayText('', '无数据')).toBe('无数据');
    });

    test('应该处理"null"字符串', () => {
      expect(formatDisplayText('null')).toBe('暂无');
      expect(formatDisplayText('null', '无数据')).toBe('无数据');
    });

    test('应该保留有效值', () => {
      expect(formatDisplayText('13812345678')).toBe('13812345678');
      expect(formatDisplayText('有效文本')).toBe('有效文本');
      expect(formatDisplayText(123)).toBe('123');
    });
  });

  describe('formatPhoneDisplay', () => {
    test('应该处理空值', () => {
      expect(formatPhoneDisplay(null)).toBe('暂无联系电话');
      expect(formatPhoneDisplay(undefined)).toBe('暂无联系电话');
      expect(formatPhoneDisplay('')).toBe('暂无联系电话');
      expect(formatPhoneDisplay('null')).toBe('暂无联系电话');
    });

    test('应该保留有效电话号码', () => {
      expect(formatPhoneDisplay('13812345678')).toBe('13812345678');
      expect(formatPhoneDisplay('021-12345678')).toBe('021-12345678');
    });
  });

  describe('isEmpty', () => {
    test('应该正确识别空值', () => {
      expect(isEmpty(null)).toBe(true);
      expect(isEmpty(undefined)).toBe(true);
      expect(isEmpty('')).toBe(true);
      expect(isEmpty('null')).toBe(true);
    });

    test('应该正确识别非空值', () => {
      expect(isEmpty('13812345678')).toBe(false);
      expect(isEmpty('有效文本')).toBe(false);
      expect(isEmpty(0)).toBe(false);
      expect(isEmpty(false)).toBe(false);
    });
  });

  describe('safeFormValue', () => {
    test('应该将空值转换为空字符串', () => {
      expect(safeFormValue(null)).toBe('');
      expect(safeFormValue(undefined)).toBe('');
      expect(safeFormValue('')).toBe('');
      expect(safeFormValue('null')).toBe('');
    });

    test('应该保留有效值', () => {
      expect(safeFormValue('13812345678')).toBe('13812345678');
      expect(safeFormValue('有效文本')).toBe('有效文本');
      expect(safeFormValue(123)).toBe('123');
    });
  });

  describe('formatPrice', () => {
    test('应该正确格式化租房价格', () => {
      expect(formatPrice('rent', 3000)).toBe('3000 元/月');
    });

    test('应该正确格式化售房价格', () => {
      expect(formatPrice('sale', 300)).toBe('300 万元');
    });

    test('应该处理空价格', () => {
      expect(formatPrice('rent', null)).toBe('价格面议');
      expect(formatPrice('sale', undefined)).toBe('价格面议');
    });
  });

  describe('formatArea', () => {
    test('应该正确格式化面积', () => {
      expect(formatArea(100)).toBe('100㎡');
      expect(formatArea(85.5)).toBe('85.5㎡');
    });

    test('应该处理空面积', () => {
      expect(formatArea(null)).toBe('');
      expect(formatArea(undefined)).toBe('');
    });
  });
});
