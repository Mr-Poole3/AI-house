#!/bin/bash

# 启动后端开发服务器脚本

echo "启动房屋中介管理系统后端服务..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "复制环境变量示例文件..."
    cp ../.env.example .env
    echo "请编辑 .env 文件配置数据库和API密钥"
fi

# 启动服务器
echo "启动FastAPI开发服务器..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000