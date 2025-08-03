"""
认证服务
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..config import settings
from ..models.user import User
from ..models.user_session import UserSession
from ..schemas.auth import TokenPayload


class AuthService:
    """认证服务类"""
    
    def __init__(self):
        # 密码加密上下文
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # JWT配置
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # 添加标准JWT声明
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32)  # JWT ID
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 验证必要字段
            username: str = payload.get("username")
            user_id: str = payload.get("sub")
            exp: int = payload.get("exp")
            iat: int = payload.get("iat")
            jti: str = payload.get("jti")
            
            if username is None or user_id is None:
                return None
            
            # 创建TokenPayload对象
            token_data = TokenPayload(
                sub=user_id,
                username=username,
                exp=exp,
                iat=iat,
                jti=jti
            )
            return token_data
            
        except JWTError:
            return None
    
    def hash_token(self, token: str) -> str:
        """对令牌进行哈希处理用于存储"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """验证用户身份"""
        user = User.get_by_username(db, username)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    def create_user_session(self, db: Session, user: User, token: str) -> UserSession:
        """创建用户会话"""
        token_hash = self.hash_token(token)
        expires_in_days = self.access_token_expire_minutes // (24 * 60)  # 转换为天数
        
        # 创建会话记录
        session = UserSession.create(
            db=db,
            user_id=user.id,
            token_hash=token_hash,
            expires_in_days=expires_in_days
        )
        
        return session
    
    def get_current_user(self, db: Session, token: str) -> Optional[User]:
        """获取当前用户"""
        # 验证令牌
        token_data = self.verify_token(token)
        if token_data is None:
            return None
        
        # 检查会话是否存在且有效
        token_hash = self.hash_token(token)
        session = UserSession.get_by_token_hash(db, token_hash)
        
        if not session or session.is_expired():
            return None
        
        # 获取用户信息
        user = db.query(User).filter(User.id == int(token_data.sub)).first()
        return user
    
    def refresh_token(self, db: Session, token: str) -> Optional[str]:
        """刷新令牌"""
        # 验证当前令牌
        token_data = self.verify_token(token)
        if token_data is None:
            return None
        
        # 检查会话
        token_hash = self.hash_token(token)
        session = UserSession.get_by_token_hash(db, token_hash)
        
        if not session or session.is_expired():
            return None
        
        # 获取用户
        user = db.query(User).filter(User.id == int(token_data.sub)).first()
        if not user:
            return None
        
        # 创建新令牌
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        new_token = self.create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires
        )
        
        # 更新会话记录
        new_token_hash = self.hash_token(new_token)
        session.token_hash = new_token_hash
        session.extend_expiry(db, days=7)
        
        return new_token
    
    def logout_user(self, db: Session, token: str) -> bool:
        """用户登出"""
        token_hash = self.hash_token(token)
        session = UserSession.get_by_token_hash(db, token_hash)
        
        if session:
            session.revoke(db)
            return True
        
        return False
    
    def logout_all_sessions(self, db: Session, user_id: int) -> int:
        """登出用户的所有会话"""
        return UserSession.revoke_all_user_sessions(db, user_id)
    
    def cleanup_expired_sessions(self, db: Session) -> int:
        """清理过期会话"""
        return UserSession.cleanup_expired(db)


# 创建全局认证服务实例
auth_service = AuthService()