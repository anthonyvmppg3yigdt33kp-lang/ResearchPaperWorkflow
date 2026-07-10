# ARCHIVED CASE STUDIES v2.0

> Historical examples. Do not use their stage counts or outputs as current
> workflow truth. Current validation examples are the PBMC3K Research Intent
> and TargetTask contracts under `intents/examples/` and `targets/examples/`.

**Version**: 2.0.0 | **Cases**: 3 real + 1 test

---

## Case 1: IgG4&MALT — 生物标志物发现 (WGCNA + ML)

### 项目背景

| 属性 | 值 |
|------|-----|
| **研究问题** | IgG4-ROD vs MALT Lymphoma 鉴别诊断生物标志物 |
| **数据类型** | 转录组 (microarray/RNA-seq) |
| **分析方法** | DE分析 → CIBERSORT免疫浸润 → WGCNA → ML |
| **目标期刊** | Arthritis Research & Therapy |
| **当前状态** | WGCNA完成 (17 modules, 132 hub-DEG)，待ML + 论文写作 |

### 管线映射

```
已完成的阶段:

Phase 1: Research & Planning
  ① select_topic ✓ — "IgG4-ROD vs MALT differential biomarkers"
  ③ literature_search ✓ — IgG4-RD, MALT lymphoma, WGCNA biomarker studies

Phase 2: Data & Methods
  ⑤ data_audit ✓ — GEO dataset validated
  ⑦ run_analysis (partial):
    ├── DE analysis ✓ — 842 DEGs identified
    ├── CIBERSORT ✓ — 6 immune cell types significant
    └── WGCNA ✓ — power=20, 17 modules, 8 disease-immune, 132 hub-DEG

待完成的阶段:

Phase 1: ② target_journal, ④ formulate_hypotheses
Phase 2: ⑥ figure_planning, ⑦ run_analysis (ML部分), ⑧ verify_methods
Phase 3-6: 全文写作 + 审查 + 修订 + 定稿
```

### 工作流执行计划

```python
# 当前项目快速写作路径 (From Results pattern)
wf = E2EWorkflow(paper_id="paper_igg4malt_20260620")

# Phase 1: 补完策略
wf.run(phases=[1])  # target_journal + hypotheses (已有 topic + literature)

# Phase 2: 补完分析
wf.run(phases=[2])  # figure_planning + ML analysis + verify

# Phase 3-6: 写作+审查+定稿
wf.run(phases=[3, 4, 5], stop_at_checkpoint=True)
```

### 特定配置覆盖

```yaml
# paper_config.yaml (项目级覆盖)
paper_type: original_research
target_journal: "Arthritis Research & Therapy"

writing_standards:
  sections:
    abstract:
      max_words: 300
    methods:
      subsections:
        - "Data Acquisition and Preprocessing"
        - "Differential Expression Analysis"
        - "Immune Cell Deconvolution (CIBERSORT)"
        - "Weighted Gene Co-expression Network Analysis (WGCNA)"
        - "Machine Learning-Based Feature Selection"
        - "Diagnostic Model Construction and Validation"
```

### 关键质量门关注点

- **G1.4 (claim_artifact_binding)**: WGCNA power=20, 17 modules, 132 hub-DEG — 必须可追溯到 `results/wgcna/` 下的具体文件
- **G2.4 (methods_parameters_complete)**: WGCNA 参数必须完整 — softPower, minModuleSize, mergeCutHeight, signedKME 等
- **G2.7 (statistics_reported)**: DE 结果必须报告 log2FC + CI + adjusted p-value

---

## Case 2: 肝骨轴MR — 孟德尔随机化中介分析

### 项目背景

| 属性 | 值 |
|------|-----|
| **研究问题** | 验证"肝骨轴"因果假说: LiverPDFF → BMFF → BMD |
| **数据类型** | GWAS summary statistics (公开) |
| **分析方法** | 两样本MR → 中介MR (四步) → MVMR → 敏感性分析 |
| **核心结果** | LiverPDFF→BMFF β=+0.0621(P=4e-5), BMFF→BMD β=-0.0883(P=2e-7), 中介 α×β=-0.00548(P=0.001) |
| **当前状态** | v17.5 主分析完成，论文待整合 |

### 管线映射

```
Phase 2: Data & Methods
  ⑤ data_audit — GWAS catalog + OpenGWAS 数据验证
  ⑦ run_analysis:
    ├── Two-sample MR (IVW, MR-Egger, Weighted Median, MR-PRESSO)
    ├── Bidirectional MR (排除反向因果)
    ├── Two-step Mediation MR (中介效应)
    ├── Multivariable MR (竞争性中介)
    └── Sensitivity: Cochran's Q, Leave-one-out, Steiger, F-statistic
  ⑧ verify_methods:
    └── Gate G2.8 (pseudoreplication_check) — 对 MR 特别重要:
        确保暴露和结局 GWAS 样本不重叠
        确保 IV 选择无 winner's curse

Phase 3: Writing
  ⑨ write_methods — 需遵循 STROBE-MR 报告指南
  ⑩ write_results — 每个 β 必须带 CI + p-value + 敏感性检验结果
  ⑪ write_introduction — 肝骨轴生物学背景 + MR 方法学空白
  ⑫ write_discussion — 中介比例解释 + 竞争性中介讨论
```

### 特定质量门

```
MR 特定的额外检查:
  □ F-statistic ≥ 10 for all IVs (弱工具变量排除)
  □ MR-Egger intercept p > 0.05 (无显著水平多效性)
  □ MR-PRESSO global test (异常值检测)
  □ Cochran's Q p > 0.05 (无异质性)
  □ Steiger directionality: "TRUE" (因果方向正确)
  □ 中介效应 Sobel test + Bootstrap CI
```

### 工作流执行

```python
wf = E2EWorkflow(paper_id="paper_liver_bone_axis_mr")

# 快速写作路径 (已有完整分析结果)
wf.run(phases=[3, 4, 5], stop_at_checkpoint=True)

# 如果审稿人要求额外敏感性分析:
wf.run(phases=[2, 3, 4, 5])  # 回到 Phase 2 补充分析
```

---

## Case 3: StereoSeq — 空间转录组学平台

### 项目背景

| 属性 | 值 |
|------|-----|
| **研究问题** | 健康肾脏空间转录组参考图谱 → 空间解卷积 → 衰老通路机制 |
| **数据类型** | Stereo-seq bin50 (30,904 spots × 34,363 genes) + scRNA-seq 参考 (GSE185809, 56,728 cells) |
| **分析方法** | QC → scRNA参考图谱 → 空间解卷积 → 区域分割 → PCD通路分析 |
| **当前状态** | 全部分析完成，Methods section 修订中 |

### 管线映射

```
Phase 1:
  ① select_topic — "Spatial transcriptomic atlas of aging human kidney"
  ③ literature_search — 空间转录组肾脏研究, 解卷积方法比较

Phase 2 (已完成全部分析):
  ⑤ data_audit — bin50 QC: MT<25%/30%, Leiden r=0.6
  ⑦ run_analysis:
    ├── scRNA reference (5 samples, 19 cell types, KIDNEY_COLORS)
    ├── Spatial deconvolution (SpecWeight NNLS + Anatomical Prior + Sinkhorn-Knopp, MAE=0.19%)
    ├── Area domain segmentation (3-area: glomeruli/cortex/medulla)
    ├── PCD pathway analysis (18 pathways × 3 areas × 2 samples, 42/54 significant)
    └── Spatial expression visualization (星云热图 144 PDF + 通路等高线 12图)
  ⑧ verify_methods:
    └── Gate G2.4 — 参数完整性至关重要:
        解卷积方法选择 (SpecWeight>DWLS 的论据)
        区域分割参数 (graph morphological)
        PCD 通路评分方法

Phase 3 (写作中):
  ⑨ write_methods:
    └── 必须精确记录:
        - 空间解卷积: SpecWeight NNLS 参数, Anatomical Prior 构建
        - 区域分割: 图形态学分割方法, boundary detection
        - PCD 分析: 18种细胞死亡通路评分, FDR 校正
```

### 方法学论文特征

```yaml
paper_type: methods  # 方法学/平台论文

# 重点:
# - 解卷积 Benchmark: SpecWeight vs DWLS vs RCTD vs SPOTlight
# - 计算效率: 30,904 spots 处理时间
# - 可复现性: Docker + renv.lock + 固定 seeds
# - 数据可用性: GEO accession (参考数据) + Zenodo (处理数据)
```

### 关键交叉验证点

```
论文 Methods vs 代码:
  □ "MT<25%" — mt_filter.py 默认值 25 ✓
  □ "Leiden r=0.6" — leiden_clustering.py 默认值 0.6 ✓
  □ "SpecWeight NNLS" — 实际使用的方法 vs DWLS (曾尝试但效果差)
  □ "MAE=0.19%" — deconvolution 评估指标
  □ "42/54 significant" — PCD 分析 FDR<0.05 统计
  □ "Anoikis δ=0.55-0.67" — 效应量报告
```

---

## Case 4: test_e2e_live — 端到端测试案例

### 测试概述

位于 `papers/test_e2e_live/`，展示了完整的项目文件结构:

```
papers/test_e2e_live/
├── project_passport.yaml
├── checkpoint_ledger.jsonl
├── artifact_ledger.jsonl
├── research_plan/
│   ├── feasibility_decision.md
│   ├── formatting_requirements.yaml
│   └── journal_profile.md
├── data/
│   ├── data_audit_report.md
│   ├── data_inventory.yaml
│   └── qc_filter_report.md
├── results/
│   ├── cell_annotation.md
│   └── clustering_results.yaml
├── integrity/
│   ├── integrity_report.json
│   └── integrity_report.md
└── workflow_state/
    ├── e2e_state_20260618_170203.json
    └── pending_invocations/  (5 个 skill 调用等待)
```

### 测试覆盖

```python
# tests/test_all.py 和 tests/test_integration.py
# 测试内容:
# - P0 verification: 核心流程完整性
# - E2E workflow: 5 phase 全流程
# - Integrity gates: 16 rules 执行
# - Passport: artifact 哈希记录+验证
# - Agent dispatch: 12 agent 调度
# - Config loading: YAML 配置解析
```

---

## 跨案例对比

| 维度 | IgG4&MALT | 肝骨轴MR | StereoSeq |
|------|----------|---------|-----------|
| **研究类型** | 生物标志物发现 | 因果推断 | 方法学/平台 |
| **论文类型** | original_research | original_research | methods |
| **数据来源** | GEO (转录组) | GWAS (公开) | Stereo-seq + scRNA-seq |
| **核心方法** | WGCNA + ML | MR + Mediation | Deconv + Spatial |
| **报告指南** | — | STROBE-MR | — |
| **关键Gate** | G2.4 (WGCNA参数) | G2.8 (样本独立性) | G2.4 (解卷积参数) |
| **工作流模式** | Pattern 2 (From Results) | Pattern 2 (From Results) | Pattern 4 (Methods Paper) |
| **当前阶段** | Phase 2→3 过渡 | Phase 3 写作 | Phase 3 写作 |
| **预估完成** | 4-6 周 | 2-4 周 | 2-4 周 |
