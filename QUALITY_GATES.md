# QUALITY GATES — 7类41规则质量门体系 (v3.0)

**Version**: 3.0.0 | **Total Gates**: 41 | **Severities**: CRITICAL(17) + HIGH(21) + MEDIUM(3)

> v3.0: 从论文完整性升级为医学证据可信度门控系统。新增5大类别25个医学专用门。

---

## 1. 质量门概览

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    INTEGRITY GATE SYSTEM                         │
  │                                                                  │
  │  G1: CITATION       G2: CLAIM          G3: CONTENT              │
  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
  │  │ bibtex_      │    │ citation_    │    │ results_no_ │          │
  │  │ existence    │    │ evidence_    │    │ citations   │          │
  │  │              │    │ traceability │    │             │          │
  │  │ figures_     │    │ claim_       │    │ no_local_   │          │
  │  │ referenced   │    │ artifact_    │    │ paths       │          │
  │  │              │    │ binding      │    │             │          │
  │  └─────────────┘    └─────────────┘    └─────────────┘          │
  │                                                                  │
  │  G4: DATA            G5: STATISTICS      G6: FORMAT              │
  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
  │  │ data_        │    │ statistics_ │    │ section_    │          │
  │  │ availability │    │ reported    │    │ length_     │          │
  │  │              │    │             │    │ minimum     │          │
  │  │ code_        │    │ pseudo-     │    │ no_bullets_ │          │
  │  │ availability │    │ replication │    │ in_prose    │          │
  │  │              │    │ _check      │    │             │          │
  │  │ methods_     │    │ results_no_ │    │ figure_     │          │
  │  │ parameters_  │    │ overinter-  │    │ count_      │          │
  │  │ complete     │    │ pretation   │    │ requirements│          │
  │  │              │    │             │    │             │          │
  │  │ discussion_  │    │             │    │             │          │
  │  │ limitations  │    │             │    │             │          │
  │  └─────────────┘    └─────────────┘    └─────────────┘          │
  └─────────────────────────────────────────────────────────────────┘
```

---

## 2. CRITICAL 规则（5条 — 阻塞管线）

### G1.1 — bibtex_citation_existence
```
严重级别: CRITICAL ⛔
描述: 手稿中每个引用密钥必须在 references.bib 中存在
检查: 提取所有 \cite{key} → 验证 key ∈ BibTeX entries
阻塞: 是
自动修复: 否 (需人工补充缺失引用)
```

### G1.2 — citation_evidence_traceability
```
严重级别: CRITICAL ⛔
描述: 每个事实性声称必须可追溯到至少一条引用证据
检查: 提取声称 → 匹配 citation_evidence.csv → 验证 DOI/PMID
阻塞: 是
自动修复: 否
```

### G1.3 — results_no_citations
```
严重级别: CRITICAL ⛔
描述: Results 部分不得包含对外部文献的引用
检查: 扫描 Results 段落 → 检测 \cite{} 或 (Author, Year) 模式
阻塞: 是
自动修复: 否 (需移至 Discussion)
```

### G1.4 — claim_artifact_binding
```
严重级别: CRITICAL ⛔
描述: 手稿中每个数值声称必须可追溯到具体的分析制品文件
检查: 提取数值声称 → 匹配 artifact_ledger.jsonl → 验证 hash 一致性
阻塞: 是
自动修复: 否
示例:
  声称: "WGCNA identified 17 co-expression modules"
  追溯: results/wgcna/module_assignment.csv → hash SHA256:abc123...
  验证: artifact_ledger.jsonl 中存在该 hash ✓
```

### G1.5 — figures_referenced
```
严重级别: CRITICAL ⛔
描述: figures/ 目录中的每个图形文件必须至少在手稿中被引用一次
检查: list figures/ → grep manuscript for each figure filename
阻塞: 是
自动修复: 否
```

---

## 3. HIGH 规则（8条 — 必须在提交前解决）

### G2.1 — data_availability_statement
```
严重级别: HIGH ⚠️
描述: 手稿必须包含完整的数据可用性声明及存储库 accession 号
检查: 搜索 "Data Availability" 段落 → 验证 accession 格式
阻塞: 是 (但支持自动修复)
自动修复: 是 (基于 data_inventory.yaml 生成模板)
```

### G2.2 — code_availability_statement
```
严重级别: HIGH ⚠️
描述: 手稿必须包含代码可用性声明及仓库 DOI/URL
检查: 搜索 "Code Availability" 段落 → 验证 DOI/URL 格式
阻塞: 是
自动修复: 是
```

### G2.3 — no_local_paths
```
严重级别: HIGH ⚠️
描述: 手稿不得包含本地文件路径 (C:/Users/..., /home/...)
检查: regex 扫描 → 标记路径模式
阻塞: 是
自动修复: 是 (替换为相对路径或通用描述)
```

### G2.4 — methods_parameters_complete
```
严重级别: HIGH ⚠️
描述: Methods 必须报告所有软件版本、参数值和随机种子
检查: 解析 Methods → 验证必需字段:
  [software_versions, parameters, random_seeds, thresholds]
阻塞: 是
自动修复: 否 (需人机协作提取参数)
```

### G2.5 — discussion_limitations
```
严重级别: HIGH ⚠️
描述: Discussion 必须包含至少一个专门的局限性段落
检查: 在 Discussion 中搜索 "limitation" / "limitations" / "caveat" 关键词
阻塞: 是
自动修复: 否 (需结合具体研究内容)
```

### G2.6 — results_no_overinterpretation
```
严重级别: HIGH ⚠️
描述: Results 不得包含因果语言（用于相关性发现）或推测性解释
检查: 扫描因果词汇 ("causes", "leads to", "triggers") + 推测信号
阻塞: 是
自动修复: 否
```

### G2.7 — statistics_reported
```
严重级别: HIGH ⚠️
描述: 每个统计检验必须报告: 检验统计量, 效应量, 置信区间, 精确p值
检查: 解析统计声称 → 验证字段完整性:
  [test_statistic, effect_size, ci, p_value]
阻塞: 是
自动修复: 否
```

### G2.8 — pseudoreplication_check
```
严重级别: HIGH ⚠️
描述: 无伪重复: 生物重复与技术重复正确区分
检查: 识别重复结构 → 验证独立性假设
阻塞: 是
自动修复: 否
```

---

## 4. MEDIUM 规则（3条 — 警告不阻塞）

### G3.1 — section_length_minimum
```
严重级别: MEDIUM ℹ️
描述: 各部分满足最低字数要求
检查: word_count(section) vs paper_type minimum
阻塞: 否
自动修复: 否
```

### G3.2 — no_bullets_in_prose
```
严重级别: MEDIUM ℹ️
描述: 正文段落不得使用项目符号或编号列表
检查: 扫描正文 → 检测 bullet/list markers
阻塞: 否
自动修复: 是 (自动转换为段落)
```

### G3.3 — figure_count_requirements
```
严重级别: MEDIUM ℹ️
描述: 图表数量不超过目标期刊限制
检查: count(figures) + count(tables) vs journal limits
阻塞: 否
自动修复: 否
```

---

## 5. 门触发矩阵

| Stage | bibtex | citation_trace | results_no_cite | claim_bind | fig_ref | data_avail | code_avail | no_paths | params | limits | no_overinterp | stats | pseudo | length | no_bullets | fig_count |
|-------|--------|----------------|-----------------|------------|---------|------------|------------|----------|--------|--------|---------------|-------|--------|--------|------------|-----------|
| ① select_topic | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| ④ hypotheses | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| ⑧ verify_methods | — | — | — | ✓ | — | — | — | — | — | — | — | — | — | — | — | — |
| ⑨ write_methods | — | — | — | — | — | — | — | ✓ | ✓ | — | — | — | — | — | — | — |
| ⑩ write_results | — | — | ✓ | — | ✓ | — | — | — | — | — | ✓ | ✓ | ✓ | — | — | — |
| ⑪ write_intro | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| ⑫ write_discussion | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — | — | — | — |
| ⑭ integrity_check | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ⑰ re_review | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ⑱ finalize | — | — | — | — | — | ✓ | ✓ | — | — | — | — | — | — | ✓ | ✓ | ✓ |

---

## 6. 门执行流程

### 6.1 IntegrityGateChecker 检查顺序

```python
class IntegrityGateChecker:
    def run_all_checks(self, manuscript_sections, bibtex_path, 
                       figure_plan=None, journal_target=None):
        report = IntegrityReport()
        
        # Phase 1: Content-independent checks (fast)
        for section_name, content in manuscript_sections.items():
            self._check_no_local_paths(content, report)      # G2.3
            self._check_no_bullets(content, report)           # G3.2
            self._check_section_length(content, report)       # G3.1
        
        # Phase 2: Citation checks (medium)
        if bibtex_path:
            self._check_bibtex_existence(manuscript_sections, 
                                         bibtex_path, report) # G1.1
            self._check_citation_traceability(
                manuscript_sections, bibtex_path, report)     # G1.2
        
        # Phase 3: Results-specific checks (slowest)
        if 'results' in manuscript_sections:
            self._check_results_no_citations(
                manuscript_sections['results'], report)       # G1.3
            self._check_claim_artifact_binding(
                manuscript_sections['results'], 
                self.artifact_ledger, report)                 # G1.4
            self._check_statistics_reported(
                manuscript_sections['results'], report)       # G2.7
        
        # Phase 4: Structure checks
        self._check_figures_referenced(...)                   # G1.5
        self._check_data_availability(...)                    # G2.1
        self._check_code_availability(...)                    # G2.2
        self._check_methods_parameters(...)                   # G2.4
        self._check_discussion_limitations(...)               # G2.5
        self._check_no_overinterpretation(...)                # G2.6
        self._check_pseudoreplication(...)                    # G2.8
        self._check_figure_count(...)                         # G3.3
        
        # Final: determine blocking status
        report.blocks_pipeline = report.critical_failures > 0
        return report
```

### 6.2 门结果数据结构

```python
@dataclass
class IntegrityReport:
    report_id: str
    passed: bool                     # all CRITICAL passed?
    critical_failures: int
    high_failures: int
    medium_failures: int
    blocks_pipeline: bool            # True if critical_failures > 0
    results: list[GateResult]        # detailed per-rule results
    
@dataclass  
class GateResult:
    rule: str                        # e.g. "bibtex_citation_existence"
    severity: str                    # CRITICAL | HIGH | MEDIUM
    passed: bool
    message: str                     # Human-readable explanation
    violations: list[dict]           # Specific violations with location + fix
```

---

## 7. 默认门规则（按阶段自动推导）

当 stage 未显式定义 gate_rules 时，系统按 phase 自动应用默认规则:

```python
def _get_default_gate_rules(stage_name, phase):
    if phase <= 2:    # Research & Data
        return [{"rule": "all_outputs_exist", "severity": "critical"}]
    elif phase == 3:   # Writing
        return [
            {"rule": "no_local_paths", "severity": "high"},
            {"rule": "section_length_minimum", "severity": "medium"},
            {"rule": "no_bullets_in_prose", "severity": "medium"},
        ]
    elif phase == 4:   # Assembly & Review
        return [
            {"rule": "bibtex_citation_existence", "severity": "critical"},
            {"rule": "results_no_citations", "severity": "critical"},
            {"rule": "figures_referenced", "severity": "critical"},
        ]
    else:              # Phase 5-6: Revision & Finalize
        return [
            {"rule": "data_availability_statement", "severity": "high"},
            {"rule": "code_availability_statement", "severity": "high"},
            {"rule": "figure_count_requirements", "severity": "medium"},
        ]
```

---

## 8. 门与管线的交互

```
Stage 执行完成
  │
  ▼
PaperWorkflow._execute_stage(stage)
  ├── engine.run_stage(stage)           # 执行阶段
  ├── engine.verify_stage(stage)        # 运行 gate checks
  │     └── IntegrityGateChecker.run_all_checks()
  │           │
  │           ├── all CRITICAL pass? → StageStatus.COMPLETED
  │           ├── any CRITICAL fail? → StageStatus.FAILED
  │           │   └── PipelineState.GATE_FAILURE
  │           └── MEDIUM fails? → 仅警告, 不阻塞
  │
  ├── passport.record_artifact(...)     # 记录制品
  └── engine.record_and_sync()          # 同步状态 + 检测过期
```

---

## 9. 自动修复能力

| 规则 | 可自动修复 | 修复方式 |
|------|-----------|---------|
| data_availability_statement | ✅ | 从 data_inventory.yaml 生成模板 |
| code_availability_statement | ✅ | 从 git remote + 配置生成 |
| no_local_paths | ✅ | regex 替换本地路径为通用描述 |
| no_bullets_in_prose | ✅ | 将列表转换为段落 |
| bibtex_citation_existence | ❌ | 需人工查找缺失引用 |
| citation_evidence_traceability | ❌ | 需人工验证声称-证据对应 |
| claim_artifact_binding | ❌ | 需人工追溯数值来源 |
| methods_parameters_complete | ❌ | 需人机协作提取参数 |
| discussion_limitations | ❌ | 需基于具体研究撰写 |
| results_no_overinterpretation | ❌ | 需人工判断语义边界 |
