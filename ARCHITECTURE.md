# Historical Note

This document is retained for background. The current production architecture is
the V4 truth-layer design documented in `docs/NEXT_GEN_V4_TRUTH_LAYER.md`.
Older counts such as 18 stages, 16 gates, or legacy E2E execution should be
treated as historical unless they are repeated in the next-generation guide.

# ARCHITECTURE — ResearchPaperWorkflow v4 系统架构

**Version**: 4.0.0 | **Layer Count**: 4 | **Design Pattern**: Layered + Event-Driven + Pipeline

---

## 1. 架构全景

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                          ResearchPaperWorkflow v2 Architecture                          │
│                                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │                         LAYER 4: SUPERVISION                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │  │
│  │  │   Passport   │  │  Integrity   │  │  Provenance  │  │  Stale Detection   │   │  │
│  │  │   System     │  │  Gate Checker│  │  Tracker     │  │  Engine            │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────┬───────────┘   │  │
│  │         │                 │                 │                   │               │  │
│  │         └─────────────────┴─────────────────┴───────────────────┘               │  │
│  │                                    │                                             │  │
│  └────────────────────────────────────┼─────────────────────────────────────────────┘  │
│                                       │                                                │
│  ┌────────────────────────────────────┼─────────────────────────────────────────────┐  │
│  │                         LAYER 3: EXECUTION                                        │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐    │  │
│  │  │   Pipeline           │  │   Quality Gates      │  │   CLI Surface        │    │  │
│  │  │   Orchestrator       │  │   Engine (16 rules)  │  │   (10 commands)      │    │  │
│  │  │   (18 stages)        │  │                      │  │                      │    │  │
│  │  └──────────┬───────────┘  └──────────┬───────────┘  └──────────┬───────────┘    │  │
│  │             │                         │                         │                │  │
│  └─────────────┼─────────────────────────┼─────────────────────────┼────────────────┘  │
│                │                         │                         │                   │
│  ┌─────────────┼─────────────────────────┼─────────────────────────┼────────────────┐  │
│  │             │           LAYER 2: DECISION                       │                │  │
│  │  ┌──────────▼───────────┐  ┌──────────▼───────────┐  ┌─────────▼───────────┐    │  │
│  │  │   Skills Dispatcher  │  │   MCP Router          │  │   Paper Loop        │    │  │
│  │  │   (17 skills)        │  │   (PubMed/Consensus/  │  │   Engine            │    │  │
│  │  │                      │  │    Context7/Grok)     │  │   (observe→decide→  │    │  │
│  │  │                      │  │                       │  │    run→verify→      │    │  │
│  │  │                      │  │                       │  │    record→repeat)   │    │  │
│  │  └──────────┬───────────┘  └──────────┬───────────┘  └─────────┬───────────┘    │  │
│  │             │                         │                         │                │  │
│  └─────────────┼─────────────────────────┼─────────────────────────┼────────────────┘  │
│                │                         │                         │                   │
│  ┌─────────────┼─────────────────────────┼─────────────────────────┼────────────────┐  │
│  │             │           LAYER 1: STRATEGY                       │                │  │
│  │  ┌──────────▼───────────┐  ┌──────────▼───────────┐  ┌─────────▼───────────┐    │  │
│  │  │   Topic Selector     │  │   Journal Targeter   │  │   Feasibility        │    │  │
│  │  │   + PICO Framework   │  │   + Requirements DB  │  │   Assessor           │    │  │
│  │  └──────────────────────┘  └──────────────────────┘  └──────────────────────┘    │  │
│  │                                                                                   │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐                               │  │
│  │  │   Hypothesis         │  │   Research Strategy  │                               │  │
│  │  │   Framework          │  │   Manager            │                               │  │
│  │  └──────────────────────┘  └──────────────────────┘                               │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                        │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 四层架构详解

### 2.1 Layer 1: Strategy（策略层）

**职责**: 研究问题定义、期刊选择、可行性评估、假设生成

| 组件 | 源码位置 | 功能 |
|------|---------|------|
| `TopicSelector` | `src/paper_workflow/strategy/topic_selector.py` | 从研究想法生成结构化主题，评估创新度 |
| `JournalTargeter` | `src/paper_workflow/strategy/journal_targeter.py` | 匹配目标期刊，生成格式要求清单 |
| `FeasibilityAssessor` | `src/paper_workflow/strategy/feasibility.py` | 多维度可行性评分（数据/方法/期刊/时间线） |
| `HypothesisFramework` | `src/paper_workflow/strategy/hypothesis_framework.py` | 结构化假设生成（category + type + statement） |
| `ResearchStrategyManager` | `src/paper_workflow/strategy/research_strategy.py` | 策略持久化、加载、版本管理 |

**数据流**:
```
idea + field → TopicSelector → Topic (innovation_level, scope, knowledge_gaps)
                                    ↓
                            JournalTargeter → Journal (IF, fit_score, requirements)
                                    ↓
                            HypothesisFramework → [Hypothesis] (PICO-structured)
                                    ↓
                            FeasibilityAssessor → FeasibilityReport (go/no-go)
```

### 2.2 Layer 2: Decision（决策层）

**职责**: 技能调度、MCP路由、管线循环控制

| 组件 | 源码位置 | 功能 |
|------|---------|------|
| `SkillsDispatcher` | `config/default_config.yaml §6` | 触发词→技能映射，17技能覆盖6阶段 |
| `MCP Router` | 内置（Claude Code harness） | PubMed/Consensus/Context7/Grok 路由 |
| `PaperLoopEngine` | `src/paper_workflow/engine/loop_engine.py` | observe→decide→run→verify→record→sync 循环 |
| `AgentDispatcher` | `src/paper_workflow/engine/agent_dispatcher.py` | Stage→Agent→Skill 三级调度 |

**Loop Engine 状态机**:
```
                    ┌──────────┐
                    │ PENDING  │
                    └────┬─────┘
                         │ upstream_ready()
                         ▼
                    ┌──────────┐
               ┌───▶│ RUNNING  │
               │    └────┬─────┘
               │         │ run_stage()
               │         ▼
               │    ┌──────────────┐
               │    │ VERIFY       │◀── integrity gate checks
               │    └──┬───────┬───┘
               │       │       │
               │   pass│       │fail (retry_count < max)
               │       │       ▼
               │       │  ┌──────────┐
               │       │  │  FAILED  │──retry──┐
               │       │  └──────────┘         │
               │       ▼                       │
               │  ┌──────────┐                 │
               │  │COMPLETED │                 │
               │  └────┬─────┘                 │
               │       │ upstream_changed()    │
               │       ▼                       │
               │  ┌──────────┐                 │
               └───│  STALE   │                │
                  └──────────┘                 │
                                               │
                  ┌────────────────────────────┘
                  │ retry_count < max_retries
                  ▼
             (back to RUNNING)
```

**Pipeline State 转换**:
```
CLEAN → IN_PROGRESS → CLEAN (all stages OK)
CLEAN → IN_PROGRESS → GATE_FAILURE (integrity check failed)
CLEAN → IN_PROGRESS → STALE_STAGES (upstream artifact changed)
CLEAN → IN_PROGRESS → BLOCKED (unresolvable dependency)
CLEAN → IN_PROGRESS → DRIFT_DETECTED (artifact hash mismatch)
```

### 2.3 Layer 3: Execution（执行层）

**职责**: 18阶段管线编排、质量门执行、CLI命令接口

| 组件 | 源码位置 | 功能 |
|------|---------|------|
| `PaperWorkflow` | `src/paper_workflow/workflow.py` | 统一工作流编排器（初始化→运行→诊断） |
| `E2EWorkflow` | `src/paper_workflow/e2e_workflow.py` | 5阶段端到端主控（含回调+检查点+报告） |
| `IntegrityGateChecker` | `src/paper_workflow/supervision/integrity.py` | 16规则完整性检查（5C+8H+3M） |
| CLI | `src/paper_workflow/cli/main.py` | 10命令CLI界面 |

**E2E 5-Phase 结构**:
```
Phase 1: Topic Research (4 stages)
  deep_research → topic_research → journal_targeting → feasibility_assessment
  [CHECKPOINT: Review research question and approve]

Phase 2: Data Analysis (7 stages)
  data_audit → qc_filtering → clustering → cell_annotation
  → statistical_testing → pathway_inference → figure_planning
  [CHECKPOINT: Review analysis outputs and approve]

Phase 3: Paper Writing (4 stages)
  scientific_writing_plan → nature_writing → nature_citation → research_paper_writing
  [CHECKPOINT: Review complete manuscript draft]

Phase 4: Polish & Review (6 stages)
  academic_polish → humanizer → nature_figure → academic_review
  → nature_data → ai_writing_detection
  [CHECKPOINT: Review polished manuscript + review feedback]

Phase 5: Submission (3 stages)
  cover_letter → integrity_check → presentation (optional)
  [CHECKPOINT: Final review before submission]
```

### 2.4 Layer 4: Supervision（监督层）

**职责**: 护照追踪、完整性验证、溯源审计、过期检测

| 组件 | 源码位置 | 功能 |
|------|---------|------|
| `PaperPassport` | `src/paper_workflow/supervision/passport.py` | Hash-based artifact ledger + checkpoint记录 |
| `IntegrityGateChecker` | `src/paper_workflow/supervision/integrity.py` | 16-rule 完整检查套件 |
| `ErrorTracker` | `src/paper_workflow/utils/error_tracker.py` | 结构化错误日志 + 分级 |
| `Reproducibility` | `src/paper_workflow/utils/reproducibility.py` | 种子验证 + 环境快照 |

**Passport 数据结构**:
```
papers/<paper_id>/
├── project_passport.yaml        # 项目身份 + 元数据
├── artifact_ledger.jsonl        # Append-only 制品哈希日志
├── checkpoint_ledger.jsonl      # 用户批准的检查点
└── integrity_ledger.jsonl       # 完整性门事件
```

---

## 3. 核心数据流

### 3.1 论文生产全流程数据流

```
Research Idea
     │
     ▼
[TopicSelector] ──→ Topic (innovation_level, scope, gaps)
     │
     ▼
[JournalTargeter] ──→ Journal (IF, fit_score, formatting reqs)
     │
     ▼
[Literature Searcher] ──→ references.bib + citation_evidence.csv
     │
     ▼
[HypothesisFramework] ──→ hypotheses.yaml + research_questions
     │
     ▼
[Data Auditor] ──→ data_audit_report.md + data_inventory.yaml
     │
     ▼
[Figure Planner] ──→ figure_plan.json + figure_specs.yaml
     │
     ▼
[Analysis Executor] ──→ results/* + run_manifest.yaml
     │
     ▼
[Method Verifier] ──→ methods/run_manifest.yaml (verified)
     │
     ▼
[Report Writer] ×4 ──→ manuscript/{intro,methods,results,discussion}.md
     │
     ▼
[Assembler] ──→ manuscript/manuscript.tex + manuscript.pdf
     │
     ▼
[Integrity Checker] ──→ integrity/integrity_report.json
     │
     ▼
[Internal Reviewer] ──→ review/review_report.md
     │
     ▼
[Revision Applier] ──→ manuscript/manuscript_revised.tex
     │
     ▼
[Re-Reviewer] ──→ review/re_review_report.md
     │
     ▼
[Finalizer] ──→ submission/manuscript_final.pdf + cover_letter.pdf
```

### 3.2 Agent 间通信数据流

```
research_strategist ──(topic, hypotheses)──▶ literature_reviewer
        │                                            │
        │                                    (citation_evidence)
        │                                            │
        ▼                                            ▼
  data_auditor ◀──────────────▶ figure_planner
        │                            │
   (data_inventory)           (figure_plan)
        │                            │
        ▼                            ▼
  analysis_executor ──(results)──▶ pipeline_engineer
        │                                │
        │                         (verified_manifest)
        │                                │
        ▼                                ▼
  report_writer ◀────────────────────────┘
        │
   (manuscript sections)
        │
        ▼
  integrity_checker ──(integrity_report)──▶ team_orchestrator
        │                                        │
        │                                 (review_report)
        │                                        │
        ▼                                        ▼
  report_writer (revision) ◀─────────────────────┘
        │
   (revised_manuscript)
        │
        ▼
  integrity_checker (final) ──▶ submission_package
```

---

## 4. 状态管理

### 4.1 StageState（管线阶段状态）

```python
@dataclass
class StageState:
    definition: StageDefinition    # 阶段定义（不可变）
    status: StageStatus            # PENDING|RUNNING|COMPLETED|FAILED|STALE|SKIPPED|BLOCKED
    started_at: Optional[str]
    completed_at: Optional[str]
    retry_count: int
    artifacts_produced: list[str]  # 产出文件路径
    artifact_hashes: dict[str, str]  # SHA-256 哈希
    errors: list[str]
    gate_results: list[dict]       # 质量门检查结果
```

### 4.2 WorkflowState（工作流状态）

```python
@dataclass
class WorkflowState:
    paper_id: str
    started_at: str
    completed_at: Optional[str]
    strategy: Optional[ResearchStrategy]
    pipeline_state: str            # clean|drift_detected|stale_stages|gate_failure|in_progress|blocked
    stages_completed: int
    stages_failed: int
    errors: list[dict]
    decisions: list[dict]          # 每个阶段的决策记录
```

### 4.3 状态持久化

```
每次 run() 调用后:
  ┌─ _execute_stage(stage) → self.engine.run_stage()
  │   └─ 写入 project_passport.yaml (updated_at + stages snapshot)
  ├─ verify_stage(stage) → self.engine.verify_stage()
  │   └─ integrity gate checks
  ├─ passport.record_artifact(art, stage=stage)
  │   └─ Append to artifact_ledger.jsonl (SHA-256 hash + timestamp)
  ├─ engine.record_and_sync()
  │   └─ _update_passport() + _sync_stale()
  └─ state.decisions.append(...)
      └─ 内存中累积，save_state() 时写入 workflow_state/*.json
```

---

## 5. 可扩展性设计

### 5.1 扩展点（来自 `default_config.yaml §12`）

| 扩展类型 | 注册方式 | 约束 |
|---------|---------|------|
| 自定义分析脚本 | 放入 `scripts/custom/` 自动发现 | 语法检查 + 导入验证 |
| 自定义 Agent | `config/custom_agents.yaml` 清单 | 必须声明 primary_skills + stages |
| 自定义 Skill | `config/custom_skills.yaml` 清单 | 必须声明 triggers + phase + agent |
| 自定义 Gate Rule | 在 quality_gates 块添加 | 声明 severity + check type + rule |

### 5.2 配置覆盖链

```
default_config.yaml (基線)
    ↓
<paper_dir>/paper_config.yaml (项目级覆盖)
    ↓
环境变量 PAPER_WORKFLOW_* (运行时覆盖)
    ↓
CLI --config 参数 (命令行覆盖)
```

---

## 6. 技术栈

| 层面 | 技术选择 |
|------|---------|
| 语言 | Python 3.9+ (核心管线) + R 4.0+ (分析模块) |
| 配置 | YAML (default_config.yaml, 2100+ 行) |
| 状态持久化 | JSONL (append-only ledgers) + YAML (passport) |
| 制品哈希 | SHA-256 |
| 包管理 | pip (Python) + renv (R) |
| 容器化 | Docker (Dockerfile.template) |
| 测试 | pytest (test_all.py + test_integration.py) |
| CLI | argparse (10 命令) |
| 输出格式 | Markdown, LaTeX, PDF, SVG, JSON, YAML |

---

## 7. 关键设计决策

### 决策 1: 硬编码 + 配置双轨制
- **选择**: `loop_engine.py` 内置 `PIPELINE_STAGES` 硬编码回退 + YAML 配置覆盖
- **理由**: 配置损坏时管线仍可运行；配置可用时灵活调整阶段定义
- **实现**: `PaperLoopEngine.__init__` 的 `config_path` 参数

### 决策 2: Append-Only Ledger
- **选择**: `artifact_ledger.jsonl` 和 `checkpoint_ledger.jsonl` 使用 append-only 模式
- **理由**: 完整审计追踪；支持时间旅行调试；不可篡改
- **代价**: 文件持续增长（通过 checkpoint 归档管理）

### 决策 3: 阶段级 Gate 而非管线级 Gate
- **选择**: 每个 StageDefinition 携带自己的 gate_rules
- **理由**: 不同阶段有不同质量要求；失败隔离更精确
- **实现**: `StageDefinition.gate_rules: list[dict]`

### 决策 4: Human Checkpoint 而非全自动
- **选择**: 关键阶段（select_topic, formulate_hypotheses, figure_planning, internal_review, finalize）标记 `human_checkpoint: true`
- **理由**: 科研决策不能全自动化；人在回路保证质量
- **实现**: `stop_at_checkpoint=True` 时在 checkpoint 阶段暂停
