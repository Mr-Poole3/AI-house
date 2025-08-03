"""
豆包大模型聊天服务
支持文本聊天和图片+文本聊天，自动选择合适的模型
"""

import os
import base64
import json
import logging
import asyncio
import re
from typing import Optional, AsyncGenerator, Dict, Any, List, Tuple
from pathlib import Path
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..config import settings
from ..config.prompts import DoubaoPrompts
from ..database import get_db
from ..models.property import Property

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
        纯文本聊天，支持流式输出和意图识别
        
        Args:
            message: 用户消息
            conversation_history: 对话历史
            
        Yields:
            str: 流式输出的文本片段或意图识别结果
        """
        if self.client is None:
            yield "错误：聊天服务未初始化"
            return
            
        try:
            # 检查是否为房源查询确认消息
            if message.startswith("PROPERTY_QUERY_CONFIRM:"):
                logger.info(f"📋 收到房源查询确认消息: {message}")
                try:
                    intent_json = message[len("PROPERTY_QUERY_CONFIRM:"):]
                    logger.debug(f"📋 提取的意图JSON字符串: {intent_json}")
                    intent_data = json.loads(intent_json)
                    logger.info(f"📋 解析后的意图数据: {intent_data}")
                    
                    # 处理房源查询并返回结构化结果
                    query_result = await self.process_property_query(intent_data, intent_data.get("original_query", "房源查询"))
                    
                    # 将结构化结果转换为JSON格式返回
                    result_json = json.dumps(query_result, ensure_ascii=False, indent=2)
                    logger.info(f"📋 返回查询结果: {query_result}")
                    yield f"QUERY_RESULT:{result_json}"
                    return
                except (json.JSONDecodeError, Exception) as e:
                    logger.error(f"❌ 解析确认消息中的意图数据失败: {e}")
                    yield "❌ 确认消息格式错误，请重新开始查询。"
                    return
            
            # 使用prompt配置构建消息列表
            messages = DoubaoPrompts.get_chat_messages(message, conversation_history)
            
            # 先收集完整响应以检查是否包含意图识别
            full_response = ""
            
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
                    full_response += content
            
            # 检查是否包含房源查询意图
            intent_data = self._extract_intent_from_response(full_response, message)
            
            if intent_data:
                # 发现房源查询意图，输出确认信息（非流式，一次性完整输出）
                confirmation_msg = intent_data.get("confirmation_message", "是否开始为您搜索房源？")
                
                full_confirmation = f"""🏠 **房源查询意图识别** 🏠

{confirmation_msg}

💡 **提示**: 如果确认查询，请回复 '确认' 或 '开始查询'；如果要修改需求，请重新描述。

<!-- INTENT_DATA: {json.dumps(intent_data, ensure_ascii=False)} -->"""
                
                # 一次性输出完整内容，确保不被截断
                yield full_confirmation
                
            else:
                # 正常聊天，逐字符流式输出（保持打字机效果）
                for char in full_response:
                    yield char
                    # 添加小延迟实现打字机效果
                    if ord(char) > 127:  # 中文字符
                        await asyncio.sleep(0.05)
                    else:  # 英文字符
                        await asyncio.sleep(0.03)
                    
        except Exception as e:
            logger.error(f"文本聊天失败: {e}")
            yield f"错误：{str(e)}"
    
    async def stream_chat_with_confirmation(
        self, 
        message: str, 
        intent_data: Dict[str, Any],
        conversation_history: Optional[list] = None
    ) -> AsyncGenerator[str, None]:
        """
        处理用户确认后的房源查询
        
        Args:
            message: 用户确认消息
            intent_data: 之前识别的意图数据
            conversation_history: 对话历史
            
        Yields:
            str: 查询过程和结果
        """
        # 检查用户是否确认查询
        confirm_keywords = ["确认", "开始查询", "是的", "好的", "查询", "搜索", "找找"]
        user_input = message.lower().strip()
        
        if any(keyword in user_input for keyword in confirm_keywords):
            # 用户确认，开始执行房源查询
            original_query = intent_data.get("original_query", "房源查询")
            async for chunk in self.process_property_query(intent_data, original_query):
                yield chunk
        else:
            # 用户不确认或要修改需求，回到正常聊天
            async for chunk in self.stream_chat_text(message, conversation_history):
                yield chunk
    
    async def chat_with_image(
        self, 
        message: str, 
        image_path: str,
        conversation_history: Optional[list] = None
    ) -> str:
        """
        图片+文本聊天，支持房源图片意图识别
        
        Args:
            message: 用户消息
            image_path: 图片文件路径
            conversation_history: 对话历史（注意：包含图片的对话历史处理较复杂）
            
        Returns:
            str: 完整的回复内容或意图识别结果
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
            
            full_response = response.choices[0].message.content
            
            # 检查是否包含房源图片查询意图
            intent_data = self._extract_intent_from_response(full_response, message)
            
            if intent_data:
                # 发现房源图片查询意图，返回确认信息
                confirmation_msg = intent_data.get("confirmation_message", "是否开始为您搜索类似房源？")
                
                result = "🏠 **房源图片查询意图识别** 🏠\n\n"
                result += confirmation_msg + "\n\n"
                result += "💡 **提示**: 如果确认查询，请回复 '确认' 或 '开始查询'；如果要修改需求，请重新描述。\n\n"
                
                # 嵌入意图数据以供后续处理使用
                result += f"<!-- INTENT_DATA: {json.dumps(intent_data, ensure_ascii=False)} -->"
                
                return result
            else:
                # 正常图片分析
                return full_response
            
        except Exception as e:
            logger.error(f"图片聊天失败: {e}")
            return f"错误：{str(e)}"
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.client is not None
    
    def _extract_intent_from_response(self, response: str, original_query: str = "") -> Optional[Dict[str, Any]]:
        """
        从LLM响应中提取JSON格式的意图识别结果
        
        Args:
            response: LLM的完整响应
            original_query: 用户原始查询
            
        Returns:
            Dict: 提取到的意图数据，如果没有找到则返回None
        """
        logger.info(f"🔍 开始提取意图 - 原始查询: {original_query}")
        logger.debug(f"🔍 LLM完整响应: {response}")
        
        try:
            # 查找JSON代码块
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            logger.info(f"🔍 JSON匹配结果: 找到 {len(matches)} 个JSON块")
            
            if matches:
                logger.debug(f"🔍 提取到的JSON字符串: {matches[0]}")
                intent_data = json.loads(matches[0])
                logger.info(f"🔍 解析后的意图数据: {intent_data}")
                
                # 验证是否为房源查询意图
                if intent_data.get("intent_type") in ["property_query", "property_image_query"]:
                    # 添加原始查询到意图数据中
                    intent_data["original_query"] = original_query
                    logger.info(f"✅ 意图识别成功: {intent_data}")
                    return intent_data
                else:
                    logger.warning(f"⚠️ 意图类型不匹配: {intent_data.get('intent_type')}")
            else:
                logger.warning("⚠️ 未找到JSON代码块")
                    
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"❌ JSON解析失败: {e}")
            
        logger.warning("❌ 意图提取失败")
        return None
    
    async def _generate_sql_query(self, query_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        根据查询参数生成SQL查询语句
        
        Args:
            query_params: 查询参数
            
        Returns:
            Dict: 包含SQL语句和参数的字典
        """
        logger.info(f"🔧 开始生成SQL - 输入参数: {query_params}")
        
        if self.client is None:
            logger.error("❌ 客户端未初始化")
            return None
            
        try:
            # 构建SQL生成prompt
            schema_prompt = DoubaoPrompts.DATABASE_SCHEMA_PROMPT
            sql_prompt = DoubaoPrompts.get_sql_generation_prompt(query_params)
            
            logger.debug(f"🔧 SQL生成prompt: {sql_prompt}")
            
            messages = [
                {"role": "system", "content": schema_prompt},
                {"role": "user", "content": sql_prompt}
            ]
            
            # 调用豆包API生成SQL
            response = self.client.chat.completions.create(
                model=self.text_model,
                messages=messages,
                temperature=0.1,  # 较低的温度确保生成稳定的SQL
                max_tokens=1000,
            )
            
            sql_response = response.choices[0].message.content
            logger.info(f"🔧 大模型SQL响应: {sql_response}")
            
            # 提取JSON格式的SQL查询
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, sql_response, re.DOTALL)
            
            logger.info(f"🔧 SQL JSON匹配结果: 找到 {len(matches)} 个JSON块")
            
            if matches:
                logger.debug(f"🔧 提取到的SQL JSON: {matches[0]}")
                sql_data = json.loads(matches[0])
                logger.info(f"🔧 解析后的SQL数据: {sql_data}")
                
                # 安全检查：确保只是SELECT查询
                sql = sql_data.get("sql", "").strip().upper()
                if sql.startswith("SELECT"):
                    logger.info(f"✅ SQL生成成功: {sql_data}")
                    return sql_data
                else:
                    logger.warning(f"❌ 非SELECT查询被拒绝: {sql}")
            else:
                logger.warning("⚠️ 未找到SQL JSON代码块")
                    
        except Exception as e:
            logger.error(f"❌ SQL生成失败: {e}")
            
        logger.warning("❌ SQL生成失败")
        return None
    
    def _execute_sql_query(self, sql_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行SQL查询（只读）
        
        Args:
            sql_data: 包含SQL和参数的字典
            
        Returns:
            List: 查询结果列表
        """
        try:
            # 获取数据库会话
            db_gen = get_db()
            db = next(db_gen)
            
            sql = sql_data.get("sql")
            params = sql_data.get("params", {})
            
            # 再次安全检查
            if not sql.strip().upper().startswith("SELECT"):
                logger.warning("非SELECT查询被拒绝")
                return []
            
            # 执行查询
            result = db.execute(text(sql), params)
            
            # 转换为字典列表
            columns = result.keys()
            rows = result.fetchall()
            
            query_results = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # 处理特殊类型
                    if hasattr(value, 'isoformat'):  # datetime对象
                        value = value.isoformat()
                    elif hasattr(value, '__float__'):  # Decimal对象
                        value = float(value)
                    row_dict[column] = value
                query_results.append(row_dict)
            
            # 限制结果数量，避免返回过多数据
            return query_results[:20]  # 最多返回20条记录
            
        except Exception as e:
            logger.error(f"SQL查询执行失败: {e}")
            return []
        finally:
            if 'db' in locals():
                db.close()
    
    async def _process_query_results(self, query_results: List[Dict[str, Any]], user_query: str) -> str:
        """
        处理查询结果，生成用户友好的回答
        
        Args:
            query_results: 数据库查询结果
            user_query: 用户原始查询
            
        Returns:
            str: 格式化的回答
        """
        if self.client is None:
            return "错误：聊天服务未初始化"
            
        try:
            # 构建结果处理prompt
            result_prompt = DoubaoPrompts.get_result_processing_prompt(query_results, user_query)
            
            messages = [
                {"role": "system", "content": "你是专业的房源信息助手，请根据查询结果生成友好的回答。"},
                {"role": "user", "content": result_prompt}
            ]
            
            # 调用豆包API处理结果
            response = self.client.chat.completions.create(
                model=self.text_model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"查询结果处理失败: {e}")
            return f"查询完成，但结果处理出现错误：{str(e)}"
    
    async def stream_property_query_steps(
        self, 
        intent_data: Dict[str, Any], 
        user_query: str
    ) -> AsyncGenerator[str, None]:
        """
        流式处理房源查询的每个步骤
        
        Args:
            intent_data: 意图识别数据
            user_query: 用户原始查询
            
        Yields:
            str: 每个步骤的结果信息
        """
        logger.info(f"🎯 开始流式处理房源查询")
        
        try:
            # 步骤1: 分析查询参数
            yield "STEP:param_analysis:start"
            query_params = intent_data.get("query_params", {})
            logger.info(f"🎯 提取到的查询参数: {query_params}")
            await asyncio.sleep(0.5)  # 模拟分析时间
            
            param_json = json.dumps(query_params, ensure_ascii=False, indent=2)
            yield f"STEP:param_analysis:complete:{param_json}"
            
            # 步骤2: 生成SQL查询
            yield "STEP:sql_generation:start"
            sql_data = await self._generate_sql_query(query_params)
            
            if not sql_data:
                yield "STEP:sql_generation:error:SQL查询生成失败，请重新描述您的需求。"
                return
            
            sql_json = json.dumps(sql_data, ensure_ascii=False, indent=2)
            yield f"STEP:sql_generation:complete:{sql_json}"
            
            # 步骤3: 执行SQL查询
            yield "STEP:sql_execution:start"
            query_results = self._execute_sql_query(sql_data)
            await asyncio.sleep(0.3)  # 模拟查询时间
            
            result_count = len(query_results) if query_results else 0
            yield f"STEP:sql_execution:complete:{result_count}"
            
            # 步骤4: 生成最终回答
            if not query_results:
                no_result_msg = "很抱歉，没有找到符合条件的房源。建议您：\n• 放宽价格范围\n• 考虑其他区域\n• 调整房型要求"
                yield f"STEP:final_answer:complete:{no_result_msg}"
                return
            
            yield "STEP:answer_generation:start"
            final_answer = await self._process_query_results(query_results, user_query)
            yield f"STEP:answer_generation:complete:{final_answer}"
            
        except Exception as e:
            logger.error(f"❌ 流式房源查询处理失败: {e}")
            yield f"STEP:error:查询过程出现错误：{str(e)}"
    
    async def process_property_query(
        self, 
        intent_data: Dict[str, Any], 
        user_query: str
    ) -> Dict[str, Any]:
        """
        处理房源查询的完整流程 - 返回完整结果
        
        Args:
            intent_data: 意图识别数据
            user_query: 用户原始查询
            
        Returns:
            Dict: 包含查询过程和结果的完整信息
        """
        logger.info(f"🎯 开始处理房源查询")
        logger.info(f"🎯 意图数据: {intent_data}")
        logger.info(f"🎯 用户查询: {user_query}")
        
        try:
            # 第一步：生成SQL查询
            query_params = intent_data.get("query_params", {})
            logger.info(f"🎯 提取到的查询参数: {query_params}")
            
            sql_data = await self._generate_sql_query(query_params)
            
            if not sql_data:
                return {
                    "success": False,
                    "error": "SQL查询生成失败，请重新描述您的需求。",
                    "query_params": query_params
                }
            
            # 第二步：执行SQL查询
            query_results = self._execute_sql_query(sql_data)
            
            if not query_results:
                return {
                    "success": True,
                    "found_count": 0,
                    "query_params": query_params,
                    "sql_info": sql_data,
                    "results": [],
                    "message": "很抱歉，没有找到符合条件的房源。建议您：\n• 放宽价格范围\n• 考虑其他区域\n• 调整房型要求"
                }
            
            # 第三步：处理查询结果
            final_answer = await self._process_query_results(query_results, user_query)
            
            return {
                "success": True,
                "found_count": len(query_results),
                "query_params": query_params,
                "sql_info": sql_data,
                "results": query_results,
                "formatted_answer": final_answer
            }
                    
        except Exception as e:
            logger.error(f"房源查询处理失败: {e}")
            return {
                "success": False,
                "error": f"查询过程出现错误：{str(e)}",
                "query_params": query_params if 'query_params' in locals() else {}
            }

# 创建全局服务实例
chat_service = ChatService()