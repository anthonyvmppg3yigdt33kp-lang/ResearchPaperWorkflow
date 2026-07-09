"""
导出 ResearchPaperWorkflow v2 所有文档 → 合并 PDF
markdown-it-py → HTML → Edge headless → PDF
"""
import re
import subprocess
from pathlib import Path
from markdown_it import MarkdownIt

PROJECT = Path(r"%USERPROFILE%\Desktop\ResearchPaperWorkflow_v2")
OUTPUT = Path(r"%USERPROFILE%\Desktop\ResearchPaperWorkflow_v2_Complete_Documentation.pdf")
HTML_PATH = PROJECT / "MERGED_FULL.html"
EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"

DOC_ORDER = [
    ("README.md",           "README — 工作流概述与快速开始"),
    ("ARCHITECTURE.md",     "ARCHITECTURE — 4层系统架构"),
    ("AGENT_ROLES.md",      "AGENT_ROLES — 12类Agent协作体系"),
    ("PIPELINE_DESIGN.md",  "PIPELINE_DESIGN — 18阶段调度管线"),
    ("QUALITY_GATES.md",    "QUALITY_GATES — 16规则质量门体系"),
    ("WORKFLOW_PATTERNS.md","WORKFLOW_PATTERNS — 5种工作流模式"),
    ("INTEGRATION_MAP.md",  "INTEGRATION_MAP — 技能集成与工具矩阵"),
    ("QUICK_REFERENCE.md",  "QUICK_REFERENCE — 一页速查卡"),
]

CSS = """
* { box-sizing: border-box; }
body {
    font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.65;
    color: #1a1a1a;
    max-width: 100%;
    margin: 0;
    padding: 0;
}

/* ===== COVER PAGE ===== */
.cover-page {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    text-align: center;
    page-break-after: always;
}
.cover-content h1 {
    font-size: 32pt;
    color: #1a3a5c;
    border-bottom: 4px solid #1a3a5c;
    padding-bottom: 16px;
    margin-bottom: 20px;
}
.cover-content h2 {
    font-size: 16pt;
    color: #2d5a87;
    font-weight: 400;
    margin-bottom: 30px;
}
.cover-content .cover-subtitle {
    font-size: 12pt;
    color: #555;
    font-style: italic;
    margin-bottom: 40px;
}
.cover-content .cover-date {
    font-size: 11pt;
    color: #777;
    margin-bottom: 8px;
}
.cover-content .cover-desc {
    font-size: 10pt;
    color: #888;
    max-width: 550px;
    margin: 20px auto 0;
    line-height: 1.6;
}

/* ===== TOC ===== */
.toc { page-break-after: always; padding: 20px 0; }
.toc h1 {
    font-size: 22pt;
    color: #1a3a5c;
    border-bottom: 2.5px solid #1a3a5c;
    padding-bottom: 8px;
}
.toc ul { list-style: none; padding-left: 0; }
.toc li {
    padding: 8px 0;
    border-bottom: 1px dotted #ccc;
    font-size: 12pt;
}
.toc li a {
    color: #2d5a87;
    text-decoration: none;
    font-weight: 500;
}

/* ===== HEADINGS ===== */
h1 {
    font-size: 20pt;
    color: #1a3a5c;
    border-bottom: 2.5px solid #1a3a5c;
    padding-bottom: 8px;
    margin: 32px 0 16px 0;
    page-break-before: always;
}
h1.no-break { page-break-before: avoid; }
h2 {
    font-size: 15pt;
    color: #2d5a87;
    border-bottom: 1px solid #c0d0e0;
    padding-bottom: 4px;
    margin: 24px 0 12px 0;
}
h3 {
    font-size: 12.5pt;
    color: #3d6a97;
    margin: 18px 0 10px 0;
}
h4 {
    font-size: 11.5pt;
    color: #4a7aA7;
    margin: 14px 0 8px 0;
}

/* ===== CODE ===== */
code {
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
    background: #f4f6f8;
    padding: 2px 5px;
    border-radius: 3px;
    color: #c7254e;
}
pre {
    background: #f7f9fb;
    border: 1px solid #dde3ea;
    border-left: 4px solid #2d5a87;
    padding: 12px 14px;
    font-size: 8pt;
    line-height: 1.4;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-word;
    border-radius: 4px;
    margin: 10px 0;
}
pre code {
    background: transparent;
    padding: 0;
    color: #333;
}

/* ===== TABLES ===== */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 14px 0;
    font-size: 9pt;
    page-break-inside: avoid;
}
th {
    background: #1a3a5c;
    color: white;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
}
td {
    padding: 6px 10px;
    border-bottom: 1px solid #dde3ea;
}
tr:nth-child(even) td { background: #f7f9fb; }

/* ===== OTHERS ===== */
blockquote {
    border-left: 4px solid #1a3a5c;
    margin: 12px 0;
    padding: 8px 16px;
    background: #f0f4f8;
    color: #444;
}
hr { border: none; border-top: 1.5px solid #d0d8e0; margin: 24px 0; }
ul, ol { margin: 6px 0; padding-left: 24px; }
li { margin: 3px 0; }
a { color: #2d5a87; text-decoration: none; }
strong { color: #1a3a5c; }
.page-break { page-break-after: always; }
.section-anchor { scroll-margin-top: 20px; }
"""

def merge_docs():
    """Merge all .md files with a cover page and TOC"""
    parts = []

    # ── Cover Page (raw HTML) ──
    parts.append("""<div class="cover-page">
<div class="cover-content">
<h1>ResearchPaperWorkflow v2</h1>
<h2>科研论文多智能体协作工作流<br>完整设计文档</h2>
<p class="cover-subtitle">4层架构 · 12类Agent · 18阶段管线 · 16质量门 · 5工作流模式</p>
<p class="cover-date">Version 2.0.0 &mdash; June 20, 2026</p>
<p class="cover-desc">本文档由 8 份设计文档合并生成，涵盖系统架构、Agent协作、管线调度、质量门、工作流模式、技能集成等完整内容。适用于科研论文写作工作流的设计评审、技术选型与团队培训。</p>
</div>
</div>
<div class="page-break"></div>
""")

    # ── Table of Contents (raw HTML) ──
    parts.append('<div class="toc">\n')
    parts.append('<h1>目 录</h1>\n<ul>\n')
    for fname, display_title in DOC_ORDER:
        anchor = fname.replace('.md', '').lower()
        parts.append(f'<li><a href="#{anchor}">{display_title}</a></li>\n')
    parts.append('</ul>\n</div>\n<div class="page-break"></div>\n')

    # ── Each document ──
    md = MarkdownIt("commonmark").enable(["table", "strikethrough"])

    for fname, display_title in DOC_ORDER:
        fpath = PROJECT / fname
        if not fpath.exists():
            continue

        raw = fpath.read_text(encoding="utf-8")

        # Strip original H1 and version line
        raw = re.sub(r'^#\s+.*$', '', raw, count=1, flags=re.MULTILINE)
        raw = re.sub(r'^\*\*Version\*\*:.*$', '', raw, count=1, flags=re.MULTILINE)
        raw = raw.strip()

        anchor = fname.replace('.md', '').lower()
        # Re-insert a styled H1 with anchor
        parts.append(f'<div id="{anchor}" class="section-anchor">\n')
        parts.append(f'<h1>{display_title}</h1>\n')

        # Render the rest as markdown
        html_body = md.render(raw)
        parts.append(html_body)
        parts.append('\n</div>\n')
        parts.append('<div class="page-break"></div>\n')

    full_html_body = '\n'.join(parts)

    # ── Full HTML document ──
    full = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ResearchPaperWorkflow v2 — 完整设计文档</title>
<style>
{CSS}
@media print {{
    body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    @page {{ size: A4; margin: 2cm 2.2cm 2cm 2.2cm; }}
}}
</style>
</head>
<body>
{full_html_body}
</body>
</html>"""

    HTML_PATH.write_text(full, encoding="utf-8")
    print(f"  [OK] Merged {len(DOC_ORDER)} files → {HTML_PATH}")
    file_uri = HTML_PATH.as_uri()
    return file_uri


def html_to_pdf_via_edge(html_uri):
    """Use Edge headless to print HTML to PDF"""
    cmd = [
        EDGE, "--headless", "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={OUTPUT}",
        "--print-to-pdf-no-header",
        html_uri
    ]
    print(f"  Running Edge headless...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"  Edge stderr: {result.stderr[:500]}")
        raise RuntimeError(f"Edge exited with code {result.returncode}")
    print(f"  [OK] PDF exported: {OUTPUT}")


if __name__ == "__main__":
    print("=" * 65)
    print("  ResearchPaperWorkflow v2 — Merged PDF Export")
    print("=" * 65)

    print("\n[1/3] Merging + converting Markdown → HTML ...")
    html_uri = merge_docs()

    print("\n[2/3] Rendering HTML → PDF via Edge headless ...")
    html_to_pdf_via_edge(html_uri)

    print("\n[3/3] Verifying output ...")
    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"  File: {OUTPUT}")
    print(f"  Size: {size_mb:.2f} MB")

    print(f"\n{'=' * 65}")
    print(f"  DONE! PDF ready on your desktop.")
    print(f"{'=' * 65}")
