# WORKFLOW PATTERNS — 5种工作流模式库

**Version**: 2.0.0 | **Patterns**: 5 Core + 3 Composable

---

## 1. 模式总览

```
┌──────────────────────────────────────────────────────────────────────┐
│                      WORKFLOW PATTERN LIBRARY                         │
│                                                                       │
│  PATTERN 1           PATTERN 2           PATTERN 3                    │
│  Full Research       From Results        Revision Cycle               │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐                 │
│  │18 stages│         │Phase 3-6│         │Phase 5-6│                 │
│  │8-12 wks │         │ 2-4 wks │         │ 1-2 wks │                 │
│  └─────────┘         └─────────┘         └─────────┘                 │
│                                                                       │
│  PATTERN 4           PATTERN 5                                       │
│  Methods Paper       Literature Review                               │
│  ┌─────────┐         ┌─────────┐                                     │
│  │ 13 stgs │         │ 12 stgs │                                     │
│  │ 3-6 wks │         │ 4-8 wks │                                     │
│  └─────────┘         └─────────┘                                     │
│                                                                       │
│  COMPOSABLE:                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                  │
│  │Code→Paper    │ │Multi-Journal  │ │Collaborative │                  │
│  │Verification  │ │Targeting      │ │Multi-Author  │                  │
│  └──────────────┘ └──────────────┘ └──────────────┘                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Pattern 1: Full Research (完整研究路径)

### 2.1 阶段序列

```
Phase 1: Research & Planning (4 stages)
  ① select_topic [CP]
  ② target_journal ──────┐
  ③ literature_search ───┼──→ ④ formulate_hypotheses [CP]

Phase 2: Data & Methods (4 stages)
  ⑤ data_audit ──┬──→ ⑥ figure_planning [CP]
                 └──→ ⑦ run_analysis → ⑧ verify_methods

Phase 3: Writing (4 stages)
  ⑧ → ⑨ write_methods [CP]
  ⑧+⑥ → ⑩ write_results [CP]
  ③+④ → ⑪ write_introduction [CP]
  ⑩+③ → ⑫ write_discussion [CP]

Phase 4: Assembly & Review (3 stages)
  ⑨+⑩+⑪+⑫ → ⑬ assemble_manuscript [CP]
  ⑬ → ⑭ integrity_check
  ⑭ → ⑮ internal_review [CP]

Phase 5: Revision (2 stages)
  ⑮ → ⑯ apply_revision ↻
       ⑰ re_review [CP] ─┘ (max 5 loops)

Phase 6: Finalize (1 stage)
  ⑰ → ⑱ finalize [CP]
```

### 2.2 适用范围

| 条件 | 说明 |
|------|------|
| 数据类型 | 原始数据在手，需要全流程分析 |
| 论文状态 | 从零开始 |
| 团队配置 | 需要全部 12 个 Agent |
| 时间预算 | 8-12 周 |

### 2.3 调用方式

```python
from paper_workflow.e2e_workflow import run_e2e_workflow

wf = run_e2e_workflow(
    paper_id="paper_igg4malt_20260620",
    phases=[1, 2, 3, 4, 5],
    stop_at_checkpoint=True,
    export_report=True
)
```

---

## 3. Pattern 2: From Results (快速写作路径)

### 3.1 阶段序列

```
已有: 分析代码 + 结果文件
跳过: Phase 1 策略 + Phase 2 分析执行

Phase 2 (简略):
  ⑤ data_audit (简略 — 仅验证现有制品)
  ⑥ figure_planning [CP]

Phase 3-6: 同 Pattern 1
```

### 3.2 触发条件

- 分析代码已在项目中
- `results/` 目录已有完整输出
- `artifact_ledger.jsonl` 已有制品记录
- 只需论文写作和审查

### 3.3 调用方式

```python
wf = E2EWorkflow(paper_id="paper_igg4malt_20260620", auto_load=True)
# 自动检测到已有 artifacts，跳过 Phase 1-2
wf.run(phases=[3, 4, 5], stop_at_checkpoint=True)
```

### 3.4 优化

- `data_audit` 变为纯验证模式（不重新生成）
- `run_analysis` 被替换为 `verify_existing_results`
- 时间从 8-12 周缩短到 2-4 周

---

## 4. Pattern 3: Revision Cycle (修订循环)

### 4.1 循环逻辑

```
Reviewer Comments Received
        │
        ▼
  ┌─────────────────────┐
  │ ⑯ apply_revision    │ ← 根据审稿意见修改手稿
  └────────┬────────────┘
           │
           ▼
  ┌─────────────────────┐
  │ ⑰ re_review [CP]    │ ← 多视角重审
  └────────┬────────────┘
           │
     ┌─────┴─────┐
     │           │
   PASS        FAIL (retry ≤ 5)
     │           │
     ▼           └──→ 回到 ⑯
  ┌──────────┐
  │ ⑱ finalize│
  └──────────┘
```

### 4.2 修订智能路由

```python
# revision_routing skill 分析审稿意见类型:
revision_type = classify_reviewer_comments(comments)

if revision_type == "minor":
    # 仅修改措辞/格式 → 1次迭代
    wf.run(phases=[5], max_iterations=1)
elif revision_type == "major":
    # 需要补充分析 → 回到 Phase 2 部分阶段
    wf.run(phases=[2, 3, 4, 5])
elif revision_type == "reject_with_resubmit":
    # 重大修改 → 近乎完整重跑
    wf.run(phases=[1, 2, 3, 4, 5])
```

---

## 5. Pattern 4: Methods Paper (方法学论文)

### 5.1 核心差异

```
标准 IMRAD → 方法学论文:
  Introduction   → Introduction (含现有方法综述)
  Methods        → Methods (扩展 — 算法详述 + 实现细节)
  Results        → Results (替换为 Validation + Benchmark)
  Discussion     → Discussion (含与其他方法比较 + 适用场景)
```

### 5.2 自动跳过的阶段

```yaml
# config/default_config.yaml → paper_types.methods.skipped_stages
skipped_stages:
  - formulate_hypotheses    # 方法学无假设检验
  - figure_planning         # 图表更灵活
  - write_results           # 替换为 validation
  - write_introduction      # 结构不同
  - write_discussion        # 替换为 comparison
```

### 5.3 新增阶段

```
methods_paper 特有:
  benchmark_against_baselines  → 性能对比表
  ablation_study               → 消融实验
  computational_efficiency     → 计算效率报告
  installation_guide           → 安装指南
  api_documentation            → API 文档
```

---

## 6. Pattern 5: Literature Review (文献综述)

### 6.1 核心差异

```
跳过: data_audit, figure_planning, run_analysis, verify_methods, 
      write_methods, write_results

扩展:
  literature_search → 时间延长至 3600s, 深度搜索多源
  write_introduction → 替换为 thematic_sections (主题分区写作)
  write_discussion → 替换为 synthesis + future_directions
```

### 6.2 检索策略

```yaml
literature_search (extended for review):
  sources:
    - PubMed (MeSH terms)
    - Semantic Scholar (citation graph)
    - Scopus (author tracking)
    - arXiv (preprints)
    - bioRxiv (preprints)
  dedup_method: "DOI-based + title fuzzy match"
  quality_filter:
    - min_citations: 5
    - peer_reviewed_only: true
    - exclude_predatory: true
  synthesis_method: "thematic clustering + gap analysis"
```

---

## 7. 可组合模式

### 7.1 Code→Paper Verification (代码-论文交叉验证)

```
目的: 确保代码输出与论文声称 100% 一致

流程:
  1. 提取论文中所有数值声称
  2. 运行分析代码
  3. 逐项比对:
     ┌─ 统计量 (β, OR, HR, p-value)
     ├─ 样本量 (n=...)
     ├─ 阈值 (FDR<0.05, |log2FC|>1)
     └─ 模块/聚类数
  4. 生成差异报告
  5. 自动修复可修复的不一致
```

### 7.2 Multi-Journal Targeting (多期刊适配)

```
目的: 同一研究快速适配不同期刊格式

流程:
  1. 定义核心内容 (研究问题+结果+方法)
  2. 对每个目标期刊:
     ├─ 调整 abstract (字数限制)
     ├─ 调整 图表数量
     ├─ 重新格式化引用
     └─ 调整 Discussion 侧重点
  3. 并行生成多版本手稿
```

### 7.3 Collaborative Multi-Author (多作者协作)

```
目的: 支持分布式作者团队

流程:
  1. team_orchestrator 分配写作任务:
     ├─ Author A → Introduction
     ├─ Author B → Methods
     ├─ Author C → Results (含图表)
     └─ Author D → Discussion
  2. 并行写作 (各作者在自己的工作树中)
  3. assemble_manuscript 合并
  4. integrity_check 验证一致性
  5. internal_review 交叉审查
```

---

## 8. 模式选择决策树

```
START
  │
  ├─ 有新数据需要分析?
  │   ├─ YES → Pattern 1: Full Research
  │   └─ NO  → 是否有论文初稿?
  │              ├─ YES → 是否需要修订?
  │              │         ├─ YES → Pattern 3: Revision Cycle
  │              │         └─ NO  → Pattern 2: From Results
  │              └─ NO  → 论文类型?
  │                        ├─ 方法学/工具 → Pattern 4: Methods
  │                        ├─ 文献综述    → Pattern 5: Review
  │                        └─ 原始研究    → Pattern 1: Full Research
```

---

## 9. 模式性能特征

| Pattern | 阶段数 | Agent 数 | 并行度 | 典型耗时 | Token 用量 |
|---------|--------|---------|--------|---------|-----------|
| Full Research | 18 | 12 | 高 (4-5 并行) | 8-12 周 | ~500K |
| From Results | 12 | 7 | 高 (3-4 并行) | 2-4 周 | ~200K |
| Revision Cycle | 3 | 4 | 中 (2 并行) | 1-2 周 | ~100K |
| Methods Paper | 13 | 8 | 中 (2-3 并行) | 3-6 周 | ~300K |
| Literature Review | 12 | 5 | 低 (串行为主) | 4-8 周 | ~400K |

---

## 10. 模式组合示例

### 场景: 先做 Full Research，收到审稿意见后进入 Revision Cycle

```python
# Round 1: Full Research
wf1 = run_e2e_workflow("paper_igg4malt", phases=[1,2,3,4,5])
# 提交 → 收到审稿意见

# Round 2: Revision Cycle
wf2 = E2EWorkflow("paper_igg4malt", auto_load=True)
wf2.run(phases=[5])  # 仅修订+重审+定稿

# 如果是重大修改:
wf2.run(phases=[2, 3, 4, 5])  # 从分析验证重新开始
```

### 场景: Code→Paper Verification + Revision Cycle

```python
# 先交叉验证
verify_code_paper_consistency(paper_id="paper_igg4malt")

# 如有不一致，触发修订
if inconsistencies_found:
    wf = E2EWorkflow("paper_igg4malt", auto_load=True)
    wf.run(phases=[5])
```
