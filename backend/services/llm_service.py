"""
豆包大模型集成服务
专门用于房源文本解析，重点强调租房/售房类型识别
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
from openai import OpenAI
from pydantic import BaseModel, Field
from ..config import settings
from ..utils.property_parser import PropertyParsingValidator, PropertyParsingFallback

# 配置日志
logger = logging.getLogger(__name__)

class PropertyParsingResult(BaseModel):
    """房源解析结果数据模型"""
    property_type: str = Field(..., description="房屋类型: rent(租房) 或 sale(售房)")
    community_name: Optional[str] = Field(None, description="小区名称")
    street_address: Optional[str] = Field(None, description="街道地址")
    floor_info: Optional[str] = Field(None, description="楼层信息")
    price: Optional[float] = Field(None, description="价格(租房为月租金，售房为总价万元)")
    room_count: Optional[str] = Field(None, description="房间配置(如: 2室1厅)")
    area: Optional[float] = Field(None, description="面积(平米)")
    furniture_appliances: Optional[str] = Field(None, description="家具家电配置")
    decoration_status: Optional[str] = Field(None, description="装修情况")
    confidence: float = Field(0.0, description="解析置信度(0-1)")
    validation_warnings: list = Field(default_factory=list, description="验证警告信息")
    is_fallback: bool = Field(False, description="是否使用了降级处理")

class LLMService:
    """豆包大模型服务类"""
    
    def __init__(self):
        """初始化LLM服务"""
        self.client = None
        self.model = "doubao-1-5-thinking-pro-250415"  # 使用豆包模型端点
        try:
            self.client = self._create_client()
        except ValueError as e:
            logger.warning(f"LLM服务初始化失败: {e}")
        
    def _create_client(self) -> OpenAI:
        """创建豆包客户端"""
        api_key = os.environ.get("ARK_API_KEY") or settings.ARK_API_KEY or settings.DOUBAO_API_KEY
        if not api_key:
            raise ValueError("请在环境变量中设置 ARK_API_KEY 或在配置中设置 ARK_API_KEY/DOUBAO_API_KEY")
        
        return OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key,
        )
    
    def _get_parsing_prompt(self, input_text: str) -> str:
        """获取房源解析的提示词模板"""
        return f"""
你是一个专业的房地产信息提取助手。请从以下房源描述文本中提取结构化信息，特别注意区分租房和售房：

文本：{input_text}

请按照以下JSON格式返回结果，确保JSON格式正确：
{{
    "property_type": "rent或sale",
    "community_name": "小区名称或null",
    "street_address": "详细地址或null", 
    "floor_info": "楼层信息或null",
    "price": 数字或null,
    "room_count": "几室几厅或null",
    "area": 数字或null,
    "furniture_appliances": "家具家电情况或null",
    "decoration_status": "装修情况或null",
    "confidence": 0.95
}}

重要的类型识别规则：
1. 租房标识词：包含"租"、"出租"、"月租"、"押金"、"月付"、"租金"等 → property_type设为"rent"
2. 售房标识词：包含"售"、"出售"、"万元"、"总价"、"首付"、"按揭"等 → property_type设为"sale"
3. 价格判断：几千元通常是月租金(rent)，几十万/几百万是售价(sale)
4. 如果无法确定类型，根据价格范围判断：500-20000元可能是租金，30万-2000万可能是售价

请只返回JSON格式的结果，不要包含其他文字说明。
"""

    async def parse_property_text(self, text: str) -> PropertyParsingResult:
        """
        解析房源文本，包含验证和降级处理
        
        Args:
            text: 房源描述文本
            
        Returns:
            PropertyParsingResult: 解析结果
        """
        try:
            logger.info(f"开始解析房源文本，长度: {len(text)}")
            
            # 尝试LLM解析
            result = await self._try_llm_parsing(text)
            
            if result is None:
                # LLM解析失败，使用降级处理
                logger.warning("LLM解析失败，使用降级处理机制")
                return self._create_fallback_result(text)
            
            # 验证解析结果
            validated_result = self._validate_parsing_result(text, result)
            
            logger.info(f"解析完成，房屋类型: {validated_result.property_type}, 置信度: {validated_result.confidence}")
            return validated_result
            
        except Exception as e:
            logger.error(f"房源文本解析过程失败: {e}")
            # 最后的降级处理
            return self._create_fallback_result(text)
    
    async def _try_llm_parsing(self, text: str) -> Optional[PropertyParsingResult]:
        """
        尝试使用LLM解析文本
        
        Args:
            text: 房源描述文本
            
        Returns:
            PropertyParsingResult或None: 解析结果，失败时返回None
        """
        try:
            # 检查客户端是否可用
            if self.client is None:
                logger.warning("LLM客户端未初始化，跳过LLM解析")
                return None
                
            # 构建提示词
            prompt = self._get_parsing_prompt(text)
            
            # 调用豆包API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的房地产信息提取助手，专门负责从房源描述中提取结构化信息。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # 降低随机性，提高一致性
                max_tokens=1000,
                timeout=30  # 30秒超时
            )
            
            # 解析响应
            content = response.choices[0].message.content.strip()
            logger.info(f"LLM原始响应: {content}")
            
            # 尝试解析JSON
            try:
                # 清理可能的markdown代码块标记
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                parsed_data = json.loads(content)
                
                # 创建结果对象
                result = PropertyParsingResult(
                    property_type=parsed_data.get("property_type", "rent"),
                    community_name=parsed_data.get("community_name"),
                    street_address=parsed_data.get("street_address"),
                    floor_info=parsed_data.get("floor_info"),
                    price=parsed_data.get("price"),
                    room_count=parsed_data.get("room_count"),
                    area=parsed_data.get("area"),
                    furniture_appliances=parsed_data.get("furniture_appliances"),
                    decoration_status=parsed_data.get("decoration_status"),
                    confidence=parsed_data.get("confidence", 0.8),
                    is_fallback=False
                )
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}, 原始内容: {content}")
                return None
                
        except Exception as e:
            logger.error(f"LLM API调用失败: {e}")
            return None
    
    def _validate_parsing_result(self, text: str, result: PropertyParsingResult) -> PropertyParsingResult:
        """
        验证解析结果并添加警告信息
        
        Args:
            text: 原始文本
            result: 解析结果
            
        Returns:
            PropertyParsingResult: 验证后的结果
        """
        warnings = []
        
        try:
            # 验证房屋类型
            type_validation = PropertyParsingValidator.validate_property_type(text, result.property_type)
            if not type_validation.is_valid:
                warnings.append(f"类型验证: {type_validation.message}")
                warnings.extend(type_validation.suggestions)
                # 降低置信度
                result.confidence = max(0.1, result.confidence - 0.3)
            
            # 验证价格范围
            price_validation = PropertyParsingValidator.validate_price_range(result.property_type, result.price)
            if not price_validation.is_valid:
                warnings.append(f"价格验证: {price_validation.message}")
                warnings.extend(price_validation.suggestions)
                # 降低置信度
                result.confidence = max(0.1, result.confidence - 0.2)
            
            # 更新验证警告
            result.validation_warnings = warnings
            
            logger.info(f"验证完成，警告数量: {len(warnings)}")
            
        except Exception as e:
            logger.error(f"结果验证失败: {e}")
            warnings.append(f"验证过程出错: {str(e)}")
            result.validation_warnings = warnings
        
        return result
    
    def _create_fallback_result(self, text: str) -> PropertyParsingResult:
        """
        创建降级处理结果
        
        Args:
            text: 原始文本
            
        Returns:
            PropertyParsingResult: 降级处理结果
        """
        try:
            fallback_data = PropertyParsingFallback.create_fallback_result(text)
            
            result = PropertyParsingResult(
                property_type=fallback_data.get("property_type", "rent"),
                community_name=fallback_data.get("community_name"),
                street_address=fallback_data.get("street_address"),
                floor_info=fallback_data.get("floor_info"),
                price=fallback_data.get("price"),
                room_count=fallback_data.get("room_count"),
                area=fallback_data.get("area"),
                furniture_appliances=fallback_data.get("furniture_appliances"),
                decoration_status=fallback_data.get("decoration_status"),
                confidence=fallback_data.get("confidence", 0.3),
                validation_warnings=["使用了降级处理机制，建议手动检查结果"],
                is_fallback=True
            )
            
            logger.info("创建降级处理结果成功")
            return result
            
        except Exception as e:
            logger.error(f"降级处理失败: {e}")
            # 最基础的结果
            return PropertyParsingResult(
                property_type="rent",
                confidence=0.0,
                validation_warnings=["解析完全失败，请手动填写"],
                is_fallback=True
            )
    
    def _extract_keywords(self, text: str) -> Dict[str, int]:
        """提取关键词并计算权重（用于类型识别验证）"""
        rent_keywords = ["租", "出租", "月租", "押金", "月付", "租金", "租房"]
        sale_keywords = ["售", "出售", "万元", "总价", "首付", "按揭", "售房", "买房"]
        
        rent_score = sum(1 for keyword in rent_keywords if keyword in text)
        sale_score = sum(1 for keyword in sale_keywords if keyword in text)
        
        return {
            "rent_score": rent_score,
            "sale_score": sale_score
        }

# 创建全局服务实例
llm_service = LLMService()