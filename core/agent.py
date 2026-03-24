"""
BioAgent 核心类
参考 POPGENAGENT 架构设计，引入 Planner-Executor 模式
"""
import json
import os
import requests
from typing import Dict, List, Any, Optional
from .prompts import SYSTEM_PROMPT


class BioAgent:
    """
    生物信息学分析 Agent (重构版)
    支持：
    - Planner-Executor 双阶段模式（复杂任务）
    - 直接 FC 模式（简单任务）
    - 工具自动发现与 Function Calling
    - 工作流引擎
    - 知识库上下文注入
    - 会话记忆管理
    """
    
    def __init__(
        self,
        name: str = "BioAgent",
        model: str = None,
        enable_planner: bool = False,  # 默认关闭，模型升级后可启用
        planner_threshold: int = 2,
        session_id: str = None,
    ):
        from config_loader import get_config, get_llm_config
        from tools.base import ToolRegistry
        from tools import discover_and_register_tools
        
        cfg = get_config()
        llm_cfg = get_llm_config()
        
        self.name = name
        self.model = model or cfg.llm.model
        self.enable_planner = enable_planner and cfg.agent.enable_planner
        self.planner_threshold = planner_threshold or cfg.agent.planner_threshold
        self.session_id = session_id
        
        # FC 循环配置
        self.max_tool_rounds = cfg.agent.max_tool_rounds
        
        # LLM 配置
        self.llm_base_url = cfg.llm.base_url
        self.llm_timeout = cfg.llm.timeout
        self.temperature = cfg.llm.temperature
        
        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []
        
        # 加载知识库
        self.knowledge_context = self._load_knowledge()
        
        # 加载工具
        discover_and_register_tools()
        self._load_workflows()
        
        self.tools = ToolRegistry.to_openai_functions()
        
        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()
        
        # Planner 和 Executor 实例
        self.planner = None
        self.executor = None
        if self.enable_planner:
            from .planner import Planner
            from .executor import Executor
            self.planner = Planner(
                llm_base_url=self.llm_base_url,
                model=self.model,
                temperature=self.temperature,
                timeout=self.llm_timeout,
            )
            self.executor = Executor(
                llm_base_url=self.llm_base_url,
                model=self.model,
                temperature=self.temperature,
                timeout=self.llm_timeout,
                tools=self.tools,
            )
    
    def _load_knowledge(self) -> str:
        """加载知识库内容"""
        from config_loader import get_knowledge_dir
        
        knowledge_context = []
        knowledge_dir = get_knowledge_dir()
        
        if os.path.exists(knowledge_dir):
            for filename in os.listdir(knowledge_dir):
                if filename.endswith('.md'):
                    filepath = os.path.join(knowledge_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        knowledge_context.append(f"\n\n=== {filename} ===\n{content}")
        
        return "\n".join(knowledge_context)
    
    def _load_workflows(self):
        """加载工作流引擎（作为知识参考，不注册为工具）"""
        try:
            # 不再注册 workflow_run 工具，只加载工作流信息用于知识库
            from workflow.runner_tool import register_workflow_tools
            register_workflow_tools()  # 现在是空操作
            from workflow import get_engine
            engine = get_engine()
            wf_count = len(engine.workflows)
            print(f"[BioAgent] 已加载 {wf_count} 个工作流（作为知识参考）")
        except Exception as e:
            print(f"[BioAgent] 警告: 工作流引擎加载失败: {e}")
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tools_info = "\n".join([
            f"- {t['function']['name']}: {t['function']['description'][:80]}"
            for t in self.tools
        ])
        
        # 工作流信息（作为知识参考，不暴露为可调用工具）
        workflow_info = ""
        try:
            from workflow import list_workflows
            workflows = list_workflows()
            if workflows:
                workflow_info = "\n可用工作流:\n"
                for wf in workflows:
                    workflow_info += f"- {wf['name']}: {wf['description']}"
                    if wf.get("triggers"):
                        workflow_info += f" (适用场景: {', '.join(wf['triggers'])})"
                    workflow_info += "\n"
                workflow_info += "\n注意：仅当用户明确要求'运行工作流'时才使用 workflow_run。"
        except Exception:
            pass
        
        return SYSTEM_PROMPT.format(
            tools_info=tools_info,
            workflow_info=workflow_info,
            knowledge=self.knowledge_context,
        )
    
    def chat(self, user_input: str) -> str:
        """
        处理用户输入 - 统一 FC 循环模式
        LLM 自主决定调用哪些工具，Agent 执行并回填结果，循环直到完成
        """
        # 初始化消息
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.conversation_history,
            {"role": "user", "content": user_input}
        ]
        
        # 多轮 FC 循环
        max_rounds = self.max_tool_rounds
        for round_idx in range(max_rounds):
            result = self._call_llm(messages, tools=self.tools)
            
            if "error" in result:
                return f"错误: {result['error']}"
            
            message = result["choices"][0]["message"]
            tool_calls = message.get("tool_calls", [])
            
            if not tool_calls:
                # 无工具调用，直接返回回复
                content = message.get("content", "")
                self.conversation_history.append({"role": "user", "content": user_input})
                self.conversation_history.append({"role": "assistant", "content": content})
                return content
            
            # 有工具调用，执行并回填结果
            tool_results = []
            for tc in tool_calls:
                func = tc.get("function", {})
                tool_name = func.get("name")
                args = json.loads(func.get("arguments", "{}"))
                
                result_str = self._execute_tool(tool_name, args)
                tool_results.append({
                    "tool_call_id": tc.get("id", ""),
                    "content": result_str
                })
                
                # 添加工具调用和结果到消息
                messages.append({"role": "assistant", "content": None, "tool_calls": [tc]})
                messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result_str})
            
            # 循环继续，LLM 会根据工具结果决定下一步
        
        # 达到最大轮次，返回最后结果
        return "已达到最大工具调用轮次，请检查任务是否完成。"
    
    def _find_similar_tool(self, tool_name: str) -> Optional[str]:
        """从已注册工具中找到最相似的工具名（模糊匹配）"""
        from tools.base import ToolRegistry
        import difflib
        
        available_tools = list(ToolRegistry._tools.keys())
        if not available_tools:
            return None
        
        # 使用 difflib 找最相似的工具名
        matches = difflib.get_close_matches(tool_name, available_tools, n=1, cutoff=0.6)
        return matches[0] if matches else None
    
    def _execute_tool(self, tool_name: str, args: Dict) -> str:
        """执行工具（带模糊匹配自动纠正）"""
        from tools import execute_tool
        from tools.base import ToolRegistry
        
        # 精确匹配
        if ToolRegistry.has_tool(tool_name):
            try:
                return execute_tool(tool_name, **args)
            except Exception as e:
                return f"工具执行错误: {str(e)}"
        
        # 模糊匹配：尝试找到最相似的工具名
        best_match = self._find_similar_tool(tool_name)
        if best_match:
            # 尝试自动映射参数（针对常见参数名错误）
            import inspect
            try:
                sig = inspect.signature(execute_tool)
                param_names = list(sig.parameters.keys())
                
                # 如果原始参数不在目标工具中，尝试映射
                corrected_args = {}
                for k, v in args.items():
                    if k in param_names:
                        corrected_args[k] = v
                    elif k == "input_file" and "file" in param_names:
                        corrected_args["file"] = v
                    elif k == "output_file" and "output" in param_names:
                        corrected_args["output"] = v
                    else:
                        corrected_args[k] = v  # 保留原参数，让工具报错
                
                result = execute_tool(best_match, **corrected_args)
                return f"[自动纠正工具名: '{tool_name}' → '{best_match}', 参数已适配]\n{result}"
            except Exception as e:
                return f"工具名已自动纠正为 '{best_match}'，但参数适配失败: {str(e)}\n请检查工具参数格式。"
        
        # 无法匹配
        available = ", ".join(ToolRegistry._tools.keys())
        return f"错误: 未知工具 '{tool_name}'。\n可用工具: {available}"
    
    def _call_llm(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict] = None,
        model: str = None,
        temperature: float = None,
    ) -> Dict[str, Any]:
        """调用 LLM API"""
        model = model or self.model
        temperature = temperature or self.temperature
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        if tools:
            payload["tools"] = tools
        
        try:
            response = requests.post(
                f"{self.llm_base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.llm_timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": f"LLM调用超时（{self.llm_timeout}s），请尝试：1) 缩小问题范围 2) 增大config.yaml中timeout值"}
        except requests.exceptions.ConnectionError:
            return {"error": "无法连接LLM服务，请确认Ollama正在运行（ollama serve）"}
        except requests.exceptions.RequestException as e:
            return {"error": f"LLM调用失败: {str(e)}"}
    
    def _extract_content(self, result: Dict) -> str:
        """从响应中提取内容"""
        choices = result.get("choices", [])
        if not choices:
            return "错误: 无有效响应"
        
        message = choices[0].get("message", {})
        return message.get("content", "")
    
    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.copy()
