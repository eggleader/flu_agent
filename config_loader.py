"""
配置加载器
参考 POPGENAGENT 的 config_loader.py
支持从 YAML 文件加载配置，支持环境变量覆盖
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


# 默认配置文件路径
DEFAULT_CONFIG_FILE = "config.yaml"


@dataclass
class LLMConfig:
    """LLM 配置"""
    base_url: str = "http://localhost:11434"
    model: str = "qwen3:4b"
    temperature: float = 0.7
    timeout: int = 300
    max_tokens: int = 4096


@dataclass
class PathsConfig:
    """路径配置"""
    tools_dir: str = "tools"
    knowledge_dir: str = "knowledge"
    workflow_dir: str = "workflow"
    data_dir: str = "data"
    reports_dir: str = "reports"
    example_dir: str = "example"


@dataclass
class AgentConfig:
    """Agent 配置"""
    max_tool_rounds: int = 10
    enable_planner: bool = True
    planner_threshold: int = 2
    default_threads: int = 4
    command_timeout: int = 600


@dataclass
class WebConfig:
    """Web UI 配置"""
    enable: bool = False
    port: int = 7860
    share: bool = False
    debug: bool = False


@dataclass
class DatabaseConfig:
    """数据库配置"""
    type: str = "sqlite"
    path: str = "data/sessions/bioagent.db"


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "bioagent.log"


@dataclass
class Config:
    """全局配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    tools: Dict[str, str] = field(default_factory=dict)
    agent: AgentConfig = field(default_factory=AgentConfig)
    web: WebConfig = field(default_factory=WebConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # 运行时属性（非配置文件）
    skill_dir: str = ""


class ConfigLoader:
    """配置加载器"""
    
    _instance: Optional[Config] = None
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or DEFAULT_CONFIG_FILE
    
    @classmethod
    def get_instance(cls, config_file: Optional[str] = None) -> Config:
        """获取配置单例"""
        if cls._instance is None:
            cls._instance = cls(config_file).load()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """重置单例（用于测试）"""
        cls._instance = None
    
    def load(self) -> Config:
        """加载配置文件"""
        # 查找配置文件
        config_path = self._find_config_file()
        
        if config_path and os.path.isfile(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
        
        # 应用环境变量覆盖
        data = self._apply_env_overrides(data)
        
        # 构建配置对象
        return self._build_config(data, config_path)
    
    def _find_config_file(self) -> Optional[str]:
        """查找配置文件"""
        # 当前目录
        if os.path.isfile(self.config_file):
            return os.path.abspath(self.config_file)
        
        # 父目录
        parent = os.path.dirname(os.path.abspath(self.config_file))
        if os.path.isfile(os.path.join(parent, self.config_file)):
            return os.path.join(parent, self.config_file)
        
        # 技能目录
        skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_in_skill = os.path.join(skill_dir, self.config_file)
        if os.path.isfile(config_in_skill):
            return config_in_skill
        
        return None
    
    def _apply_env_overrides(self, data: Dict) -> Dict:
        """应用环境变量覆盖"""
        # LLM 配置
        if 'OLLAMA_BASE_URL' in os.environ:
            data.setdefault('llm', {})['base_url'] = os.environ['OLLAMA_BASE_URL']
        if 'OLLAMA_MODEL' in os.environ:
            data.setdefault('llm', {})['model'] = os.environ['OLLAMA_MODEL']
        
        return data
    
    def _build_config(self, data: Dict, config_path: Optional[str]) -> Config:
        """构建配置对象"""
        skill_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 解析路径
        paths_data = data.get('paths', {})
        paths = PathsConfig(**paths_data) if paths_data else PathsConfig()
        
        # 确保绝对路径
        def resolve_path(p: str) -> str:
            if os.path.isabs(p):
                return p
            return os.path.join(skill_dir, p)
        
        config = Config(
            llm=LLMConfig(**data.get('llm', {})),
            paths=paths,
            tools=data.get('tools', {}),
            agent=AgentConfig(**data.get('agent', {})),
            web=WebConfig(**data.get('web', {})),
            database=DatabaseConfig(**data.get('database', {})),
            logging=LoggingConfig(**data.get('logging', {})),
            skill_dir=skill_dir,
        )
        
        return config


def get_config() -> Config:
    """获取全局配置（快捷函数）"""
    return ConfigLoader.get_instance()


# 兼容旧代码：导出常用配置
def get_skill_dir() -> str:
    return get_config().skill_dir


def get_tools_dir() -> str:
    cfg = get_config()
    return os.path.join(cfg.skill_dir, cfg.paths.tools_dir)


def get_knowledge_dir() -> str:
    cfg = get_config()
    return os.path.join(cfg.skill_dir, cfg.paths.knowledge_dir)


def get_reports_dir() -> str:
    cfg = get_config()
    return os.path.join(cfg.skill_dir, cfg.paths.reports_dir)


def get_llm_config() -> Dict[str, Any]:
    """获取 LLM 配置字典"""
    cfg = get_config()
    return {
        "base_url": cfg.llm.base_url,
        "model": cfg.llm.model,
        "temperature": cfg.llm.temperature,
        "timeout": cfg.llm.timeout,
        "max_tokens": cfg.llm.max_tokens,
    }
