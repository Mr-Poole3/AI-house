"""
豆包大模型聊天服务
支持文本聊天和图片+文本聊天，自动选择合适的模型
"""

import os
import base64
import json
import logging
import asyncio
from typing import Optional, AsyncGenerator, Dict, Any
from pathlib import Path
from openai import OpenAI
from ..config import settings
from ..config.prompts import DoubaoPrompts

# 配置日志
logger = logging.getLogger(__name__)

class ChatService:
    """豆包大模型聊天服务类"""
    
    def __init__(self):
        """初始化聊天服务"""
        self.client = None
        self.text_model = "doubao-1-5-thinking-pro-250415"  # 文本聊天模型
        self.vision_model = "doubao-1.5-vision-pro-250328"  # 图片+文本聊天模型
        try:
            self.client = self._create_client()
        except ValueError as e:
            logger.warning(f"聊天服务初始化失败: {e}")
        
    def _create_client(self) -> OpenAI:
        """创建豆包客户端"""
        api_key = os.environ.get("ARK_API_KEY") or settings.ARK_API_KEY or settings.DOUBAO_API_KEY
        if not api_key:
            raise ValueError("请在环境变量中设置 ARK_API_KEY")
        
        return OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key,
        )
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        将图片文件转换为base64编码
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            str: base64编码的图片字符串，包含数据URL前缀
        """
        img_path = Path(image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {img_path}")
        
        try:
            with open(img_path, "rb") as image_file:
                image_data = image_file.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
                
                # 获取文件扩展名确定MIME类型
                ext = img_path.suffix.lower()
                mime_type = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg', 
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }.get(ext, 'image/jpeg')
                
                return f"data:{mime_type};base64,{base64_image}"
                
        except Exception as e:
            raise Exception(f"图片编码失败: {e}")
    
    async def stream_chat_text(
        self, 
        message: str, 
        conversation_history: Optional[list] = None
    ) -> AsyncGenerator[str, None]:
        """
        纯文本聊天，支持流式输出
        
        Args:
            message: 用户消息
            conversation_history: 对话历史
            
        Yields:
            str: 流式输出的文本片段
        """
        if self.client is None:
            yield "错误：聊天服务未初始化"
            return
            
        try:
            # 使用prompt配置构建消息列表
            messages = DoubaoPrompts.get_chat_messages(message, conversation_history)
            
            # 调用豆包API进行流式聊天
            stream = self.client.chat.completions.create(
                model=self.text_model,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=2000,
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    # 逐字符输出，实现真正的流式效果
                    for char in content:
                        yield char
                        # 添加小延迟实现打字机效果（中文字符稍慢一点）
                        if ord(char) > 127:  # 中文字符
                            await asyncio.sleep(0.05)  # 50ms
                        else:  # 英文字符
                            await asyncio.sleep(0.03)  # 30ms
                    
        except Exception as e:
            logger.error(f"文本聊天失败: {e}")
            yield f"错误：{str(e)}"
    
    async def chat_with_image(
        self, 
        message: str, 
        image_path: str,
        conversation_history: Optional[list] = None
    ) -> str:
        """
        图片+文本聊天，不支持流式输出（豆包视觉模型限制）
        
        Args:
            message: 用户消息
            image_path: 图片文件路径
            conversation_history: 对话历史（注意：包含图片的对话历史处理较复杂）
            
        Returns:
            str: 完整的回复内容
        """
        if self.client is None:
            return "错误：聊天服务未初始化"
            
        try:
            # 编码图片
            base64_image = self._encode_image_to_base64(image_path)
            
            # 使用prompt配置构建消息列表
            messages = DoubaoPrompts.get_image_analysis_messages(message, base64_image)
            
            # 调用豆包视觉API
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"图片聊天失败: {e}")
            return f"错误：{str(e)}"
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.client is not None

# 创建全局服务实例
chat_service = ChatService()