"""
Web UI 模块
基于 Gradio 的 Web 界面
"""
import os
import sys
import gradio as gr
from typing import List, Tuple, Dict

# 确保可以导入 basic-agent 模块
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if skill_dir not in sys.path:
    sys.path.insert(0, skill_dir)


class BioAgentWeb:
    """BioAgent Web 界面"""

    def __init__(self):
        self.agent = None
        self.model_map: Dict[str, Dict] = {}  # {"[Provider] model": {base_url, api_key, model}}
        self._init_agent()

    def _init_agent(self):
        """初始化 Agent（使用 config.yaml 默认配置）"""
        try:
            from core.agent import BioAgent
            self.agent = BioAgent()
            print("[BioAgent Web] Agent 初始化成功")
        except Exception as e:
            print(f"[BioAgent Web] Agent 初始化失败: {e}")

    def _detect_models(self) -> List[Dict]:
        """检测可用模型，返回模型列表"""
        from core.provider_manager import detect_available_providers
        providers = detect_available_providers()
        models = []
        for p in providers:
            for m in p.resolved_models:
                label = f"[{p.name}] {m}"
                self.model_map[label] = {
                    "base_url": p.base_url,
                    "api_key": p.api_key,
                    "model": m,
                }
                models.append(label)
        return models

    def switch_model(self, model_label: str) -> str:
        """切换模型，返回状态信息"""
        if not model_label or model_label not in self.model_map:
            return "请选择一个有效的模型"

        info = self.model_map[model_label]
        try:
            from core.agent import BioAgent
            self.agent = BioAgent(
                model=info["model"],
                _base_url=info["base_url"],
                _api_key=info["api_key"],
            )
            return f"已切换到: {model_label}"
        except Exception as e:
            return f"切换失败: {e}"

    def chat(self, message: str, history: List[Tuple[str, str]]) -> str:
        """处理聊天"""
        if not self.agent:
            return "Agent 未初始化，请检查配置"

        try:
            response = self.agent.chat(message)
            return response
        except Exception as e:
            return f"错误: {str(e)}"

    def upload_file(self, file):
        """处理文件上传"""
        if file is None:
            return "未选择文件"

        from config_loader import get_config
        cfg = get_config()
        upload_dir = os.path.join(cfg.skill_dir, cfg.paths.data_dir, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        import shutil
        filename = os.path.basename(file.name)
        dest_path = os.path.join(upload_dir, filename)
        shutil.copy(file.name, dest_path)

        return f"文件已上传: {filename}\n保存路径: {dest_path}"


def create_app() -> gr.Blocks:
    """创建 Gradio 应用"""
    web = BioAgentWeb()

    with gr.Blocks(title="BioAgent - 生物信息学分析助手") as app:
        gr.Markdown("# BioAgent\n生物信息学分析助手")
        gr.Markdown("基于 LLM 的生物信息学分析工具，支持序列分析、质控、组装、进化分析等")

        with gr.Row():
            with gr.Column(scale=3):
                # 聊天界面
                chatbot = gr.Chatbot(
                    label="对话历史",
                    height=400,
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        label="输入",
                        placeholder="请输入您的分析需求...",
                        scale=4,
                    )
                    submit_btn = gr.Button("发送", variant="primary", scale=1)

                clear_btn = gr.Button("清除对话")

            with gr.Column(scale=1):
                # 侧边栏
                gr.Markdown("### 模型选择")
                with gr.Row():
                    model_dropdown = gr.Dropdown(
                        label="选择模型",
                        choices=[],
                        interactive=True,
                        scale=4,
                    )
                    refresh_btn = gr.Button("刷新", scale=1)

                model_status = gr.Textbox(label="模型状态", interactive=False)

                gr.Markdown("### 文件上传")
                file_input = gr.File(
                    label="上传数据文件",
                    file_count="single",
                )
                upload_btn = gr.Button("上传文件")
                upload_status = gr.Textbox(label="上传状态", interactive=False)

                gr.Markdown("### 工具状态")
                tools_status = gr.JSON(label="可用工具")

                # 显示工具列表
                try:
                    from tools.base import ToolRegistry
                    tools = ToolRegistry.list_tools()
                    tools_status.value = {"tools_count": len(tools), "tools": [t.name for t in tools]}
                except Exception as e:
                    tools_status.value = {"error": str(e)}

        # ---- 模型刷新逻辑 ----
        def refresh_models():
            """刷新可用模型列表"""
            models = web._detect_models()
            choices = models if models else ["无可用模型"]
            status_msg = f"检测到 {len(models)} 个可用模型" if models else "未检测到可用模型"
            return gr.update(choices=choices, value=choices[0] if choices else None), status_msg

        # 页面加载时自动检测
        app.load(
            fn=refresh_models,
            outputs=[model_dropdown, model_status],
        )

        refresh_btn.click(
            fn=refresh_models,
            outputs=[model_dropdown, model_status],
        )

        # 切换模型
        def on_model_change(model_label):
            if not model_label:
                return ""
            return web.switch_model(model_label)

        model_dropdown.change(
            fn=on_model_change,
            inputs=[model_dropdown],
            outputs=[model_status],
        )

        # ---- 聊天逻辑 ----
        def respond(message, history):
            if not message.strip():
                return "", history

            response = web.chat(message, history)
            history.append((message, response))
            return "", history

        submit_btn.click(respond, [msg_input, chatbot], [msg_input, chatbot])
        msg_input.submit(respond, [msg_input, chatbot], [msg_input, chatbot])

        def clear_history():
            if web.agent:
                web.agent.reset_conversation()
            return []

        clear_btn.click(lambda: [], None, chatbot)

        # 文件上传
        def handle_upload(file):
            return web.upload_file(file)

        upload_btn.click(handle_upload, [file_input], [upload_status])

        # 示例问题
        gr.Examples(
            examples=[
                ["统计 sequences.fasta 文件的序列数量"],
                ["对 sample.fastq 进行质控"],
                ["使用多序列比对后建树的工作流"],
            ],
            inputs=msg_input,
        )

    return app


def launch_web(share: bool = False, debug: bool = False, port: int = 7861):
    """启动 Web 服务"""
    from config_loader import get_config

    cfg = get_config()
    app = create_app()

    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=share,
        debug=debug,
    )


if __name__ == "__main__":
    launch_web()
