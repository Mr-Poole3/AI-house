#!/bin/bash

# 启动前端开发服务器脚本

echo "启动房屋中介管理系统前端服务..."

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "安装npm依赖..."
    npm install
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "复制环境变量示例文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置API地址"
fi

# 启动开发服务器
echo "启动React开发服务器..."
npm start