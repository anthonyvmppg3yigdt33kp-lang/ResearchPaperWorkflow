# INTEGRATION MAP — 技能集成映射与工具矩阵

**Version**: 2.0.0 | **Internal Skills**: 12 | **External Skills**: 28 | **MCP Servers**: 5

---

## 1. 技能全景映射

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SKILL INTEGRATION LANDSCAPE                        │
│                                                                          │
│  RESEARCH LAYER                    WRITING LAYER                         │
│  ┌────────────────────┐           ┌────────────────────┐                │
│  │ topic_research     │           │ scientific-writing │                │
│  │ deep-research      │           │ nature-writing     │                │
│  │ literature_search  │           │ nature-polishing   │                │
│  │ nature-academic-   │           │ nature-citation    │                │
│  │     search         │           │ humanizer          │                │
│  └────────┬───────────┘           │ research-paper-    │                │
│           │                       │     writing        │                │
│           │                       └────────┬───────────┘                │
│           │                                │                             │
│  ANALYSIS LAYER                   QUALITY LAYER                          │
│  ┌────────────────────┐           ┌────────────────────┐                │
│  │ spatial_analysis   │           │ academic-paper-    │                │
│  │ statistical_testing│           │     reviewer       │                │
│  │ pathway_inference  │           │ qc_pipeline        │                │
│  │ figure_planning    │           │ reproducibility    │                │
│  │ multi_omics        │           │ ai-writing-        │                │
│  │ nature-figure      │           │     detection      │                │
│  └────────┬───────────┘           │ revision_routing   │                │
│           │                       │ paper_loop         │                │
│           │                       └────────┬───────────┘                │
│           │                                │                             │
│  SUBMISSION LAYER                  DATA LAYER                            │
│  ┌────────────────────┐           ┌────────────────────┐                │
│  │ nature-response    │           │ nature-data        │                │
│  │ nature-paper2ppt   │           │                    │                │
│  └────────────────────┘           └────────────────────┘                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 内部技能 (12 Framework Skills)

### 2.1 技能定义文件

| 技能 | 定义文件 | Agent | Phase |
|------|---------|-------|-------|
| `topic_research` | `.claude/skills/topic_research.md` | research_strategist | 1 |
| `literature_search` | `.claude/skills/literature_search.md` | literature_reviewer | 1 |
| `qc_pipeline` | `.claude/skills/qc_pipeline.md` | integrity_checker | 2,4,5 |
| `figure_planning` | `.claude/skills/figure_planning.md` | figure_planner | 2 |
| `spatial_analysis` | `.claude/skills/spatial_analysis.md` | analysis_executor | 2 |
| `statistical_testing` | `.claude/skills/statistical_testing.md` | statistician | 2 |
| `pathway_inference` | `.claude/skills/pathway_inference.md` | analysis_executor | 2 |
| `multi_omics` | `.claude/skills/multi_omics.md` | multi_omics_integrator | 2 |
| `paper_writing` | `.claude/skills/paper_writing.md` | report_writer | 3 |
| `paper_loop` | `.claude/skills/paper_loop.md` | team_orchestrator | 4 |
| `revision_routing` | `.claude/skills/revision_routing.md` | report_writer | 5 |
| `reproducibility` | `.claude/skills/reproducibility.md` | pipeline_engineer | 2,6 |

### 2.2 技能调度触发器（来自 `default_config.yaml §6`）

```yaml
# 关键触发器映射
deep-research:
  triggers: [literature search, comprehensive review, state of the art,
             deep调研, 系统性检索, 文献综述]

scientific-writing:
  triggers: [write Methods, write Results, write Introduction, 
             write Discussion, IMRAD, 医学论文, 科研写作段落]

nature-polishing:
  triggers: [polish manuscript, improve language, 润色, 改写, proofreading]

nature-citation:
  triggers: [add citations, insert references, Nature系列引用, 
             CNS子刊, 补引用, 配文献]

humanizer:
  triggers: [remove AI traces, 去AI味, 不像AI写的, 更自然]

academic-paper-reviewer:
  triggers: [review manuscript, peer review, 审稿, critique paper]
```

---

## 3. 外部技能集成 (28 External Skills)

### 3.1 按阶段分组

| 阶段 | 外部技能 | 用途 |
|------|---------|------|
| **Phase 1** | `deep-research` | 多源文献调研 + 引用追踪 |
| | `nature-academic-search` | PubMed/CrossRef/arXiv 检索 |
| | `summarize` | 论文快速理解 |
| | `paper-glance` | 论文深度分析 + 审稿意见 |
| **Phase 2** | `nature-figure` | 发表级图表 (≥300 DPI) |
| | `nature-data` | FAIR 数据管理 |
| **Phase 3** | `scientific-writing` | IMRAD 结构段落写作 |
| | `nature-writing` | Nature 风格手稿构建 |
| | `nature-citation` | CNS/子刊引用集成 |
| | `research-paper-writing` | ML/CV/NLP 风格论文 |
| | `academic-paper` | 12-Agent 学术写作管线 |
| **Phase 4** | `academic-paper-polish` | 学术润色 |
| | `nature-polishing` | Nature 风格润色 + LaTeX 排版 |
| | `humanizer` | AI 痕迹移除 |
| | `academic-paper-reviewer` | 多视角内审 (EIC+3Reviewers+Devil) |
| | `ai-writing-detection` | AI 写作检测 |
| | `remove-ai-flavor` | 中文 AI 味道去除 |
| **Phase 5** | `nature-response` | 审稿回复信 |
| | `academic-paper-reviewer` | 重审 (re-review mode) |
| **Phase 6** | `nature-paper2ppt` | 论文转 PPT |
| | `nature-data` | 数据可用性声明 |

### 3.2 完整外部技能列表

```
academic-paper           academic-paper-polish      academic-paper-reviewer
academic-pipeline        ai-writing-detection       darwin-skill
deep-research            find-skills                gws-docs
humanizer                nature-academic-search     nature-citation
nature-data              nature-figure              nature-paper2ppt
nature-polishing         nature-reader              nature-response
nature-writing           paper-glance               remove-ai-flavor
research-paper-writing   scientific-writing         skill-creator
summarize                tavily-research
```

---

## 4. MCP 工具集成

### 4.1 MCP Server 矩阵

| MCP Server | 工具 | 用途 | 频率 |
|-----------|------|------|------|
| **consensus** | `search` | 2亿+学术论文搜索，引用计数+期刊质量 | Phase 1 |
| **context7** | `resolve-library-id`, `query-docs` | R/Python 库最新文档查询 | Phase 2 |
| **exa** | `web_search_exa`, `web_fetch_exa` | 网页搜索+内容提取 | Phase 1,5 |
| **grok-search** | `web_search`, `web_fetch`, `web_map` | 通用搜索+网站地图 | All phases |
| **MiniMax** | `web_search`, `understand_image` | 通用搜索+图像理解 | Phase 2,4 |
| **fast-context** | `fast_context_search` | AI 驱动代码语义搜索 | Phase 2 |
| **pubmed** | `search_articles` | PubMed 生物医学文献 | Phase 1 |

### 4.2 按任务类型的工具选择

| 任务 | 首选工具 | 备选工具 |
|------|---------|---------|
| 生物医学文献搜索 | `mcp__pubmed__search_articles` | `mcp__consensus__search` |
| 跨学科学术搜索 | `mcp__consensus__search` | `mcp__exa__web_search_exa` |
| R/Bioconductor 文档 | `mcp__context7__query-docs` | Web search |
| 期刊投稿要求 | `mcp__grok-search__web_search` | `mcp__exa__web_search_exa` |
| 代码语义搜索 | `mcp__fast-context__fast_context_search` | Grep |
| 论文全文获取 | `mcp__exa__web_fetch_exa` | `mcp__grok-search__web_fetch` |
| 图形内容分析 | `mcp__MiniMax__understand_image` | — |
| 网站结构分析 | `mcp__grok-search__web_map` | — |

---

## 5. 阶段 → 技能 → 工具 路由表

### 5.1 Phase 1: Research & Planning

```
Stage ① select_topic
  ├── Skill: topic_research
  │     └── MCP: grok-search (最新研究趋势)
  └── Skill: deep-research
        └── MCP: consensus + pubmed (全方位检索)

Stage ② target_journal
  ├── Skill: topic_research
  │     └── MCP: grok-search (期刊 Guide for Authors)
  └── Skill: nature-academic-search
        └── MCP: pubmed (期刊范围+发表记录)

Stage ③ literature_search
  ├── Skill: deep-research
  │     └── MCP: consensus + pubmed (系统检索)
  ├── Skill: nature-academic-search
  │     └── MCP: pubmed (MeSH 检索策略)
  └── Skill: nature-citation
        └── MCP: pubmed (引用验证)

Stage ④ formulate_hypotheses
  ├── Skill: topic_research
  └── Skill: scientific-writing
```

### 5.2 Phase 2: Data & Methods

```
Stage ⑤ data_audit
  ├── Skill: nature-data (FAIR 检查)
  └── Skill: qc_pipeline (QC 指标验证)

Stage ⑥ figure_planning
  ├── Skill: figure_planning (图表策略)
  └── Skill: nature-figure (发表标准)

Stage ⑦ run_analysis
  ├── Skill: spatial_analysis
  ├── Skill: statistical_testing
  ├── Skill: pathway_inference
  │     └── MCP: context7 (R包文档参考)
  └── MCP: fast-context (代码定位+调试)

Stage ⑧ verify_methods
  ├── Skill: qc_pipeline (输出验证)
  ├── Skill: reproducibility (环境快照)
  └── Skill: statistical_testing (统计审核)
```

### 5.3 Phase 3: Writing

```
Stage ⑨-⑫ Write IMRAD
  ├── Skill: scientific-writing (段落草稿)
  ├── Skill: nature-writing (Nature 风格)
  ├── Skill: nature-citation (引用集成)
  │     └── MCP: pubmed (DOI/PMID 验证)
  └── Skill: research-paper-writing (claim-support 对齐)
```

### 5.4 Phase 4: Assembly & Review

```
Stage ⑬ assemble_manuscript
  ├── Skill: paper_writing
  ├── Skill: nature-figure (图形嵌入)
  └── Skill: nature-citation (引用编号)

Stage ⑭ integrity_check
  └── Skill: qc_pipeline (16 gate rules)

Stage ⑮ internal_review
  ├── Skill: academic-paper-reviewer (5 reviewer personas)
  └── Skill: humanizer (AI traces check)
```

### 5.5 Phase 5-6: Revision & Finalize

```
Stage ⑯ apply_revision
  ├── Skill: paper_writing
  ├── Skill: nature-polishing
  ├── Skill: humanizer
  └── Skill: nature-response

Stage ⑰ re_review
  └── Skill: academic-paper-reviewer (re-review mode)

Stage ⑱ finalize
  ├── Skill: qc_pipeline (最终完整性)
  ├── Skill: nature-data (数据声明)
  ├── Skill: nature-polishing (最终润色)
  └── Skill: nature-paper2ppt (可选)
```

---

## 6. Agent → 技能 → MCP 分配矩阵

| Agent | Internal Skills | External Skills | MCP Tools |
|-------|----------------|-----------------|-----------|
| research_strategist | topic_research | deep-research, nature-academic-search | consensus, grok-search, pubmed |
| literature_reviewer | literature_search | deep-research, nature-academic-search, nature-citation | consensus, pubmed |
| data_auditor | qc_pipeline | nature-data | context7 |
| figure_planner | figure_planning | nature-figure | — |
| analysis_executor | spatial_analysis, pathway_inference, qc_pipeline | — | fast-context, context7 |
| pipeline_engineer | qc_pipeline, reproducibility | — | context7 |
| statistician | statistical_testing | — | — |
| report_writer | paper_writing, revision_routing | scientific-writing, nature-writing, nature-polishing, nature-citation, nature-response, humanizer, research-paper-writing | pubmed |
| integrity_checker | qc_pipeline | academic-paper-reviewer, nature-data, ai-writing-detection | — |
| multi_omics_integrator | multi_omics, spatial_analysis, pathway_inference | — | context7 |
| code_librarian | qc_pipeline | — | fast-context |
| team_orchestrator | paper_loop | deep-research, academic-pipeline | grok-search |

---

## 7. Skill 注册表 (`.claude/SKILL_REGISTRY.md`)

### 7.1 触发词索引

基于 `config/default_config.yaml §6 (skills_dispatcher)`，每个 skill 有完整的中英文触发词列表:

```yaml
# 示例: scientific-writing 触发词
scientific-writing:
  triggers:
    english:
      - "write Methods"
      - "write Results"  
      - "write Introduction"
      - "write Discussion"
      - "draft section"
      - "IMRAD"
      - "scientific manuscript"
      - "draft manuscript"
      - "reporting guidelines"
      - "CONSORT"
      - "STROBE"
    chinese:
      - "医学论文"
      - "科研写作段落"
      - "写论文段落"
```

### 7.2 自动触发机制

```
用户输入 → 技能触发词匹配 → SkillsDispatcher
  ├── 精确匹配 → 直接调度
  ├── 模糊匹配 → 列出候选, 请求确认
  └── 无匹配 → 回退到 team_orchestrator (通用 Agent)
```

---

## 8. 扩展集成

### 8.1 添加自定义技能

```yaml
# config/custom_skills.yaml
my_custom_analysis:
  triggers:
    - "custom analysis"
    - "my specific method"
  phase: "analysis"
  agent: "analysis_executor"
  description: "My specialized analysis pipeline"
```

### 8.2 添加新 MCP Server

```json
// .claude/mcp.json
{
  "mcpServers": {
    "my-new-server": {
      "command": "my-mcp-server",
      "args": ["--config", "path/to/config"]
    }
  }
}
```
