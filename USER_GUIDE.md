# Historical Note

This user guide predates the next-generation V4 truth layer. Use
`docs/NEXT_GEN_V4_TRUTH_LAYER.md` for the current 20-stage workflow,
`WorkflowAPI`, agent harness, and validation commands.

# ResearchPaperWorkflow v4 — 完整操作指南

**面向科研人员的多智能体论文写作工作流 · 从零到投稿的完整手册**

Version 4.0.0 · June 2026

---

## 目录

1. [快速入门：10分钟上手](#1-快速入门10分钟上手)
2. [核心概念：理解工作流](#2-核心概念理解工作流)
3. [五步工作流详解](#3-五步工作流详解)
4. [五大工作模式](#4-五大工作模式)
5. [Agent体系：你的AI科研团队](#5-agent体系你的ai科研团队)
6. [质量门：41项自动检查](#6-质量门41项自动检查)
7. [配置与定制](#7-配置与定制)
8. [真实案例演练](#8-真实案例演练)
9. [常见问题排查](#9-常见问题排查)
10. [最佳实践与建议](#10-最佳实践与建议)
11. [快速参考卡](#11-快速参考卡)

---

## 1. 快速入门：10分钟上手

### 1.1 这是什么？

ResearchPaperWorkflow 是一个**AI驱动的科研论文写作系统**。

**你可以用它做什么：**
- 🚀 从研究想法开始，自动完成文献检索、数据分析、论文写作、审稿模拟、修订润色
- 🔍 自动检查论文中的数据完整性、引用准确性、统计报告规范性
- 🤖 让12个专业AI Agent协作完成论文（策略规划、文献调研、数据分析、统计审核、写作指导...）
- ✅ 41项自动质量门确保论文达到投稿标准

### 1.2 安装

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/ResearchPaperWorkflow_v2.git
cd ResearchPaperWorkflow_v2

# 2. 安装核心依赖
pip install -e .

# 3. （可选）安装可视化依赖
pip install -e ".[plotting]"

# 4. （可选）安装全部依赖
pip install -e ".[full]"

# 5. 验证安装
python -m paper_workflow.cli --help
```

你应该看到10个子命令：`create-project`、`status`、`run-pipeline`、`checkpoint`、`run-integrity-gate`、`diagnose-gate-failures`、`detect-artifact-drift`、`sync-artifact-stale`、`list-papers`、`strategy`。

### 1.3 创建第一个论文项目

```bash
python -m paper_workflow.cli create-project \
  --idea "Single-cell transcriptomics reveals immune cell infiltration in kidney disease" \
  --field "single-cell, nephrology, immunology" \
  --journal "Genome Biology"
```

这条命令会自动完成4件事：
1. 生成研究策略（主题评估 → 期刊匹配 → 假设生成 → 可行性报告）
2. 在 `papers/` 下创建论文目录
3. 初始化项目护照 (`project_passport.yaml`)
4. 设置管线状态为 `ready`

### 1.4 查看项目状态

```bash
# 查看所有论文项目
python -m paper_workflow.cli list-papers

# 查看特定项目的管线进度
python -m paper_workflow.cli status --paper <paper_id>
```

**状态图标含义：**

| 图标 | 含义 |
|------|------|
| `[OK]` | 阶段已成功完成 |
| `[..]` | 阶段正在运行 |
| `[FAIL]` | 阶段失败 |
| `[STALE]` | 阶段需要重新运行（上游文件已改变） |
| `[   ]` | 待执行 |
| `[BLOCK]` | 被上游失败阻塞 |
| `[SKIP]` | 跳过（此类型论文不需要） |

### 1.5 运行管线

```bash
# 自动模式运行
python -m paper_workflow.cli run-pipeline --paper <paper_id>

# 遇到失败立即停止
python -m paper_workflow.cli run-pipeline --paper <paper_id> --stop-on-failure
```

管线会在**人类检查点**（标记 `[CP]`）自动暂停，等待你的审核决定：

```bash
python -m paper_workflow.cli checkpoint \
  --paper <paper_id> \
  --stage "research_plan" \
  --decision "approved" \
  --notes "研究设计合理，继续数据分析阶段"
```

### 1.6 运行质量检查

```bash
# 运行全部41项完整性检查
python -m paper_workflow.cli run-integrity-gate --paper <paper_id>

# 诊断失败原因
python -m paper_workflow.cli diagnose-gate-failures --paper <paper_id>
```

---

## 2. 核心概念：理解工作流

### 2.1 四层架构

整个系统分为四层，从上到下依次是：

```
┌─────────────────────────────────────────────┐
│  STRATEGY（策略层）                          │
│  研究问题定义 → 期刊匹配 → 可行性 → 假设       │
├─────────────────────────────────────────────┤
│  DECISION（决策层）                          │
│  技能调度 → MCP工具路由 → 管线循环引擎         │
├─────────────────────────────────────────────┤
│  EXECUTION（执行层）                         │
│  18阶段管线 → 质量门 → CLI命令                │
├─────────────────────────────────────────────┤
│  SUPERVISION（监督层）                       │
│  护照追踪 → 溯源审计 → 完整性 → 过期检测       │
└─────────────────────────────────────────────┘
```

**关键理解：**
- **策略层**决定"做什么研究"——从不清晰的想法到结构化的研究方案
- **决策层**决定"如何调度"——何时调用哪个AI Agent、哪个技能、哪个工具
- **执行层**负责"具体执行"——运行分析、写作文本、检查质量
- **监督层**确保"不出错"——所有制品有哈希追踪、文本声称可溯源到数据

### 2.2 护照系统：一切皆有记录

每个论文项目维护4个护照文件，确保全程可审计：

```
papers/<paper_id>/
├── project_passport.yaml    # 项目身份：ID、标题、期刊、管线状态（7种状态）
├── artifact_ledger.jsonl    # 制品日志：每个输出文件的SHA-256哈希
├── checkpoint_ledger.jsonl  # 检查点日志：每次人工审批决定
└── integrity_ledger.jsonl   # 完整性日志：每次质量门事件
```

**为什么重要：** 如果你的某个分析结果被更新了（比如重新跑了一次聚类），护照系统会自动检测到哈希变化，然后把所有依赖这个结果的下游阶段标记为STALE。

### 2.3 管线状态机

管线有7种状态，反映当前论文项目的健康状况：

| 状态 | 含义 | 你需要做什么 |
|------|------|-------------|
| `clean` | 一切正常 | 继续下一阶段 |
| `in_progress` | 有阶段在运行 | 等待完成 |
| `drift_detected` | 制品哈希不匹配 | 运行 `sync-artifact-stale` |
| `stale_stages` | 下游阶段需要重跑 | 重新运行STALE阶段 |
| `gate_failure` | 质量门失败 | 运行 `diagnose-gate-failures` |
| `blocked` | 无法继续 | 解决阻塞问题 |
| `ready` | 初始化完成，等待开始 | 运行管线 |

---

## 3. 五步工作流详解

### Phase 1: 研究与规划（4个阶段）

```
select_topic → target_journal → literature_search → formulate_hypotheses
     [CP]                                                    [CP]
```

**做什么：** 将模糊的研究想法转化为有假设、有期刊目标、有文献基础的结构化方案。

**调用Agent：** `research_strategist` + `literature_reviewer`

**产出物：**
- `strategy/research_strategy.yaml` — 完整研究策略
- `strategy/journal_profile.md` — 目标期刊要求清单
- `strategy/feasibility_decision.md` — 可行性评估（go/no-go）
- 文献检索结果和假设文档

**人工检查点：**
1. **select_topic完成后**：审核研究方向和选题创新性
2. **formulate_hypotheses完成后**：审核假设框架是否合理

**CLI命令：**
```bash
# 单独运行Phase 1
python -m paper_workflow.e2e_workflow --paper-id <id> --phases 1

# 仅做策略评估（不创建完整项目）
python -m paper_workflow.cli strategy \
  --idea "your idea" --field "your field" --journal "target journal"
```

### Phase 2: 数据与方法（4个阶段）

```
data_audit → figure_planning → run_analysis → verify_methods
                 [CP]
```

**做什么：** 审核数据质量、设计图表架构、执行分析、验证方法可复现性。

**调用Agent：** `data_auditor` + `figure_planner` + `analysis_executor` + `pipeline_engineer` + `statistician`

**产出物：**
- `data/data_audit_report.md` — 数据质量报告
- `data/data_inventory.yaml` — 数据清册
- `results/` — 所有分析输出（表格、统计结果）
- `strategy/figure_plan.yaml` — 图表规划

**关键：** run_analysis和figure_planning可以部分并行——数据审计通过后，图表规划和分析执行可同时启动。

**人工检查点：**
- **figure_planning完成后**：确认图表布局和分析路线图

### Phase 3: 论文写作（4个阶段）

```
write_methods → write_results → write_introduction → write_discussion
    [CP]           [CP]              [CP]               [CP]
```

**做什么：** 按IMRAD结构撰写论文各个部分。

**调用Agent：** `report_writer`

**并行策略：** Methods和Results几乎可以同时写（都依赖分析输出），Introduction和Discussion可以随后并行（Introduction只依赖文献，Discussion依赖Results）。

**写作标准：**
- 完整段落（禁止项目符号）
- 精确p值 + 效应量 + 置信区间
- 每个数字可追溯到分析输出
- Methods参数与代码完全一致

**人工检查点：** 每个部分完成后均可审核。

### Phase 4: 组装与审稿（3个阶段）

```
assemble_manuscript → integrity_check → internal_review
      [CP]                                  [CP]
```

**做什么：** 组装完整手稿、运行41项质量门、5人模拟同行评审。

**调用Agent：** `report_writer` + `integrity_checker` + `team_orchestrator`

**产出物：**
- `manuscript/manuscript_assembled.md` — 组装好的手稿
- `integrity/integrity_report.md` — 完整性检查报告
- `review/internal_review_report.md` — 5人模拟审稿报告

**质量门（41项）：**
- 17项CRITICAL：阻塞管线，必须修复
- 21项HIGH：警告，需记录或修复
- 3项MEDIUM：建议，不阻塞

**人工检查点：**
1. **assemble_manuscript完成后**：审核全文草稿
2. **internal_review完成后**：审核模拟同行评审意见

### Phase 5: 修订与定稿（3个阶段）

```
apply_revision → re_review → finalize
                     [CP]         [CP]
```

**做什么：** 根据审稿意见修订、重新审查、生成最终投稿包。

**调用Agent：** `report_writer` + `integrity_checker`

**修订循环：** `apply_revision → re_review` 可以循环最多5次，直到审稿通过。

**最终产出物：**
```
submission/
├── manuscript_final.pdf       # 最终PDF
├── manuscript_final.docx      # Word版本
├── manuscript_final.tex       # LaTeX源文件
├── cover_letter.md            # 投稿信
├── supplementary_package.zip  # 补充材料包
├── provenance_report.json     # 溯源报告
└── data_availability_statement.md
```

---

## 4. 五大工作模式

### 模式1：完整研究（Full Research）
```
适用：有原始数据，从零开始的新项目
流程：Phase 1 → 2 → 3 → 4 → 5（全部18个阶段）
```

```bash
# 创建项目
python -m paper_workflow.cli create-project \
  --idea "你的研究想法" --field "领域关键词" --journal "目标期刊"

# 运行全部5阶段（在检查点暂停）
python -m paper_workflow.e2e_workflow --paper-id <id> --phases 1,2,3,4,5 --stop-at-checkpoint
```

### 模式2：从结果快速写作（From Results）

```
适用：分析已完成，有结果和图表，只需要论文写作
流程：Phase 3 → 4 → 5（跳过研究和分析阶段）
```

```python
from paper_workflow.workflow import PaperWorkflow
from paper_workflow.engine.loop_engine import StageStatus

wf = PaperWorkflow()
wf.initialize(idea="...", field="...", journal="...")

# 标记早期阶段为手动完成
skip_stages = ["search_literature", "research_plan", "data_audit",
               "figure_planning", "run_analysis", "verify_methods"]
for s in skip_stages:
    wf.engine.stages[s].status = StageStatus.COMPLETED

# 把已有结果放入 papers/<paper_id>/results/
# 把已有图表放入 papers/<paper_id>/figures/

# 从写作阶段开始
wf.run(stop_at_checkpoint=True)
```

### 模式3：修订循环（Revision Cycle）

```
适用：收到审稿意见后的修回
流程：diagnose → apply_revision → re_review → quality_check → finalize
```

```bash
# 1. 诊断问题
python -m paper_workflow.cli diagnose-gate-failures --paper <paper_id>

# 2. 修复问题后，运行修订管线
python -m paper_workflow.cli run-pipeline --paper <paper_id>
# 这会自动运行 apply_revision → re_review → quality_check → finalize

# 3. 确认修订满意
python -m paper_workflow.cli checkpoint \
  --paper <paper_id> --stage re_review --decision approved
```

### 模式4：方法学论文（Methods Paper）

```
适用：工具/方法/软件论文
特点：侧重验证和基准测试，跳过假设生成
阶段数：约13个（跳过假设和研究规划的某些阶段）
```

在创建项目时指定类型：
```python
wf.initialize(idea="...", field="...", journal="Bioinformatics", paper_type="methods")
```

### 模式5：文献综述（Literature Review）

```
适用：系统综述或叙述性综述
特点：侧重文献检索和综合，跳过原始数据分析
阶段数：约12个
```

```python
wf.initialize(idea="...", field="...", journal="...", paper_type="review")
```

---

## 5. Agent体系：你的AI科研团队

### 5.1 12个核心Agent

| Agent | 角色 | 负责阶段 | 核心技能 |
|-------|------|---------|---------|
| **research_strategist** | 研究策略师 | ①②④ | 选题、期刊匹配、假设生成 |
| **literature_reviewer** | 文献审阅员 | ③ | 文献检索、书目管理、证据综合 |
| **data_auditor** | 数据审计师 | ⑤ | 数据质量、批次效应检测 |
| **figure_planner** | 图表规划师 | ⑥ | 图表架构、配色设计 |
| **analysis_executor** | 分析执行者 | ⑦ | 运行R/Python分析管线 |
| **pipeline_engineer** | 管线工程师 | ⑦⑧ | 环境管理、可复现性验证 |
| **statistician** | 统计师 | ⑧ | 统计方法审核、检验选择 |
| **report_writer** | 报告撰写员 | ⑨⑩⑪⑫⑬⑯ | IMRAD写作、格式调整 |
| **integrity_checker** | 完整性检查员 | ⑧⑭⑱ | 41项质量门执行 |
| **multi_omics_integrator** | 多组学整合师 | ⑦⑧ | MOFA、DIABLO等跨组学分析 |
| **code_librarian** | 代码管理员 | ⑦⑧⑱ | 代码库维护、复用 |
| **team_orchestrator** | 团队协调员 | ⑮⑰ | 任务分解、并行调度 |

### 5.2 6个医学专用Agent（v3.0新增）

| Agent | 角色 |
|-------|------|
| **causal_inference_reviewer** | 因果推断审核（MR/中介分析） |
| **clinical_methodologist** | 临床方法学家 |
| **ethics_compliance_auditor** | 伦理合规审计 |
| **external_validation_planner** | 外部验证规划 |
| **novelty_killer** | 创新性挑战者（魔鬼代言人） |
| **reviewer_simulator** | 同行审稿模拟 |

### 5.3 Agent责任边界

每个Agent有严格的"我做/我不做"边界：

> **research_strategist**: 我定义研究问题、评估可行性 —— 但我不运行代码、不亲自搜索文献
>
> **data_auditor**: 我评估数据质量 —— 但我不修改数据、不写论文
>
> **statistician**: 我审核统计方法 —— 但我不修改数据、不代替写作
>
> **report_writer**: 我写所有IMRAD段落 —— 但我不运行分析、不检查引用完整性

---

## 6. 质量门：41项自动检查

### 6.1 质量门体系

```
G1 引用完整性 (4 CRITICAL)
G2 声称-证据绑定 (2 CRITICAL)
G3 内容规范 (5 CRITICAL + HIGH)
G4 数据与代码 (3 HIGH)
G5 统计规范 (3 HIGH)
G6 格式规范 (3 MEDIUM)
加上医学专用 25 个门 (v3.0)
```

### 6.2 CRITICAL规则（阻塞管线，必须修复）

| # | 门名称 | 检查内容 |
|---|--------|---------|
| C1 | `bibtex_citation_existence` | 每次 `\cite{}` 必须在 references.bib 中有对应条目 |
| C2 | `citation_evidence_traceability` | 每个事实性声称可追溯到引用证据 |
| C3 | `results_no_citations` | Results部分不得引用外部文献 |
| C4 | `claim_artifact_binding` | 每个数值声称可追溯到具体分析文件 |
| C5 | `figures_referenced` | 每次 `\ref{fig:...}` 指向真实存在的文件 |

### 6.3 失败后的处理流程

```
CRITICAL失败 → 管线阻塞
  → integrity_checker 生成 integrity_report.json + .md
  → 你运行 diagnose-gate-failures 查看详情
  → team_orchestrator 路由到负责Agent：
      • 引用问题 → literature_reviewer
      • 声称绑定 → report_writer
      • 统计问题 → statistician
      • 格式问题 → report_writer
  → 修复后重新运行 integrity_check
  → 所有决定记录到 checkpoint_ledger.jsonl
```

---

## 7. 配置与定制

### 7.1 核心配置文件

| 文件 | 用途 | 何时修改 |
|------|------|---------|
| `config/default_config.yaml` | 主配置：管线阶段、论文类型、质量门、写作标准、技能路由、Agent定义 | 改变全局行为 |
| `config/journal_database.yaml` | 25个期刊配置文件 | 添加/更新目标期刊 |
| `config/templates/` | 论文各部分模板 | 自定义段落结构 |
| `papers/<paper_id>/paper_config.yaml` | 单项目覆盖配置 | 为特定论文定制 |

### 7.2 添加新期刊

编辑 `config/journal_database.yaml`：

```yaml
journals:
  Your Journal Name:
    full_name: "Full Journal Name"
    impact_factor: X.X
    category: specialty-high
    format_type: LaTeX
    citation_style: Vancouver
    abstract_word_limit: 250
    figure_limit: 8
    main_text_word_limit: 5000
    requires_data_availability: true
    requires_code_availability: true
    open_access: false
    submission_system: "Editorial Manager"
    special_requirements:
      - "要求1"
      - "要求2"
    scope_keywords:
      - 关键词1
      - 关键词2
```

### 7.3 支持的论文类型

| 类型 | 管线模式 | 说明 |
|------|---------|------|
| `original_research` | 完整18阶段 | 标准IMRAD、所有报告指南 |
| `methods` | 方法学集中 | 侧重验证+基准测试 |
| `review` | 综述模式 | 侧重文献检索+综合 |
| `clinical_research` | 完整+临床 | 增加伦理+临床统计门 |
| `data_resource` | 数据集中 | 侧重数据审计+可用性 |
| `brief_communication` | 精简模式 | 更严格限制、合并段落 |

### 7.4 自定义质量门

在 `paper_config.yaml` 中覆盖默认质量门设置：

```yaml
quality_gates:
  g12_no_bullets_in_prose:
    enabled: false          # 关闭某一项检查
  g13_statistics_reported:
    severity: CRITICAL      # 将HIGH提升为CRITICAL
```

---

## 8. 常见问题排查

### Q1：`pip install -e .` 失败显示 "No module named setuptools"

```bash
pip install --upgrade setuptools wheel
pip install -e .
```

### Q2：`ModuleNotFoundError: No module named 'paper_workflow'`

确保以开发模式安装：
```bash
pip install -e .
```
验证入口点：
```bash
paper-workflow --help
```

### Q3：管线显示 BLOCKED

```bash
# 步骤1：诊断
python -m paper_workflow.cli diagnose-gate-failures --paper <paper_id>

# 查看输出中的：
#   - failed_stages：出错的阶段
#   - gate_failures：失败的完整性规则
#   - stale stages：需要重跑的阶段

# 步骤2：先修复CRITICAL失败（它们阻塞管线）

# 步骤3：重新运行质量门
python -m paper_workflow.cli run-integrity-gate --paper <paper_id>

# 步骤4：重新运行管线
python -m paper_workflow.cli run-pipeline --paper <paper_id>
```

### Q4：阶段标记为STALE（制品漂移）

这意味着上游输出文件被修改了，使用了该文件的下游阶段需要重新运行：

```bash
# 查看哪些文件发生了变化
python -m paper_workflow.cli detect-artifact-drift --paper <paper_id>

# 标记受影响的下游阶段为STALE
python -m paper_workflow.cli sync-artifact-stale --paper <paper_id>

# 重新运行管线（会优先处理STALE阶段）
python -m paper_workflow.cli run-pipeline --paper <paper_id>
```

### Q5：阶段重试次数耗尽

每个阶段默认最多重试3次：

```python
from paper_workflow.engine.loop_engine import PaperLoopEngine, StageStatus
from pathlib import Path

engine = PaperLoopEngine(Path.cwd(), '<paper_id>')
engine.stages['<failed_stage>'].status = StageStatus.PENDING
engine.stages['<failed_stage>'].retry_count = 0
engine.stages['<failed_stage>'].errors = []
engine._update_passport()
print('阶段已重置，可重新运行管线。')
```

### Q6：测试失败显示 "AGENTS.md not found"

框架通过`AGENTS.md`发现项目根目录，确保该文件存在：
```bash
ls AGENTS.md  # 应存在
```

### Q7："No bullets in prose" 完整性门失败

手稿正文必须使用自然段落，不能使用项目符号。只在图注、表格、补充材料中允许项目符号。

### Q8："Statistics reported" 完整性门失败

确保所有定量声明包含：
- 精确p值（不只是 "p < 0.05"）
- 效应量和置信区间（OR/HR/β/Cohen d + 95% CI）
- 检验统计量名称和值

**通过示例：**
> "Treated group showed significantly higher expression (log2FC = 1.42, 95% CI [1.12, 1.72], p = 0.003, Wald test)."

### Q9：如何查看和手动修复引用问题

```bash
# 检查引用完整性
python -m paper_workflow.cli run-integrity-gate --paper <paper_id>

# 如果有引用缺失，在以下位置添加：
# papers/<paper_id>/references/references.bib
```

### Q10：如何切换目标期刊

1. 编辑 `papers/<paper_id>/strategy/research_strategy.yaml`，更新 `target_journal`
2. 更新 `papers/<paper_id>/project_passport.yaml` 中的期刊名
3. 运行 `run-integrity-gate` 检查新期刊的格式合规性

---

## 10. 最佳实践与建议

### 10.1 项目组织

```
✅ 好的做法：
- 每个新研究一个独立的 paper_id
- 数据文件统一放在 papers/<paper_id>/data/ 下
- 分析代码放在 code_library/ 中以备复用
- 在 paper_config.yaml 中记录项目特定的配置

❌ 避免的做法：
- 在多个论文项目间共享 paper_id
- 硬编码绝对路径（会被质量门检测到）
- 跳过人工检查点（它们是质量控制的关键环节）
- 忽略 STALE 标记（下游阶段可能使用过时的结果）
```

### 10.2 写作建议

1. **先跑分析，后写论文**：确保Methods中报告的每个参数值都与实际代码一致
2. **每个数字可溯源**：使用 `claim_artifact_binding` 门验证
3. **Discussion要有局限性**：至少100字的局限性段落（H5门检查）
4. **定量结果要完整**：p值+效应量+置信区间+检验名
5. **Results不引用文献**：Discussion才是与文献对话的地方

### 10.3 质量门策略

- **CRITICAL失败（阻塞）**：必须修复才能继续管线
- **HIGH失败（警告）**：建议修复，如不修复需记录原因
- **MEDIUM失败（建议）**：信息性提示，不强制修复

### 10.4 检查点决策指南

在每个检查点，你有三种决策选项：

| 决策 | 含义 | 何时使用 |
|------|------|---------|
| `approved` | 通过，继续前进 | 内容符合预期 |
| `revision_needed` | 需要修改 | 方向正确但细节需调整 |
| `rejected` | 退回 | 需要重新规划 |

### 10.5 技能调度优先级

当你的请求匹配多个技能时，系统按以下优先级调度：

1. **领域特定分析**（如 `wgcna-analyst`）—— 最具体，最高优先级
2. **管线编排**（`academic-pipeline`）—— 如果要求 "端到端"/"完整工作流"
3. **核心写作**（`academic-paper`、`scientific-writing`等）
4. **研究搜索**（`deep-research`、`nature-academic-search`）
5. **质量审查**（`academic-paper-reviewer`、`ai-writing-detection`）
6. **语言润色**（`nature-polishing`、`humanizer`）
7. **图表制作**（`nature-figure`）
8. **引用管理**（`nature-citation`）

---

## 11. 快速参考卡

### 11.1 CLI命令速查

| 命令 | 用途 |
|------|------|
| `create-project --idea "..." --field "..." --journal "..."` | 创建新论文项目 |
| `status --paper <id>` | 显示管线状态 |
| `run-pipeline --paper <id> [--stop-on-failure]` | 运行管线 |
| `checkpoint --paper <id> --stage <s> --decision approved` | 批准检查点 |
| `run-integrity-gate --paper <id>` | 运行41项完整性检查 |
| `diagnose-gate-failures --paper <id>` | 诊断失败原因 |
| `detect-artifact-drift --paper <id>` | 检测文件变化 |
| `sync-artifact-stale --paper <id>` | 标记下游阶段过期 |
| `list-papers` | 列出所有论文项目 |
| `strategy --idea "..." --field "..." [--journal "..."]` | 仅评估策略 |

### 11.2 Makefile速查

| 命令 | 用途 |
|------|------|
| `make install` | 安装核心依赖 |
| `make test` | 运行所有测试 |
| `make init-paper IDEA="..." FIELD="..." JOURNAL="..."` | 创建论文项目 |
| `make status PAPER=<id>` | 查看状态 |
| `make run PAPER=<id>` | 运行管线 |
| `make integrity PAPER=<id>` | 运行完整性门 |
| `make list` | 列出所有论文 |
| `make clean` | 清理缓存文件 |

### 11.3 E2E Workflow速查

```python
from paper_workflow.e2e_workflow import E2EWorkflow

# 创建/加载
wf = E2EWorkflow(paper_id="paper_my_project", auto_load=True)

# 运行指定阶段
wf.run(phases=[1, 2])                          # 研究+分析
wf.run(phases=[3, 4, 5])                       # 写作+审稿+定稿
wf.run(phases=[1, 2, 3, 4, 5])                # 全流程
wf.run(phases=[1, 2, 3, 4, 5], stop_at_checkpoint=True)  # 每阶段暂停

# 试运行
wf.dry_run(phases=[1, 2])
```

### 11.4 18阶段快速查询

| # | 阶段 | 阶段 | Agent | CP |
|---|------|------|-------|-----|
| ① | select_topic | 1:Research | research_strategist | ✓ |
| ② | target_journal | 1:Research | research_strategist | - |
| ③ | literature_search | 1:Research | literature_reviewer | - |
| ④ | formulate_hypotheses | 1:Research | research_strategist | ✓ |
| ⑤ | data_audit | 2:Data | data_auditor | - |
| ⑥ | figure_planning | 2:Data | figure_planner | ✓ |
| ⑦ | run_analysis | 2:Data | analysis_executor | - |
| ⑧ | verify_methods | 2:Data | pipeline_engineer | - |
| ⑨ | write_methods | 3:Writing | report_writer | ✓ |
| ⑩ | write_results | 3:Writing | report_writer | ✓ |
| ⑪ | write_introduction | 3:Writing | report_writer | ✓ |
| ⑫ | write_discussion | 3:Writing | report_writer | ✓ |
| ⑬ | assemble_manuscript | 4:Assembly | report_writer | ✓ |
| ⑭ | integrity_check | 4:Assembly | integrity_checker | - |
| ⑮ | internal_review | 4:Assembly | team_orchestrator | ✓ |
| ⑯ | apply_revision | 5:Revision | report_writer | - |
| ⑰ | re_review | 5:Revision | team_orchestrator | ✓ |
| ⑱ | finalize | 6:Finalize | integrity_checker | ✓ |

CP = Human Checkpoint（人类检查点）

### 11.5 三个团队配置

| 团队 | 用途 | 组成 |
|------|------|------|
| `paper_writing_team` | 全周期手稿生产 | 全部12个Agent |
| `review_team` | 内部同行评审 | integrity_checker + statistician + literature_reviewer |
| `analysis_team` | 数据分析管线 | analysis_executor + pipeline_engineer + data_auditor |

---

## 附录：目录结构一览

```
ResearchPaperWorkflow_v2/
├── README.md                          # 项目概述
├── USER_GUIDE.md                      # 本操作指南
├── AGENTS.md                          # AI助手启动时读取的规则文件
├── ARCHITECTURE.md                    # 四层系统架构详解
├── AGENT_ROLES.md                     # 18个Agent协作体系
├── PIPELINE_DESIGN.md                 # 18阶段管线设计
├── QUALITY_GATES.md                   # 41项质量门详解
├── WORKFLOW_PATTERNS.md               # 5+3种工作流模式
├── INTEGRATION_MAP.md                 # 技能与工具集成映射
├── CASE_STUDIES.md                    # 真实项目案例研究
├── QUICK_REFERENCE.md                 # 一页速查卡
├── MERGED_FULL.html                   # 完整文档合并版
├── export_pdf.py                      # PDF导出脚本
├── LICENSE                            # MIT许可证
├── Makefile                           # Make快捷命令
├── Dockerfile.template                # Docker环境模板
├── pyproject.toml                     # Python项目配置
├── src/paper_workflow/                # 核心Python包
│   ├── strategy/                      # 策略层
│   ├── engine/                        # 决策层（循环引擎）
│   ├── supervision/                   # 监督层（护照+完整性）
│   ├── outputs/                       # 输出定义
│   ├── reporting/                     # 报告生成
│   ├── cli/                           # CLI界面
│   ├── meta/                          # 元模块（方法雷达+事后分析+沙盒）
│   ├── utils/                         # 工具函数
│   └── workflow.py                    # 统一编排器
├── config/                            # 配置文件
│   ├── default_config.yaml            # 主配置
│   ├── journal_database.yaml          # 25个期刊配置
│   ├── deprecated_methods.yaml        # 废弃方法列表
│   ├── method_cards/                  # 方法卡片
│   └── templates/                     # 论文模板
├── code_library/                      # 可复用分析代码
│   ├── modules/                       # 完整分析模块
│   ├── patterns/                      # 分析模式（QC、聚类）
│   ├── snippets/                      # 代码片段（I/O、日志、配置）
│   ├── solutions/                     # 常见问题解决方案
│   └── r/                             # R分析脚本
├── .claude/                           # Claude Code配置
│   ├── SKILL_REGISTRY.md              # 28项技能注册表
│   ├── skills/                        # 框架技能定义
│   ├── agents/                        # Agent定义
│   └── teams/                         # 团队定义
├── docs/                              # 补充文档
│   ├── ARCHITECTURE.md                # 架构文档
│   ├── QUICK_START.md                 # 快速入门
│   └── FRAMEWORK_BLUEPRINT.md         # 框架蓝图
├── tests/                             # 测试
│   ├── test_all.py                    # 全量测试
│   └── test_integration.py            # 集成测试
├── papers/                            # 论文项目（gitignored）
└── examples/                          # 示例项目
```

---

*本指南基于 ResearchPaperWorkflow v4.0.0 编写。如有疑问，请参阅各模块的 README 和 DESIGN 文档。*

*Last updated: June 20, 2026*
