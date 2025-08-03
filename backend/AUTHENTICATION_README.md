# 认证和安全系统实现文档

## 概述

本文档描述了房屋中介管理系统的认证和安全系统实现，包括用户认证、会话管理、安全防护机制等功能。

## 已实现功能

### 3.1 用户认证服务

#### 核心组件
- **AuthService** (`backend/services/auth_service.py`): 核心认证服务类
- **认证路由** (`backend/routers/auth.py`): 提供认证相关的API端点
- **认证模式** (`backend/schemas/auth.py`): 定义请求和响应的数据结构

#### 主要功能
1. **JWT令牌管理**
   - 创建访问令牌 (7天有效期)
   - 令牌验证和解析
   - 令牌刷新机制

2. **用户身份验证**
   - 用户名密码验证
   - 密码哈希存储 (bcrypt)
   - 会话管理

3. **API端点**
   - `POST /api/auth/login` - 用户登录
   - `POST /api/auth/refresh` - 刷新令牌
   - `POST /api/auth/logout` - 用户登出
   - `POST /api/auth/logout-all` - 登出所有会话
   - `GET /api/auth/me` - 获取当前用户信息
   - `POST /api/auth/cleanup-sessions` - 清理过期会话

### 3.2 安全防护机制

#### 核心组件
- **安全工具** (`backend/utils/security.py`): 速率限制、密码策略等
- **安全中间件** (`backend/middleware/security.py`): 请求安全处理
- **异常处理** (`backend/utils/exceptions.py`): 统一错误处理
- **依赖注入** (`backend/utils/dependencies.py`): 认证依赖

#### 主要功能
1. **速率限制**
   - IP级别的登录尝试限制 (5次/15分钟)
   - 失败后自动锁定 (30分钟)
   - 不同API端点的独立速率限制

2. **密码安全**
   - bcrypt哈希算法
   - 密码策略验证
   - 弱密码检测

3. **会话安全**
   - 会话令牌哈希存储
   - 自动过期清理
   - 并发会话限制

4. **安全中间件**
   - 安全HTTP头部添加
   - 请求大小限制
   - 请求方法验证
   - 请求日志记录

5. **认证中间件**
   - 自动保护指定路径
   - 令牌验证
   - 用户信息注入

## 安全特性

### 防护机制
- **防暴力破解**: 登录失败次数限制和IP锁定
- **令牌安全**: JWT令牌哈希存储，防止令牌泄露
- **会话管理**: 自动过期和清理机制
- **输入验证**: 请求数据验证和清理
- **错误处理**: 统一的错误响应格式

### 安全头部
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

## 使用方法

### 1. 创建测试用户
```bash
cd backend
python create_test_user.py
```

### 2. 启动服务器
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 测试认证系统
```bash
cd backend
python test_auth.py
```

### 4. API使用示例

#### 登录
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

#### 访问受保护端点
```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 配置说明

### 环境变量 (.env)
```env
# JWT配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7天

# 数据库配置
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/real_estate_db
```

### 速率限制配置
可在 `backend/middleware/security.py` 中的 `RateLimitMiddleware` 类中调整:
- 登录端点: 5次/5分钟
- 刷新端点: 10次/分钟
- 房源API: 100次/分钟
- 上传API: 20次/分钟

## 数据库表

### users 表
- 存储用户基本信息和密码哈希

### user_sessions 表
- 存储用户会话信息和令牌哈希
- 支持会话过期和清理

## 错误处理

系统提供统一的错误响应格式:
```json
{
  "error": "ERROR_CODE",
  "message": "错误描述",
  "details": "详细信息(可选)"
}
```

常见错误码:
- `AUTHENTICATION_ERROR`: 认证失败
- `AUTHORIZATION_ERROR`: 权限不足
- `VALIDATION_ERROR`: 数据验证错误
- `RATE_LIMIT_EXCEEDED`: 速率限制超出
- `INVALID_TOKEN`: 无效令牌

## 性能考虑

- 使用内存缓存进行速率限制 (生产环境建议使用Redis)
- JWT令牌无状态设计，减少数据库查询
- 定期清理过期会话，保持数据库性能
- 异步处理，支持高并发

## 安全建议

1. **生产环境配置**
   - 更改默认的SECRET_KEY
   - 使用HTTPS协议
   - 配置防火墙和反向代理

2. **监控和日志**
   - 监控登录失败次数
   - 记录安全相关事件
   - 定期审查用户会话

3. **定期维护**
   - 定期清理过期会话
   - 更新依赖包
   - 安全漏洞扫描

## 扩展功能

未来可以考虑添加的功能:
- 双因素认证 (2FA)
- OAuth2集成
- 用户角色和权限管理
- 设备管理和信任设备
- 地理位置验证
- 审计日志