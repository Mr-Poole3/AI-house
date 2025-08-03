# 房屋中介管理系统

基于React + FastAPI的房屋中介管理系统，集成豆包大模型进行房源文本智能解析。

## 项目结构

```
├── backend/                 # 后端API服务
│   ├── main.py             # FastAPI应用入口
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库连接
│   ├── requirements.txt    # Python依赖
│   ├── models/             # 数据模型
│   ├── schemas/            # 数据模式
│   ├── services/           # 业务逻辑
│   ├── routers/            # API路由
│   └── utils/              # 工具函数
├── frontend/               # 前端React应用
│   ├── public/             # 静态文件
│   ├── src/                # 源代码
│   │   ├── components/     # React组件
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API服务
│   │   └── utils/          # 工具函数
│   └── package.json        # 前端依赖
├── .env.example            # 环境变量示例
└── README.md               # 项目说明
```

## 开发环境设置

### 后端设置

1. 创建Python虚拟环境：
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp ../.env.example .env
# 编辑.env文件，填入实际配置
```

4. 启动开发服务器：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端设置

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，填入实际配置
```

3. 启动开发服务器：
```bash
npm start
```

## 功能特性

- 🏠 房源文本智能解析（基于豆包大模型）
- 📝 结构化房源信息管理
- 🔍 房源搜索和筛选
- 📸 图片上传和管理
- 🔐 用户认证和会话管理
- 📱 响应式设计

## 技术栈

**后端：**
- FastAPI - Web框架
- SQLAlchemy - ORM
- MySQL - 数据库
- JWT - 身份认证
- 豆包大模型 - 文本解析

**前端：**
- React 18 - UI框架
- Ant Design - UI组件库
- React Router - 路由管理
- Axios - HTTP客户端

## 开发指南

请参考 `.kiro/specs/real-estate-management-system/` 目录下的需求文档、设计文档和任务列表。