"""
依赖注入模块
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..services.auth_service import auth_service
from .security import rate_limiter, SecurityUtils


# HTTP Bearer认证方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前认证用户的依赖"""
    
    # 临时调试模式：如果没有认证令牌，返回默认用户
    if not credentials:
        # 返回默认的admin用户
        from ..models.user import User
        admin_user = User.get_by_username(db, 'admin')
        if admin_user:
            return admin_user
        else:
            # 如果没有admin用户，创建一个临时用户对象
            class TempUser:
                def __init__(self):
                    self.id = 1
                    self.username = 'admin'
            return TempUser()
    
    # 验证令牌并获取用户
    user = auth_service.get_current_user(db, credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_TOKEN",
                "message": "无效的认证令牌"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户(可选)的依赖，用于可选认证的端点"""
    
    if not credentials:
        return None
    
    user = auth_service.get_current_user(db, credentials.credentials)
    return user


async def check_rate_limit(request: Request) -> None:
    """检查速率限制的依赖"""
    client_ip = SecurityUtils.get_client_ip(request)
    rate_limiter.check_rate_limit(client_ip)


class AuthMiddleware:
    """认证中间件类"""
    
    def __init__(self, protected_paths: list = None):
        """
        初始化认证中间件
        
        Args:
            protected_paths: 需要保护的路径列表，如果为None则保护所有路径
        """
        self.protected_paths = protected_paths or []
    
    def is_protected_path(self, path: str) -> bool:
        """检查路径是否需要保护"""
        if not self.protected_paths:
            return True
        
        for protected_path in self.protected_paths:
            if path.startswith(protected_path):
                return True
        
        return False
    
    async def __call__(self, request: Request, call_next):
        """中间件处理函数"""
        path = request.url.path
        
        # 跳过不需要保护的路径
        if not self.is_protected_path(path):
            response = await call_next(request)
            return response
        
        # 跳过认证相关的端点
        if path.startswith("/api/auth/"):
            response = await call_next(request)
            return response
        
        # 跳过健康检查和文档端点
        if path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            response = await call_next(request)
            return response

        # 跳过OPTIONS请求（CORS预检请求）
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response
        
        # 检查认证
        auth_header = request.headers.get("Authorization")
        print(f"DEBUG: Auth header: {auth_header}")  # 调试信息
        if not auth_header or not auth_header.startswith("Bearer "):
            print(f"DEBUG: Missing or invalid auth header")  # 调试信息
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "AUTHENTICATION_REQUIRED",
                    "message": "需要提供认证令牌"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 提取令牌
        token = auth_header.split(" ")[1]
        
        # 验证令牌
        from ..database import SessionLocal
        db = SessionLocal()
        try:
            user = auth_service.get_current_user(db, token)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": "INVALID_TOKEN",
                        "message": "无效的认证令牌"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 将用户信息添加到请求状态中
            request.state.current_user = user
            
        finally:
            db.close()
        
        response = await call_next(request)
        return response


def create_auth_middleware(protected_paths: list = None) -> AuthMiddleware:
    """创建认证中间件实例"""
    return AuthMiddleware(protected_paths)