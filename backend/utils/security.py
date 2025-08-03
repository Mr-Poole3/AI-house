"""
安全工具模块
"""
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Request
from collections import defaultdict


class RateLimiter:
    """简单的内存速率限制器"""
    
    def __init__(self):
        # 存储每个IP的登录尝试记录
        self.login_attempts: Dict[str, list] = defaultdict(list)
        # 存储被锁定的IP和解锁时间
        self.locked_ips: Dict[str, datetime] = {}
        
        # 配置参数
        self.max_attempts = 5  # 最大尝试次数
        self.window_minutes = 15  # 时间窗口(分钟)
        self.lockout_minutes = 30  # 锁定时间(分钟)
    
    def is_ip_locked(self, ip: str) -> bool:
        """检查IP是否被锁定"""
        if ip in self.locked_ips:
            unlock_time = self.locked_ips[ip]
            if datetime.utcnow() < unlock_time:
                return True
            else:
                # 锁定时间已过，移除锁定
                del self.locked_ips[ip]
                return False
        return False
    
    def record_failed_attempt(self, ip: str) -> None:
        """记录失败的登录尝试"""
        now = datetime.utcnow()
        
        # 清理过期的尝试记录
        cutoff_time = now - timedelta(minutes=self.window_minutes)
        self.login_attempts[ip] = [
            attempt_time for attempt_time in self.login_attempts[ip]
            if attempt_time > cutoff_time
        ]
        
        # 添加新的尝试记录
        self.login_attempts[ip].append(now)
        
        # 检查是否超过最大尝试次数
        if len(self.login_attempts[ip]) >= self.max_attempts:
            # 锁定IP
            self.locked_ips[ip] = now + timedelta(minutes=self.lockout_minutes)
    
    def clear_attempts(self, ip: str) -> None:
        """清除IP的尝试记录(登录成功时调用)"""
        if ip in self.login_attempts:
            del self.login_attempts[ip]
        if ip in self.locked_ips:
            del self.locked_ips[ip]
    
    def get_remaining_lockout_time(self, ip: str) -> Optional[int]:
        """获取剩余锁定时间(秒)"""
        if ip in self.locked_ips:
            unlock_time = self.locked_ips[ip]
            remaining = (unlock_time - datetime.utcnow()).total_seconds()
            return max(0, int(remaining))
        return None
    
    def check_rate_limit(self, ip: str) -> None:
        """检查速率限制，如果超限则抛出异常"""
        if self.is_ip_locked(ip):
            remaining_time = self.get_remaining_lockout_time(ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "TOO_MANY_ATTEMPTS",
                    "message": f"登录尝试次数过多，请在 {remaining_time} 秒后重试",
                    "retry_after": remaining_time
                }
            )


class SecurityUtils:
    """安全工具类"""
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头部
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 取第一个IP地址
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 回退到直接连接IP
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: list = None) -> bool:
        """检查重定向URL是否安全"""
        if not url:
            return False
        
        # 简单的安全检查
        if url.startswith("//") or url.startswith("http://") or url.startswith("https://"):
            # 外部URL，需要检查是否在允许列表中
            if allowed_hosts:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                return parsed.netloc in allowed_hosts
            return False
        
        # 相对URL被认为是安全的
        return url.startswith("/")
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名，移除危险字符"""
        import re
        # 移除路径分隔符和其他危险字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 移除控制字符
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        # 限制长度
        return filename[:255]
    
    @staticmethod
    def generate_secure_filename(original_filename: str) -> str:
        """生成安全的文件名"""
        import uuid
        import os
        
        # 获取文件扩展名
        _, ext = os.path.splitext(original_filename)
        # 生成UUID作为文件名
        secure_name = str(uuid.uuid4()) + ext.lower()
        return secure_name


# 创建全局速率限制器实例
rate_limiter = RateLimiter()


class PasswordPolicy:
    """密码策略类"""
    
    def __init__(self):
        self.min_length = 8
        self.max_length = 128
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special_chars = False
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    def validate_password(self, password: str) -> tuple[bool, list[str]]:
        """
        验证密码是否符合策略
        
        Returns:
            tuple: (是否有效, 错误消息列表)
        """
        errors = []
        
        # 检查长度
        if len(password) < self.min_length:
            errors.append(f"密码长度至少需要 {self.min_length} 个字符")
        
        if len(password) > self.max_length:
            errors.append(f"密码长度不能超过 {self.max_length} 个字符")
        
        # 检查大写字母
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("密码必须包含至少一个大写字母")
        
        # 检查小写字母
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("密码必须包含至少一个小写字母")
        
        # 检查数字
        if self.require_digits and not any(c.isdigit() for c in password):
            errors.append("密码必须包含至少一个数字")
        
        # 检查特殊字符
        if self.require_special_chars and not any(c in self.special_chars for c in password):
            errors.append(f"密码必须包含至少一个特殊字符: {self.special_chars}")
        
        # 检查常见弱密码
        weak_passwords = [
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "root", "user", "guest"
        ]
        
        if password.lower() in weak_passwords:
            errors.append("密码过于简单，请使用更复杂的密码")
        
        return len(errors) == 0, errors
    
    def generate_password_requirements(self) -> str:
        """生成密码要求说明"""
        requirements = [f"长度 {self.min_length}-{self.max_length} 个字符"]
        
        if self.require_uppercase:
            requirements.append("至少一个大写字母")
        
        if self.require_lowercase:
            requirements.append("至少一个小写字母")
        
        if self.require_digits:
            requirements.append("至少一个数字")
        
        if self.require_special_chars:
            requirements.append("至少一个特殊字符")
        
        return "密码要求: " + ", ".join(requirements)


class SessionSecurity:
    """会话安全管理"""
    
    def __init__(self):
        # 可疑活动检测
        self.max_concurrent_sessions = 5  # 最大并发会话数
        self.session_timeout_minutes = 30  # 会话超时时间(分钟)
        self.max_idle_time_minutes = 15  # 最大空闲时间(分钟)
    
    def detect_suspicious_activity(self, user_id: int, ip: str, user_agent: str, db) -> bool:
        """检测可疑活动"""
        from ..models.user_session import UserSession
        
        # 检查并发会话数
        active_sessions = UserSession.get_active_by_user_id(db, user_id)
        if len(active_sessions) > self.max_concurrent_sessions:
            return True
        
        # 检查IP地址变化(简单实现)
        # 在实际应用中，可能需要更复杂的地理位置检测
        recent_sessions = active_sessions[-5:]  # 最近5个会话
        if recent_sessions:
            # 这里可以添加IP地址变化检测逻辑
            pass
        
        return False
    
    def should_require_reauth(self, session, current_ip: str) -> bool:
        """判断是否需要重新认证"""
        # 检查会话年龄
        session_age = (datetime.utcnow() - session.created_at).total_seconds() / 60
        if session_age > self.session_timeout_minutes:
            return True
        
        # 这里可以添加更多的重新认证条件
        # 比如IP地址变化、用户代理变化等
        
        return False


# 创建全局实例
password_policy = PasswordPolicy()
session_security = SessionSecurity()