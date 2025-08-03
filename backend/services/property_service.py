"""
房源业务逻辑服务
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from decimal import Decimal
import os

from ..models.property import Property, PropertyType
from ..models.property_image import PropertyImage
from ..schemas.property import PropertyCreate, PropertyUpdate, PropertySearchParams
from ..utils.exceptions import NotFoundError, ValidationError


class PropertyService:
    """房源服务类"""
    
    @staticmethod
    def create_property(db: Session, property_data: PropertyCreate) -> Property:
        """创建房源"""
        try:
            # 转换PropertyType枚举 - 如果已经是枚举类型就直接使用，如果是字符串则转换
            if isinstance(property_data.property_type, PropertyType):
                property_type = property_data.property_type
            else:
                property_type = PropertyType(property_data.property_type)
            
            # 提取图片路径
            image_paths = property_data.image_paths or []
            
            # 创建房源数据字典（排除image_paths）
            property_dict = property_data.dict(exclude={'image_paths'})
            property_dict['property_type'] = property_type
            
            # 创建房源
            property_obj = Property.create(db, **property_dict)
            
            # 如果有图片路径，创建图片关联
            if image_paths:
                PropertyService._associate_images_to_property(db, property_obj.id, image_paths)
            
            # 重新加载房源以包含图片信息
            db.refresh(property_obj)
            return property_obj
            
        except Exception as e:
            db.rollback()
            raise ValidationError(f"创建房源失败: {str(e)}")
    
    @staticmethod
    def _associate_images_to_property(db: Session, property_id: int, image_paths: List[str]) -> None:
        """将图片关联到房源"""
        for i, image_path in enumerate(image_paths):
            try:
                # 从URL中提取文件名
                if image_path.startswith('/api/upload/images/'):
                    filename = image_path.replace('/api/upload/images/', '')
                else:
                    filename = os.path.basename(image_path)
                
                # 构建文件路径
                file_path = f"uploads/{filename}"
                full_path = os.path.join(os.getcwd(), file_path)
                
                # 验证文件是否存在
                if not os.path.exists(full_path):
                    print(f"警告: 图片文件不存在: {full_path}")
                    continue
                
                # 获取文件信息
                file_size = os.path.getsize(full_path)
                file_extension = filename.lower().split('.')[-1] if '.' in filename else 'jpg'
                mime_type = f"image/{file_extension}"
                
                # 创建图片记录
                PropertyImage.create(
                    db=db,
                    property_id=property_id,
                    file_path=file_path,
                    file_name=filename,
                    file_size=file_size,
                    mime_type=mime_type,
                    is_primary=(i == 0)  # 第一张图片设为主图
                )
                
            except Exception as e:
                print(f"关联图片失败 {image_path}: {str(e)}")
                continue
    
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
                    # 转换PropertyType枚举 - 如果已经是枚举类型就直接使用，如果是字符串则转换
                    if isinstance(value, PropertyType):
                        update_data[field] = value
                    else:
                        update_data[field] = PropertyType(value)
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
            if isinstance(search_params.property_type, PropertyType):
                property_type = search_params.property_type
            else:
                property_type = PropertyType(search_params.property_type)
        
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