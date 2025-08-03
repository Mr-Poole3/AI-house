"""
聊天API路由
支持文本聊天和图片+文本聊天，自动选择合适的模型
"""

import os
import tempfile
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ..services.chat_service import chat_service
from ..utils.dependencies import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessage(BaseModel):
    """聊天消息数据模型"""
    role: str  # "user" 或 "assistant"
    content: str

class TextChatRequest(BaseModel):
    """纯文本聊天请求"""
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    """聊天响应"""
    message: str
    success: bool = True
    error: Optional[str] = None

@router.post("/text/stream")
async def stream_text_chat(
    request: TextChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    纯文本聊天，流式输出响应
    """
    if not chat_service.is_available():
        raise HTTPException(status_code=503, detail="聊天服务不可用")
    
    try:
        # 转换对话历史格式
        history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 创建流式响应生成器
        async def generate_response():
            """生成流式响应数据"""
            try:
                async for chunk in chat_service.stream_chat_text(
                    request.message, 
                    history
                ):
                    # 使用Server-Sent Events格式
                    yield f"data: {chunk}\n\n"
                
                # 发送结束信号
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                yield f"data: 错误: {str(e)}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")

@router.post("/text")
async def text_chat(
    request: TextChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    纯文本聊天，非流式输出（用于不支持流式的情况）
    """
    if not chat_service.is_available():
        raise HTTPException(status_code=503, detail="聊天服务不可用")
    
    try:
        # 转换对话历史格式
        history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 收集流式输出为完整消息
        response_text = ""
        async for chunk in chat_service.stream_chat_text(
            request.message, 
            history
        ):
            response_text += chunk
        
        return ChatResponse(
            message=response_text,
            success=True
        )
        
    except Exception as e:
        return ChatResponse(
            message="",
            success=False,
            error=str(e)
        )

@router.post("/image")
async def image_chat(
    message: str = Form(...),
    conversation_history: str = Form("[]"),  # JSON字符串格式的对话历史
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    图片+文本聊天
    """
    if not chat_service.is_available():
        raise HTTPException(status_code=503, detail="聊天服务不可用")
    
    # 验证图片文件
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传有效的图片文件")
    
    try:
        import json
        
        # 解析对话历史
        try:
            history_data = json.loads(conversation_history) if conversation_history else []
        except json.JSONDecodeError:
            history_data = []
        
        # 保存临时图片文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 调用图片聊天服务
            response_text = await chat_service.chat_with_image(
                message=message,
                image_path=temp_file_path,
                conversation_history=history_data
            )
            
            return ChatResponse(
                message=response_text,
                success=True
            )
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        return ChatResponse(
            message="",
            success=False,
            error=str(e)
        )

@router.get("/status")
async def chat_status():
    """
    获取聊天服务状态
    """
    return {
        "available": chat_service.is_available(),
        "text_model": chat_service.text_model if chat_service.is_available() else None,
        "vision_model": chat_service.vision_model if chat_service.is_available() else None
    }