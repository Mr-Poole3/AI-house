"""
房源业务逻辑服务
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from decimal import Decimal

from ..models.property import Property, PropertyType
from ..schemas.property import PropertyCreate, PropertyUpdate, PropertySearchParams
from ..utils.exceptions import NotFoundError, ValidationError


class PropertyService:
    """房源服务类"""
    
    @staticmethod
    def create_property(db: Session, property_data: PropertyCreate) -> Property:
        """创建房源"""
        try:
            # 转换PropertyType枚举
            property_type = PropertyType(property_data.property_type.value)
            
            # 创建房源数据字典
            property_dict = property_data.dict()
            property_dict['property_type'] = property_type
            
            # 创建房源
            property_obj = Property.create(db, **property_dict)
            return property_obj
            
        except Exception as e:
            raise ValidationError(f"创建房源失败: {str(e)}")
    
    @staticmethod
    def get_property_by_id(db: Session, property_id: int) -> Property:
        """根据ID获取房源"""
        property_obj = Property.get_by_id(db, property_id)
        if not property_obj:
            raise NotFoundError(f"房源ID {property_id} 不存在")
        return property_obj
    
    @staticmethod
    def update_property(db: Session, property_id: int, property_data: PropertyUpdate) -> Property:
        """更新房源"""
        property_obj = PropertyService.get_property_by_id(db, property_id)
        
        # 只更新非空字段
        update_data = {}
        for field, value in property_data.dict(exclude_unset=True).items():
            if value is not None:
                if field == 'property_type':
                    update_data[field] = PropertyType(value.value)
                else:
                    update_data[field] = value
        
        if update_data:
            property_obj.update(db, **update_data)
        
        return property_obj
    
    @staticmethod
    def delete_property(db: Session, property_id: int) -> bool:
        """删除房源"""
        property_obj = PropertyService.get_property_by_id(db, property_id)
        return property_obj.delete(db)
    
    @staticmethod
    def search_properties(db: Session, search_params: PropertySearchParams) -> Tuple[List[Property], int]:
        """搜索房源"""
        # 转换PropertyType枚举
        property_type = None
        if search_params.property_type:
            property_type = PropertyType(search_params.property_type.value)
        
        # 计算偏移量
        skip = (search_params.page - 1) * search_params.size
        
        # 搜索房源
        properties = Property.search(
            db=db,
            property_type=property_type,
            community=search_params.community,
            street=search_params.street,
            min_price=search_params.min_price,
            max_price=search_params.max_price,
            skip=skip,
            limit=search_params.size
        )
        
        # 获取总数
        total = PropertyService._count_properties(
            db=db,
            property_type=property_type,
            community=search_params.community,
            street=search_params.street,
            min_price=search_params.min_price,
            max_price=search_params.max_price
        )
        
        return properties, total
    
    @staticmethod
    def get_properties_by_type(db: Session, property_type: PropertyType, 
                              page: int = 1, size: int = 20,
                              community: Optional[str] = None,
                              street: Optional[str] = None,
                              min_price: Optional[Decimal] = None,
                              max_price: Optional[Decimal] = None) -> Tuple[List[Property], int]:
        """根据类型获取房源列表"""
        skip = (page - 1) * size
        
        properties = Property.search(
            db=db,
            property_type=property_type,
            community=community,
            street=street,
            min_price=min_price,
            max_price=max_price,
            skip=skip,
            limit=size
        )
        
        total = PropertyService._count_properties(
            db=db,
            property_type=property_type,
            community=community,
            street=street,
            min_price=min_price,
            max_price=max_price
        )
        
        return properties, total
    
    @staticmethod
    def _count_properties(db: Session, property_type: Optional[PropertyType] = None,
                         community: Optional[str] = None,
                         street: Optional[str] = None,
                         min_price: Optional[Decimal] = None,
                         max_price: Optional[Decimal] = None) -> int:
        """统计符合条件的房源数量"""
        query = db.query(Property)
        
        if property_type:
            query = query.filter(Property.property_type == property_type)
        
        if community:
            query = query.filter(Property.community_name.contains(community))
        
        if street:
            query = query.filter(Property.street_address.contains(street))
        
        if min_price is not None:
            query = query.filter(Property.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Property.price <= max_price)
        
        return query.count()


# 创建服务实例
property_service = PropertyService()