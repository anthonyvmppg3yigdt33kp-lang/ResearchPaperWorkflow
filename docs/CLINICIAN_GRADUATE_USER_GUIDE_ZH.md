# ResearchPaperWorkflow v4.1 临床医生与研究生使用指南

本指南面向第一次接触 ResearchPaperWorkflow 的临床医生、医学研究生、生信研究生和课题组成员。它不假设你已经会写完整代码，也不把系统描述成“自动论文工厂”。正确的理解是：

> 这是一个把课题设计、数据分析、论文撰写、质量审查和投稿准备工程化的科研工作流内核。人负责方向、证据和决策，系统负责记录、检查、路由和防止伪完成。

当前权威技术说明见 `docs/NEXT_GEN_V4_TRUTH_LAYER.md`。本文重点讲怎么用。

## 1. 你应该先选择哪种使用模式

| 你的状态 | 推荐入口 | 第一目标 | 不建议立刻做的事 |
|---|---|---|---|
| 1. 尚未起步 | `create-project` + `select_topic` | 明确研究问题、疾病/队列/技术路线、目标期刊 | 不要直接写论文 |
| 2. 已有方向，需要选题调研 | `target_journal` + `literature_search` + `formulate_hypotheses` | 做文献地图、研究空白、可检验假设 | 不要把综述当结果 |
| 3. 已有选题，需要数据分析 | `design_analysis_plan` + `data_audit` + `run_analysis` | 冻结 SAP、确认 patient-level 统计单位、记录分析输出 | 不要先看结果再改终点 |
| 4. 已有部分进展，需要完善工作流 | `validate-contract` + `validate-workflow` + checkpoint | 把已有材料接入 artifact ledger，补齐缺口 | 不要把散乱文件直接视为 completed |
| 5. 已有多数材料，需要论文撰写 | `write_methods` -> `finalize` | 从证据写 IMRAD，做 AIGC hygiene 和 integrity check | 不要只做润色，不做 claim-evidence 审计 |

## 2. 三个能力层级

### 2.1 低阶用户：只想按步骤推进课题

适合：临床医生、刚入门研究生、不会 Python/R 但能准备病例表、文献和结果图的人。

你只需要掌握这些命令：

```bash
python -m paper_workflow.cli create-project --idea "你的课题想法" --field "你的领域" --journal "目标期刊"
python -m paper_workflow.cli status --paper <paper_id>
python -m paper_workflow.cli run-pipeline --paper <paper_id> --stop-on-failure
python -m paper_workflow.cli checkpoint --paper <paper_id> --stage <stage> --decision approved --notes "人工确认意见"
python -m paper_workflow.cli validate-workflow --paper <paper_id> --strict
```

低阶用户的核心习惯：

- 每完成一个阶段先看 `status`，不要自己猜 pipeline 进度。
- 系统停在 checkpoint 时，先阅读对应产物，再批准。
- 系统停在 `pending_harness` 时，说明需要你或外部 agent 补真实材料。
- 不要把模板、空 BibTeX、空结果表当作已完成。

### 2.2 中阶用户：已有数据或会做基础分析

适合：会整理 Excel/CSV、会导出 BibTeX、会运行 R/Python 脚本或已有合作生信同学的人。

你需要多掌握三类文件：

```text
papers/<paper_id>/references/library.bib
papers/<paper_id>/data/data_inventory_input.yaml
papers/<paper_id>/results/analysis_outputs/primary_results.csv
```

推荐最小数据清单：

```yaml
statistical_unit: patient
n_patients: 24
n_samples: 24
batch_variables: [center, platform]
data_types: [single_cell, clinical_metadata]
files:
  - path: data/raw/clinical_metadata.csv
    size_bytes: 128
```

中阶用户的核心任务：

- 在 `design_analysis_plan` 阶段冻结 SAP。
- 在 `data_audit` 阶段明确数据来源、样本量、批次、平台、患者级统计单位。
- 在 `run_analysis` 后保留 `run_manifest.yaml`、主结果表、代码版本和随机种子。
- 在 `write_results` 前确认每个结果都有图、表或统计输出支撑。

### 2.3 高阶用户：要扩展工作流或接入课题组规范

适合：课题组 workflow 负责人、生信工程师、需要添加 gate/agent/方法模板的人。

高阶入口：

```bash
python -m paper_workflow.cli validate-contract --strict
python -m pytest -q
```

你主要维护这些文件：

```text
workflow_contract.yaml
config/default_config.yaml
src/paper_workflow/engine/agent_dispatcher.py
src/paper_workflow/supervision/integrity.py
docs/NEXT_GEN_V4_TRUTH_LAYER.md
```

高阶用户原则：

- 新 stage 必须同时更新 contract、config、dispatcher、tests。
- 新 gate 必须定义 severity，并说明 fail-open 还是 fail-closed；临床/统计关键 gate 默认 fail-closed。
- 新 agent 不应直接改 pipeline 状态，只能产出 artifact 或 pending invocation。
- `completed` 只能来自 truth layer，不允许脚本手动改状态伪完成。

## 3. 五类起点的具体操作路径

### 3.1 尚未起步：从一个模糊想法开始

目标：把“我想研究某病/某基因/某现象”变成可评估课题。

命令：

```bash
python -m paper_workflow.cli create-project \
  --idea "T2DM modifies immune microenvironment in ccRCC" \
  --field "clinical oncology, single-cell, bioinformatics" \
  --journal "Genome Biology"

python -m paper_workflow.cli status --paper <paper_id>
```

你需要人工判断：

- 临床问题是否真实重要。
- 是否有足够样本或公开数据。
- 是否适合目标期刊。
- 主要终点是否能被数据支持。

阶段产物：

- `research_plan/research_question.md`
- `research_plan/hypotheses.yaml`
- `research_plan/journal_profile.md`

通过标准：你能用一句话说明研究对象、数据来源、统计单位、主要终点和目标期刊。

### 3.2 已有方向，需要选题调研

目标：把方向变成文献地图、研究空白和可检验假设。

命令：

```bash
python -m paper_workflow.cli run-pipeline --paper <paper_id> --stop-on-failure
python -m paper_workflow.cli list-harness-invocations --paper <paper_id>
```

如果停在 `literature_search`，补充真实 BibTeX：

```text
papers/<paper_id>/references/library.bib
```

然后验证 harness：

```bash
python -m paper_workflow.cli complete-harness-invocation \
  --paper <paper_id> \
  --invocation literature_search \
  --strict

python -m paper_workflow.cli run-pipeline --paper <paper_id> --stop-on-failure
```

你需要人工判断：

- 文献是不是和你的疾病、数据类型、方法学直接相关。
- 假设是否能被现有数据检验。
- 是否存在明显同质化或缺乏创新。

通过标准：`references/library.bib` 非空且真实，假设不是泛泛描述，而是可被数据验证。

### 3.3 已有选题，需要数据分析

目标：先冻结分析计划，再分析数据。

关键 checkpoint：

```bash
python -m paper_workflow.cli checkpoint \
  --paper <paper_id> \
  --stage design_analysis_plan \
  --decision approved \
  --notes "SAP frozen before primary analysis; patient-level unit confirmed."
```

你需要准备：

```text
data/data_inventory_input.yaml
results/analysis_outputs/primary_results.csv
```

临床/生信分析的硬要求：

- `statistical_unit` 优先是 patient/donor，而不是 cell/spot。
- 主终点、协变量、多重检验、缺失值处理要写在 SAP。
- 单细胞或空间组学不能把细胞数当患者数。
- 如果没有外部验证，Discussion 必须保守表述。

通过标准：`data_audit`、`figure_planning`、`run_analysis`、`verify_methods` 通过，且 `validate-workflow --strict` 不报告伪完成。

### 3.4 已有部分进展，需要完善工作流设计

目标：把散乱进展变成可追踪 artifact。

先做全局接线检查：

```bash
python -m paper_workflow.cli validate-contract --strict
```

再做项目检查：

```bash
python -m paper_workflow.cli validate-workflow --paper <paper_id> --strict
python -m paper_workflow.cli detect-artifact-drift --paper <paper_id>
```

如果你修改过上游文件：

```bash
python -m paper_workflow.cli sync-artifact-stale --paper <paper_id>
```

你需要人工整理：

- 哪些文件是真实结果，哪些只是草稿。
- 哪些图表支持哪些 claim。
- 哪些阶段需要重新运行。
- 哪些 checkpoint 需要 PI 或导师确认。

通过标准：旧材料进入正确目录，关键 artifact 有 ledger，漂移能传播到下游 stage。

### 3.5 已有多数材料，需要论文撰写

目标：从证据写作，而不是从空白页写作。

推荐路径：

```bash
python -m paper_workflow.cli run-pipeline --paper <paper_id> --stop-on-failure
```

写作阶段顺序：

```text
write_methods -> write_results -> write_introduction -> write_discussion
-> assemble_manuscript -> aigc_humanizer_review -> integrity_check
-> internal_review -> apply_revision -> re_review -> finalize
```

写作原则：

- Methods 写“实际做了什么”，不要写计划中但没做的分析。
- Results 不放引用，不做因果过度解释。
- Introduction 使用真实 BibTeX 文献。
- Discussion 必须写限制：样本量、批次、混杂、验证不足、同患者证据不足。
- Finalize 前必须有 data/code availability statement。

通过标准：`finalize` 产出投稿包，`validate-workflow --strict` valid，`detect-artifact-drift` no drift。

## 4. 全量 20-stage 工作流如何运作

完整流程：

```text
select_topic
target_journal
literature_search
formulate_hypotheses
design_analysis_plan
data_audit
figure_planning
run_analysis
verify_methods
write_methods
write_results
write_introduction
write_discussion
assemble_manuscript
aigc_humanizer_review
integrity_check
internal_review
apply_revision
re_review
finalize
```

每个 stage 都遵守同一循环：

```text
observe -> decide -> run -> verify -> record -> mark_stale -> diagnose -> repeat
```

系统不会因为“生成了一个文件”就认为完成。它会检查：

- 文件是否存在。
- 文件是否非空。
- 是否是模板或占位。
- 质量门是否真实运行。
- checkpoint 是否批准。
- 上游 artifact 是否漂移。

## 5. 人机交互方式

人负责：

- 研究方向和临床意义。
- 数据是否适合回答问题。
- 关键 checkpoint 的批准、拒绝或要求修改。
- 判断结果是否可发表、是否过度解释。

系统负责：

- 阶段路由。
- 产物记录。
- 质量门检查。
- artifact hash 和 drift 检测。
- pending harness 的外部任务记录。
- 失败诊断和恢复路径。

推荐 checkpoint 审核问题：

| Checkpoint | 必问问题 |
|---|---|
| `select_topic` | 问题是否重要，数据是否可能支撑？ |
| `formulate_hypotheses` | 假设是否可检验，是否避免空泛？ |
| `design_analysis_plan` | SAP 是否冻结，统计单位是否 patient-level？ |
| `figure_planning` | 图表是否对应主线，是否缺关键分析？ |
| `internal_review` | 哪些 claim 需要降级或补证据？ |
| `finalize` | 投稿包是否完整，数据/代码声明是否可接受？ |

## 6. 方法论：为什么这样设计

### 6.1 SAP 优先

医学和生信论文最常见的问题之一是“看完结果再改问题”。工作流把 `design_analysis_plan` 放在分析前，要求先写清：

- primary endpoint
- secondary/exploratory endpoint
- statistical unit
- covariates
- multiple testing
- missing data policy
- validation plan

### 6.2 Patient-level independence

单细胞、空间转录组和影像组学容易把 cell/spot/image tile 当作独立样本。工作流要求将临床推断绑定到 patient/donor 级别，避免伪重复。

### 6.3 Claim-evidence binding

每个 Results claim 都应该能追溯到图、表、统计输出或 claim ledger。没有证据的 claim 不进入投稿稿。

### 6.4 Fail-closed

对 critical/high gate，未检查不等于通过。缺输入、无 gate result、pending harness、模板文件都不能 completed。

### 6.5 人在回路

系统可以自动化检查，但不能替代临床判断、导师意见、伦理判断和投稿策略。checkpoint 是系统设计的一部分，不是障碍。

## 7. 常见问题

### pipeline 停在 literature_search

通常是没有真实 BibTeX。补 `references/library.bib`，再运行：

```bash
python -m paper_workflow.cli complete-harness-invocation --paper <paper_id> --invocation literature_search --strict
python -m paper_workflow.cli run-pipeline --paper <paper_id> --stop-on-failure
```

### pipeline 停在 data_audit

通常是没有数据清单或统计单位不清楚。补 `data/data_inventory_input.yaml`，重点写 `statistical_unit: patient`。

### validate-workflow 失败

先看失败 code：

- `completed_missing_outputs`: completed stage 缺产物。
- `completed_non_real_execution`: 模板或 pending 被误标完成。
- `completed_gate_not_run`: gate 配置了但没跑出结果。
- `checkpoint_required`: 人工 checkpoint 还没批准。
- `artifact_drift_propagated`: 上游文件改动导致下游 stale。

### 我只想写论文，不想跑全流程

可以，但仍要把已有材料放入正确目录，并让 workflow 记录它们。已有多数材料时，从写作阶段进入，不代表可以跳过 evidence 和 integrity check。

## 8. 给临床医生的最小清单

开始前请准备：

- 疾病/人群/干预或暴露/结局的 PICO 描述。
- 数据来源和纳入排除标准。
- 患者数量，而不是细胞数量。
- 目标期刊或期刊层级。
- 主要终点和临床意义。
- 是否有伦理、注册、数据可用性限制。

每次 checkpoint 问自己：

- 这个结论是否能被我的数据直接支持？
- 是否把相关性写成因果？
- 是否把模型发现写成临床可用 biomarker？
- 是否有独立验证？

## 9. 给研究生的每周推进法

周一：

- 跑 `status` 和 `validate-workflow --strict`。
- 列出本周要解锁的 stage。

周二到周四：

- 补 artifact，不直接改 pipeline 状态。
- 完成 pending harness 中的任务。
- 每次改上游产物后跑 drift 检查。

周五：

- 运行 `validate-workflow --strict`。
- 写 checkpoint notes。
- 和导师确认下周是否推进到下一阶段。

## 10. 最小生产级验收

在你准备投稿或交给导师前，至少应满足：

```bash
python -m paper_workflow.cli validate-contract --strict
python -m paper_workflow.cli validate-workflow --paper <paper_id> --strict
python -m paper_workflow.cli detect-artifact-drift --paper <paper_id>
```

期望结果：

- contract valid。
- workflow valid。
- no artifact drift。
- `stage_results/` 中关键阶段都有 JSON 记录。
- 所有人工 checkpoint 都有明确 notes。
