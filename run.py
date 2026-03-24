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


def run_cli(model_override: str = None):
    """命令行 REPL 模式"""
    from core.agent import BioAgent
    from core.provider_manager import detect_available_providers, user_select_model

    print("=" * 50)
    print("BioAgent - 生物信息学分析助手")
    print("=" * 50)

    # 确定模型配置
    selected = None
    if model_override:
        # --model 参数指定，使用 config.yaml 中的配置
        selected = None
    else:
        # 自动检测并让用户选择
        providers = detect_available_providers()
        selected = user_select_model(providers)

    # 构建 Agent 参数
    agent_kwargs = {}
    if selected:
        agent_kwargs["model"] = selected["model"]
        # 临时覆盖 LLM 配置
        agent_kwargs["_base_url"] = selected["base_url"]
        agent_kwargs["_api_key"] = selected["api_key"]

    print("输入您的分析需求，输入 'quit' 或 'exit' 退出")
    print()

    agent = BioAgent(**agent_kwargs)
    
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
        default=7861,
        help="Web/API 端口 (默认: 7861)"
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
        run_cli(model_override=args.model)
    elif args.mode == "web":
        run_web(share=args.share, debug=args.debug, port=args.port)
    elif args.mode == "api":
        # TODO: API 模式
        print("API 模式开发中...")
        sys.exit(1)


if __name__ == "__main__":
    main()
