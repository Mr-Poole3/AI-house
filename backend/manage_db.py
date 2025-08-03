#!/usr/bin/env python3
"""
数据库管理脚本
"""
import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import create_tables, drop_tables, SessionLocal
from models import User, Property, PropertyImage, UserSession, PropertyType
from utils.db_utils import DatabaseUtils
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user():
    """创建管理员用户"""
    db = SessionLocal()
    try:
        # 检查是否已存在admin用户
        existing_user = User.get_by_username(db, "admin")
        if existing_user:
            print("管理员用户已存在")
            return
        
        # 创建管理员用户
        password_hash = pwd_context.hash("admin123")
        admin_user = User.create(db, username="admin", password_hash=password_hash)
        print(f"创建管理员用户成功: {admin_user.username}")
        
    except Exception as e:
        print(f"创建管理员用户失败: {e}")
    finally:
        db.close()

def show_statistics():
    """显示数据库统计信息"""
    db = SessionLocal()
    try:
        stats = DatabaseUtils.get_property_statistics(db)
        print("\n=== 房源统计 ===")
        print(f"总房源数: {stats['total_properties']}")
        print(f"租房数量: {stats['rent_properties']}")
        print(f"售房数量: {stats['sale_properties']}")
        print(f"平均租金: {stats['rent_avg_price']:.2f} 元/月")
        print(f"平均售价: {stats['sale_avg_price']:.2f} 万元")
        
        community_stats = DatabaseUtils.get_community_statistics(db)
        print(f"\n=== 小区统计 ===")
        print(f"小区数量: {len(community_stats)}")
        
        for community in community_stats[:5]:  # 显示前5个小区
            print(f"- {community['community_name']}: "
                  f"总计{community['total_count']}套 "
                  f"(租房{community['rent_count']}套, 售房{community['sale_count']}套)")
        
    except Exception as e:
        print(f"获取统计信息失败: {e}")
    finally:
        db.close()

def cleanup_expired_sessions():
    """清理过期会话"""
    db = SessionLocal()
    try:
        count = DatabaseUtils.cleanup_expired_sessions(db)
        print(f"清理了 {count} 个过期会话")
    except Exception as e:
        print(f"清理过期会话失败: {e}")
    finally:
        db.close()

def create_sample_data():
    """创建示例数据"""
    db = SessionLocal()
    try:
        # 创建示例房源数据
        sample_properties = [
            {
                "community_name": "阳光花园",
                "street_address": "中山路188号",
                "floor_info": "8/15层",
                "price": 2800.00,
                "property_type": PropertyType.RENT,
                "furniture_appliances": "全套家具家电",
                "decoration_status": "精装修",
                "room_count": "2室1厅1卫",
                "area": 78.5,
                "description": "阳光花园2室1厅，精装修，家具家电齐全",
                "parsed_confidence": 0.92
            },
            {
                "community_name": "绿城小区",
                "street_address": "解放路66号",
                "floor_info": "12/20层",
                "price": 150.00,
                "property_type": PropertyType.SALE,
                "furniture_appliances": "无",
                "decoration_status": "毛坯",
                "room_count": "3室2厅2卫",
                "area": 120.0,
                "description": "绿城小区3室2厅，毛坯房，采光好",
                "parsed_confidence": 0.88
            },
            {
                "community_name": "海景豪庭",
                "street_address": "滨海大道999号",
                "floor_info": "18/25层",
                "price": 4500.00,
                "property_type": PropertyType.RENT,
                "furniture_appliances": "高端家具家电",
                "decoration_status": "豪华装修",
                "room_count": "3室2厅2卫",
                "area": 135.0,
                "description": "海景豪庭3室2厅，豪华装修，海景房",
                "parsed_confidence": 0.95
            }
        ]
        
        created_properties = DatabaseUtils.bulk_create_properties(db, sample_properties)
        print(f"创建了 {len(created_properties)} 个示例房源")
        
    except Exception as e:
        print(f"创建示例数据失败: {e}")
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="数据库管理工具")
    parser.add_argument("command", choices=[
        "create", "drop", "reset", "admin", "stats", "cleanup", "sample"
    ], help="要执行的命令")
    
    args = parser.parse_args()
    
    if args.command == "create":
        print("创建数据库表...")
        create_tables()
        print("✓ 数据库表创建成功")
        
    elif args.command == "drop":
        confirm = input("确定要删除所有表吗？这将删除所有数据！(y/N): ")
        if confirm.lower() == 'y':
            drop_tables()
            print("✓ 数据库表删除成功")
        else:
            print("操作已取消")
            
    elif args.command == "reset":
        confirm = input("确定要重置数据库吗？这将删除所有数据！(y/N): ")
        if confirm.lower() == 'y':
            drop_tables()
            create_tables()
            create_admin_user()
            print("✓ 数据库重置成功")
        else:
            print("操作已取消")
            
    elif args.command == "admin":
        create_admin_user()
        
    elif args.command == "stats":
        show_statistics()
        
    elif args.command == "cleanup":
        cleanup_expired_sessions()
        
    elif args.command == "sample":
        create_sample_data()

if __name__ == "__main__":
    main()