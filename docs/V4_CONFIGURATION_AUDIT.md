# V4 配置与链路审计记录

审计日期：2026-06-21  
仓库：`anthonyvmppg3yigdt33kp-lang/ResearchPaperWorkflow`  
版本目标：`v4.0.0`

## 已发现并修复的问题

1. fast-context MCP 未暴露

   - 现象：用户工作区说明要求优先使用 `mcp__fast-context__fast_context_search`，但当前会话工具列表中没有该 MCP；`tool_search` 也未发现可调用 fast-context 工具。
   - 处理：记录为配置环境问题，本次代码审计使用 `rg`、文件读取和测试作为替代。

2. 配置漂移

   - 现象：测试 18 stages、16 gates、`create_project`、`search_literature`、`research_plan`。
   - 当前真实链路：20 stages、44 gates、`select_topic`、`literature_search`、`formulate_hypotheses`、`design_analysis_plan`、`aigc_humanizer_review`。
   - 修复：同步 `test_p0_verification.py`、`tests/test_integration.py`、`tests/test_all.py`。

3. 配置与代码版本漂移

   - 现象：`pyproject.toml`、`__version__`、README 和配置描述仍处于 v3 或更早语义。
   - 修复：核心版本升至 `4.0.0`，README 重写为 V4 入口，`default_config.yaml` 更新为 20-stage / 44-gate / 13-agent 配置。

4. 新增 AIGC/Humanizer stage 的验证路径不完整

   - 现象：`verify_stage` 只读取分章节 `abstract.md`、`methods.md` 等，无法验证 `manuscript_humanized.md` 这类完整稿件。
   - 修复：当分章节稿件不存在时，自动识别 `manuscript_humanized.md`、`manuscript_full.md`、`manuscript.md`。

5. CLI 模块运行警告

   - 现象：`python -m paper_workflow.cli.main` 触发 `runpy` warning，因为 `cli/__init__.py` 提前导入 `main.py`。
   - 修复：改为懒加载 `main()`。

6. 安装后 skill 缺失

   - 现象：仓库内 `.claude/skills` 与本机 skill roots 没有自动比对机制。
   - 修复：新增 `config/required_skills.yaml` 和 `paper_workflow.utils.skill_installer`，安装/CLI 启动时可自动补齐 bundled skills。

## V4 新增能力

- 新增 pipeline stage：`aigc_humanizer_review`
- 新增 agent：`aigc_humanizer_reviewer`
- 新增或纳入 bundled skills：
  - `ai-writing-detection`
  - `humanizer`
  - `aigc_humanizer_review`
- 新增 integrity gates：
  - `aigc_artifact_scan`
  - `aigc_style_signal_density`
  - `humanizer_revision_trace`
- 新增 CLI：
  - `install-skills`
  - `run-aigc-humanizer`

## 验证结果

```bash
python -m pytest -q
```

结果：`42 passed, 4 warnings`

说明：4 个 warning 来自旧 P0 脚本中测试函数返回 `True`，不影响功能。

```bash
python -m paper_workflow.cli.main run-aigc-humanizer --paper v4_smoke
```

结果：成功生成：

- `review/aigc_detection_report.md`
- `review/humanizer_revision_plan.yaml`
- `manuscript/manuscript_humanized.md`


