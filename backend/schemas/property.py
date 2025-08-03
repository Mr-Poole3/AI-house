"""
房源相关数据模式
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from enum import Enum


# 导入统一的PropertyType枚举
from ..models.property import PropertyType


class PropertyBase(BaseModel):
    """房源基础模式"""
    community_name: str = Field(..., min_length=1, max_length=100, description="小区名称")
    street_address: str = Field(..., min_length=1, max_length=200, description="街道地址")
    floor_info: Optional[str] = Field(None, max_length=50, description="楼层信息")
    price: Decimal = Field(..., gt=0, description="价格(租房为月租金，售房为总价)")
    property_type: PropertyType = Field(..., description="房屋类型")
    furniture_appliances: Optional[str] = Field(None, description="家具家电配置")
    decoration_status: Optional[str] = Field(None, max_length=100, description="装修情况")
    room_count: Optional[str] = Field(None, max_length=20, description="房间数量")
    area: Optional[Decimal] = Field(None, gt=0, description="面积(平米)")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    description: Optional[str] = Field(None, description="原始描述文本")
    parsed_confidence: Optional[Decimal] = Field(None, ge=0, le=1, description="解析置信度")

    @validator('price')
    def validate_price_range(cls, v, values):
        """验证价格范围是否合理"""
        if 'property_type' in values:
            property_type = values['property_type']
            if property_type == PropertyType.RENT:
                if not (500 <= v <= 20000):
                    raise ValueError('租房月租金应在500-20000元范围内')
            elif property_type == PropertyType.SALE:
                if not (30 <= v <= 2000):
                    raise ValueError('售房价格应在30-2000万元范围内')
        return v


class PropertyCreate(PropertyBase):
    """创建房源请求模式"""
    image_paths: Optional[List[str]] = Field(default=[], description="图片URL路径列表")


class PropertyUpdate(BaseModel):
    """更新房源请求模式"""
    community_name: Optional[str] = Field(None, min_length=1, max_length=100)
    street_address: Optional[str] = Field(None, min_length=1, max_length=200)
    floor_info: Optional[str] = Field(None, max_length=50)
    price: Optional[Decimal] = Field(None, gt=0)
    property_type: Optional[PropertyType] = None
    furniture_appliances: Optional[str] = None
    decoration_status: Optional[str] = Field(None, max_length=100)
    room_count: Optional[str] = Field(None, max_length=20)
    area: Optional[Decimal] = Field(None, gt=0)
    contact_phone: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    parsed_confidence: Optional[Decimal] = Field(None, ge=0, le=1)

    @validator('price')
    def validate_price_range(cls, v, values):
        """验证价格范围是否合理"""
        if v is not None and 'property_type' in values and values['property_type']:
            property_type = values['property_type']
            if property_type == PropertyType.RENT:
                if not (500 <= v <= 20000):
                    raise ValueError('租房月租金应在500-20000元范围内')
            elif property_type == PropertyType.SALE:
                if not (30 <= v <= 2000):
                    raise ValueError('售房价格应在30-2000万元范围内')
        return v


class PropertyImageResponse(BaseModel):
    """房源图片响应模式"""
    id: int
    file_path: str
    file_name: str
    file_size: int
    mime_type: str
    is_primary: bool
    created_at: datetime
    image_url: Optional[str] = None  # 添加image_url字段
    thumbnail_url: Optional[str] = None  # 添加缩略图URL字段

    class Config:
        from_attributes = True

    @staticmethod
    def from_orm_with_urls(obj):
        """从ORM对象创建响应，并添加URL信息"""
        import os
        data = PropertyImageResponse.from_orm(obj)
        filename = os.path.basename(obj.file_path)
        data.image_url = f"/api/upload/images/{filename}"
        data.thumbnail_url = f"/api/upload/thumbnails/{filename}"
        return data


class PropertyResponse(PropertyBase):
    """房源响应模式"""
    id: int
    created_at: datetime
    updated_at: datetime
    images: Optional[List[PropertyImageResponse]] = []

    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    """房源列表响应模式"""
    items: List[PropertyResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class PropertySearchParams(BaseModel):
    """房源搜索参数"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")
    property_type: Optional[PropertyType] = Field(None, description="房屋类型")
    community: Optional[str] = Field(None, description="小区名称")
    street: Optional[str] = Field(None, description="街道地址")
    min_price: Optional[Decimal] = Field(None, ge=0, description="最低价格")
    max_price: Optional[Decimal] = Field(None, ge=0, description="最高价格")

    @validator('max_price')
    def validate_price_range(cls, v, values):
        """验证价格范围"""
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('最高价格不能小于最低价格')
        return v


class PropertyTextRequest(BaseModel):
    """房源文本解析请求模型"""
    text: str = Field(..., min_length=1, description="房源描述文本")


class PropertyParseResponse(BaseModel):
    """房源文本解析响应模型"""
    success: bool
    parsed_data: dict
    message: str = ""
    has_warnings: bool = False
    is_fallback: bool = False