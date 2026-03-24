#!/usr/bin/env python3
"""
BioAgent 启动入口
支持多种模式：CLI / Web / API
参考 POPGENAGENT 的 run.py 设计
"""
import argparse
import sys
import os

# 添加技能目录到路径
skill_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, skill_dir)


def run_cli():
    """命令行 REPL 模式"""
    from core.agent import BioAgent
    
    print("=" * 50)
    print("BioAgent - 生物信息学分析助手")
    print("=" * 50)
    print("输入您的分析需求，输入 'quit' 或 'exit' 退出")
    print()
    
    agent = BioAgent()
    
    while True:
        try:
            user_input = input("\n用户> ").strip()
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("再见!")
                break
            
            if not user_input:
                continue
            
            response = agent.chat(user_input)
            print(f"\nBioAgent> {response}")
            
        except KeyboardInterrupt:
            print("\n\n退出...")
            break
        except Exception as e:
            print(f"错误: {e}")


def run_web(share: bool = False, debug: bool = False, port: int = 7860):
    """Web UI 模式"""
    from web.app import launch_web
    
    print(f"启动 Web 服务: http://localhost:{port}")
    launch_web(share=share, debug=debug, port=port)


def main():
    parser = argparse.ArgumentParser(description="BioAgent 启动器")
    parser.add_argument(
        "--mode", 
        choices=["cli", "web", "api"], 
        default="cli",
        help="运行模式: cli (命令行), web (Web界面), api (API服务)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=7860,
        help="Web/API 端口 (默认: 7860)"
    )
    parser.add_argument(
        "--share", 
        action="store_true",
        help="创建公开链接 (仅 Web 模式)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="开启调试模式"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="指定 LLM 模型"
    )
    
    args = parser.parse_args()
    
    if args.mode == "cli":
        run_cli()
    elif args.mode == "web":
        run_web(share=args.share, debug=args.debug, port=args.port)
    elif args.mode == "api":
        # TODO: API 模式
        print("API 模式开发中...")
        sys.exit(1)


if __name__ == "__main__":
    main()
