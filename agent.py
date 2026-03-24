#!/usr/bin/env python3
"""
BioAgent 入口文件
导入并使用 core.agent 中的 BioAgent 类
"""

from core.agent import BioAgent

__all__ = ["BioAgent"]


def create_bio_agent(model: str = None, **kwargs) -> BioAgent:
    """创建生物信息学分析 Agent"""
    return BioAgent(model=model, **kwargs)


if __name__ == "__main__":
    agent = create_bio_agent()
    agent.run()
