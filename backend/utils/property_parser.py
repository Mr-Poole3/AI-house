"""
房源文本解析工具和验证器
专门用于房屋类型识别验证和价格范围检查
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum
from ..models.property import PropertyType

logger = logging.getLogger(__name__)

class ValidationResult:
    """验证结果类"""
    def __init__(self, is_valid: bool, message: str = "", suggestions: List[str] = None):
        self.is_valid = is_valid
        self.message = message
        self.suggestions = suggestions or []

class PropertyParsingValidator:
    """房源解析结果验证器"""
    
    # 租房关键词
    RENT_KEYWORDS = [
        "租", "出租", "月租", "押金", "月付", "租金", "租房", 
        "押一付三", "押二付一", "押一付一", "包水电", "中介费"
    ]
    
    # 售房关键词
    SALE_KEYWORDS = [
        "售", "出售", "万元", "总价", "首付", "按揭", "售房", "买房",
        "房价", "单价", "平米", "贷款", "过户", "税费"
    ]
    
    # 价格范围配置（仅用于类型判断，不限制用户输入）
    RENT_PRICE_RANGE = (100, 50000)      # 月租金参考范围：100-50000元
    SALE_PRICE_RANGE = (1, 10000)        # 售价参考范围：1-10000万元
    
    @classmethod
    def validate_property_type(cls, text: str, parsed_type: str) -> ValidationResult:
        """
        验证房屋类型识别是否正确
        
        Args:
            text: 原始房源文本
            parsed_type: 解析出的房屋类型
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            # 计算关键词权重
            rent_score = cls._calculate_keyword_score(text, cls.RENT_KEYWORDS)
            sale_score = cls._calculate_keyword_score(text, cls.SALE_KEYWORDS)
            
            logger.info(f"类型验证 - 租房得分: {rent_score}, 售房得分: {sale_score}")
            
            # 基于价格进行二次验证
            price_validation = cls._validate_price_context(text, parsed_type)
            
            # 综合判断
            if parsed_type == PropertyType.RENT.value:
                if rent_score >= sale_score or price_validation.is_valid:
                    return ValidationResult(True, "房屋类型识别正确：租房")
                else:
                    return ValidationResult(
                        False, 
                        "房屋类型可能识别错误，建议检查是否为售房",
                        ["检查文本中是否包含售房相关信息", "确认价格是否为售价而非租金"]
                    )
            else:  # sale
                if sale_score >= rent_score or price_validation.is_valid:
                    return ValidationResult(True, "房屋类型识别正确：售房")
                else:
                    return ValidationResult(
                        False,
                        "房屋类型可能识别错误，建议检查是否为租房",
                        ["检查文本中是否包含租房相关信息", "确认价格是否为租金而非售价"]
                    )
                    
        except Exception as e:
            logger.error(f"房屋类型验证失败: {e}")
            return ValidationResult(False, f"验证过程出错: {str(e)}")
    
    @classmethod
    def validate_price_range(cls, property_type: str, price: Optional[float]) -> ValidationResult:
        """
        验证价格范围是否合理
        
        Args:
            property_type: 房屋类型
            price: 价格
            
        Returns:
            ValidationResult: 验证结果
        """
        if price is None:
            return ValidationResult(True, "价格为空，跳过验证")
        
        try:
            if property_type == PropertyType.RENT.value:
                min_price, max_price = cls.RENT_PRICE_RANGE
                if min_price <= price <= max_price:
                    return ValidationResult(True, f"月租金 {price} 元在合理范围内")
                else:
                    return ValidationResult(
                        True,  # 改为True，不再报错
                        f"月租金 {price} 元",
                        [
                            f"价格较为特殊，请确认单位是否正确",
                            f"常见月租金范围：{min_price}-{max_price} 元"
                        ]
                    )
            else:  # sale
                min_price, max_price = cls.SALE_PRICE_RANGE
                if min_price <= price <= max_price:
                    return ValidationResult(True, f"售价 {price} 万元在合理范围内")
                else:
                    return ValidationResult(
                        True,  # 改为True，不再报错
                        f"售价 {price} 万元",
                        [
                            f"价格较为特殊，请确认单位是否正确",
                            f"常见售价范围：{min_price}-{max_price} 万元"
                        ]
                    )
                    
        except Exception as e:
            logger.error(f"价格范围验证失败: {e}")
            return ValidationResult(False, f"价格验证出错: {str(e)}")
    
    @classmethod
    def _calculate_keyword_score(cls, text: str, keywords: List[str]) -> int:
        """计算关键词匹配得分"""
        score = 0
        text_lower = text.lower()
        
        for keyword in keywords:
            # 简单匹配计1分，完整词匹配计2分
            if keyword in text_lower:
                score += 1
                # 检查是否为完整词匹配
                if re.search(rf'\b{re.escape(keyword)}\b', text_lower):
                    score += 1
                    
        return score
    
    @classmethod
    def _validate_price_context(cls, text: str, parsed_type: str) -> ValidationResult:
        """基于价格上下文验证房屋类型"""
        try:
            # 提取文本中的数字
            numbers = re.findall(r'\d+(?:\.\d+)?', text)
            
            if not numbers:
                return ValidationResult(True, "未找到价格信息")
            
            # 转换为浮点数并排序
            prices = [float(num) for num in numbers]
            prices.sort(reverse=True)  # 降序排列
            
            # 分析最大的几个数字
            max_price = prices[0] if prices else 0
            
            if parsed_type == PropertyType.RENT.value:
                # 租房：价格通常在几千元范围
                if 500 <= max_price <= 20000:
                    return ValidationResult(True, f"价格 {max_price} 符合租房特征")
                elif max_price > 100000:  # 超过10万，可能是售价
                    return ValidationResult(False, f"价格 {max_price} 更像售价")
            else:  # sale
                # 售房：价格通常在几十万到几千万
                if max_price >= 300000:  # 30万以上
                    return ValidationResult(True, f"价格 {max_price} 符合售房特征")
                elif max_price <= 50000:  # 5万以下，可能是租金
                    return ValidationResult(False, f"价格 {max_price} 更像租金")
            
            return ValidationResult(True, "价格上下文验证通过")
            
        except Exception as e:
            logger.error(f"价格上下文验证失败: {e}")
            return ValidationResult(True, "价格上下文验证跳过")

class PropertyParsingFallback:
    """解析失败的降级处理机制"""
    
    @staticmethod
    def create_fallback_result(text: str) -> Dict:
        """
        创建降级解析结果
        当LLM解析完全失败时，使用规则提取基础信息
        
        Args:
            text: 原始文本
            
        Returns:
            Dict: 基础解析结果
        """
        try:
            result = {
                "property_type": PropertyParsingFallback._guess_property_type(text),
                "community_name": PropertyParsingFallback._extract_community_name(text),
                "street_address": None,
                "floor_info": PropertyParsingFallback._extract_floor_info(text),
                "price": PropertyParsingFallback._extract_price(text),
                "room_count": PropertyParsingFallback._extract_room_count(text),
                "area": PropertyParsingFallback._extract_area(text),
                "furniture_appliances": None,
                "decoration_status": PropertyParsingFallback._extract_decoration(text),
                "contact_phone": PropertyParsingFallback._extract_contact_phone(text),
                "confidence": 0.3  # 降级处理的置信度较低
            }
            
            logger.info("使用降级处理机制生成基础解析结果")
            return result
            
        except Exception as e:
            logger.error(f"降级处理失败: {e}")
            return {
                "property_type": "rent",
                "confidence": 0.0
            }
    
    @staticmethod
    def _guess_property_type(text: str) -> str:
        """基于关键词猜测房屋类型"""
        rent_count = sum(1 for keyword in PropertyParsingValidator.RENT_KEYWORDS if keyword in text)
        sale_count = sum(1 for keyword in PropertyParsingValidator.SALE_KEYWORDS if keyword in text)
        
        return PropertyType.RENT.value if rent_count >= sale_count else PropertyType.SALE.value
    
    @staticmethod
    def _extract_community_name(text: str) -> Optional[str]:
        """提取小区名称"""
        # 简单的小区名称提取规则
        patterns = [
            r'([^，。！？\s]+小区)',
            r'([^，。！？\s]+花园)',
            r'([^，。！？\s]+公寓)',
            r'([^，。！？\s]+大厦)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _extract_floor_info(text: str) -> Optional[str]:
        """提取楼层信息"""
        patterns = [
            r'(\d+楼)',
            r'(\d+层)',
            r'(第\d+层)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _extract_price(text: str) -> Optional[float]:
        """提取价格信息"""
        # 查找价格模式
        price_patterns = [
            r'(\d+(?:\.\d+)?)万元',  # X万元
            r'(\d+(?:\.\d+)?)元/月',  # X元/月
            r'月租[金]?(\d+(?:\.\d+)?)',  # 月租金X
            r'租金(\d+(?:\.\d+)?)',  # 租金X
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        
        # 如果没有明确的价格模式，查找数字
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if numbers:
            # 返回最大的数字作为可能的价格
            return max(float(num) for num in numbers)
        
        return None
    
    @staticmethod
    def _extract_room_count(text: str) -> Optional[str]:
        """提取房间配置"""
        patterns = [
            r'(\d+室\d+厅)',
            r'(\d+房\d+厅)',
            r'(\d+室\d+厅\d+卫)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _extract_area(text: str) -> Optional[float]:
        """提取面积信息"""
        patterns = [
            r'(\d+(?:\.\d+)?)平[米方]',
            r'(\d+(?:\.\d+)?)㎡',
            r'面积(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        
        return None
    
    @staticmethod
    def _extract_decoration(text: str) -> Optional[str]:
        """提取装修情况"""
        decoration_keywords = ['精装修', '简装', '毛坯', '豪装', '中装']
        
        for keyword in decoration_keywords:
            if keyword in text:
                return keyword
        
        return None
    
    @staticmethod
    def _extract_contact_phone(text: str) -> Optional[str]:
        """提取联系电话"""
        # 电话号码匹配模式
        phone_patterns = [
            r'1[3-9]\d{9}',  # 11位手机号码
            r'(?:联系|电话|手机|☎)\s*[:：]?\s*(1[3-9]\d{9})',  # 带前缀的手机号
            r'(\d{3}-\d{8}|\d{4}-\d{7})',  # 固定电话格式
            r'(\d{11})',  # 11位数字
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # 如果是元组，取最后一个匹配项
                phone = match if isinstance(match, str) else match[-1]
                # 验证是否为有效手机号
                if re.match(r'^1[3-9]\d{9}$', phone):
                    return phone
        
        return None