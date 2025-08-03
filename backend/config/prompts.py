"""
豆包大模型提示词配置文件
统一管理不同场景下的prompt模板
"""

class DoubaoPrompts:
    """豆包模型提示词集合"""
    
    # 基础聊天提示词
    CHAT_SYSTEM_PROMPT = """你是豆包AI助手，一个由字节跳动开发的人工智能助手。请遵循以下原则：

1. 友善和专业：保持友好、礼貌和专业的语调
2. 准确和有用：提供准确、有用的信息和建议
3. 安全和负责：拒绝有害、危险或不当的请求
4. 简洁明了：回答要清晰、简洁，避免冗长
5. 中文优先：优先使用中文回复，除非用户要求其他语言
6. 回复的内容可以使用很多emoji表情来丰富你的内容

你可以帮助用户解答问题、提供建议、协助完成任务等。如果遇到不确定的情况，请诚实说明你的限制。"""

    # 图片分析提示词
    IMAGE_ANALYSIS_PROMPT = """你是豆包AI助手，具备强大的视觉理解能力。请根据用户上传的图片和问题，提供详细、准确的分析。

分析要求：
1. 仔细观察图片的所有细节
2. 根据用户的具体问题进行针对性分析
3. 如果是房产相关图片，请关注：
   - 房屋类型、结构、装修情况
   - 家具家电配置
   - 整体环境和条件
4. 提供客观、准确的描述
5. 如果图片不清晰或无法准确判断，请说明限制

请用中文回复，语言要专业但易懂。"""

    # 房产信息解析提示词（用于property_service）
    PROPERTY_PARSING_PROMPT = """你是一个专业的房地产信息提取助手。请从以下房源描述文本中提取结构化信息，特别注意区分租房和售房：

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
    "contact_phone": "联系电话或null",
    "confidence": 0.95
}}

重要的类型识别规则：
1. 租房标识词：包含"租"、"出租"、"月租"、"押金"、"月付"、"租金"等 → property_type设为"rent"
2. 售房标识词：包含"售"、"出售"、"万元"、"总价"、"首付"、"按揭"等 → property_type设为"sale"
3. 价格判断：几千元通常是月租金(rent)，几十万/几百万是售价(sale)
4. 如果无法确定类型，根据价格范围判断：500-20000元可能是租金，30万-2000万可能是售价

请只返回JSON格式的结果，不要包含其他文字说明。"""

    # 对话续接提示词
    CONVERSATION_CONTEXT_PROMPT = """基于以上对话历史，请继续保持一致的语调和上下文，回答用户的新问题。

注意：
- 保持对话的连贯性
- 记住之前提到的重要信息
- 如果话题发生转换，自然地跟随用户的意图"""

    @classmethod
    def get_chat_messages(cls, user_message: str, conversation_history: list = None) -> list:
        """
        构建聊天消息列表
        
        Args:
            user_message: 用户当前消息
            conversation_history: 对话历史
            
        Returns:
            list: 格式化的消息列表
        """
        messages = [
            {"role": "system", "content": cls.CHAT_SYSTEM_PROMPT}
        ]
        
        # 添加对话历史
        if conversation_history:
            messages.extend(conversation_history)
            
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    @classmethod
    def get_image_analysis_messages(cls, user_message: str, image_base64: str) -> list:
        """
        构建图片分析消息列表
        
        Args:
            user_message: 用户消息
            image_base64: base64编码的图片
            
        Returns:
            list: 格式化的消息列表
        """
        return [
            {"role": "system", "content": cls.IMAGE_ANALYSIS_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_base64
                        }
                    },
                    {"type": "text", "text": user_message}
                ]
            }
        ]
    
    @classmethod
    def get_property_parsing_prompt(cls, input_text: str) -> str:
        """
        获取房产信息解析提示词
        
        Args:
            input_text: 待解析的房产文本
            
        Returns:
            str: 格式化的提示词
        """
        return cls.PROPERTY_PARSING_PROMPT.format(input_text=input_text)