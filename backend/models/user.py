"""
用户模型
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系映射
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_username(cls, db, username: str):
        """根据用户名查询用户"""
        return db.query(cls).filter(cls.username == username).first()
    
    @classmethod
    def create(cls, db, username: str, password_hash: str):
        """创建新用户"""
        user = cls(username=username, password_hash=password_hash)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def update_password(self, db, new_password_hash: str):
        """更新密码"""
        self.password_hash = new_password_hash
        db.commit()
        db.refresh(self)
        return self