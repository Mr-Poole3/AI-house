#!/usr/bin/env python3
"""
房屋中介管理系统启动脚本
运行方式: python run.py
"""

import sys
import os
from pathlib import Path

def load_env():
    """初始化项目环境"""
    project_root = Path(__file__).parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 设置工作目录
    os.chdir(project_root)
    return project_root

# 必须在导入其他模块之前调用
load_env()

def main():
    """主启动函数"""
    import uvicorn
    
    print("🏠 启动房屋中介管理系统...")
    print("📍 API文档: http://localhost:8000/docs")
    print("🔧 ReDoc文档: http://localhost:8000/redoc")
    print("💻 健康检查: http://localhost:8000/health")
    print("=" * 50)
    
    # 启动服务器 - 使用导入字符串而不是直接导入对象
    uvicorn.run(
        "backend.main:app",  # 使用导入字符串
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)