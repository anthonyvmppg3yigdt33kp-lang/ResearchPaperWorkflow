# AI Harness 交互指南：让 Claude/Codex 代执行工作流

本指南面向临床医生、研究生和课题组成员。你不需要自己写 Python 代码，也不需要记住所有 CLI 参数。推荐使用方式是：

> 你用自然语言告诉 Claude/Codex 你的科研状态和目标；模型读取本仓库规则后，调用 `python -m paper_workflow.cli ai ...` 执行工作流，再把结果、缺口和下一步决策点报告给你。

这里的 AI harness 不是新的论文生产逻辑。它只是 Claude/Codex 与 V4 truth layer 之间的命令桥。真正能把 stage 标为 `completed` 的路径仍然只有：

```text
WorkflowAPI -> PaperLoopEngine -> run_stage -> verify_stage -> stage_results
```

因此，模板、空文件、未完成 harness、未运行 quality gate、未批准 checkpoint 都不会被伪装成完成。

## 1. 给 Claude/Codex 的系统用法

把下面这段作为你在 Claude/Codex 中使用本仓库时的工作约定：

```text
你是 ResearchPaperWorkflow 的工作流控制器。
用户只用自然语言描述课题需求，不要求用户复制 Python 命令。
你需要根据用户意图调用：
python -m paper_workflow.cli ai --request "<用户原始需求>" --json

如已有 paper_id，则加 --paper <paper_id>。
每次默认只推进一个 stage；遇到 checkpoint、pending_harness、needs_input、gate failure 必须停止并向用户解释。
不得把模板、空 BibTeX、空结果表、pending harness 标记为 completed。
生产运行前先执行 validate-contract；投稿前执行 validate-workflow。
```

模型实际调用的入口是：

```bash
python -m paper_workflow.cli ai --request "<自然语言需求>" --json
```

你作为用户只需要说：

```text
我还没起步，想做肾癌合并糖尿病的单细胞和空间转录组课题。
```

模型负责调用 harness、读取 JSON、告诉你 paper_id、当前阶段、缺哪些文件、是否需要你批准。

## 2. Harness 支持的核心意图

| 用户自然语言 | Harness intent | 实际工作流动作 |
|---|---|---|
| “我还没起步，想创建课题” | `create_project` | 创建 paper project，完成 `select_topic` 初始产物 |
| “看一下进度/现在到哪了” | `status` | 读取 passport、stage result、drift 状态 |
| “继续推进一步” | `run_pipeline` | 默认只跑 1 个 stage，失败或 checkpoint 即停 |
| “静态检查配置/接线” | `validate_contract` | 检查 config、contract、engine、dispatcher、gate、AI harness |
| “检查这个项目是否可信” | `validate_workflow` | 检查 completed stage 的真实产物、gate、checkpoint、drift |
| “有哪些 pending harness” | `list_harness_invocations` | 列出需要人工或外部 agent 补产物的任务 |
| “我补好了文献/结果，验证一下” | `complete_harness_invocation` | 检查 required outputs 是否存在、非空、非占位 |
| “我批准这个 checkpoint” | `approve_checkpoint` | 写入人工检查点记录 |
| “跑完整性检查/质量门” | `run_integrity_gate` | 对已有稿件执行 integrity gate |
| “为什么失败” | `diagnose_gate_failures` | 汇总 stage/gate failure 原因 |

## 3. 五类起步场景的模型交互示例

### 3.1 尚未起步

用户说：

```text
我还没有起步，想做肾癌合并糖尿病相关的临床生信课题，最好结合单细胞或空间转录组。
```

模型执行，不需要用户复制：

```bash
python -m paper_workflow.cli ai \
  --request "我还没有起步，想做肾癌合并糖尿病相关的临床生信课题，最好结合单细胞或空间转录组。" \
  --journal "Genome Biology" \
  --timeline 8 \
  --json
```

模型应回复：

```text
已创建项目：<paper_id>。
当前完成的是 select_topic 初始层，下一步我会检查 status，然后推进 target_journal 或 literature_search。
你需要确认：疾病问题是否真实重要、是否有公开数据或自有队列、目标期刊是否合适。
```

### 3.2 已有方向，需要选题调研

用户说：

```text
我已有方向：T2DM 是否改变 ccRCC 免疫微环境。请帮我做选题调研和文献空白分析。
```

模型执行：

```bash
python -m paper_workflow.cli ai \
  --request "我已有方向：T2DM 是否改变 ccRCC 免疫微环境。请帮我做选题调研和文献空白分析。" \
  --paper <paper_id> \
  --max-stages 1 \
  --json
```

如果停在 `literature_search` 的 `pending_harness`，模型应告诉用户：

```text
文献检索需要真实参考文献库。请提供 BibTeX、RIS、PMID 列表或允许我继续检索并生成 references/library.bib。
未补齐前，literature_search 不能 completed。
```

### 3.3 已有选题，需要数据分析

用户说：

```text
我已经确定研究题目，也有临床表和单细胞数据。请进入 SAP、数据审计和分析阶段。
```

模型执行：

```bash
python -m paper_workflow.cli ai \
  --request "我已经确定研究题目，也有临床表和单细胞数据。请进入 SAP、数据审计和分析阶段。" \
  --paper <paper_id> \
  --max-stages 1 \
  --json
```

模型应检查并要求用户补齐：

```text
papers/<paper_id>/data/data_inventory_input.yaml
papers/<paper_id>/results/analysis_outputs/primary_results.csv
```

如果没有这些真实文件，`data_audit` 或 `run_analysis` 会进入 `needs_input` / `pending_harness`，不能继续伪完成。

### 3.4 已有部分进展，需要完善工作流设计

用户说：

```text
我已经有一些图、表、代码和草稿，但文件比较散。请帮我接入工作流，检查缺口。
```

模型先执行静态和项目检查：

```bash
python -m paper_workflow.cli ai \
  --request "静态检查全局配置、AI harness 和 workflow contract 接线" \
  --json

python -m paper_workflow.cli ai \
  --request "检查这个项目的 stage truth、产物、quality gate、checkpoint 和 drift" \
  --paper <paper_id> \
  --json
```

模型应输出：

```text
哪些 stage 已有真实产物；
哪些产物缺失、为空或仍是占位符；
哪些 checkpoint 需要人工批准；
哪些下游 stage 因上游 artifact drift 变 stale；
下一步应该先补哪个最关键文件。
```

### 3.5 已有多数材料，需要论文撰写

用户说：

```text
我已有结果图、主结果表、方法代码和文献库。请进入论文撰写和投稿包整理。
```

模型执行：

```bash
python -m paper_workflow.cli ai \
  --request "我已有结果图、主结果表、方法代码和文献库。请进入论文撰写和投稿包整理。" \
  --paper <paper_id> \
  --max-stages 1 \
  --json
```

模型不能直接“润色成终稿”。它必须先确认：

- `references/library.bib` 非空且真实；
- `results/analysis_outputs/primary_results.csv` 非空且含统计字段；
- `methods/run_manifest.yaml` 或等价可复现记录存在；
- `claims/claim_ledger.jsonl` 能绑定结果和证据；
- `integrity_check`、`aigc_humanizer_review`、`internal_review` 未被跳过。

## 4. 推荐的人机交互循环

每一轮对话都遵循：

```text
用户自然语言目标
-> 模型调用 ai harness
-> harness 返回 JSON
-> 模型解释当前 stage truth
-> 用户补文件或批准 checkpoint
-> 模型再次调用 harness
```

模型应避免一次跑完整个 pipeline。默认单步推进更适合科研场景，因为医学/生信项目经常需要人工判断研究问题、样本单位、终点、文献、图表逻辑和投稿策略。

## 5. 给模型的最低工程纪律

- 先跑 `validate-contract --strict`，再做生产运行。
- 对具体 paper，投稿前必须跑 `validate-workflow --strict`。
- 缺 paper_id 且存在多个项目时，先问用户，不猜。
- 看到 `pending_harness`，说明要补真实产物，不是失败噪声。
- 看到 `needs_input`，先列出缺什么文件，而不是继续生成模板。
- 看到 checkpoint，必须让用户批准或要求修订。
- 不要改 `project_passport.yaml` 来伪造进度；所有完成状态必须由 workflow 运行和验证生成。

## 6. 维护者入口

维护者仍可直接运行底层命令：

```bash
python -m paper_workflow.cli validate-contract --strict
python -m paper_workflow.cli status --paper <paper_id>
python -m paper_workflow.cli run-pipeline --paper <paper_id> --stop-on-failure
python -m paper_workflow.cli validate-workflow --paper <paper_id> --strict
```

但面向临床医生和研究生的默认说明应使用 AI harness 交互，而不是要求他们记住这些命令。
