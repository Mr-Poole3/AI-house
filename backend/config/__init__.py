"""
后端配置模块
包含应用配置、提示词配置等
"""

from .prompts import DoubaoPrompts
from .settings import settings

__all__ = ['DoubaoPrompts', 'settings']