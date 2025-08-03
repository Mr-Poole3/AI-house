"""
认证相关的数据模式
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """登录请求模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class LoginResponse(BaseModel):
    """登录响应模式"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")
    user_info: dict = Field(..., description="用户信息")


class TokenRefreshResponse(BaseModel):
    """令牌刷新响应模式"""
    access_token: str = Field(..., description="新的访问令牌")
    expires_in: int = Field(..., description="过期时间(秒)")


class LogoutResponse(BaseModel):
    """登出响应模式"""
    message: str = Field(default="Successfully logged out", description="登出消息")


class UserInfo(BaseModel):
    """用户信息模式"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class TokenPayload(BaseModel):
    """JWT令牌载荷模式"""
    sub: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    exp: int = Field(..., description="过期时间戳")
    iat: int = Field(..., description="签发时间戳")
    jti: str = Field(..., description="JWT ID")