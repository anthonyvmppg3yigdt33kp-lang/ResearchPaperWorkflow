# ARCHIVED PIPELINE DESIGN v2.0

> Historical 18-stage design reference. It is not the current operating
> contract. Use `ARCHITECTURE.md`, `workflow_contract.yaml`, and
> `docs/V5_1_RESEARCHER_EXPERIENCE_TUNING_PLAN.md` for v5.1.

**Version**: 2.0.0 | **Total Stages**: 18 | **Total Phases**: 6 | **Max Parallelism**: min(16, cpu-2)

---

## 1. 管线全景：18-Stage Pipeline

```
Phase 1: Research & Planning          Phase 2: Data & Methods
┌─────────────────────────┐           ┌─────────────────────────┐
│ ① select_topic          │           │ ⑤ data_audit            │
│     └→ ② target_journal │           │     └→ ⑥ figure_planning│
│     └→ ③ literature_    │           │     └→ ⑦ run_analysis   │
│          search          │           │          └→ ⑧ verify_   │
│ ②+③ ─→ ④ formulate_     │           │              methods    │
│          hypotheses      │           │                         │
└──────────┬──────────────┘           └──────────┬──────────────┘
           │                                     │
           └──────────────┬──────────────────────┘
                          │
Phase 3: Writing          ▼               Phase 4: Assembly & Review
┌─────────────────────────┐           ┌─────────────────────────┐
│ ⑨ write_methods         │           │ ⑬ assemble_manuscript   │
│ ⑩ write_results         │           │ ⑭ integrity_check       │
│ ⑪ write_introduction    │           │ ⑮ internal_review       │
│ ⑫ write_discussion      │           │                         │
└──────────┬──────────────┘           └──────────┬──────────────┘
           │                                     │
           └──────────────┬──────────────────────┘
                          │
Phase 5: Revision         ▼               Phase 6: Finalize
┌─────────────────────────┐           ┌─────────────────────────┐
│ ⑯ apply_revision        │           │ ⑱ finalize              │
│ ⑰ re_review             │           │    → manuscript_final   │
│    ↻ (loop until pass)  │           │    → cover_letter       │
└─────────────────────────┘           │    → reproducibility    │
                                      └─────────────────────────┘
```

---

## 2. 阶段依赖图 (DAG)

```
                          ┌───────────────────────┐
                          │   ① select_topic [CP] │
                          └──────┬────────┬───────┘
                                 │        │
                    ┌────────────┘        └────────────┐
                    ▼                                  ▼
          ┌─────────────────┐                ┌──────────────────┐
          │② target_journal │                │③ literature_search│
          └────────┬────────┘                └────────┬─────────┘
                   │                                  │
                   └──────────┬───────────────────────┘
                              ▼
                    ┌───────────────────────┐
                    │④ formulate_hypo [CP]  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   ⑤ data_audit        │
                    └──────┬────────┬───────┘
                           │        │
              ┌────────────┘        └────────────┐
              ▼                                  ▼
    ┌──────────────────┐               ┌──────────────────┐
    │⑥ figure_plan [CP]│               │⑦ run_analysis    │
    └────────┬─────────┘               └────────┬─────────┘
             │                                  │
             │                         ┌────────┘
             │                         ▼
             │               ┌──────────────────┐
             │               │⑧ verify_methods  │
             │               └────────┬─────────┘
             │                        │
             │           ┌────────────┼────────────┐
             │           ▼            ▼            ▼
             │   ┌──────────┐ ┌──────────┐ ┌──────────────┐
             │   │⑨ methods │ │⑩ results │ │⑪ introduction│
             │   │   [CP]   │ │   [CP]   │ │    [CP]      │
             │   └────┬─────┘ └────┬─────┘ └──────┬───────┘
             │        │            │               │
             │        │            ▼               │
             │        │     ┌──────────────┐       │
             │        │     │⑫ discussion  │       │
             │        │     │     [CP]     │       │
             │        │     └──────┬───────┘       │
             │        │            │               │
             └────────┼────────────┼───────────────┘
                      │            │
                      └─────┬──────┘
                            ▼
                  ┌──────────────────┐
                  │⑬ assemble [CP]   │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │⑭ integrity_check │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │⑮ internal_review │
                  │      [CP]        │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │⑯ apply_revision  │◀──┐
                  └────────┬─────────┘   │
                           │             │ (max 5 retries)
                           ▼             │
                  ┌──────────────────┐   │
                  │⑰ re_review  [CP] ├───┘
                  └────────┬─────────┘
                           │ (pass)
                           ▼
                  ┌──────────────────┐
                  │⑱ finalize   [CP] │
                  └──────────────────┘

  [CP] = Human Checkpoint (需要人工审核批准)
```

---

## 3. 并行调度策略

### 3.1 阶段内并行 (Intra-Phase Parallelism)

Phase 3 Writing 的4个写作为什么可以并行:

```
⑧ verify_methods ──┬─→ ⑨ write_methods       (depends: ⑧)
                    └─→ ⑩ write_results       (depends: ⑧ + ⑥)

③ literature ──────┬─→ ⑪ write_introduction  (depends: ③ + ④)
④ hypotheses       │
                    └─→ ⑫ write_discussion    (depends: ⑩ + ③)
                         (⑩ 必须 COMPLETED)

并行窗口:
  t0: ⑧ COMPLETED → ⑨ + ⑩ 可同时启动 (⑨只需⑧, ⑩需要⑧+⑥)
  t1: ⑩ COMPLETED → ⑫ 启动 (⑫ 依赖 ⑩)
  t0-t1 期间: ⑨ + ⑪ 可以并行 (⑨ 在用⑧, ⑪ 在用③+④)
```

### 3.2 decide_next_stage() 调度逻辑

```python
def decide_next_stage(self) -> Optional[str]:
    for stage_def in self._active_stages:          # 按 phase order 扫描
        stage = self.stages[stage_def.name]
        if stage.status == StageStatus.COMPLETED:   # 跳过已完成
            continue
        if stage.status == StageStatus.FAILED and \
           stage.retry_count >= stage_def.max_retries:  # 跳过重试耗尽
            continue
        upstream_ready = all(
            self.stages[u].status == StageStatus.COMPLETED
            for u in stage_def.upstream              # 检查所有上游
        )
        if upstream_ready:
            return stage_def.name                    # 返回第一个就绪阶段
    # 全完成 → CLEAN, 否则 BLOCKED
    return None
```

**关键特性**: 非贪心 — 按 order 顺序选择，不跳级。保证逻辑顺序前提下最大化并行度。

---

## 4. 工作路径设计（5种模式）

### 4.1 完整研究路径 (Full Research)

```
Idea → ① Topic → ② Journal → ③ Literature → ④ Hypotheses [CP1]
  → ⑤ Data Audit → ⑥ Figure Plan [CP2] → ⑦ Analysis
  → ⑧ Verify → ⑨ Method → ⑩ Results → ⑪ Intro → ⑫ Discussion [CP3]
  → ⑬ Assemble → ⑭ Integrity → ⑮ Review [CP4]
  → ⑯ Revise → ⑰ Re-review [CP5]
  → ⑱ Finalize [CP6]

适用: 全新项目，有原始数据，从头写论文
耗时: 8-12 周
调用: wf.run(phases=[1,2,3,4,5])
```

### 4.2 快速写作路径 (From Results)

```
已有结果 → ⑤ Data Audit (简略) → ⑥ Figure Plan [CP]
  → ⑨ Methods → ⑩ Results → ⑪ Intro → ⑫ Discussion
  → ⑬ Assemble → ⑭ Integrity → ⑮ Review [CP]
  → ⑯ Revise → ⑰ Re-review → ⑱ Finalize

适用: 分析代码已完成，结果在手，只需写论文
耗时: 2-4 周
调用: wf.run(phases=[3,4,5])
```

### 4.3 修订循环路径 (Revision Cycle)

```
Reviewer Comments
  → ⑯ Apply Revision → ⑰ Re-review
  ↻ loop: 如果 re-review 不通过，修改后重来 (最多5次)
  → ⑱ Finalize

适用: 收到审稿意见需要修回
耗时: 1-2 周
调用: wf.run(phases=[5])
```

### 4.4 方法学论文路径 (Methods Paper)

```
跳过 hypothesis + figure_planning + intro writing
保留: analysis + verify_methods + methods writing (extended)

配置: paper_type = "methods"
自动跳过: formulate_hypotheses, figure_planning, write_results, write_introduction, write_discussion
```

### 4.5 文献综述路径 (Review Paper)

```
跳过 data + analysis + methods + results
保留: literature_search (extended) + introduction + discussion

配置: paper_type = "review"
自动跳过: data_audit, figure_planning, run_analysis, verify_methods, write_methods, write_results
```

---

## 5. 检查点系统 (6 Human Checkpoints)

```
CP1 ─ ① select_topic         → "审查研究主题和范围，批准进入文献检索"
CP2 ─ ④ formulate_hypotheses → "审查假设和实验设计，批准进入数据分析"
CP3 ─ ⑥ figure_planning      → "审查图表策略和证据逻辑，批准进入分析执行"
CP4 ─ ⑮ internal_review      → "审查完整手稿和审稿意见，批准进入修订"
CP5 ─ ⑰ re_review            → "确认修订充分，批准进入最终化"
CP6 ─ ⑱ finalize             → "最终质量审核，批准提交"
```

**决策三态**:
- `approved` → 继续
- `revision_needed` → 暂停，等待修复后 `resume()`
- `rejected` → 中止管线

---

## 6. 容错与恢复机制

### 6.1 重试策略

```yaml
retry:
  strategy: exponential_backoff
  base_seconds: 60
  multiplier: 2.0          # 1min → 2min → 4min → 8min → 15min (max)
  max_delay_seconds: 900
  jitter: true             # 随机抖动避免雷鸣群效应
  max_cumulative_retries: 20
```

### 6.2 熔断器 (Circuit Breaker)

```yaml
circuit_breaker:
  failure_threshold: 5       # 5次失败后熔断
  recovery_timeout: 600s     # 10分钟后尝试恢复
  on_open: skip_stage        # 跳过故障阶段，管线继续
```

### 6.3 过期检测 (Stale Detection)

```
Artifact hash 变更触发链:
  data_audit 更新 data_inventory.yaml (hash 变化)
    → artifact_ledger.jsonl 记录新 hash
    → _sync_stale() 扫描:
        run_analysis.status == COMPLETED
        但 data_audit artifact hash ≠ 记录值
        → run_analysis → STALE
        → 所有下游 (verify_methods, write_*, assemble, ...) → STALE
    → decide_next_stage() 返回 run_analysis (stale 优先)
```

---

## 7. 文件系统布局

```
papers/<paper_id>/
├── project_passport.yaml           # 项目护照
├── research_plan/                  # Phase 1
│   ├── research_question.md
│   ├── journal_profile.md
│   ├── formatting_requirements.yaml
│   ├── hypotheses.yaml
│   └── feasibility_decision.md
├── references/                     # 文献
│   ├── library.bib
│   └── citation_evidence.csv
├── data/                           # Phase 2
│   ├── data_audit_report.md
│   ├── data_inventory.yaml
│   └── qc_filter_report.md
├── results/                        # 分析结果
│   ├── figure_plan.json
│   ├── clustering_results.yaml
│   ├── de_results.csv
│   └── figures/
├── manuscript/                     # Phase 3-5
│   ├── {abstract,introduction,methods,results,discussion}.md
│   ├── manuscript.tex / .pdf
│   └── manuscript_revised.tex
├── review/                         # Phase 4
│   ├── review_report.md
│   └── re_review_report.md
├── integrity/                      # 质量
│   ├── integrity_report.json
│   └── integrity_report.md
├── submission/                     # Phase 6
│   ├── manuscript_final.pdf
│   └── cover_letter.pdf
├── workflow_state/                 # 状态持久化
│   ├── e2e_state_*.json
│   └── pending_invocations/*.json
├── artifact_ledger.jsonl           # 制品 hash 日志
├── checkpoint_ledger.jsonl         # 检查点决策日志
└── workflow_report.md              # 最终报告
```

---

## 8. CLI 控制

```bash
# 创建项目
python -m paper_workflow.cli create-project \
  --idea "IgG4-ROD vs MALT lymphoma biomarker discovery" \
  --field "bioinformatics, immunology" \
  --journal "Arthritis Research & Therapy"

# 试运行 (不实际执行)
python -m paper_workflow.e2e_workflow --paper-id <id> --dry-run

# 运行特定阶段
python -m paper_workflow.e2e_workflow --paper-id <id> --phases 1,2 --stop-at-checkpoint

# 恢复暂停的工作流
python -m paper_workflow.cli resume --paper <id>

# 诊断 + 导出报告
python -m paper_workflow.cli diagnose --paper <id>
python -m paper_workflow.cli export-report --paper <id>
```
