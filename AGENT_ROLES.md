# AGENT ROLES — 多智能体协作体系 (v3.0)

**Version**: 3.0.0 | **Agent Count**: 18 (12 original + 6 medical v3.0) | **Team Count**: 1

---

## 1. Agent 体系总览

```
                          ┌─────────────────────┐
                          │  team_orchestrator   │  ← 总调度
                          │  (Lead Agent)        │
                          └──────────┬──────────┘
                                     │
        ┌────────────┬───────────────┼───────────────┬────────────┐
        │            │               │               │            │
        ▼            ▼               ▼               ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ research_    │ │ literature_  │ │ data_        │ │ figure_      │ │ analysis_    │
│ strategist   │ │ reviewer     │ │ auditor      │ │ planner      │ │ executor     │
│ [Strategy]   │ │ [Research]   │ │ [Data]       │ │ [Visual]     │ │ [Compute]    │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        │            │               │               │            │
        └────────────┴───────────────┼───────────────┴────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │ pipeline_    │ │ statistician │ │ code_        │
            │ engineer     │ │ [Stats]      │ │ librarian    │
            │ [Infra]      │ │              │ │ [Code]       │
            └──────────────┘ └──────────────┘ └──────────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                                     ▼
            ┌──────────────────────────────────────────────┐
            │              report_writer                    │
            │  [Writing] × IMRAD sections                   │
            └──────────────────┬───────────────────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────────────┐
            │          integrity_checker                    │
            │  [Quality] × 16 gates                         │
            └──────────────────┬───────────────────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────────────┐
            │       multi_omics_integrator                  │
            │  [Integration] × cross-platform               │
            └──────────────────────────────────────────────┘
```

---

## 2. Agent 详细定义

### 2.1 research_strategist（研究策略师）

| 属性 | 值 |
|------|-----|
| **定位** | Strategy Layer 核心，定义研究方向 |
| **负责阶段** | select_topic, target_journal, formulate_hypotheses |
| **主要技能** | topic_research, deep-research, nature-academic-search |
| **输入** | 研究想法 (idea), 领域 (field) |
| **输出** | Topic对象, Journal推荐, Hypothesis列表, Feasibility报告 |
| **协作对象** | → literature_reviewer（传递研究问题和知识空白） |
| **人机交互** | select_topic + formulate_hypotheses 需要人工 checkpoint |

**决策能力**:
- 评估创新度 (innovation_level: 1-5)
- 推荐匹配期刊 (fit_score: 1-5)
- Go/No-Go 可行性判断
- PICO 框架假设结构化

**配置片段** (来自 `default_config.yaml`):
```yaml
research_strategist:
  description: "Designs research strategy, formulates hypotheses, selects target journals"
  primary_skills: [topic_research, deep-research, nature-academic-search]
  stages: [select_topic, target_journal, formulate_hypotheses]
```

### 2.2 literature_reviewer（文献审阅者）

| 属性 | 值 |
|------|-----|
| **定位** | Research Layer 核心，系统性文献检索与综合 |
| **负责阶段** | literature_search |
| **主要技能** | deep-research, nature-academic-search, nature-citation |
| **输入** | 研究主题、知识空白列表 |
| **输出** | references.bib, citation_evidence.csv, literature_review.md |
| **协作对象** | research_strategist →（接收假设）→ report_writer（传递引用证据） |
| **超时设置** | 3600秒（文献检索耗时最长） |

**关键工作流**:
1. 多源检索 (PubMed + Semantic Scholar + Scopus + arXiv)
2. 去重与质量管理
3. 引文证据映射 (claim → citation evidence)
4. BibTeX 库生成与验证

### 2.3 data_auditor（数据审计师）

| 属性 | 值 |
|------|-----|
| **定位** | Data Layer，数据质量守门人 |
| **负责阶段** | data_audit |
| **主要技能** | nature-data, qc_pipeline |
| **输入** | 数据路径、格式声明 |
| **输出** | data_audit_report.md, data_inventory.yaml, data_availability_statement.md |
| **协作对象** | analysis_executor → figure_planner → |

**审计维度**:
- 完整性: 所有声明文件存在且可读
- 格式: 符合预期 schema (h5ad, CSV, FASTQ...)
- 质量: 基本 QC 指标 (MT%, 基因数, UMI数)
- 合规: 人类/动物数据伦理声明
- 可复现: 原始数据来源记录 (GEO/SRA accession)

### 2.4 figure_planner（图表规划师）

| 属性 | 值 |
|------|-----|
| **定位** | Visual Layer，论文叙事视觉化 |
| **负责阶段** | figure_planning |
| **主要技能** | figure_planning, nature-figure |
| **输入** | 假设列表、分析结果预览 |
| **输出** | figure_plan.json, figure_plan.html, figure_specs.yaml |
| **协作对象** | data_auditor →（接收数据概况）→ analysis_executor（传递图表需求） |
| **人机交互** | checkpoint: 审核图表规划 |

**Figure Plan 结构** (6-8 图标准):
```json
{
  "Figure 1": {"title": "Study overview and data landscape", "panels": ["A-D"], "type": "schematic + UMAP"},
  "Figure 2": {"title": "Differential expression analysis", "panels": ["A-F"], "type": "volcano + heatmap"},
  "Figure 3": {"title": "WGCNA module discovery", "panels": ["A-E"], "type": "dendrogram + heatmap"},
  "Figure 4": {"title": "Module-trait associations", "panels": ["A-D"], "type": "correlation matrix"},
  "Figure 5": {"title": "Hub gene identification", "panels": ["A-C"], "type": "network + bar"},
  "Figure 6": {"title": "Validation and clinical relevance", "panels": ["A-D"], "type": "ROC + boxplot"}
}
```

### 2.5 analysis_executor（分析执行器）

| 属性 | 值 |
|------|-----|
| **定位** | Compute Layer，核心计算引擎 |
| **负责阶段** | run_analysis |
| **主要技能** | spatial_analysis, statistical_testing, pathway_inference, qc_pipeline |
| **输入** | 已审计数据 + 图表规划 |
| **输出** | analysis_results.yaml, statistical_outputs/*, figures/* |
| **超时设置** | 7200秒（计算密集型） |
| **重试次数** | 3次 |

**计算管线**:
```
raw_data.h5ad
  → QC filtering (mt_filter.py)
  → Normalization + HVG selection
  → Leiden clustering (multi_resolution.py)
  → Cell type annotation (cell_type_annotation.py)
  → Differential expression (statistical_testing)
  → Pathway enrichment (pathway_inference)
  → Results packaging (run_manifest.yaml)
```

### 2.6 pipeline_engineer（管线工程师）

| 属性 | 值 |
|------|-----|
| **定位** | Infra Layer，可复现性保障 |
| **负责阶段** | run_analysis, verify_methods |
| **主要技能** | qc_pipeline, spatial_analysis |
| **输入** | 分析结果 manifest |
| **输出** | methods_verification_report.md |
| **Gate Rules** | all_outputs_exist (CRITICAL), code_reproducible (CRITICAL) |

### 2.7 statistician（统计师）

| 属性 | 值 |
|------|-----|
| **定位** | Validation Layer，统计方法审核 |
| **负责阶段** | verify_methods |
| **主要技能** | statistical_testing |
| **输入** | DE结果、统计报告 |
| **输出** | 统计审核意见 |

**审核清单**:
- 检验假设满足（正态性、方差齐性、独立性）
- 多重检验校正正确（Bonferroni/FDR/BH）
- 效应量 + 置信区间完整
- 伪重复检查（生物 vs 技术重复）
- 样本量/功效分析

### 2.8 code_librarian（代码管理员）

| 属性 | 值 |
|------|-----|
| **定位** | Code Layer，代码资产管理 |
| **负责阶段** | run_analysis, verify_methods, finalize |
| **主要技能** | qc_pipeline |
| **输入** | 代码库路径 |
| **输出** | 插件注册、依赖锁定、代码文档 |

**管理范围**:
- `code_library/patterns/` — 可复用模式 (QC, clustering)
- `code_library/modules/` — 完整分析模块
- `code_library/solutions/` — 常见问题解决方案
- `code_library/snippets/` — 工具函数

### 2.9 report_writer（报告撰写者）

| 属性 | 值 |
|------|-----|
| **定位** | Writing Layer，论文文本生产 |
| **负责阶段** | write_methods, write_results, write_introduction, write_discussion, assemble_manuscript, apply_revision |
| **主要技能** | scientific-writing, nature-writing, nature-polishing, humanizer, nature-citation, nature-response |
| **输入** | 已验证的方法+结果，文献库 |
| **输出** | IMRAD 各部分 Markdown，完整手稿 LaTeX/PDF |
| **Gate Rules** | no_local_paths, parameters_complete, citations_exist, limitations_discussed |

**写作管线**:
```
Methods (from verified pipeline)
   ↓ 参数提取 + 代码引用
Results (from analysis outputs)
   ↓ 数值追溯 + 图表交叉引用 + 禁止解释
Introduction (from literature + hypotheses)
   ↓ 漏斗结构: 背景→空白→假设→目标
Discussion (from results + literature comparison)
   ↓ 总结→对比→局限→意义→展望
Assembly → manuscript.tex + manuscript.pdf
```

### 2.10 integrity_checker（完整性检查者）

| 属性 | 值 |
|------|-----|
| **定位** | Quality Layer，最终质量守门人 |
| **负责阶段** | verify_methods, integrity_check, internal_review, re_review |
| **主要技能** | qc_pipeline, academic-paper-reviewer, nature-data, nature-citation |
| **Gate 执行** | 16 规则 × 3 严重级别 |

**Gate 执行流程**:
```
1. 加载手稿 sections (intro, methods, results, discussion)
2. 加载 BibTeX 库 (references/library.bib)
3. 加载图表计划 (figure_plan.json)
4. 加载期刊目标 (formatting_requirements.yaml)
5. 逐规则执行检查
6. 生成 IntegrityReport
   ├── passed: bool
   ├── critical_failures: int  → blocks_pipeline = True
   ├── high_failures: int      → blocking but fixable
   ├── medium_failures: int    → warning only
   └── results: [{rule, passed, message}]
```

### 2.11 multi_omics_integrator（多组学整合师）

| 属性 | 值 |
|------|-----|
| **定位** | Integration Layer，跨平台数据整合 |
| **负责阶段** | run_analysis, verify_methods |
| **主要技能** | multi_omics, spatial_analysis, pathway_inference |
| **输入** | 多组学数据集 |
| **输出** | 跨平台整合结果 |

**整合方法库**:
- 跨平台归一化 (ComBat, Harmony, scVI)
- 联合降维 (MOFA, Multi-Omics Factor Analysis)
- 多视图聚类 (Spectrum, SNF)
- 生物网络推断 (multi-omics network)

### 2.12 team_orchestrator（团队调度者）

| 属性 | 值 |
|------|-----|
| **定位** | Lead Agent，全局协调 |
| **负责阶段** | finalize（总结）, 作为 fallback agent |
| **主要技能** | deep-research（全局视角） |
| **输入** | 完整管线状态 |
| **输出** | 最终提交包 |
| **特殊能力** | 跨 Agent 协调、冲突解决、回退处理 |

---

### 2.13 clinical_methodologist（临床方法学家）— v3.0 NEW

| 属性 | 值 |
|------|-----|
| **定位** | 研究设计审核，PICO/PECO/PIRD框架，偏倚评估，报告指南选择 |
| **负责阶段** | design_analysis_plan, data_audit |
| **主要技能** | 研究设计分类、偏倚风险评估、终点定义验证、报告指南匹配 |
| **输入** | hypotheses.yaml, research_questions.yaml, clinical_value_matrix.yaml |
| **输出** | study_design_protocol.yaml, design_assessment_report.md |

### 2.14 ethics_compliance_auditor（伦理合规审计师）— v3.0 NEW

| 属性 | 值 |
|------|-----|
| **定位** | IRB/伦理批准验证，数据隐私合规，ICMJE AI声明，利益冲突审核 |
| **负责阶段** | data_audit, integrity_check, finalize |
| **主要技能** | 伦理批准文件验证、知情同意审核、数据隐私合规、临床试验注册验证 |
| **输入** | study_design_protocol.yaml, ethics_documentation/ |
| **输出** | ethics_compliance_report.md, compliance_checklist.yaml |

### 2.15 causal_inference_reviewer（因果推断审查员）— v3.0 NEW

| 属性 | 值 |
|------|-----|
| **定位** | DAG审查，混杂评估，工具变量假设验证，敏感性分析(E-value)，因果语言审核 |
| **负责阶段** | design_analysis_plan, verify_methods, write_discussion |
| **主要技能** | DAG后门路径识别、IV三假设验证、E-value计算、中介分析假设检查 |
| **输入** | statistical_analysis_plan.yaml, hypotheses.yaml, analysis_results |
| **输出** | causal_assumption_audit.md, causal_evidence_rating.yaml |

### 2.16 external_validation_planner（外部验证规划师）— v3.0 NEW

| 属性 | 值 |
|------|-----|
| **定位** | 独立队列验证策略设计，样本独立性验证，跨中心/跨平台验证规划 |
| **负责阶段** | design_analysis_plan, verify_methods, integrity_check |
| **主要技能** | 验证层级设计(内部→时间→地理→外部)、验证队列识别、性能阈值设定 |
| **输入** | study_design_protocol.yaml, statistical_analysis_plan.yaml |
| **输出** | validation_plan.yaml, validation_cohort_candidates.md |

### 2.17 reviewer_simulator（多角色审稿模拟器）— v3.0 NEW

| 属性 | 值 |
|------|-----|
| **定位** | 4角色独立审稿模拟(EIC+统计+临床+生信)，致命缺陷检测，反辩策略生成 |
| **负责阶段** | internal_review, re_review |
| **主要技能** | 多角色独立审稿、投稿准备度评分(0-100)、反辩要点预生成 |
| **输入** | manuscript_draft.md, figures/, journal_requirements.yaml |
| **输出** | simulated_peer_review.md, rebuttal_talking_points.md |

### 2.18 novelty_killer（创新杀手/红队）— v3.0 NEW

| 属性 | 值 |
|------|-----|
| **定位** | 对抗性审查——主动寻找致命缺陷：样本不足、无外部验证、ML无增量、机制链断裂 |
| **负责阶段** | formulate_hypotheses, internal_review |
| **主要技能** | 10类致命缺陷系统评估(FATAL/MAJOR/MINOR/ABSENT)、竞争力对比、拒稿风险评分 |
| **输入** | hypotheses.yaml, data_inventory.yaml, study_design_protocol.yaml |
| **输出** | fatal_flaws_report.md, rejection_risk_summary.yaml |

---

## 3. Agent 协作模式

### 3.1 串联协作 (Sequential Handoff)

```
research_strategist → literature_reviewer → report_writer → integrity_checker

每个 Agent 完成工作后，下一个 Agent 以上一个的输出为输入。
适用场景: 线性无分支的任务（如写 Introduction）。
```

### 3.2 扇出协作 (Fan-Out Parallel)

```
                     ┌──▶ analysis_executor (clustering)
data_auditor ────────┼──▶ analysis_executor (DE)
                     └──▶ analysis_executor (pathway)

                     并行执行独立分析，结果汇聚到 figure_planner。
                     适用场景: 多分析同时运行。
```

### 3.3 交叉验证协作 (Adversarial Verify)

```
report_writer ──→ manuscript_draft
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
  integrity_checker  statistician   literature_reviewer
  (格式+引用)        (统计完整性)    (文献准确性)
        │               │               │
        └───────────────┼───────────────┘
                        ▼
                  team_orchestrator
                  (冲突裁决 + 综合报告)
```

### 3.4 迭代修订协作 (Loop-until-Clean)

```
report_writer → integrity_checker → [PASS?]
                                     ├─ YES → team_orchestrator
                                     └─ NO  → report_writer (revise)
                                              ↓
                                         integrity_checker → ...
                        最多迭代 max_retries=5 次 (apply_revision 阶段)
```

---

## 4. Agent 到 Stage 的映射

| Stage (18) | Phase | Primary Agent | Support Agents |
|------------|-------|---------------|----------------|
| select_topic | 1 | research_strategist | — |
| target_journal | 1 | research_strategist | — |
| literature_search | 1 | literature_reviewer | — |
| formulate_hypotheses | 1 | research_strategist | literature_reviewer |
| data_audit | 2 | data_auditor | code_librarian |
| figure_planning | 2 | figure_planner | data_auditor |
| run_analysis | 2 | analysis_executor | pipeline_engineer, multi_omics_integrator, code_librarian |
| verify_methods | 2 | pipeline_engineer | statistician, integrity_checker |
| write_methods | 3 | report_writer | pipeline_engineer |
| write_results | 3 | report_writer | figure_planner |
| write_introduction | 3 | report_writer | literature_reviewer |
| write_discussion | 3 | report_writer | literature_reviewer |
| assemble_manuscript | 4 | report_writer | — |
| integrity_check | 4 | integrity_checker | — |
| internal_review | 4 | team_orchestrator | integrity_checker |
| apply_revision | 5 | report_writer | — |
| re_review | 5 | team_orchestrator | integrity_checker |
| finalize | 6 | integrity_checker | team_orchestrator, code_librarian |

---

## 5. Agent 通信协议

### 5.1 Artifact-Based Communication

Agent 之间**不直接通信**，而是通过写入/读取共享制品文件交换信息:

```
Agent A 写入: papers/<id>/results/de_results.csv
                ↓ (artifact_ledger.jsonl 记录 hash)
Agent B 读取: papers/<id>/results/de_results.csv
                ↓ (验证 hash 一致性)
Agent B 处理并写入新制品
```

### 5.2 Passport 同步

```
每次 stage 完成后:
  1. AgentDispatcher.dispatch() → StageResult (含 artifacts + errors)
  2. PaperWorkflow._execute_stage() → passport.record_artifact()
  3. PaperLoopEngine.record_and_sync() → _update_passport() + _sync_stale()
  4. 下游 stage 的 upstream_ready() 检查上游 status == COMPLETED
```

### 5.3 过期检测

```
当上游 stage 的 artifact hash 变化:
  1. PaperPassport.detect_artifact_drift() 检测到 hash 不匹配
  2. 所有下游 stage 的 status → STALE
  3. PipelineState → STALE_STAGES
  4. decide_next_stage() 优先返回 stale stages (重运行)
```

---

## 6. Paper Writing Team（协作团队）

### 6.1 团队定义

`paper_writing_team` 是一个预配置的协作团队，包含全部 12 个 Agent，用于完整的论文生产周期。

**触发**: 当用户请求 "写完整论文" / "full paper workflow" / "academic pipeline"

**协调模式**: team_orchestrator 作为 Lead，分配任务给其他 Agent

### 6.2 团队工作流

```
Phase 1: Research  ──┬── research_strategist + literature_reviewer (并行)
Phase 2: Data      ──┬── data_auditor → analysis_executor → pipeline_engineer
Phase 3: Writing   ──┬── report_writer (串联 IMRAD)
Phase 4: Review    ──┬── integrity_checker + statistician (交叉验证)
Phase 5: Finalize  ──┬── team_orchestrator + integrity_checker
```
