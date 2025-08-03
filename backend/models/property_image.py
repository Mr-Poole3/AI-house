"""
房源图片模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class PropertyImage(Base):
    __tablename__ = "property_images"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False, comment="图片文件路径")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_size = Column(Integer, nullable=False, comment="文件大小(字节)")
    mime_type = Column(String(50), nullable=False, comment="MIME类型")
    is_primary = Column(Boolean, default=False, index=True, comment="是否为主图")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系映射
    property = relationship("Property", back_populates="images")
    
    def __repr__(self):
        return f"<PropertyImage(id={self.id}, property_id={self.property_id}, file_name='{self.file_name}')>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "property_id": self.property_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "is_primary": self.is_primary,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create(cls, db, property_id: int, file_path: str, file_name: str, 
               file_size: int, mime_type: str, is_primary: bool = False):
        """创建新图片记录"""
        image = cls(
            property_id=property_id,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            is_primary=is_primary
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        return image
    
    @classmethod
    def get_by_property_id(cls, db, property_id: int):
        """根据房源ID查询所有图片"""
        return db.query(cls).filter(cls.property_id == property_id).all()
    
    @classmethod
    def get_by_id(cls, db, image_id: int):
        """根据ID查询图片"""
        return db.query(cls).filter(cls.id == image_id).first()
    
    @classmethod
    def set_primary(cls, db, property_id: int, image_id: int):
        """设置主图"""
        # 先取消该房源的所有主图标记
        db.query(cls).filter(cls.property_id == property_id).update({"is_primary": False})
        
        # 设置新的主图
        image = db.query(cls).filter(cls.id == image_id, cls.property_id == property_id).first()
        if image:
            image.is_primary = True
            db.commit()
            db.refresh(image)
            return image
        return None
    
    def delete(self, db):
        """删除图片记录"""
        db.delete(self)
        db.commit()
        return True
    
    def update_file_info(self, db, file_path: str = None, file_size: int = None):
        """更新文件信息"""
        if file_path:
            self.file_path = file_path
        if file_size:
            self.file_size = file_size
        db.commit()
        db.refresh(self)
        return self