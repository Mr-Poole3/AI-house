"""
异常处理模块
"""
from typing import Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthenticationError(HTTPException):
    """认证错误"""
    def __init__(self, detail: str = "认证失败"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "AUTHENTICATION_ERROR",
                "message": detail
            },
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """授权错误"""
    def __init__(self, detail: str = "权限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "AUTHORIZATION_ERROR",
                "message": detail
            }
        )


class ValidationError(HTTPException):
    """数据验证错误"""
    def __init__(self, detail: str = "数据验证失败", field: str = None):
        error_detail = {
            "error": "VALIDATION_ERROR",
            "message": detail
        }
        if field:
            error_detail["field"] = field
        
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_detail
        )


class NotFoundError(HTTPException):
    """资源不存在错误"""
    def __init__(self, detail: str = "资源不存在"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NOT_FOUND_ERROR",
                "message": detail
            }
        )


class DuplicateError(HTTPException):
    """数据重复错误"""
    def __init__(self, detail: str = "数据已存在"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DUPLICATE_ERROR",
                "message": detail
            }
        )


class FileUploadError(HTTPException):
    """文件上传错误"""
    def __init__(self, detail: str = "文件上传失败"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "FILE_UPLOAD_ERROR",
                "message": detail
            }
        )


class LLMServiceError(HTTPException):
    """大模型服务错误"""
    def __init__(self, detail: str = "大模型服务错误"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "LLM_SERVICE_ERROR",
                "message": detail
            }
        )


class DatabaseError(HTTPException):
    """数据库错误"""
    def __init__(self, detail: str = "数据库操作失败"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "DATABASE_ERROR",
                "message": detail
            }
        )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    # 确保返回统一的错误格式
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {
            "error": "HTTP_ERROR",
            "message": str(exc.detail)
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=getattr(exc, 'headers', None)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    logger.warning(f"Validation Error: {exc.errors()}")
    
    # 提取第一个验证错误的详细信息
    first_error = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "数据验证失败")
    
    content = {
        "error": "VALIDATION_ERROR",
        "message": f"字段 '{field}' {message}",
        "details": exc.errors()
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """SQLAlchemy异常处理器"""
    logger.error(f"Database Error: {str(exc)}")
    
    content = {
        "error": "DATABASE_ERROR",
        "message": "数据库操作失败"
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content
    )


async def jwt_exception_handler(request: Request, exc: JWTError):
    """JWT异常处理器"""
    logger.warning(f"JWT Error: {str(exc)}")
    
    content = {
        "error": "INVALID_TOKEN",
        "message": "无效的认证令牌"
    }
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=content,
        headers={"WWW-Authenticate": "Bearer"}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"Unexpected Error: {str(exc)}", exc_info=True)
    
    content = {
        "error": "INTERNAL_SERVER_ERROR",
        "message": "服务器内部错误"
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content
    )


def add_exception_handlers(app):
    """添加异常处理器到应用"""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(JWTError, jwt_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    return app