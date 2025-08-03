"""
房源管理相关API路由
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, Union
from decimal import Decimal
import logging
import os

from ..database import get_db
from ..models.property import PropertyType
from ..models.user import User
from ..schemas.property import (
    PropertyCreate, PropertyUpdate, PropertyResponse, PropertyListResponse,
    PropertySearchParams, PropertyTextRequest, PropertyParseResponse, PropertyImageResponse
)
from ..services.property_service import property_service
from ..services.llm_service import llm_service
from ..utils.dependencies import get_current_user
from ..utils.exceptions import NotFoundError, ValidationError

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/properties", tags=["properties"])

def get_username(current_user: Union[User, Dict[str, Any]]) -> str:
    """获取用户名，兼容User对象和字典格式"""
    if isinstance(current_user, User):
        return current_user.username
    elif isinstance(current_user, dict):
        return current_user.get('username', 'unknown')
    else:
        return 'unknown'


def create_property_response_with_images(property_obj) -> PropertyResponse:
    """创建包含图片URL的房源响应"""
    # 使用标准的from_orm方法
    response = PropertyResponse.from_orm(property_obj)
    
    # 为每个图片添加URL信息
    if property_obj.images:
        images_with_urls = []
        for image in property_obj.images:
            image_response = PropertyImageResponse.from_orm(image)
            filename = os.path.basename(image.file_path)
            image_response.image_url = f"/api/upload/images/{filename}"
            image_response.thumbnail_url = f"/api/upload/thumbnails/{filename}"
            images_with_urls.append(image_response)
        response.images = images_with_urls
    
    return response


# CRUD API端点

@router.post("", response_model=PropertyResponse, status_code=201)
async def create_property(
    property_data: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: Union[User, Dict[str, Any]] = Depends(get_current_user)
):
    """
    创建房源API
    
    Args:
        property_data: 房源数据
        db: 数据库会话
        current_user: 当前登录用户
        
    Returns:
        PropertyResponse: 创建的房源信息
    """
    try:
        logger.info(f"用户 {get_username(current_user)} 创建房源: {property_data.community_name}")
        
        property_obj = property_service.create_property(db, property_data)
        
        logger.info(f"房源创建成功，ID: {property_obj.id}")
        # 重新查询以确保包含图片关系
        property_with_images = property_service.get_property_by_id(db, property_obj.id)
        return create_property_response_with_images(property_with_images)
        
    except ValidationError as e:
        logger.error(f"房源创建验证失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"房源创建失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建房源失败: {str(e)}")


@router.get("", response_model=PropertyListResponse)
async def get_properties(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    property_type: Optional[str] = Query(None, description="房屋类型(rent/sale)"),
    community: Optional[str] = Query(None, description="小区名称"),
    street: Optional[str] = Query(None, description="街道地址"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="最高价格"),
    db: Session = Depends(get_db),
    current_user: Union[User, Dict[str, Any]] = Depends(get_current_user)
):
    """
    获取房源列表API，支持分页和筛选

    Args:
        page: 页码
        size: 每页数量
        property_type: 房屋类型
        community: 小区名称
        street: 街道地址
        min_price: 最低价格
        max_price: 最高价格
        db: 数据库会话
        current_user: 当前登录用户

    Returns:
        PropertyListResponse: 房源列表
    """
    try:
        logger.info(f"用户 {get_username(current_user)} 查询房源列表")
        
        # 构建搜索参数
        search_params = PropertySearchParams(
            page=page,
            size=size,
            property_type=property_type,
            community=community,
            street=street,
            min_price=min_price,
            max_price=max_price
        )
        
        properties, total = property_service.search_properties(db, search_params)
        
        # 构建响应
        property_responses = [create_property_response_with_images(prop) for prop in properties]
        
        return PropertyListResponse(
            items=property_responses,
            total=total,
            page=page,
            size=size,
            has_next=page * size < total,
            has_prev=page > 1
        )
        
    except ValidationError as e:
        logger.error(f"房源查询参数验证失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"房源查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询房源失败: {str(e)}")


# 租房/售房专门API端点 - 必须在/{property_id}之前定义

@router.get("/rent", response_model=PropertyListResponse)
async def get_rent_properties(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    community: Optional[str] = Query(None, description="小区名称"),
    street: Optional[str] = Query(None, description="街道地址"),
    min_rent: Optional[Decimal] = Query(None, ge=0, description="最低租金"),
    max_rent: Optional[Decimal] = Query(None, ge=0, description="最高租金"),
    db: Session = Depends(get_db),
    current_user: Union[User, Dict[str, Any]] = Depends(get_current_user)
):
    """
    获取租房信息专用API
    
    Args:
        page: 页码
        size: 每页数量
        community: 小区名称
        street: 街道地址
        min_rent: 最低租金
        max_rent: 最高租金
        db: 数据库会话
        current_user: 当前登录用户
        
    Returns:
        PropertyListResponse: 租房列表
    """
    try:
        logger.info(f"用户 {get_username(current_user)} 查询租房列表")
        
        properties, total = property_service.get_properties_by_type(
            db=db,
            property_type=PropertyType.RENT,
            page=page,
            size=size,
            community=community,
            street=street,
            min_price=min_rent,
            max_price=max_rent
        )
        
        property_responses = [create_property_response_with_images(prop) for prop in properties]
        
        return PropertyListResponse(
            items=property_responses,
            total=total,
            page=page,
            size=size,
            has_next=page * size < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"租房查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询租房失败: {str(e)}")


@router.get("/sale", response_model=PropertyListResponse)
async def get_sale_properties(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    community: Optional[str] = Query(None, description="小区名称"),
    street: Optional[str] = Query(None, description="街道地址"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="最低售价"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="最高售价"),
    db: Session = Depends(get_db),
    current_user: Union[User, Dict[str, Any]] = Depends(get_current_user)
):
    """
    获取售房信息专用API
    
    Args:
        page: 页码
        size: 每页数量
        community: 小区名称
        street: 街道地址
        min_price: 最低售价
        max_price: 最高售价
        db: 数据库会话
        current_user: 当前登录用户
        
    Returns:
        PropertyListResponse: 售房列表
    """
    try:
        logger.info(f"用户 {get_username(current_user)} 查询售房列表")
        
        properties, total = property_service.get_properties_by_type(
            db=db,
            property_type=PropertyType.SALE,
            page=page,
            size=size,
            community=community,
            street=street,
            min_price=min_price,
            max_price=max_price
        )
        
        property_responses = [create_property_response_with_images(prop) for prop in properties]
        
        return PropertyListResponse(
            items=property_responses,
            total=total,
            page=page,
            size=size,
            has_next=page * size < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"售房查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询售房失败: {str(e)}")


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: Union[User, Dict[str, Any]] = Depends(get_current_user)
):
    """
    获取房源详情API

    Args:
        property_id: 房源ID
        db: 数据库会话
        current_user: 当前登录用户

    Returns:
        PropertyResponse: 房源详情
    """
    try:
        logger.info(f"用户 {get_username(current_user)} 查询房源详情: {property_id}")
        
        property_obj = property_service.get_property_by_id(db, property_id)
        
        return create_property_response_with_images(property_obj)
        
    except NotFoundError as e:
        logger.error(f"房源不存在: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"房源查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询房源失败: {str(e)}")


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: Union[User, Dict[str, Any]] = Depends(get_current_user)
):
    """
    更新房源API
    
    Args:
        property_id: 房源ID
        property_data: 更新的房源数据
        db: 数据库会话
        current_user: 当前登录用户
        
    Returns:
        PropertyResponse: 更新后的房源信息
    """
    try:
        logger.info(f"用户 {get_username(current_user)} 更新房源: {property_id}")
        
        property_obj = property_service.update_property(db, property_id, property_data)
        
        logger.info(f"房源更新成功，ID: {property_id}")
        return create_property_response_with_images(property_obj)
        
    except NotFoundError as e:
        logger.error(f"房源不存在: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.error(f"房源更新验证失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"房源更新失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新房源失败: {str(e)}")


@router.delete("/{property_id}")
async def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: Union[User, Dict[str, Any]] = Depends(get_current_user)
):
    """
    删除房源API
    
    Args:
        property_id: 房源ID
        db: 数据库会话
        current_user: 当前登录用户
        
    Returns:
        dict: 删除结果
    """
    try:
        logger.info(f"用户 {get_username(current_user)} 删除房源: {property_id}")
        
        property_service.delete_property(db, property_id)
        
        logger.info(f"房源删除成功，ID: {property_id}")
        return {"message": "房源删除成功"}
        
    except NotFoundError as e:
        logger.error(f"房源不存在: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"房源删除失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除房源失败: {str(e)}")


# 文本解析API端点

@router.post("/parse", response_model=PropertyParseResponse)
async def parse_property_text(
    request: PropertyTextRequest,
    current_user: Union[User, Dict[str, Any]] = Depends(get_current_user)
):
    """
    解析房源文本API端点
    
    Args:
        request: 包含房源文本的请求
        current_user: 当前登录用户
        
    Returns:
        PropertyParseResponse: 解析结果
    """
    try:
        logger.info(f"用户 {get_username(current_user)} 请求解析房源文本")
        
        # 调用LLM服务解析文本
        parsed_result = await llm_service.parse_property_text(request.text.strip())
        
        logger.info(f"文本解析完成，类型: {parsed_result.property_type}")
        
        # 构建响应消息
        message = "文本解析成功"
        if parsed_result.is_fallback:
            message = "LLM解析失败，使用了基础规则解析，建议手动检查结果"
        elif parsed_result.validation_warnings:
            message = f"解析完成，但有 {len(parsed_result.validation_warnings)} 个验证警告"
        
        return PropertyParseResponse(
            success=True,
            parsed_data=parsed_result.dict(),
            message=message,
            has_warnings=len(parsed_result.validation_warnings) > 0,
            is_fallback=parsed_result.is_fallback
        )
        
    except Exception as e:
        logger.error(f"房源文本解析失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"文本解析失败: {str(e)}"
        )