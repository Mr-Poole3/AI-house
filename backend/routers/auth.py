"""
认证路由
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.auth import (
    LoginRequest, LoginResponse, TokenRefreshResponse, 
    LogoutResponse, UserInfo
)
from ..services.auth_service import auth_service
from ..utils.dependencies import get_current_user, check_rate_limit
from ..utils.security import rate_limiter, SecurityUtils
from ..models.user import User


router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """
    用户登录端点
    
    - **username**: 用户名
    - **password**: 密码
    
    返回JWT访问令牌和用户信息
    """
    client_ip = SecurityUtils.get_client_ip(request)
    
    try:
        # 验证用户身份
        user = auth_service.authenticate_user(db, login_data.username, login_data.password)
        
        if not user:
            # 记录失败尝试
            rate_limiter.record_failed_attempt(client_ip)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "INVALID_CREDENTIALS",
                    "message": "用户名或密码错误"
                }
            )
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires
        )
        
        # 创建用户会话
        auth_service.create_user_session(db, user, access_token)
        
        # 清除失败尝试记录
        rate_limiter.clear_attempts(client_ip)
        
        # 返回登录响应
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,  # 转换为秒
            user_info=user.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 记录失败尝试
        rate_limiter.record_failed_attempt(client_ip)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "LOGIN_ERROR",
                "message": "登录过程中发生错误"
            }
        )


@router.post("/refresh", response_model=TokenRefreshResponse, summary="刷新令牌")
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌
    
    需要提供有效的访问令牌，返回新的访问令牌
    """
    try:
        # 从请求头获取当前令牌
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "INVALID_TOKEN_FORMAT",
                    "message": "无效的令牌格式"
                }
            )
        
        current_token = auth_header.split(" ")[1]
        
        # 刷新令牌
        new_token = auth_service.refresh_token(db, current_token)
        
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "TOKEN_REFRESH_FAILED",
                    "message": "令牌刷新失败"
                }
            )
        
        return TokenRefreshResponse(
            access_token=new_token,
            expires_in=auth_service.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "REFRESH_ERROR",
                "message": "令牌刷新过程中发生错误"
            }
        )


@router.post("/logout", response_model=LogoutResponse, summary="用户登出")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    用户登出
    
    撤销当前访问令牌
    """
    try:
        # 从请求头获取当前令牌
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            current_token = auth_header.split(" ")[1]
            
            # 登出用户
            auth_service.logout_user(db, current_token)
        
        return LogoutResponse(message="Successfully logged out")
        
    except Exception as e:
        # 即使登出过程中出错，也返回成功响应
        return LogoutResponse(message="Successfully logged out")


@router.post("/logout-all", response_model=LogoutResponse, summary="登出所有会话")
async def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    登出用户的所有会话
    
    撤销用户的所有访问令牌
    """
    try:
        # 登出所有会话
        revoked_count = auth_service.logout_all_sessions(db, current_user.id)
        
        return LogoutResponse(
            message=f"Successfully logged out from {revoked_count} sessions"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "LOGOUT_ALL_ERROR",
                "message": "登出所有会话过程中发生错误"
            }
        )


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前认证用户的信息
    """
    return UserInfo(**current_user.to_dict())


@router.post("/cleanup-sessions", summary="清理过期会话")
async def cleanup_expired_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    清理过期的会话记录
    
    管理员功能，清理数据库中的过期会话
    """
    try:
        cleaned_count = auth_service.cleanup_expired_sessions(db)
        
        return {
            "message": f"Successfully cleaned up {cleaned_count} expired sessions"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "CLEANUP_ERROR",
                "message": "清理过期会话过程中发生错误"
            }
        )