"""
文件上传路由
"""
import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from PIL import Image, ImageOps

from ..config import settings
from ..utils.dependencies import get_db
from ..models.property_image import PropertyImage
from ..models.property import Property
from ..utils.exceptions import FileUploadError, ValidationError, NotFoundError

router = APIRouter(prefix="/api/upload", tags=["文件上传"])

# 允许的文件类型
ALLOWED_MIME_TYPES = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg", 
    "image/png": "png"
}

def validate_image_file(file: UploadFile) -> None:
    """验证上传的图片文件"""
    # 检查文件类型
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"不支持的文件类型: {file.content_type}. 仅支持: {', '.join(ALLOWED_MIME_TYPES.keys())}"
        )
    
    # 检查文件扩展名
    file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    allowed_extensions = settings.ALLOWED_EXTENSIONS.split(',')
    if file_extension not in allowed_extensions:
        raise ValidationError(
            f"不支持的文件扩展名: {file_extension}. 仅支持: {', '.join(allowed_extensions)}"
        )

def generate_unique_filename(original_filename: str) -> str:
    """生成唯一的文件名"""
    file_extension = original_filename.lower().split('.')[-1] if '.' in original_filename else 'jpg'
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{file_extension}"

def ensure_upload_directory():
    """确保上传目录存在"""
    upload_path = os.path.join(os.getcwd(), settings.UPLOAD_DIR)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path, exist_ok=True)
    
    # 确保缩略图目录存在
    thumbnail_path = os.path.join(upload_path, "thumbnails")
    if not os.path.exists(thumbnail_path):
        os.makedirs(thumbnail_path, exist_ok=True)
    
    return upload_path

def generate_thumbnail(image_path: str, thumbnail_size: tuple = (200, 200)) -> str:
    """生成缩略图"""
    try:
        # 打开原图
        with Image.open(image_path) as img:
            # 转换为RGB模式（处理RGBA等格式）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 生成缩略图（保持比例）
            img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # 生成缩略图文件名
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            thumbnail_filename = f"{name}_thumb{ext}"
            
            # 缩略图保存路径
            thumbnail_dir = os.path.join(os.path.dirname(image_path), "thumbnails")
            thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
            
            # 保存缩略图
            img.save(thumbnail_path, 'JPEG', quality=85)
            
            return os.path.join("thumbnails", thumbnail_filename)
    
    except Exception as e:
        print(f"生成缩略图失败: {e}")
        return None

def cleanup_image_files(file_path: str):
    """清理图片文件（包括缩略图）"""
    try:
        # 删除原图
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
        
        # 删除缩略图
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        thumbnail_filename = f"{name}_thumb{ext}"
        thumbnail_path = os.path.join(os.getcwd(), settings.UPLOAD_DIR, "thumbnails", thumbnail_filename)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        
        return True
    except Exception as e:
        print(f"清理文件失败: {e}")
        return False

@router.post("/images", summary="上传图片文件")
async def upload_images(
    files: List[UploadFile] = File(..., description="要上传的图片文件列表"),
    db: Session = Depends(get_db)
):
    """
    上传多个图片文件
    
    - **files**: 图片文件列表 (支持JPG、PNG格式)
    - 返回上传成功的文件信息列表
    """
    if not files:
        raise ValidationError("请选择要上传的文件")
    
    if len(files) > 10:  # 限制单次上传文件数量
        raise ValidationError("单次最多上传10个文件")
    
    uploaded_files = []
    upload_dir = ensure_upload_directory()
    
    try:
        for file in files:
            # 验证文件
            validate_image_file(file)
            
            # 检查文件大小
            file_content = await file.read()
            if len(file_content) > settings.MAX_FILE_SIZE:
                raise ValidationError(
                    f"文件 {file.filename} 大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
                )
            
            # 生成唯一文件名
            unique_filename = generate_unique_filename(file.filename)
            file_path = os.path.join(upload_dir, unique_filename)
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            
            # 构建相对路径用于存储
            relative_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
            
            # 生成缩略图
            thumbnail_path = generate_thumbnail(file_path)
            
            uploaded_files.append({
                "original_filename": file.filename,
                "saved_filename": unique_filename,
                "file_path": relative_path,
                "file_size": len(file_content),
                "mime_type": file.content_type,
                "url": f"/api/upload/images/{unique_filename}",
                "thumbnail_url": f"/api/upload/thumbnails/{unique_filename}" if thumbnail_path else None
            })
            
            # 重置文件指针以便后续处理
            await file.seek(0)
    
    except Exception as e:
        # 清理已上传的文件
        for uploaded_file in uploaded_files:
            try:
                cleanup_image_files(uploaded_file["file_path"])
            except:
                pass
        
        if isinstance(e, (ValidationError, FileUploadError)):
            raise e
        else:
            raise FileUploadError(f"文件上传失败: {str(e)}")
    
    return {
        "message": f"成功上传 {len(uploaded_files)} 个文件",
        "uploaded_files": uploaded_files
    }

@router.get("/images/{filename}", summary="获取图片文件")
async def get_image(filename: str):
    """
    获取上传的图片文件
    
    - **filename**: 图片文件名
    """
    file_path = os.path.join(os.getcwd(), settings.UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片文件不存在"
        )
    
    # 验证文件扩展名安全性
    allowed_extensions = settings.ALLOWED_EXTENSIONS.split(',')
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型"
        )
    
    return FileResponse(
        path=file_path,
        media_type=f"image/{file_extension}",
        filename=filename
    )

@router.get("/thumbnails/{filename}", summary="获取缩略图")
async def get_thumbnail(filename: str):
    """
    获取图片缩略图
    
    - **filename**: 图片文件名
    """
    # 生成缩略图文件名
    name, ext = os.path.splitext(filename)
    thumbnail_filename = f"{name}_thumb{ext}"
    thumbnail_path = os.path.join(os.getcwd(), settings.UPLOAD_DIR, "thumbnails", thumbnail_filename)
    
    if not os.path.exists(thumbnail_path):
        # 如果缩略图不存在，尝试从原图生成
        original_path = os.path.join(os.getcwd(), settings.UPLOAD_DIR, filename)
        if os.path.exists(original_path):
            thumbnail_relative = generate_thumbnail(original_path)
            if thumbnail_relative:
                thumbnail_path = os.path.join(os.getcwd(), settings.UPLOAD_DIR, thumbnail_relative)
        
        if not os.path.exists(thumbnail_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="缩略图不存在"
            )
    
    # 验证文件扩展名安全性
    allowed_extensions = settings.ALLOWED_EXTENSIONS.split(',')
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型"
        )
    
    return FileResponse(
        path=thumbnail_path,
        media_type=f"image/{file_extension}",
        filename=thumbnail_filename
    )

@router.delete("/images/{filename}", summary="删除图片文件")
async def delete_image(
    filename: str,
    db: Session = Depends(get_db)
):
    """
    删除图片文件
    
    - **filename**: 要删除的图片文件名
    """
    file_path = os.path.join(os.getcwd(), settings.UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片文件不存在"
        )
    
    try:
        # 删除数据库中的相关记录
        relative_path = os.path.join(settings.UPLOAD_DIR, filename)
        images = db.query(PropertyImage).filter(PropertyImage.file_path == relative_path).all()
        for image in images:
            db.delete(image)
        
        # 删除物理文件（包括缩略图）
        cleanup_image_files(relative_path)
        
        db.commit()
        
        return {"message": f"成功删除图片文件: {filename}"}
    
    except Exception as e:
        db.rollback()
        raise FileUploadError(f"删除图片文件失败: {str(e)}")

@router.post("/images/associate/{property_id}", summary="关联图片到房源")
async def associate_images_to_property(
    property_id: int,
    file_paths: List[str],
    db: Session = Depends(get_db)
):
    """
    将上传的图片关联到指定房源
    
    - **property_id**: 房源ID
    - **file_paths**: 图片文件路径列表
    """
    try:
        created_images = []
        
        for i, file_path in enumerate(file_paths):
            # 验证文件是否存在
            full_path = os.path.join(os.getcwd(), file_path)
            if not os.path.exists(full_path):
                raise ValidationError(f"图片文件不存在: {file_path}")
            
            # 获取文件信息
            file_size = os.path.getsize(full_path)
            filename = os.path.basename(file_path)
            file_extension = filename.lower().split('.')[-1] if '.' in filename else 'jpg'
            mime_type = f"image/{file_extension}"
            
            # 创建图片记录
            image = PropertyImage.create(
                db=db,
                property_id=property_id,
                file_path=file_path,
                file_name=filename,
                file_size=file_size,
                mime_type=mime_type,
                is_primary=(i == 0)  # 第一张图片设为主图
            )
            
            created_images.append(image.to_dict())
        
        return {
            "message": f"成功关联 {len(created_images)} 张图片到房源",
            "images": created_images
        }
    
    except Exception as e:
        db.rollback()
        if isinstance(e, ValidationError):
            raise e
        else:
            raise FileUploadError(f"关联图片失败: {str(e)}")

@router.get("/properties/{property_id}/images", summary="获取房源的所有图片")
async def get_property_images(
    property_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定房源的所有图片
    
    - **property_id**: 房源ID
    """
    # 验证房源是否存在
    property_obj = Property.get_by_id(db, property_id)
    if not property_obj:
        raise NotFoundError("房源不存在")
    
    images = PropertyImage.get_by_property_id(db, property_id)
    
    # 为每个图片添加URL信息
    image_list = []
    for image in images:
        image_dict = image.to_dict()
        filename = os.path.basename(image.file_path)
        image_dict["url"] = f"/api/upload/images/{filename}"
        image_dict["thumbnail_url"] = f"/api/upload/thumbnails/{filename}"
        image_list.append(image_dict)
    
    return {
        "property_id": property_id,
        "images": image_list,
        "total": len(image_list)
    }

@router.put("/properties/{property_id}/images/{image_id}/primary", summary="设置主图")
async def set_primary_image(
    property_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    设置房源的主图
    
    - **property_id**: 房源ID
    - **image_id**: 图片ID
    """
    # 验证房源是否存在
    property_obj = Property.get_by_id(db, property_id)
    if not property_obj:
        raise NotFoundError("房源不存在")
    
    # 设置主图
    image = PropertyImage.set_primary(db, property_id, image_id)
    if not image:
        raise NotFoundError("图片不存在或不属于该房源")
    
    return {
        "message": "主图设置成功",
        "image": image.to_dict()
    }

@router.delete("/properties/{property_id}/images/{image_id}", summary="删除房源图片")
async def delete_property_image(
    property_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    删除房源的指定图片
    
    - **property_id**: 房源ID
    - **image_id**: 图片ID
    """
    # 验证房源是否存在
    property_obj = Property.get_by_id(db, property_id)
    if not property_obj:
        raise NotFoundError("房源不存在")
    
    # 查找图片
    image = PropertyImage.get_by_id(db, image_id)
    if not image or image.property_id != property_id:
        raise NotFoundError("图片不存在或不属于该房源")
    
    try:
        # 删除物理文件
        cleanup_image_files(image.file_path)
        
        # 删除数据库记录
        image.delete(db)
        
        return {"message": "图片删除成功"}
    
    except Exception as e:
        db.rollback()
        raise FileUploadError(f"删除图片失败: {str(e)}")

@router.post("/properties/{property_id}/images/upload", summary="直接上传并关联图片到房源")
async def upload_and_associate_images(
    property_id: int,
    files: List[UploadFile] = File(..., description="要上传的图片文件列表"),
    db: Session = Depends(get_db)
):
    """
    直接上传图片并关联到指定房源
    
    - **property_id**: 房源ID
    - **files**: 图片文件列表
    """
    # 验证房源是否存在
    property_obj = Property.get_by_id(db, property_id)
    if not property_obj:
        raise NotFoundError("房源不存在")
    
    # 先上传文件
    upload_result = await upload_images(files, db)
    uploaded_files = upload_result["uploaded_files"]
    
    try:
        # 关联到房源
        created_images = []
        existing_images_count = len(PropertyImage.get_by_property_id(db, property_id))
        
        for i, uploaded_file in enumerate(uploaded_files):
            image = PropertyImage.create(
                db=db,
                property_id=property_id,
                file_path=uploaded_file["file_path"],
                file_name=uploaded_file["original_filename"],
                file_size=uploaded_file["file_size"],
                mime_type=uploaded_file["mime_type"],
                is_primary=(existing_images_count == 0 and i == 0)  # 如果是第一张图片且房源没有其他图片，设为主图
            )
            
            image_dict = image.to_dict()
            filename = os.path.basename(image.file_path)
            image_dict["url"] = f"/api/upload/images/{filename}"
            image_dict["thumbnail_url"] = f"/api/upload/thumbnails/{filename}"
            created_images.append(image_dict)
        
        return {
            "message": f"成功上传并关联 {len(created_images)} 张图片到房源",
            "property_id": property_id,
            "images": created_images
        }
    
    except Exception as e:
        # 如果关联失败，清理上传的文件
        for uploaded_file in uploaded_files:
            try:
                cleanup_image_files(uploaded_file["file_path"])
            except:
                pass
        
        db.rollback()
        raise FileUploadError(f"关联图片到房源失败: {str(e)}")

@router.get("/images/orphaned", summary="获取未关联的图片")
async def get_orphaned_images(db: Session = Depends(get_db)):
    """
    获取所有未关联到房源的图片文件
    """
    # 获取上传目录中的所有图片文件
    upload_dir = os.path.join(os.getcwd(), settings.UPLOAD_DIR)
    if not os.path.exists(upload_dir):
        return {"orphaned_images": []}
    
    # 获取数据库中所有图片记录
    db_images = db.query(PropertyImage).all()
    db_file_paths = {os.path.basename(img.file_path) for img in db_images}
    
    # 查找孤立文件
    orphaned_files = []
    for filename in os.listdir(upload_dir):
        if filename.startswith('.') or filename == 'thumbnails':
            continue
        
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path) and filename not in db_file_paths:
            file_size = os.path.getsize(file_path)
            orphaned_files.append({
                "filename": filename,
                "file_path": os.path.join(settings.UPLOAD_DIR, filename),
                "file_size": file_size,
                "url": f"/api/upload/images/{filename}",
                "thumbnail_url": f"/api/upload/thumbnails/{filename}"
            })
    
    return {
        "orphaned_images": orphaned_files,
        "total": len(orphaned_files)
    }

@router.delete("/images/cleanup", summary="清理孤立图片文件")
async def cleanup_orphaned_images(db: Session = Depends(get_db)):
    """
    清理所有未关联到房源的图片文件
    """
    orphaned_result = await get_orphaned_images(db)
    orphaned_files = orphaned_result["orphaned_images"]
    
    cleaned_count = 0
    for file_info in orphaned_files:
        try:
            cleanup_image_files(file_info["file_path"])
            cleaned_count += 1
        except Exception as e:
            print(f"清理文件失败 {file_info['filename']}: {e}")
    
    return {
        "message": f"成功清理 {cleaned_count} 个孤立图片文件",
        "cleaned_count": cleaned_count,
        "total_found": len(orphaned_files)
    }