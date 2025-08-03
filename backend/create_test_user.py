#!/usr/bin/env python3
"""
创建测试用户脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, create_tables
from backend.models.user import User
from backend.services.auth_service import auth_service


def create_test_user():
    """创建测试用户"""
    # 确保数据库表存在
    create_tables()
    
    db = SessionLocal()
    try:
        # 检查用户是否已存在
        existing_user = User.get_by_username(db, "admin")
        if existing_user:
            print("测试用户 'admin' 已存在")
            return
        
        # 创建测试用户
        password_hash = auth_service.hash_password("admin123")
        user = User.create(db, "admin", password_hash)
        
        print(f"成功创建测试用户: {user.username} (ID: {user.id})")
        print("用户名: admin")
        print("密码: admin123")
        
    except Exception as e:
        print(f"创建测试用户失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()