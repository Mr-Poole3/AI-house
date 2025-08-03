"""
安全中间件
"""
import time
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

from ..utils.security import rate_limiter, SecurityUtils


class SecurityMiddleware:
    """安全中间件类"""
    
    def __init__(self, app: Callable):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """ASGI中间件入口"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # 添加安全头部
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # 添加安全头部
                security_headers = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"x-xss-protection": b"1; mode=block",
                    b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"permissions-policy": b"geolocation=(), microphone=(), camera=()"
                }
                
                for key, value in security_headers.items():
                    headers[key] = value
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        # 检查请求大小限制
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 50 * 1024 * 1024:  # 50MB限制
            response = JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "REQUEST_TOO_LARGE",
                    "message": "请求体过大"
                }
            )
            await response(scope, receive, send)
            return
        
        # 检查请求方法
        if request.method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]:
            response = JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content={
                    "error": "METHOD_NOT_ALLOWED",
                    "message": "不支持的HTTP方法"
                }
            )
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send_wrapper)


class RateLimitMiddleware:
    """速率限制中间件"""
    
    def __init__(self, app: Callable):
        self.app = app
        # 不同端点的速率限制配置
        self.rate_limits = {
            "/api/auth/login": {"max_requests": 5, "window_seconds": 300},  # 登录: 5次/5分钟
            "/api/auth/refresh": {"max_requests": 10, "window_seconds": 60},  # 刷新: 10次/分钟
            "/api/properties": {"max_requests": 100, "window_seconds": 60},  # 房源API: 100次/分钟
            "/api/upload": {"max_requests": 100, "window_seconds": 60},  # 上传: 100次/分钟
        }
        # 存储请求计数
        self.request_counts = {}
    
    def get_rate_limit_key(self, ip: str, path: str) -> str:
        """生成速率限制键"""
        return f"{ip}:{path}"
    
    def is_rate_limited(self, ip: str, path: str) -> tuple[bool, int]:
        """检查是否超过速率限制"""
        # 查找匹配的路径配置
        rate_config = None
        for pattern, config in self.rate_limits.items():
            if path.startswith(pattern):
                rate_config = config
                break
        
        if not rate_config:
            return False, 0
        
        key = self.get_rate_limit_key(ip, path)
        now = time.time()
        window_start = now - rate_config["window_seconds"]
        
        # 清理过期的请求记录
        if key in self.request_counts:
            self.request_counts[key] = [
                timestamp for timestamp in self.request_counts[key]
                if timestamp > window_start
            ]
        else:
            self.request_counts[key] = []
        
        # 检查是否超过限制
        current_count = len(self.request_counts[key])
        if current_count >= rate_config["max_requests"]:
            # 计算重试时间
            oldest_request = min(self.request_counts[key])
            retry_after = int(oldest_request + rate_config["window_seconds"] - now)
            return True, max(retry_after, 1)
        
        # 记录当前请求
        self.request_counts[key].append(now)
        return False, 0
    
    async def __call__(self, scope, receive, send):
        """ASGI中间件入口"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        client_ip = SecurityUtils.get_client_ip(request)
        path = request.url.path
        
        # 跳过静态文件和文档
        if path.startswith("/static/") or path in ["/docs", "/redoc", "/openapi.json"]:
            await self.app(scope, receive, send)
            return
        
        # 检查速率限制
        is_limited, retry_after = self.is_rate_limited(client_ip, path)
        if is_limited:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"请求过于频繁，请在 {retry_after} 秒后重试",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send)


class RequestLoggingMiddleware:
    """请求日志中间件"""
    
    def __init__(self, app: Callable):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """ASGI中间件入口"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        # 记录请求信息
        client_ip = SecurityUtils.get_client_ip(request)
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        
        # 包装send函数以捕获响应状态
        response_status = None
        
        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            response_status = 500
            raise
        finally:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录日志(这里可以集成真正的日志系统)
            log_data = {
                "timestamp": time.time(),
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "status": response_status,
                "process_time": round(process_time, 3),
                "user_agent": user_agent
            }
            
            # 简单的控制台日志(生产环境应该使用专业的日志系统)
            if response_status and response_status >= 400:
                print(f"[ERROR] {client_ip} {method} {path} - {response_status} ({process_time:.3f}s)")
            elif path not in ["/health", "/"]:  # 跳过健康检查日志
                print(f"[INFO] {client_ip} {method} {path} - {response_status} ({process_time:.3f}s)")


def add_security_middleware(app):
    """添加所有安全中间件到应用"""
    # 注意：中间件的添加顺序很重要，后添加的先执行
    
    # 1. 请求日志中间件(最外层)
    app.add_middleware(RequestLoggingMiddleware)
    
    # 2. 速率限制中间件
    app.add_middleware(RateLimitMiddleware)
    
    # 3. 安全头部中间件
    app.add_middleware(SecurityMiddleware)
    
    return app