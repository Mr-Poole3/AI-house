"""
房源模型
"""
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional, List
from ..database import Base
import enum


class PropertyType(enum.Enum):
    """房屋类型枚举"""
    SALE = "sale"  # 售房
    RENT = "rent"  # 租房


class Property(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    community_name = Column(String(100), nullable=False, index=True, comment="小区名称")
    street_address = Column(String(200), nullable=False, index=True, comment="街道地址")
    floor_info = Column(String(50), comment="楼层信息")
    price = Column(DECIMAL(12, 2), nullable=False, index=True, comment="价格(租房为月租金，售房为总价)")
    property_type = Column(Enum(PropertyType), nullable=False, index=True, comment="房屋类型")
    furniture_appliances = Column(Text, comment="家具家电配置")
    decoration_status = Column(String(100), comment="装修情况")
    room_count = Column(String(20), comment="房间数量")
    area = Column(DECIMAL(8, 2), comment="面积(平米)")
    description = Column(Text, comment="原始描述文本")
    parsed_confidence = Column(DECIMAL(3, 2), comment="解析置信度")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系映射
    images = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Property(id={self.id}, community='{self.community_name}', type='{self.property_type.value}')>"
    
    def to_dict(self, include_images: bool = False):
        """转换为字典格式"""
        result = {
            "id": self.id,
            "community_name": self.community_name,
            "street_address": self.street_address,
            "floor_info": self.floor_info,
            "price": float(self.price) if self.price else None,
            "property_type": self.property_type.value,
            "furniture_appliances": self.furniture_appliances,
            "decoration_status": self.decoration_status,
            "room_count": self.room_count,
            "area": float(self.area) if self.area else None,
            "description": self.description,
            "parsed_confidence": float(self.parsed_confidence) if self.parsed_confidence else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_images:
            result["images"] = [img.to_dict() for img in self.images]
        
        return result
    
    @classmethod
    def create(cls, db, **kwargs):
        """创建新房源"""
        property_obj = cls(**kwargs)
        db.add(property_obj)
        db.commit()
        db.refresh(property_obj)
        return property_obj
    
    @classmethod
    def get_by_id(cls, db, property_id: int):
        """根据ID查询房源"""
        return db.query(cls).filter(cls.id == property_id).first()
    
    @classmethod
    def get_by_type(cls, db, property_type: PropertyType, skip: int = 0, limit: int = 20):
        """根据类型查询房源列表"""
        return db.query(cls).filter(cls.property_type == property_type).offset(skip).limit(limit).all()
    
    @classmethod
    def search(cls, db, property_type: Optional[PropertyType] = None, 
               community: Optional[str] = None, street: Optional[str] = None,
               min_price: Optional[float] = None, max_price: Optional[float] = None,
               skip: int = 0, limit: int = 20):
        """搜索房源"""
        query = db.query(cls)
        
        if property_type:
            query = query.filter(cls.property_type == property_type)
        
        if community:
            query = query.filter(cls.community_name.contains(community))
        
        if street:
            query = query.filter(cls.street_address.contains(street))
        
        if min_price is not None:
            query = query.filter(cls.price >= min_price)
        
        if max_price is not None:
            query = query.filter(cls.price <= max_price)
        
        return query.offset(skip).limit(limit).all()
    
    @classmethod
    def count_by_type(cls, db, property_type: Optional[PropertyType] = None):
        """统计房源数量"""
        query = db.query(cls)
        if property_type:
            query = query.filter(cls.property_type == property_type)
        return query.count()
    
    def update(self, db, **kwargs):
        """更新房源信息"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.commit()
        db.refresh(self)
        return self
    
    def delete(self, db):
        """删除房源"""
        db.delete(self)
        db.commit()
        return True
    
    def get_primary_image(self):
        """获取主图"""
        for image in self.images:
            if image.is_primary:
                return image
        return self.images[0] if self.images else None