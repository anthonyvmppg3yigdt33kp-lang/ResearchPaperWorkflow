# Codex 模式化交互实践指南

Created: 2026-07-07

本指南用于把模糊请求转换成可执行、可验证、可恢复的 Codex 任务。核心模板是：

```text
模式 + 根目录 + 允许输入 + 禁止动作 + 输出位置 + 证据标准 + closeout 要求
```

先路由，再执行。不要直接说“全面优化”或“继续推进”。

## 1. 先让 Codex 路由任务

```powershell
python -m paper_workflow.cli.main route-task `
  --request "先扫描项目，找出 workflow 和 skill 的问题，不要改文件" `
  --json
```

工具、skill、agent 健康检查：

```powershell
python -m paper_workflow.cli.main doctor --json
```

如果 `fast-context` 不可用，doctor 会返回 degraded 状态，并要求使用 `rg --line-number`、直接文件读取和 Python 文件扫描作为 fallback。

## 2. exploration_mode

用途：只读定位、项目扫描、证据地图、状态汇总。

```text
Mode: exploration_mode
Canonical root: C:\Users\HP\Documents\论文\ResearchPaperWorkflow
Goal: 扫描当前 workflow、skill、agent、配置和旧版本残余，输出问题清单
Allowed inputs: AGENTS.md, README.md, ARCHITECTURE.md, config/, src/, tests/, docs/
Forbidden actions: 不运行分析、不安装包、不下载数据库、不改 papers/results 生成数据
Output: chat closeout 或 docs/ 下的审计报告
Evidence standard: 每个结论必须有文件路径、命令输出或配置字段支撑
Closeout: completed / in-progress / blockers / next safe action
```

难点：根目录不明确、文件太多、fast-context 不可用。处理方式：先列候选根和证据，只读最小文件集；fast-context 不可用时运行 `doctor`，使用 `rg` 和直接读取。

## 3. analysis_design_mode

用途：设计统计或生信分析，不执行代码。

```text
Mode: analysis_design_mode
Canonical root: C:\Users\HP\Documents\IgG4-ROD  vs  MALT-L
Goal: 为 bulk RNA-seq 差异分析设计最小可执行方案
Allowed inputs: data inventory, current_run.yaml, prior run_manifest, method contract
Forbidden actions: 不运行分析、不安装包、不下载数据库、不写最终结果
Output: results/runs/bulk_de_20260707_v1/analysis_design.yaml
Evidence standard: 定义统计单位、分组列、协变量、主要对比、预期输出和失败条件
Closeout: 明确哪些内容需要我批准后才能执行
```

难点：用户只说“做差异分析”、数据字段不清、目标期刊过早。处理方式：先生成 design；未知字段标为 `requires_human_input`；探索项目只记录 `candidate_journal_class`。

## 4. execution_mode

用途：在设计已批准后运行有边界的命令或写入受控输出。

```text
Mode: execution_mode
Canonical root: C:\Users\HP\Documents\IgG4-ROD  vs  MALT-L
Approved design: papers/<paper_id>/results/runs/bulk_de_20260707_v1/analysis_design.yaml
Run id: bulk_de_20260707_v1
Allowed inputs: design 中锁定的数据和参数
Forbidden actions: 不临时安装包、不下载数据库、不写 results/runs/<run_id>/ 之外
Output: papers/<paper_id>/results/runs/bulk_de_20260707_v1/
Evidence standard: run_manifest + parameters + logs + source maps + evaluation_report
Closeout: 说明输出是 exploratory、analysis-ready 还是 manuscript-ready
```

难点：依赖缺失、输出散落、运行失败。处理方式：停止并报告 setup 要求；只写 `results/runs/<run_id>/`；失败也保留日志和 manifest，不标记 completed。

## 5. closeout_audit_mode

用途：投稿前、release 前、checkpoint promotion 前的完整 gate。

```text
Mode: closeout_audit_mode
Canonical root: C:\Users\HP\Documents\论文\ResearchPaperWorkflow
Goal: 投稿或发布前检查 contract、CI、文档、版本、release note 和旧版本残余
Allowed inputs: workflow_contract.yaml, config/, docs/, tests/, GitHub PR/CI 状态
Forbidden actions: 不创建 release tag，除非我明确批准
Output: closeout audit report 或 PR closeout
Evidence standard: 每个 pass/fail 需要命令或 GitHub 状态支撑
Closeout: 列出 blockers、未发布原因、下一步 release 条件
```

难点：用户说“发布新版”、CI 失败、旧版本残余。处理方式：先确认是否允许 tag/release；修复后重跑本地检查和 GitHub checks；历史 release note 保留，活跃文档更新。

## 6. ppt_briefing_mode

用途：只读 briefing、slide brief、figure source map。

```text
Mode: ppt_briefing_mode
Canonical root: C:\Users\HP\Documents\IgG4-ROD  vs  MALT-L
Goal: 基于已验证 figure source map 生成 10 页科研汇报结构
Allowed inputs: brief/SLIDE_BRIEF.md, brief/FIGURE_STORYLINE.md, figure_source_map.yaml
Forbidden actions: 不新增分析、不猜 figure 来源、不使用未映射图片作最终证据
Output: brief/SLIDE_BRIEF.md and brief/FIGURE_STORYLINE.md
Evidence standard: 每页结论绑定 figure/table/source file
Closeout: 标出缺图、弱证据、需要补分析的位置
```

难点：只有漂亮图没有 source map、图和结论不匹配、缺统计单位。处理方式：降级为草稿；先改 storyline；把缺统计单位标为 blocker。

## 7. retrospective_mode

用途：把重复问题固化为规则、skill、contract、prompt macro。

```text
Mode: retrospective_mode
Canonical root: C:\Users\HP\Documents\论文\ResearchPaperWorkflow
Goal: 把 fast-context 不可用、skill/agent 检查和模式路由问题固化进仓库
Allowed inputs: AGENTS.md, config/workflow_modes.yaml, src/paper_workflow/routing/, docs/
Forbidden actions: 不改 memory，除非我明确要求；不改生成结果
Output: routing code, doctor CLI, documentation update
Evidence standard: 有测试覆盖，并能通过 validate-contract
Closeout: 说明新增能力、测试结果、剩余外部配置
```

难点：AGENTS.md 过长、外部 MCP 不可控、skill 太多导致路由混乱。处理方式：AGENTS.md 只保留短规则；外部 MCP 只能检测和降级；用 doctor 检查必需 skill，用 mode resolver 先缩小任务边界。

## 8. 推荐一句话模板

```text
请先用 route-task 判断模式；如果不是 execution_mode，不要运行代码。根目录是 [path]。只允许读取 [inputs]。禁止 [actions]。输出到 [path]。证据必须来自 [standard]。最后按 completed / blockers / next action closeout。
```
