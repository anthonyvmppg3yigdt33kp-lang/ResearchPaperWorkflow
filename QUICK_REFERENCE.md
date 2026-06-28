# Historical Note

This quick reference predates the next-generation V4 truth layer. Use
`docs/NEXT_GEN_V4_TRUTH_LAYER.md` for the current 20-stage workflow,
`WorkflowAPI`, agent harness, and validation commands.

# QUICK REFERENCE — 一页速查卡

**Version**: 2.0.0

---

## 工作流命令

```bash
# 创建新论文项目
python -m paper_workflow.cli create-project \
  --idea "your idea" --field "your field" --journal "target journal"

# 试运行 (查看计划不执行)
python -m paper_workflow.e2e_workflow --paper-id <id> --dry-run

# 运行指定阶段
python -m paper_workflow.e2e_workflow --paper-id <id> --phases 1,2

# 运行全部5阶段 (自动模式)
python -m paper_workflow.e2e_workflow --paper-id <id> --phases 1,2,3,4,5

# 检查点模式 (每阶段暂停)
python -m paper_workflow.e2e_workflow --paper-id <id> --stop-at-checkpoint

# 查看状态
python -m paper_workflow.cli status --paper <id>

# 诊断失败
python -m paper_workflow.cli diagnose --paper <id>

# 导出报告
python -m paper_workflow.cli export-report --paper <id>
```

---

## 18 Stage Pipeline 速查

| # | Stage | Phase | Agent | CP |
|---|-------|-------|-------|-----|
| ① | select_topic | 1:Research | research_strategist | ✓ |
| ② | target_journal | 1:Research | research_strategist | — |
| ③ | literature_search | 1:Research | literature_reviewer | — |
| ④ | formulate_hypotheses | 1:Research | research_strategist | ✓ |
| ⑤ | data_audit | 2:Data | data_auditor | — |
| ⑥ | figure_planning | 2:Data | figure_planner | ✓ |
| ⑦ | run_analysis | 2:Data | analysis_executor | — |
| ⑧ | verify_methods | 2:Data | pipeline_engineer | — |
| ⑨ | write_methods | 3:Writing | report_writer | ✓ |
| ⑩ | write_results | 3:Writing | report_writer | ✓ |
| ⑪ | write_introduction | 3:Writing | report_writer | ✓ |
| ⑫ | write_discussion | 3:Writing | report_writer | ✓ |
| ⑬ | assemble_manuscript | 4:Assembly | report_writer | ✓ |
| ⑭ | integrity_check | 4:Assembly | integrity_checker | — |
| ⑮ | internal_review | 4:Assembly | team_orchestrator | ✓ |
| ⑯ | apply_revision | 5:Revision | report_writer | — |
| ⑰ | re_review | 5:Revision | team_orchestrator | ✓ |
| ⑱ | finalize | 6:Finalize | integrity_checker | ✓ |

---

## 12 Agents 速查

| Agent | 负责阶段 | 核心技能 |
|-------|---------|---------|
| research_strategist | ①②④ | topic_research, deep-research |
| literature_reviewer | ③ | deep-research, nature-citation |
| data_auditor | ⑤ | nature-data, qc_pipeline |
| figure_planner | ⑥ | figure_planning, nature-figure |
| analysis_executor | ⑦ | spatial_analysis, pathway_inference |
| pipeline_engineer | ⑦⑧ | qc_pipeline, reproducibility |
| statistician | ⑧ | statistical_testing |
| report_writer | ⑨⑩⑪⑫⑬⑯ | scientific-writing, nature-*, humanizer |
| integrity_checker | ⑧⑭⑱ | qc_pipeline, academic-paper-reviewer |
| multi_omics_integrator | ⑦⑧ | multi_omics, spatial_analysis |
| code_librarian | ⑦⑧⑱ | qc_pipeline |
| team_orchestrator | ⑮⑰ | deep-research (协调) |

---

## 16 Quality Gates 速查

| # | Gate | Severity | Auto-Fix |
|---|------|----------|----------|
| 1 | bibtex_citation_existence | CRITICAL | ❌ |
| 2 | citation_evidence_traceability | CRITICAL | ❌ |
| 3 | results_no_citations | CRITICAL | ❌ |
| 4 | claim_artifact_binding | CRITICAL | ❌ |
| 5 | figures_referenced | CRITICAL | ❌ |
| 6 | data_availability_statement | HIGH | ✅ |
| 7 | code_availability_statement | HIGH | ✅ |
| 8 | no_local_paths | HIGH | ✅ |
| 9 | methods_parameters_complete | HIGH | ❌ |
| 10 | discussion_limitations | HIGH | ❌ |
| 11 | results_no_overinterpretation | HIGH | ❌ |
| 12 | statistics_reported | HIGH | ❌ |
| 13 | pseudoreplication_check | HIGH | ❌ |
| 14 | section_length_minimum | MEDIUM | ❌ |
| 15 | no_bullets_in_prose | MEDIUM | ✅ |
| 16 | figure_count_requirements | MEDIUM | ❌ |

---

## 5 Workflow Patterns

| Pattern | 阶段 | 耗时 | 适用场景 |
|---------|------|------|---------|
| Full Research | 1-6 | 8-12wk | 新项目从零开始 |
| From Results | 3-6 | 2-4wk | 分析完成, 只需写作 |
| Revision Cycle | 5-6 | 1-2wk | 审稿修回 |
| Methods Paper | 1-6 (adapted) | 3-6wk | 方法学/工具论文 |
| Literature Review | 1-4 (adapted) | 4-8wk | 文献综述 |

---

## 5 E2E Phases

| Phase | 名称 | 阶段数 | 检查点 |
|-------|------|--------|--------|
| 1 | Topic Research | 4 | ✓ |
| 2 | Data Analysis | 4+3code | ✓ |
| 3 | Paper Writing | 4 | ✓ |
| 4 | Polish & Review | 3+6ext | ✓ |
| 5 | Submission | 3 | ✓ |

---

## 关键 MCP 工具速查

| 任务 | 工具调用 |
|------|---------|
| 生物医学文献 | `mcp__pubmed__search_articles` |
| 跨学科学术 | `mcp__consensus__search` |
| R包文档 | `mcp__context7__resolve-library-id` → `mcp__context7__query-docs` |
| 代码语义搜索 | `mcp__fast-context__fast_context_search` |
| 期刊政策搜索 | `mcp__grok-search__web_search` |
| 论文全文 | `mcp__exa__web_fetch_exa` |

---

## 项目记忆参照

| 项目 | 记忆文件 | 关键信息 |
|------|---------|---------|
| IgG4&MALT | `igg4malt_wgcna_20260513` | WGCNA 17模块, 132 hub-DEG |
| 肝骨轴MR | `肝骨轴MR/` | MVMR v17.5, β/CI完整 |
| StereoSeq | `stereoseq_*` (多个) | 空间解卷积, PCD分析 |
| 肾脏多组学 | `kidney_multiomics_survey_2026` | 调研阶段 |

---

## 常见操作

### 从已有结果快速写论文

```python
from paper_workflow.e2e_workflow import E2EWorkflow
wf = E2EWorkflow(paper_id="paper_my_project", auto_load=True)
wf.run(phases=[3, 4, 5], stop_at_checkpoint=True)
```

### 只写 Methods 段落

```python
wf = E2EWorkflow(paper_id="paper_my_project", auto_load=True)
wf.run(phases=[3])  # Phase 3 第一个 stage 就是 write_methods
```

### 修订审稿意见

```python
wf = E2EWorkflow(paper_id="paper_my_project", auto_load=True)
wf.run(phases=[5])  # apply_revision → re_review ↻
```

### 重新运行分析后更新论文

```python
# 1. 重新分析
wf.run(phases=[2])
# 2. 门检测到 artifact hash 变化 → 所有下游 STALE
# 3. 自动重新写作 (stale 优先)
wf.run(phases=[3, 4, 5])
```
