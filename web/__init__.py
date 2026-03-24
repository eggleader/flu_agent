"""
Web 模块初始化
"""

from .app import BioAgentWeb, create_app, launch_web

__all__ = [
    "BioAgentWeb",
    "create_app",
    "launch_web",
]
