"""
Web UI 模块
基于 Gradio 的 Web 界面
"""
import os
import sys
import gradio as gr
from typing import List, Tuple

# 确保可以导入 basic-agent 模块
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if skill_dir not in sys.path:
    sys.path.insert(0, skill_dir)


class BioAgentWeb:
    """BioAgent Web 界面"""
    
    def __init__(self):
        self.agent = None
        self._init_agent()
    
    def _init_agent(self):
        """初始化 Agent"""
        try:
            from core.agent import BioAgent
            self.agent = BioAgent()
            print("[BioAgent Web] Agent 初始化成功")
        except Exception as e:
            print(f"[BioAgent Web] Agent 初始化失败: {e}")
    
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
        
        # 保存到上传目录
        from config_loader import get_config
        cfg = get_config()
        upload_dir = os.path.join(cfg.skill_dir, cfg.paths.data_dir, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # 复制文件
        import shutil
        filename = os.path.basename(file.name)
        dest_path = os.path.join(upload_dir, filename)
        shutil.copy(file.name, dest_path)
        
        return f"文件已上传: {filename}\n保存路径: {dest_path}"


def create_app() -> gr.Blocks:
    """创建 Gradio 应用"""
    web = BioAgentWeb()
    
    with gr.Blocks(title="BioAgent - 生物信息学分析助手") as app:
        gr.Markdown("# 🧬 BioAgent\n生物信息学分析助手")
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
                gr.Markdown("### 📁 文件上传")
                file_input = gr.File(
                    label="上传数据文件",
                    file_count="single",
                )
                upload_btn = gr.Button("上传文件")
                upload_status = gr.Textbox(label="上传状态", interactive=False)
                
                gr.Markdown("### ⚙️ 工具状态")
                tools_status = gr.JSON(label="可用工具")
                
                # 显示工具列表
                try:
                    from tools.base import ToolRegistry
                    tools = ToolRegistry.list_tools()
                    tools_status.value = {"tools_count": len(tools), "tools": list(tools.keys())}
                except Exception as e:
                    tools_status.value = {"error": str(e)}
        
        # 事件处理
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


def launch_web(share: bool = False, debug: bool = False, port: int = 7860):
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
