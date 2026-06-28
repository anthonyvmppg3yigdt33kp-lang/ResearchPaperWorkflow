# Historical Note

This guide predates the next-generation V4 truth layer. Use
`docs/NEXT_GEN_V4_TRUTH_LAYER.md` for the current 20-stage workflow,
`WorkflowAPI`, agent harness, and validation commands.

# ResearchPaperWorkflow V4 完整安装与使用教程

本文档面向第一次下载仓库的用户，覆盖安装、Claude Code/Codex 配置、skill 自动补齐、课题数据迁移、完整工作流执行和常见问题排查。

## 1. 环境准备

建议环境：

- Python 3.9+
- Git
- Claude Code 或 Codex
- 可选：`gh` GitHub CLI，用于发布 tag、release、PR

Windows PowerShell 示例：

```powershell
python --version
git --version
gh --version
```

如果你用 conda：

```powershell
conda create -n paperflow python=3.11 -y
conda activate paperflow
```

## 2. 下载与安装

```powershell
git clone https://github.com/anthonyvmppg3yigdt33kp-lang/ResearchPaperWorkflow.git
cd ResearchPaperWorkflow
python -m pip install -e .
python -m paper_workflow.cli.main install-skills
```

`install-skills` 会读取 `config/required_skills.yaml`，比较以下本机目录：

- `~/.codex/skills`
- `~/.agents/skills`
- `~/.claude/skills`

如果缺少仓库自带的 bundled skill，会安装到：

```text
~/.codex/skills/<skill_name>/SKILL.md
```

检查但不安装：

```powershell
python -m paper_workflow.cli.main install-skills --check-only
```

维护者更新仓库 bundled skill 后，强制刷新本机副本：

```powershell
python -m paper_workflow.cli.main install-skills --force
```

指定安装目录：

```powershell
$env:PAPER_WORKFLOW_SKILL_TARGET="D:\my_skills"
python -m paper_workflow.cli.main install-skills
```

跳过 CLI 启动时的自动检查：

```powershell
$env:PAPER_WORKFLOW_SKIP_SKILL_CHECK="1"
```

## 3. Claude Code / Codex 接入方式

### Claude Code

1. 在 Claude Code 中打开仓库根目录。
2. 确认根目录存在 `AGENTS.md`、`.claude/agents/`、`.claude/skills/`。
3. 首次进入后让 Claude 读取项目说明：

```text
请阅读 AGENTS.md、README.md、docs/V4_INSTALLATION_AND_USAGE_GUIDE.md，并按 V4 工作流帮我推进论文项目。
```

4. 如果 Claude 没自动识别 skill，先运行：

```powershell
python -m paper_workflow.cli.main install-skills
```

### Codex

1. 在 Codex 中打开仓库根目录。
2. 确认本机 skill 已补齐：

```powershell
python -m paper_workflow.cli.main install-skills --check-only
```

3. 对 Codex 发起任务时，建议说明当前 paper id 和目标阶段：

```text
请使用 ResearchPaperWorkflow V4，帮我运行 paper_xxx 的 data_audit 到 figure_planning，并记录 gate 结果。
```

## 4. 创建一个新论文项目

```powershell
python -m paper_workflow.cli.main create-project `
  --idea "Spatial transcriptomics reveals kidney aging mechanisms" `
  --field "spatial transcriptomics, aging, kidney" `
  --journal "Genome Biology"
```

查看所有项目：

```powershell
python -m paper_workflow.cli.main list-papers
```

查看状态：

```powershell
python -m paper_workflow.cli.main status --paper <paper_id>
```

## 5. 迁移自己的课题数据和材料

每个项目在：

```text
papers/<paper_id>/
```

推荐目录：

```text
papers/<paper_id>/
  data/
    raw/                  原始数据，只读保存
    processed/            预处理结果
    data_inventory.yaml   数据清单
  references/
    library.bib           BibTeX 文献库
    citation_evidence.csv 引文证据表
  research_plan/
    hypotheses.yaml
    statistical_analysis_plan.yaml
    study_design_protocol.yaml
  results/
    figure_plan.json
    run_manifest.yaml
  manuscript/
    abstract.md
    introduction.md
    methods.md
    results.md
    discussion.md
    manuscript.md
  review/
  integrity/
  submission/
```

迁移步骤：

1. 把原始数据放入 `data/raw/`，不要直接覆盖。
2. 把已经清洗的数据放入 `data/processed/`。
3. 把参考文献导出为 BibTeX，命名为 `references/library.bib`。
4. 把已有初稿拆成 IMRAD 文件，放入 `manuscript/`。
5. 把已有图表、统计结果和运行日志放入 `results/`。
6. 在 `data/data_inventory.yaml` 写清楚数据来源、样本量、批次、平台、患者/供体单位。
7. 在 `research_plan/statistical_analysis_plan.yaml` 写清楚主要终点、协变量、多重检验、缺失值策略和验证集。

最小 `data_inventory.yaml` 示例：

```yaml
datasets:
  - id: cohort_a
    source: public
    accession: GSE000000
    platform: Visium
    samples: 12
    biological_unit: donor
    groups: [young, aged]
batch_variables:
  - sequencing_batch
  - center
notes: "Raw data kept in data/raw; processed matrices in data/processed."
```

最小 `statistical_analysis_plan.yaml` 示例：

```yaml
primary_endpoint: "Cell-type proportion difference between young and aged donors"
statistical_unit: donor
primary_model: "mixed-effects model"
covariates: [sex, batch]
multiple_testing: "Benjamini-Hochberg FDR"
missing_data_strategy: "document and exclude samples failing pre-defined QC"
external_validation: "independent public cohort if available"
frozen_before_analysis: true
```

## 6. V4 工作流阶段

核心 20 个阶段：

```text
1  select_topic
2  target_journal
3  literature_search
4  formulate_hypotheses
5  design_analysis_plan
6  data_audit
7  figure_planning
8  run_analysis
9  verify_methods
10 write_methods
11 write_results
12 write_introduction
13 write_discussion
14 assemble_manuscript
15 aigc_humanizer_review
16 integrity_check
17 internal_review
18 apply_revision
19 re_review
20 finalize
```

运行全流程：

```powershell
python -m paper_workflow.cli.main run-pipeline --paper <paper_id> --stop-on-failure
```

在关键 checkpoint 处，建议人工确认后再继续：

```powershell
python -m paper_workflow.cli.main checkpoint `
  --paper <paper_id> `
  --stage design_analysis_plan `
  --decision approved `
  --notes "SAP frozen before primary analysis."
```

## 7. AIGC 审查与 Humanizer

V4 新增阶段：

```text
assemble_manuscript -> aigc_humanizer_review -> integrity_check
```

单独运行：

```powershell
python -m paper_workflow.cli.main run-aigc-humanizer --paper <paper_id>
```

输出：

- `review/aigc_detection_report.md`
- `review/humanizer_revision_plan.yaml`
- `manuscript/manuscript_humanized.md`

注意：该功能是文本卫生与提交前风险审查，不声称判断作者身份。它会保留科学事实、引用、数字、统计结果和方法名，只处理模板化表达、AI 界面残留和过度机械的语言结构。

## 8. 完整性门控

运行：

```powershell
python -m paper_workflow.cli.main run-integrity-gate --paper <paper_id>
```

V4 共 44 个 gate，覆盖：

- citation and claim integrity
- clinical design
- data and bias
- statistics and model
- single-cell and spatial omics
- AI/ML
- AIGC text hygiene
- format and completeness

如果 gate 失败：

```powershell
python -m paper_workflow.cli.main diagnose-gate-failures --paper <paper_id>
```

如果修改了上游数据、图表或正文，运行：

```powershell
python -m paper_workflow.cli.main detect-artifact-drift --paper <paper_id>
python -m paper_workflow.cli.main sync-artifact-stale --paper <paper_id>
```

## 9. 推荐的协作流程

1. 由我们定义研究问题和可用数据。
2. `select_topic` 和 `target_journal` 生成方向与目标期刊约束。
3. `literature_search` 建立文献库和证据表。
4. `design_analysis_plan` 冻结 SAP，防止事后解释。
5. `data_audit` 和 `figure_planning` 明确数据质量与图表故事线。
6. `run_analysis` 和 `verify_methods` 只在代码与参数可复现后放行。
7. `write_*` 阶段拆分撰写 IMRAD。
8. `assemble_manuscript` 汇总全文。
9. `aigc_humanizer_review` 清理文本风险。
10. `integrity_check` 和 `internal_review` 形成修订清单。
11. `apply_revision`、`re_review`、`finalize` 产出投稿包。

## 10. 测试与验收

```powershell
python -m pytest -q
```

当前 V4 验收结果：

```text
42 passed
```

Smoke test：

```powershell
python -m paper_workflow.cli.main run-aigc-humanizer --paper v4_smoke
```

## 11. 常见问题

### import 到旧仓库

如果 `import paper_workflow` 指向旧目录，重新安装当前仓库：

```powershell
python -m pip uninstall paper-workflow -y
python -m pip install -e .
python -c "import paper_workflow; print(paper_workflow.__version__, paper_workflow.__file__)"
```

### skill 没加载

```powershell
python -m paper_workflow.cli.main install-skills --check-only
python -m paper_workflow.cli.main install-skills
```

### GitHub 发布失败

先登录：

```powershell
gh auth login
gh auth status
```

然后重新 push/tag/release。

### 中文路径显示乱码

这是 Windows 终端编码显示问题时常见的表现。优先确认文件实际存在和 Python 读写正常；必要时将终端切换为 UTF-8：

```powershell
chcp 65001
```


