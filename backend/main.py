# FastAPI应用入口
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, properties, upload
from .utils.dependencies import create_auth_middleware
from .middleware.security import add_security_middleware
from .utils.exceptions import add_exception_handlers

app = FastAPI(
    title="房屋中介管理系统", 
    version="1.0.0",
    description="基于AI的房屋中介管理系统API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加异常处理器
add_exception_handlers(app)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加安全中间件(包括速率限制、安全头部、请求日志)
add_security_middleware(app)

# 暂时禁用认证中间件进行调试
# protected_paths = ["/api/properties", "/api/upload"]
# auth_middleware = create_auth_middleware(protected_paths)
# app.middleware("http")(auth_middleware)

# 注册路由
app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(upload.router)

@app.get("/", tags=["系统"])
async def root():
    """系统根端点"""
    return {"message": "房屋中介管理系统API", "version": "1.0.0"}

@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}