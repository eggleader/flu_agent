# BioAgent - 生物信息学分析 Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue" alt="Python">
  <img src="https://img.shields.io/badge/LLM-Ollama-green" alt="Ollama">
  <img src="https://img.shields.io/badge/UI-Gradio-purple" alt="Gradio">
</p>

## 目录

1. [架构概述](#架构概述)
2. [与 POPGENAGENT 比较](#与-popgenagent-比较)
3. [核心模块](#核心模块)
4. [技术架构图](#技术架构图)
5. [工作流程](#工作流程)
6. [快速开始](#快速开始)
7. [配置说明](#配置说明)
8. [使用指南](#使用指南)
9. [工具列表](#工具列表)

---

## 架构概述

BioAgent 是一个基于 LLM 的生物信息学分析智能体，采用**零框架依赖**的纯 Python 设计。2024 年架构重构后，移除了 Planner-Executor 双阶段模式，改为**单轮 FC 循环**架构，更适合弱模型（如 qwen3:4b）使用。

### 核心特性

```
┌─────────────────────────────────────────────────────────────┐
│                     BioAgent 架构                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   用户输入 → [LLM + 工具列表] → 工具调用 → 执行 → 回填     │
│                            ↑                      │         │
│                            └────── 循环 N 轮 ──────┘         │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                   单轮 FC 循环                        │   │
│   │  • 无需 Planner 额外 LLM 调用                         │   │
│   │  • 弱模型友好：提示词简短明确                         │   │
│   │  • Workflow 降级为知识参考                            │   │
│   └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│                   ┌─────────────┐                            │
│                   │  ToolRegistry │                          │
│                   │   (37 tools)  │                          │
│                   └─────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

### 架构设计原则

1. **单工具优先**：简单任务如"统计序列数量"直接调用 seqkit，无需规划
2. **Workflow 知识化**：工作流作为知识参考，不暴露为可调用工具
3. **提示词补偿**：通过强化工具描述和明确指引来弥补弱模型推理能力
4. **可扩展性**：保留 `enable_planner` 配置开关，未来模型升级后可重新启用

### 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| LLM 引擎 | Ollama | 本地推理，OpenAI 兼容 API |
| Agent 框架 | 自定义 | 零框架依赖 |
| 前端 UI | Gradio | Web 界面 |
| 配置管理 | PyYAML | config.yaml |
| 会话存储 | SQLite | 对话历史持久化 |
| 工具协议 | OpenAI FC | Function Calling |

---

## 与 POPGENAGENT 比较

### 架构相似点

```
┌────────────────────────────────────────────────────────────┐
│                    POPGENAGENT 架构                         │
├────────────────────────────────────────────────────────────┤
│  web/          →  前端界面                                  │
│  core/         →  核心逻辑 (Planner + Executor)           │
│  tools/        →  生信工具封装                             │
│  knowledge/    →  领域知识库                                │
│  config.yaml   →  专业配置管理                             │
│  run.py        →  启动入口                                 │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                      BioAgent 架构                          │
├────────────────────────────────────────────────────────────┤
│  web/          →  前端界面 (Gradio)                        │
│  core/         →  核心逻辑 (Planner + Executor + Memory)  │
│  tools/        →  26 个生信工具                            │
│  knowledge/    →  领域知识库 + RAG 支持                    │
│  config.yaml   →  YAML 配置管理                            │
│  run.py        →  多模式启动入口                           │
└────────────────────────────────────────────────────────────┘
```

### 关键差异

| 特性 | POPGENAGENT | BioAgent |
|------|-------------|----------|
| **LLM 后端** | 未指定 | Ollama (本地) |
| **工具协议** | 未指定 | OpenAI Function Calling |
| **工作流引擎** | 无 | YAML 驱动工作流 |
| **会话管理** | 无 | SQLite 持久化 |
| **Web UI** | 需开发 | Gradio 内置 |
| **框架依赖** | 未说明 | 零依赖 |
| **工具数量** | 未说明 | 35 个 |
| **执行模式** | Planner-Executor | 单轮 FC 循环 |

### 架构对比图

```
                        POPGENAGENT                          BioAgent
                        ───────────                          ────────

    ┌──────────┐          ┌──────────┐
    │   Web/   │          │   Web/   │         ┌─────────────┐
    │  Backend │          │   (Grad) │         │  run.py     │◀── CLI/Web/API
    └────┬─────┘          └────┬─────┘         └──────┬──────┘
         │                     │                       │
         ▼                     ▼                       ▼
    ┌──────────┐          ┌──────────┐          ┌─────────────┐
    │   Core/  │          │   Core/  │          │  BioAgent   │
    │ Planner  │          │ Planner  │          │  + Planner  │
    │ Executor │          │ Executor │          │  + Executor │
    └────┬─────┘          └────┬─────┘          │  + Memory   │
         │                     │                 └──────┬──────┘
         ▼                     ▼                       │
    ┌──────────┐          ┌──────────┐                  ▼
    │  Tools/  │          │  Tools/  │          ┌─────────────┐
    │ (封装工具)│          │ (26 tools)│          │  Tools/     │
    └──────────┘          └──────────┘          │ (ToolBase)  │
                                                └──────┬──────┘
                                                       │
                               ┌───────────────────────┼───────────────────────┐
                               ▼                       ▼                       ▼
                        ┌──────────┐           ┌──────────┐           ┌──────────┐
                        │  SeqKit  │           │  FastQC  │           │  IQ-Tree │
                        │ 工具封装  │           │ 工具封装  │           │ 工具封装  │
                        └──────────┘           └──────────┘           └──────────┘
```

---

## 核心模块

### 1. Core 模块 (`core/`)

```
core/
├── __init__.py         # 模块导出
├── agent.py            # BioAgent 主控类 + chat()/chat_v2()
├── planner.py          # 任务规划器（保留，未启用）
├── executor.py         # 工具执行器（保留，未启用）
├── memory.py           # 会话记忆管理 + 用户画像/工具统计
├── prompts.py          # 提示词模板 + 三角色提示词
├── provider_manager.py # 多 API 管理（自动检测 + 用户选择）
│
├── ask_agent.py        # [v2.0] Ask Agent - 需求理解与澄清
├── plan_agent.py       # [v2.0] Plan Agent - 技术路线规划
├── craft_agent.py      # [v2.0] Craft Agent - 任务执行
├── llm_client.py       # [v2.0] LLM 统一客户端
├── evaluator.py        # [v2.0] 评估反馈模块
├── tools_manager.py    # [v2.0] 工具管理器
└── reasoning.py        # [v2.0] 推理路由
```

#### provider_manager.py - 多 API 管理

```
功能：
- load_providers()      # 加载 api_providers.yaml 配置
- discover_ollama_models()  # 自动发现本地 Ollama 模型
- probe_provider()       # 检测 API 连通性和模型可用性
- detect_available_providers()  # 扫描所有供应商，返回可用列表
- user_select_model()   # CLI 交互式模型选择
```

#### 单轮 FC 循环流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────────────────┐
│              chat() 多轮循环                     │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │ Step 1: LLM + 工具列表                  │   │
│  │  - 判断是否需要调用工具                  │   │
│  └────────────────┬────────────────────────┘   │
│                   │                            │
│           ┌──────┴──────┐                     │
│           ▼             ▼                      │
│      有 tool_calls   无 tool_calls             │
│           │             │                      │
│           ▼             │                      │
│  ┌─────────────────┐    │                      │
│  │ 执行工具        │    │                      │
│  │ 回填结果到消息  │    │                      │
│  └────────┬────────┘    │                      │
│           │             │                      │
│           └──────┬──────┘                      │
│                  ▼                              │
│           循环直到无工具调用                     │
│           或达到 max_tool_rounds               │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
            返回最终回复
```

**配置说明**：
- `enable_planner: false`（默认关闭，弱模型友好）
- `max_tool_rounds: 10`（最大工具调用轮次）
- Planner/Executor 模块保留但未启用，未来模型升级后可开启

### 2. 工具模块 (`tools/`)

```
tools/
├── __init__.py      # 工具自动发现
├── base.py          # ToolBase ABC + ToolRegistry
├── utils.py         # 命令执行辅助
├── seqkit_tool.py   # 序列处理工具
├── qc_tool.py       # 质控工具
├── assembly_tool.py  # 组装工具
├── alignment_tool.py # 比对工具
├── taxonomy_tool.py # 分类工具
├── evolution_tool.py # 进化分析工具
├── other_tool.py    # 其他工具
├── viz_tool.py     # 可视化工具
│
├── search_tool.py   # [v2.0] 联网搜索工具
├── text_tool.py     # [v2.0] 文本处理工具
├── vitaldb_updater.py # [v2.0] VITALdb 知识库工具
├── web_fetch_tool.py # [v2.0] 网页抓取工具
└── knowledge_tool.py # [v2.0] 知识库工具
```

#### 工具基类架构

```
┌─────────────────────────────┐
│      ToolBase (ABC)         │
├─────────────────────────────┤
│ + tool_name: str            │
│ + description: str          │
│ + execute(**kwargs): Dict    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      ToolRegistry           │  ◀── 单例模式
├─────────────────────────────┤
│ + register(tool)             │
│ + get(name)                  │
│ + list_tools()               │
│ + to_openai_functions()     │
└─────────────────────────────┘
```

### 3. 工作流模块 (`workflow/`)

```
workflow/
├── __init__.py
├── engine.py           # WorkflowEngine
├── runner_tool.py      # 工作流工具
├── virus_analysis.yaml # 病毒分析工作流
├── quality_check.yaml  # 质控工作流
└── phylogenetic_analysis.yaml # 进化分析工作流
```

### 4. Web 模块 (`web/`)

```
web/
├── __init__.py
├── app.py         # Gradio 应用
└── components.py  # 自定义组件
```

---

## 技术架构图

### 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              用户层                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│  │  Web UI    │    │  CLI REPL   │    │   API       │               │
│  │ (Gradio)   │    │  (命令行)   │    │  (REST)     │               │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘               │
└─────────┼───────────────────┼───────────────────┼─────────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             入口层                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         run.py                                   │   │
│  │  python run.py --mode [cli|web|api] --port 7861               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             核心层                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        BioAgent                                  │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │              单轮 FC 循环 (chat 方法)                    │   │   │
│  │  │  • 消息构建 → LLM调用 → 工具执行 → 结果回填 → 循环          │   │   │
│  │  │  • max_tool_rounds 控制最大轮次                         │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  │                                                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │   │
│  │  │   (Planner) │  │  (Executor) │  │   Memory               │ │   │
│  │  │   (保留)     │  │   (保留)     │  │ (会话管理+SQLite)      │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             工具层                                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  SeqKit    │  │   FastP    │  │  Minimap2  │  │   IQ-Tree  │  ... │
│  │  (序列)    │  │   (质控)   │  │   (比对)   │  │  (进化)    │       │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘       │
│                                                                   ┌────┐ │
│  ┌─────────────────────────────────────────────────────────────┐ │ viz │ │
│  │                    ToolRegistry (35 tools)                 │ │     │ │
│  └─────────────────────────────────────────────────────────────┘ └────┘ │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        工作流（知识参考）                                │
│  • Workflow 不再注册为工具                                              │
│  • 工作流信息写入系统提示词作为知识库参考                                │
│  • 用户明确要求时才使用 workflow_run（需手动开启）                      │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             外部服务                                     │
│  ┌──────────────────────┐    ┌──────────────────────────────┐        │
│  │     Ollama LLM       │    │    生信命令行工具              │        │
│  │  (qwen3:4b 模型)     │    │  (seqkit, fastp, iqtree...)  │        │
│  └──────────────────────┘    └──────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 数据流

```
用户请求: "对 sample.fastq 进行质控"

                              ┌─────────────────────────┐
                              │      BioAgent.chat()    │
                              └────────────┬────────────┘
                                           │
              ┌──────────────────────────────┼──────────────────────────────┐
              │                              │                              │
              ▼                              ▼                              │
┌─────────────────────────┐    ┌─────────────────────────┐                │
│  构建消息:              │    │  LLM 判断               │                │
│  - system prompt        │    │  需要调用工具?          │                │
│  - tools (35个)        │    │                         │                │
└────────────┬───────────┘    └────────────┬───────────┘                │
             │                              │                              │
             │                              ▼                              │
             │                    ┌─────────────────────────┐                │
             │                    │  是: tool_calls        │                │
             │                    │  → fastp_qc           │                │
             │                    └────────────┬───────────┘                │
             │                             │                              │
             │                             ▼                              │
             │                    ┌─────────────────────────┐                │
             │                    │  执行工具               │                │
             │                    │  fastp -i sample.fq   │                │
             │                    └────────────┬───────────┘                │
             │                             │                              │
             │                             ▼                              │
             │                    ┌─────────────────────────┐                │
             │                    │  回填工具结果          │                │
             │                    │  → messages            │                │
             │                    └────────────┬───────────┘                │
             │                             │                              │
             │                             ▼                              │
             │                    ┌─────────────────────────┐                │
             │                    │  再次调用 LLM          │                │
             │                    │  (无 tool_calls)       │◀─────────────┘
             │                    └────────────┬───────────┘ 循环
             │                              │
             │                              ▼
             │                    ┌─────────────────────────┐
             │                    │  返回最终回复           │
             │                    └─────────────────────────┘
             │                              │
             └──────────────────────────────┘
                              │
                              ▼
                     返回分析结果
```

**与旧架构对比**：
- 旧：Planner(额外LLM) → Executor(额外LLM) → Summarizer(额外LLM) = 3-4 次调用
- 新：FC循环 = 1-3 次调用，每次都有真实工具执行支撑

---

## 快速开始

### 1. 安装依赖

```bash
# 克隆或进入项目目录
cd projects/agent

# 安装 Python 依赖
pip install -r requirements.txt

# 或使用 conda
conda env create -f environment.yml
conda activate bioagent
```

### 2. 配置

```bash
# 复制配置示例
cp config.yaml.example config.yaml

# 编辑配置
vim config.yaml
```

### 3. 启动

```bash
# 命令行模式
python run.py --mode cli

# Web UI 模式
python run.py --mode web --port 7861

# 检查工具可用性
python manage.py check-tools

# 检查 LLM 连接
python manage.py check-llm
```

---

## 配置说明

### config.yaml 完整配置

```yaml
# LLM 配置
llm:
  base_url: "http://localhost:11434"  # Ollama 地址
  model: "qwen3:4b"                   # 模型名称
  temperature: 0.7                      # 温度参数
  timeout: 300                         # 超时时间(秒)
  max_tokens: 4096                     # 最大token

# 路径配置
paths:
  tools_dir: "tools"
  knowledge_dir: "knowledge"
  workflow_dir: "workflow"
  data_dir: "data"
  reports_dir: "reports"
  example_dir: "example"

# 工具路径
tools:
  seqkit: "/path/to/seqkit"
  fastp: "/path/to/fastp"
  # ...

# Agent 配置
agent:
  max_tool_rounds: 10        # 最大工具调用轮次
  enable_planner: true       # 启用 Planner 模式
  planner_threshold: 2       # 复杂度阈值
  default_threads: 4         # 默认线程数
  command_timeout: 600       # 命令超时

# Web UI 配置
web:
  enable: false
  port: 7861
  share: false
  debug: false

# 数据库配置
database:
  type: "sqlite"
  path: "data/sessions/bioagent.db"
```

### api_providers.yaml - 多 API 配置

BioAgent 支持配置多个 LLM 供应商，启动时自动检测可用性并让用户选择：

```yaml
# api_providers.yaml
providers:
  # ========== 本地 Ollama ==========
  - name: "本地 Ollama"
    type: "ollama"
    base_url: "http://localhost:11434"
    api_key: ""
    models:
      - "qwen3:4b"
      - "deepseek-r1:7b"
    auto_discover: true  # 自动发现本地已下载模型

  # ========== 心流 API ==========
  - name: "心流 API"
    type: "openai_compatible"
    base_url: "https://apis.iflow.cn/v1"
    api_key: "sk-xxx"
    models:
      - "qwen3-32b"
      - "deepseek-r1"
```

**配置说明：**
| 字段 | 说明 |
|------|------|
| `name` | 供应商显示名称 |
| `type` | 类型：`ollama` 或 `openai_compatible` |
| `base_url` | API 地址 |
| `api_key` | API 密钥（本地模型可为空）|
| `models` | 可用模型列表（静态）|
| `auto_discover` | 是否自动发现本地模型（Ollama 专用）|

---

## 使用指南

### 1. 命令行模式

```bash
$ python run.py --mode cli

==================================================
BioAgent - 生物信息学分析助手
==================================================
[自动检测] 扫描可用 API...
[1] 本地 Ollama - 可用 - qwen3:4b, deepseek-r1:7b, deepseek-r1:32b
[2] 心流 API - 可用 - qwen3-32b, deepseek-r1
选择模型 (1-2): 1
已选择: 本地 Ollama - qwen3:4b

输入您的分析需求，输入 'quit' 或 'exit' 退出

用户> 统计 test.fa 文件的序列数量

BioAgent> 已完成序列统计...
```

**命令行模式特点：**
- 启动时自动检测 `api_providers.yaml` 中配置的 API 可用性
- 显示每个供应商的状态、模型数量
- 用户输入编号选择要使用的模型
- 选择后初始化 Agent 开始对话

### 2. Web UI 模式

```
访问 http://localhost:7861

功能:
- 文件上传 (支持 FASTA/FASTQ)
- 实时对话
- 模型下拉选择（自动检测可用模型）
- 刷新按钮重新检测
- 查看工具状态
- 分析历史
```

**Web UI 模型切换：**
- 页面加载时自动检测所有配置的 API
- 顶部模型下拉框显示可用模型
- 切换模型即时生效，无需重启

### 3. 编程使用

```python
from core.agent import BioAgent

# 创建 Agent
agent = BioAgent()

# 对话
response = agent.chat("统计 sequences.fasta 的序列数量")
print(response)

# 查看工具列表
print(f"可用工具: {len(agent.tools)}")

# 重置对话
agent.reset_conversation()
```

### 4. 三角色 Agent 模式 (v2.0)

v2.0 引入了三角色 Agent 系统，支持更复杂的任务处理：

```python
from core.agent import BioAgent

# 创建 Agent
agent = BioAgent()

# 三角色模式 (Ask-Plan-Craft)
# 自动进行需求理解、技术规划、任务执行
response = agent.chat_v2("帮我完整分析这个病毒序列")
print(response)
```

**三角色工作流程：**

1. **Ask Agent** - 需求理解与多轮澄清（最多3轮）
2. **Plan Agent** - 技术路线规划 + 数据流校验
3. **Craft Agent** - 按计划执行 + 生成分析报告

**启用方式：**
- 方式1：配置 `config.yaml` 中 `multi_agent.enable: true`
- 方式2：直接调用 `agent.chat_v2()` 自动启用

### 5. 结果保存

所有分析结果自动保存到 `reports/` 目录：

```python
# 结果自动保存到 reports/analysis_YYYYMMDD_HHMMSS.md
agent.chat("统计 sequences.fasta 的序列数量")
# 同时返回保存路径
```

### 6. 工作流使用

```python
# 使用预定义工作流
agent.chat("运行病毒分析工作流，输入文件是 sample.fastq")
```

---

## 工具列表

| 类别 | 工具 | 说明 |
|------|------|------|
| **序列处理** | seqkit | FASTA/FASTQ 序列处理 |
| **质控** | fastp, fastqc, multiqc, cutadapt | 质量控制与预处理 |
| **组装** | spades, megahit | 基因组组装 |
| **比对** | bwa, minimap2, samtools, blastn, diamond | 序列比对 |
| **分类** | kraken2 | 物种分类 |
| **多序列比对** | mafft, trimal | 多序列比对与修剪 |
| **进化分析** | iqtree2, codeml | 系统发育分析 |
| **可视化** | plot_sequence_quality, plot_gc_content | 数据可视化 |
| **联网搜索** | web_search | 联网搜索相关信息 |
| **网页抓取** | web_fetch | 抓取URL全文内容（支持微信公众号） |
| **文本处理** | text_processing | PDF/文献总结与信息提取 |
| **知识库** | vitaldb_search | VITALdb 病毒工具知识库 |

---

## 常见问题

### Q: 如何添加新的工具？

A: 在 `tools/` 目录下创建新的工具文件，继承 `ToolBase`：

```python
from .base import tool

@tool(name="my_tool", description="我的工具")
def my_tool(param: str) -> dict:
    # 实现逻辑
    return {"result": "..."}
```

### Q: 如何自定义 Planner 提示词？

A: 修改 `core/prompts.py` 文件中的模板。

### Q: LLM 连接失败怎么办？

A: 检查 Ollama 服务：
```bash
# 启动 Ollama
ollama serve

# 检查模型
ollama list
```

---

## 项目结构

```
bioagent/
├── run.py                  # 启动入口
├── manage.py               # 管理脚本
├── config.yaml             # 默认配置文件
├── api_providers.yaml      # 多 API 供应商配置
├── config_loader.py        # 配置加载器
├── push_github.sh          # GitHub 推送脚本
├── requirements.txt        # Python 依赖
├── environment.yml         # Conda 环境
│
├── core/                   # 核心模块
│   ├── agent.py            # BioAgent 主控类
│   ├── planner.py           # 任务规划器（保留）
│   ├── executor.py         # 工具执行器（保留）
│   ├── memory.py           # 会话记忆管理
│   ├── prompts.py          # 提示词模板
│   └── provider_manager.py # 多 API 管理
│
├── tools/                  # 工具模块 (37 tools)
│   ├── base.py
│   ├── utils.py
│   └── *.py
│
├── workflow/               # 工作流引擎
│   ├── engine.py
│   └── *.yaml
│
├── knowledge/              # 知识库
│   └── *.md
│
├── web/                   # Web UI
│   ├── app.py
│   └── components.py
│
└── data/                  # 数据目录
    ├── sessions/
    ├── uploads/
    └── cache/
```

---

## License

MIT License
