"""
数据库工具函数
"""
from sqlalchemy.orm import Session
from ..models import User, Property, PropertyImage, UserSession, PropertyType
from ..database import SessionLocal
from typing import Optional, List, Dict, Any
from datetime import datetime


class DatabaseUtils:
    """数据库工具类"""
    
    @staticmethod
    def get_db_session() -> Session:
        """获取数据库会话"""
        return SessionLocal()
    
    @staticmethod
    def get_property_statistics(db: Session) -> Dict[str, Any]:
        """获取房源统计信息"""
        total_properties = db.query(Property).count()
        rent_properties = db.query(Property).filter(Property.property_type == PropertyType.RENT).count()
        sale_properties = db.query(Property).filter(Property.property_type == PropertyType.SALE).count()
        
        # 价格统计
        rent_avg_price = db.query(Property).filter(Property.property_type == PropertyType.RENT).with_entities(
            Property.price
        ).all()
        sale_avg_price = db.query(Property).filter(Property.property_type == PropertyType.SALE).with_entities(
            Property.price
        ).all()
        
        rent_prices = [float(p.price) for p in rent_avg_price if p.price]
        sale_prices = [float(p.price) for p in sale_avg_price if p.price]
        
        return {
            "total_properties": total_properties,
            "rent_properties": rent_properties,
            "sale_properties": sale_properties,
            "rent_avg_price": sum(rent_prices) / len(rent_prices) if rent_prices else 0,
            "sale_avg_price": sum(sale_prices) / len(sale_prices) if sale_prices else 0,
            "rent_price_range": {
                "min": min(rent_prices) if rent_prices else 0,
                "max": max(rent_prices) if rent_prices else 0
            },
            "sale_price_range": {
                "min": min(sale_prices) if sale_prices else 0,
                "max": max(sale_prices) if sale_prices else 0
            }
        }
    
    @staticmethod
    def get_community_statistics(db: Session) -> List[Dict[str, Any]]:
        """获取小区统计信息"""
        from sqlalchemy import func
        
        result = db.query(
            Property.community_name,
            func.count(Property.id).label('total_count'),
            func.sum(func.case([(Property.property_type == PropertyType.RENT, 1)], else_=0)).label('rent_count'),
            func.sum(func.case([(Property.property_type == PropertyType.SALE, 1)], else_=0)).label('sale_count'),
            func.avg(func.case([(Property.property_type == PropertyType.RENT, Property.price)])).label('avg_rent'),
            func.avg(func.case([(Property.property_type == PropertyType.SALE, Property.price)])).label('avg_sale')
        ).group_by(Property.community_name).order_by(func.count(Property.id).desc()).all()
        
        return [
            {
                "community_name": row.community_name,
                "total_count": row.total_count,
                "rent_count": int(row.rent_count) if row.rent_count else 0,
                "sale_count": int(row.sale_count) if row.sale_count else 0,
                "avg_rent": float(row.avg_rent) if row.avg_rent else 0,
                "avg_sale": float(row.avg_sale) if row.avg_sale else 0
            }
            for row in result
        ]
    
    @staticmethod
    def cleanup_expired_sessions(db: Session) -> int:
        """清理过期会话"""
        return UserSession.cleanup_expired(db)
    
    @staticmethod
    def validate_property_data(property_data: Dict[str, Any]) -> List[str]:
        """验证房源数据"""
        errors = []
        
        # 必填字段检查
        required_fields = ["community_name", "street_address", "price", "property_type"]
        for field in required_fields:
            if not property_data.get(field):
                errors.append(f"字段 '{field}' 是必填的")
        
        # 价格范围检查
        if property_data.get("price"):
            price = float(property_data["price"])
            property_type = property_data.get("property_type")
            
            if property_type == "rent":
                if not (500 <= price <= 20000):
                    errors.append("租金价格应在500-20000元之间")
            elif property_type == "sale":
                if not (30 <= price <= 2000):
                    errors.append("售价应在30-2000万元之间")
        
        # 置信度检查
        if property_data.get("parsed_confidence"):
            confidence = float(property_data["parsed_confidence"])
            if not (0 <= confidence <= 1):
                errors.append("解析置信度应在0-1之间")
        
        return errors
    
    @staticmethod
    def bulk_create_properties(db: Session, properties_data: List[Dict[str, Any]]) -> List[Property]:
        """批量创建房源"""
        properties = []
        for data in properties_data:
            # 验证数据
            errors = DatabaseUtils.validate_property_data(data)
            if errors:
                continue
            
            # 创建房源
            property_obj = Property(**data)
            properties.append(property_obj)
        
        if properties:
            db.add_all(properties)
            db.commit()
            for prop in properties:
                db.refresh(prop)
        
        return properties
    
    @staticmethod
    def search_properties_advanced(
        db: Session,
        property_type: Optional[str] = None,
        community: Optional[str] = None,
        street: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
        decoration_status: Optional[str] = None,
        room_count: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[Property]:
        """高级房源搜索"""
        query = db.query(Property)
        
        # 筛选条件
        if property_type:
            query = query.filter(Property.property_type == PropertyType(property_type))
        
        if community:
            query = query.filter(Property.community_name.contains(community))
        
        if street:
            query = query.filter(Property.street_address.contains(street))
        
        if min_price is not None:
            query = query.filter(Property.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Property.price <= max_price)
        
        if min_area is not None:
            query = query.filter(Property.area >= min_area)
        
        if max_area is not None:
            query = query.filter(Property.area <= max_area)
        
        if decoration_status:
            query = query.filter(Property.decoration_status.contains(decoration_status))
        
        if room_count:
            query = query.filter(Property.room_count == room_count)
        
        # 排序
        if hasattr(Property, order_by):
            order_column = getattr(Property, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column)
        
        return query.offset(skip).limit(limit).all()