"""
用户会话模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from ..database import Base


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True, comment="JWT令牌哈希")
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True, comment="过期时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系映射
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at='{self.expires_at}')>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token_hash": self.token_hash,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_expired": self.is_expired()
        }
    
    def is_expired(self):
        """检查会话是否过期"""
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def create(cls, db, user_id: int, token_hash: str, expires_in_days: int = 7):
        """创建新会话"""
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        session = cls(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @classmethod
    def get_by_token_hash(cls, db, token_hash: str):
        """根据令牌哈希查询会话"""
        return db.query(cls).filter(cls.token_hash == token_hash).first()
    
    @classmethod
    def get_active_by_user_id(cls, db, user_id: int):
        """获取用户的活跃会话"""
        now = datetime.utcnow()
        return db.query(cls).filter(
            cls.user_id == user_id,
            cls.expires_at > now
        ).all()
    
    @classmethod
    def cleanup_expired(cls, db):
        """清理过期会话"""
        now = datetime.utcnow()
        expired_count = db.query(cls).filter(cls.expires_at <= now).count()
        db.query(cls).filter(cls.expires_at <= now).delete()
        db.commit()
        return expired_count
    
    def extend_expiry(self, db, days: int = 7):
        """延长会话有效期"""
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        db.commit()
        db.refresh(self)
        return self
    
    def revoke(self, db):
        """撤销会话"""
        db.delete(self)
        db.commit()
        return True
    
    @classmethod
    def revoke_all_user_sessions(cls, db, user_id: int):
        """撤销用户的所有会话"""
        count = db.query(cls).filter(cls.user_id == user_id).count()
        db.query(cls).filter(cls.user_id == user_id).delete()
        db.commit()
        return count