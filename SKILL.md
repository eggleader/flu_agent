---
name: 流感生物信息学分析 Agent
slug: bio-agent
version: 3.0.0
homepage: https://example.com/skills/bio-agent
description: "生物信息学分析 Agent，集成 26 个生信工具和 3 个预设工作流。支持序列处理、质控、组装、比对、分类、进化分析和工作流自动化编排。基于 Ollama LLM + Function Calling 构建。"
changelog: |
  - 3.0.0: 新增工作流引擎、19 个生信工具封装、3 个预设工作流、示例文件
  - 2.0.0: 重构为 BioAgent，支持 Function Calling 和工具自动发现
  - 1.0.0: 基础 AI Agent
metadata: {"clawdbot":{"emoji":"🦠","os":["linux","darwin","win32"]}}
---

## 功能特性

- **26 个生信工具**: 序列处理(seqkit)、质控(fastp/fastqc/multiqc)、组装(spades/megahit)、比对(minimap2/samtools/blastn/diamond)、分类(kraken2)、进化分析(mafft/trimal/iqtree2/codeml)、蛋白结构(hhblits/hhsearch)、其他(swarm/circos)
- **工作流引擎**: YAML 定义的自动化流水线，支持步骤间参数传递、错误处理、条件执行
- **3 个预设工作流**: 病毒全流程分析、质控报告、系统发育分析
- **LLM 驱动**: Ollama + qwen3:4b，Function Calling 自动选择工具
- **知识库注入**: 流感领域知识 + 工具使用指南 + 工作流指南
- **可扩展**: 新增工具只需创建 Python 文件，新增工作流只需添加 YAML 文件

## 快速开始

```bash
cd skills/basic-agent
python agent.py
```

使用示例：
```
> 统计 example/sample_sequences.fasta 的序列信息
> 对 example/sample.fastq 进行质控
> 运行病毒分析工作流，输入文件 example/sample.fastq
> 用 example/sample_sequences.fasta 构建系统发育树
```

## 已集成工具

| 分类 | 工具 | 功能 |
|------|------|------|
| 序列处理 | seqkit_stats/fx2tab/grep/rmdup/sort | 统计/转换/搜索/去重/排序 |
| 质控 | fastp_qc/fastqc_report/multiqc_report/cutadapt_trim | 质控过滤/报告/汇总/接头去除 |
| 组装 | spades_assembly/megahit_assembly | 小基因组组装/宏基因组组装 |
| 比对 | minimap2_map/samtools_process/blastn_search/diamond_search | 序列映射/BAM处理/核酸比对/蛋白比对 |
| 分类 | kraken2_classify | 快速物种分类 |
| 进化 | mafft_align/trimal_trim/iqtree_build/codeml_analyze | 多序列比对/裁剪/建树/选择压力 |
| 蛋白 | hhblits_search/hhsearch_search | 远程同源搜索/HMM比对 |
| 其他 | swarm_cluster/circos_plot | OTU聚类/基因组可视化 |
| 工作流 | workflow_run/workflow_list | 执行/查询工作流 |

## 预设工作流

| 工作流 | 步骤 | 触发关键字 |
|--------|------|-----------|
| virus_analysis | fastp质控 → SPAdes组装 → seqkit统计 → BLASTn鉴定 | 病毒分析、分析fastq |
| quality_check | fastp → fastqc → seqkit统计 → MultiQC汇总 | 质控、QC |
| phylogenetic_analysis | seqkit统计 → mafft比对 → trimal裁剪 → iqtree建树 | 系统发育、进化树 |

## 扩展指南

详见 `knowledge/workflow_guide.md`
