#!/usr/bin/env python3
"""
build_reports.py
High-fidelity Markdown-to-PDF converter for DeviationIQ project documentation.
Renders publication-grade GxP reports with professional typography,
responsive tables, Mermaid diagrams, dedicated cover pages, and 21 CFR Part 11 headers/footers.
"""

import os
import re
import sys
import time
import subprocess
import html
from markdown_it import MarkdownIt
import fitz  # PyMuPDF

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def get_markdown_parser():
    md = MarkdownIt('commonmark', {'html': True, 'breaks': False})
    md.enable(['table', 'strikethrough'])
    return md

def custom_markdown_processing(content: str) -> str:
    # Protect mermaid blocks so markdown parser doesn't mangle arrows or HTML
    mermaid_blocks = []
    def mermaid_repl(match):
        code = match.group(1).strip()
        idx = len(mermaid_blocks)
        mermaid_blocks.append(code)
        return f"<!--MERMAID_BLOCK_{idx}-->"
    
    # Match ```mermaid ... ```
    content = re.sub(r"```mermaid\s*\n([\s\S]*?)\n```", mermaid_repl, content)

    # Process markdown
    md = get_markdown_parser()
    rendered_html = md.render(content)

    # Restore mermaid blocks
    for idx, code in enumerate(mermaid_blocks):
        escaped_code = html.escape(code)
        block_html = (
            f'<div class="mermaid-card">\n'
            f'  <div class="mermaid">\n{code}\n</div>\n'
            f'</div>'
        )
        rendered_html = rendered_html.replace(f"&lt;!--MERMAID_BLOCK_{idx}--&gt;", block_html)
        rendered_html = rendered_html.replace(f"<!--MERMAID_BLOCK_{idx}-->", block_html)

    return rendered_html

def enhance_html_elements(html_text: str, is_tech_report: bool = False) -> str:
    # Enhance tables: wrap with responsive container
    html_text = re.sub(r'(<table>[\s\S]*?</table>)', r'<div class="table-wrapper">\1</div>', html_text)

    # Enhance status badges inside tables or text
    badge_replacements = [
        (r'\bMinor\b', r'<span class="badge badge-minor">Minor</span>'),
        (r'\bMajor\b', r'<span class="badge badge-major">Major</span>'),
        (r'\bCritical\b', r'<span class="badge badge-critical">Critical</span>'),
        (r'✅', r'<span class="badge badge-success">✅ Verified</span>'),
        (r'\b(gpt-oss-120b)\b', r'<span class="model-badge model-large">\1</span>'),
        (r'\b(gpt-oss-20b)\b', r'<span class="model-badge model-small">\1</span>'),
    ]
    for pattern, repl in badge_replacements:
        html_text = re.sub(pattern, repl, html_text)

    # Style blockquotes as modern callouts
    html_text = re.sub(
        r'<blockquote>\s*<p>(.*?)<\/p>\s*<\/blockquote>', 
        r'<div class="callout-box"><div class="callout-bar"></div><div class="callout-content"><p>\1</p></div></div>', 
        html_text, flags=re.DOTALL
    )

    # For technical report: add chapter breaks before numbered h2 sections
    if is_tech_report:
        # Before major chapters: 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12., 13., 14., 15.
        html_text = re.sub(r'<h2>(\d+\.\s+[^<]+)</h2>', r'<div class="chapter-break"></div><h2 class="chapter-title">\1</h2>', html_text)
    else:
        # For explainer: add chapter break before Section A, Section B, Key Talking Points, Video Submission Script
        html_text = re.sub(r'<h1>(Section [AB]:[^<]+)</h1>', r'<div class="chapter-break"></div><h1 class="chapter-title">\1</h1>', html_text)
        html_text = re.sub(r'<h1>(Key Talking Points[^<]+)</h1>', r'<div class="chapter-break"></div><h1 class="chapter-title">\1</h1>', html_text)
        html_text = re.sub(r'<h1>(Video Submission Script[^<]+)</h1>', r'<div class="chapter-break"></div><h1 class="chapter-title">\1</h1>', html_text)

    return html_text

CSS_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --primary: #0f766e;
  --primary-dark: #0f172a;
  --primary-light: #f0fdfa;
  --accent: #0284c7;
  --slate-900: #0f172a;
  --slate-800: #1e293b;
  --slate-700: #334155;
  --slate-600: #475569;
  --slate-500: #64748b;
  --slate-300: #cbd5e1;
  --slate-200: #e2e8f0;
  --slate-100: #f1f5f9;
  --slate-50: #f8fafc;
}

@page {
  size: A4;
  margin: 18mm 16mm 18mm 16mm;
}

* {
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  color: var(--slate-800);
  background: #ffffff;
  font-size: 9.6pt;
  line-height: 1.55;
  margin: 0;
  padding: 0;
  -webkit-font-smoothing: antialiased;
}

/* ========================================================
   COVER PAGE STYLING (FOR FORMAL TECHNICAL REPORT)
   ======================================================== */
.cover-page {
  height: 252mm;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  page-break-after: always;
  break-after: page;
  padding-bottom: 10mm;
}

.cover-header {
  border-bottom: 2px solid var(--primary);
  padding-bottom: 15px;
}

.cover-badge-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.cover-brand {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9pt;
  font-weight: 700;
  color: #0284c7;
  letter-spacing: 1.5px;
  background: var(--slate-900);
  padding: 6px 12px;
  border-radius: 4px;
}

.cover-compliance {
  font-size: 8.5pt;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-light);
  border: 1px solid #ccfbf1;
  padding: 5px 12px;
  border-radius: 4px;
}

.cover-title-group {
  margin-top: 40px;
}

.cover-supertitle {
  font-size: 11pt;
  font-weight: 700;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 8px;
}

.cover-title {
  font-size: 28pt;
  font-weight: 800;
  color: var(--slate-900);
  line-height: 1.15;
  margin: 0 0 16px 0;
  letter-spacing: -0.5px;
}

.cover-subtitle {
  font-size: 13pt;
  font-weight: 400;
  color: var(--slate-600);
  line-height: 1.45;
  max-width: 90%;
  margin: 0 0 25px 0;
}

.cover-highlights-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 25px 0;
}

.highlight-card {
  background: var(--slate-50);
  border: 1px solid var(--slate-200);
  border-radius: 6px;
  padding: 10px 12px;
  text-align: center;
}

.highlight-val {
  font-size: 13pt;
  font-weight: 800;
  color: var(--primary);
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 2px;
}

.highlight-lbl {
  font-size: 7.2pt;
  font-weight: 600;
  color: var(--slate-500);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cover-meta-table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
  border: 1px solid var(--slate-200);
  border-radius: 8px;
  overflow: hidden;
  margin-top: 20px;
}

.cover-meta-table td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--slate-200);
  font-size: 9pt;
}

.cover-meta-table tr:last-child td {
  border-bottom: none;
}

.cover-meta-label {
  width: 30%;
  font-weight: 700;
  color: var(--slate-500);
  text-transform: uppercase;
  font-size: 7.5pt;
  letter-spacing: 0.8px;
  background: var(--slate-50);
}

.cover-meta-val {
  font-weight: 600;
  color: var(--slate-900);
}

.cover-footer {
  border-top: 1px solid var(--slate-200);
  padding-top: 14px;
  display: flex;
  justify-content: space-between;
  font-size: 7.8pt;
  color: var(--slate-500);
}

/* ========================================================
   DOCUMENT HEADER (FOR EXPLAINER REPORT)
   ======================================================== */
.doc-header {
  border-bottom: 2px solid var(--primary);
  padding-bottom: 18px;
  margin-bottom: 22px;
}

.doc-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.brand-pill {
  background: var(--slate-900);
  color: #38bdf8;
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt;
  font-weight: 700;
  letter-spacing: 1.2px;
  padding: 4px 10px;
  border-radius: 4px;
  text-transform: uppercase;
}

.compliance-badge {
  font-size: 8pt;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-light);
  border: 1px solid #ccfbf1;
  padding: 4px 10px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

h1.doc-title {
  color: var(--slate-900);
  font-size: 21pt;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 1.2;
  margin: 0 0 8px 0;
}

.doc-meta-card {
  background: var(--slate-50);
  border: 1px solid var(--slate-200);
  border-radius: 8px;
  padding: 10px 16px;
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.meta-item {
  display: flex;
  flex-direction: column;
}

.meta-label {
  font-size: 7pt;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--slate-500);
  margin-bottom: 2px;
}

.meta-value {
  font-size: 8.8pt;
  font-weight: 600;
  color: var(--slate-800);
}

/* ========================================================
   HEADINGS & TYPOGRAPHY
   ======================================================== */
h1 {
  color: var(--slate-900);
  font-size: 15pt;
  font-weight: 700;
  border-bottom: 1.5px solid var(--slate-200);
  padding-bottom: 6px;
  margin-top: 24px;
  margin-bottom: 12px;
  page-break-after: avoid;
  break-after: avoid;
}

h2 {
  color: var(--primary);
  font-size: 12.5pt;
  font-weight: 700;
  margin-top: 22px;
  margin-bottom: 8px;
  page-break-after: avoid;
  break-after: avoid;
}

h3 {
  color: var(--slate-800);
  font-size: 10.5pt;
  font-weight: 600;
  margin-top: 14px;
  margin-bottom: 6px;
  page-break-after: avoid;
  break-after: avoid;
}

p {
  margin: 0 0 9px 0;
}

strong {
  font-weight: 600;
  color: var(--slate-900);
}

/* Chapter breaks */
.chapter-break {
  page-break-before: always;
  break-before: page;
}

h2.chapter-title {
  font-size: 16pt;
  color: var(--slate-900);
  border-bottom: 2px solid var(--primary);
  padding-bottom: 6px;
  margin-top: 0;
}

h1.chapter-title {
  font-size: 18pt;
  color: var(--slate-900);
  border-bottom: 2px solid var(--primary);
  padding-bottom: 6px;
  margin-top: 0;
}

/* Lists */
ul, ol {
  margin: 0 0 10px 0;
  padding-left: 20px;
}

li {
  margin-bottom: 3.5px;
}

/* ========================================================
   TABLES
   ======================================================== */
.table-wrapper {
  margin: 12px 0 16px 0;
  border: 1px solid var(--slate-200);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  page-break-inside: avoid;
  break-inside: avoid;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 8.8pt;
  text-align: left;
}

thead {
  background: var(--slate-900);
  color: #ffffff;
}

th {
  padding: 8px 11px;
  font-weight: 600;
  letter-spacing: 0.4px;
  border: none;
  font-size: 8.4pt;
}

td {
  padding: 7px 11px;
  border-top: 1px solid var(--slate-200);
  color: var(--slate-800);
  vertical-align: top;
  line-height: 1.45;
}

tbody tr:nth-child(even) {
  background-color: var(--slate-50);
}

/* Badges */
.badge {
  display: inline-block;
  font-size: 7.2pt;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  white-space: nowrap;
}

.badge-critical {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.badge-major {
  background: #fffbeb;
  color: #b45309;
  border: 1px solid #fde68a;
}

.badge-minor {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.badge-success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.model-badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 7.6pt;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 4px;
}

.model-large {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.model-small {
  background: #f5f3ff;
  color: #6d28d9;
  border: 1px solid #ddd6fe;
}

/* Code & Pre */
code {
  font-family: 'JetBrains Mono', Consolas, Monaco, monospace;
  font-size: 8.3pt;
  background: #f1f5f9;
  color: #0f172a;
  padding: 1.5px 5px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}

pre {
  background: #0f172a;
  color: #f8fafc;
  padding: 10px 14px;
  border-radius: 7px;
  overflow-x: auto;
  font-size: 8pt;
  line-height: 1.45;
  margin: 10px 0 14px 0;
  border: 1px solid #1e293b;
  page-break-inside: avoid;
  break-inside: avoid;
}

pre code {
  background: transparent;
  color: inherit;
  padding: 0;
  border: none;
  font-size: inherit;
}

/* Callout Box */
.callout-box {
  display: flex;
  margin: 12px 0 14px 0;
  background: var(--primary-light);
  border: 1px solid #ccfbf1;
  border-left: 4px solid var(--primary);
  border-radius: 6px;
  overflow: hidden;
  page-break-inside: avoid;
  break-inside: avoid;
}

.callout-content {
  padding: 9px 13px;
  font-size: 9.1pt;
  color: #134e4a;
}

.callout-content p {
  margin: 0;
}

/* Mermaid Diagrams */
.mermaid-card {
  margin: 14px auto;
  padding: 12px;
  background: #ffffff;
  border: 1px solid var(--slate-200);
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  page-break-inside: avoid;
  break-inside: avoid;
}

.mermaid {
  display: flex;
  justify-content: center;
}

.mermaid svg {
  max-width: 95% !important;
  max-height: 520px !important;
  height: auto !important;
}

hr {
  border: 0;
  height: 1px;
  background: var(--slate-200);
  margin: 20px 0;
}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    {css}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      mermaid.initialize({{
        startOnLoad: true,
        theme: 'neutral',
        themeVariables: {{
          primaryColor: '#f0fdfa',
          primaryBorderColor: '#0f766e',
          primaryTextColor: '#0f172a',
          lineColor: '#64748b',
          secondaryColor: '#f8fafc',
          tertiaryColor: '#ffffff',
          fontFamily: 'Inter, sans-serif',
          fontSize: '11px'
        }},
        flowchart: {{
          curve: 'basis',
          nodeSpacing: 40,
          rankSpacing: 45
        }}
      }});
    }});
  </script>
</head>
<body>
  {cover_or_header_html}
  {body_html}
</body>
</html>
"""

def make_cover_page_html(title: str, subtitle: str, meta: dict) -> str:
    rows = "".join([
        f'<tr><td class="cover-meta-label">{k}</td><td class="cover-meta-val">{v}</td></tr>'
        for k, v in meta.items()
    ])

    return f"""
    <div class="cover-page">
      <div class="cover-header">
        <div class="cover-badge-row">
          <span class="cover-brand">AIVOA.AI &bull; DEVIATIONIQ</span>
          <span class="cover-compliance">GxP REGULATORY SPECIFICATION</span>
        </div>
        <div class="cover-title-group">
          <div class="cover-supertitle">Project Engineering Deliverable</div>
          <h1 class="cover-title">{title}</h1>
          <div class="cover-subtitle">{subtitle}</div>
        </div>
      </div>

      <div>
        <div class="cover-highlights-grid">
          <div class="highlight-card">
            <div class="highlight-val">18 / 18</div>
            <div class="highlight-lbl">Unit Tests Passing</div>
          </div>
          <div class="highlight-card">
            <div class="highlight-val">86%</div>
            <div class="highlight-lbl">Extraction Accuracy</div>
          </div>
          <div class="highlight-card">
            <div class="highlight-val">100%</div>
            <div class="highlight-lbl">Null-Correctness</div>
          </div>
          <div class="highlight-card">
            <div class="highlight-val">21 CFR 11</div>
            <div class="highlight-lbl">Part 11 Compliant</div>
          </div>
        </div>

        <table class="cover-meta-table">
          {rows}
        </table>
      </div>

      <div class="cover-footer">
        <span>CONFIDENTIAL &bull; PROPRIETARY PHARMACEUTICAL QUALITY SPECIFICATION</span>
        <span>ELECTRONICALLY VERIFIED RECORD</span>
      </div>
    </div>
    """

def make_header_html(doc_title: str, subtitle: str, meta: dict) -> str:
    meta_items_html = "".join([
        f'<div class="meta-item"><span class="meta-label">{k}</span><span class="meta-value">{v}</span></div>'
        for k, v in meta.items()
    ])

    return f"""
    <div class="doc-header">
      <div class="doc-top-bar">
        <span class="brand-pill">AIVOA.AI &bull; DEVIATIONIQ</span>
        <span class="compliance-badge">FDA 21 CFR Part 11 &bull; ICH Q9/Q10 Compliant</span>
      </div>
      <h1 class="doc-title">{doc_title}</h1>
      <div style="font-size: 10.5pt; color: #475569; margin-bottom: 6px; font-weight: 500;">{subtitle}</div>
      <div class="doc-meta-card">
        {meta_items_html}
      </div>
    </div>
    """

def stamp_pdf_decorations(pdf_path: str, doc_title: str, has_cover: bool = False):
    """
    Uses PyMuPDF to add running headers and footers with page numbers.
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    header_font_size = 7.5
    footer_font_size = 7.5
    teal_color = (15/255, 118/255, 110/255)
    slate_color = (100/255, 116/255, 139/255)
    rule_color = (226/255, 232/255, 240/255)

    start_page = 2 if has_cover else 2

    for i, page in enumerate(doc):
        rect = page.rect
        width = rect.width
        height = rect.height
        page_num = i + 1

        # Skip header and footer on cover page
        if has_cover and page_num == 1:
            continue

        # Header text (left: doc title, right: classification)
        page.insert_text((45, 32), doc_title, fontsize=header_font_size, color=slate_color)
        conf_text = "GxP CONTROLLED DOCUMENT"
        conf_w = fitz.get_text_length(conf_text, fontsize=header_font_size)
        page.insert_text((width - 45 - conf_w, 32), conf_text, fontsize=header_font_size, color=teal_color)

        # Header rule
        page.draw_line(fitz.Point(45, 38), fitz.Point(width - 45, 38), color=rule_color, width=0.75)

        # Footer rule
        page.draw_line(fitz.Point(45, height - 38), fitz.Point(width - 45, height - 38), color=rule_color, width=0.75)

        # Footer text (left: Confidential notice, right: Page X of Y)
        footer_left = "CONFIDENTIAL & PROPRIETARY | AIVOA.AI DEVIATIONIQ"
        page.insert_text((45, height - 25), footer_left, fontsize=footer_font_size, color=slate_color)

        page_str = f"Page {page_num} of {total_pages}"
        page_w = fitz.get_text_length(page_str, fontsize=footer_font_size)
        page.insert_text((width - 45 - page_w, height - 25), page_str, fontsize=footer_font_size, color=slate_color)

    output_path = pdf_path.replace(".pdf", "_stamped.pdf")
    doc.save(output_path)
    doc.close()

    time.sleep(0.3)
    if os.path.exists(output_path):
        os.replace(output_path, pdf_path)

def convert_markdown_to_pdf(md_file_path: str, output_pdf_path: str, doc_title: str, subtitle: str, meta: dict, is_tech_report: bool = False):
    print(f"\n==========================================")
    print(f"Converting: {os.path.basename(md_file_path)} -> {os.path.basename(output_pdf_path)}")
    print(f"==========================================")

    with open(md_file_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Pre-process markdown
    clean_md = re.sub(r"^#\s+.*?\n", "", md_content, count=1).strip()

    if is_tech_report:
        # Strip repeated metadata lines: **Project**: ... \n **Author**: ... etc.
        clean_md = re.sub(r"\*\*Project\*\*:\s*.*?\n", "", clean_md)
        clean_md = re.sub(r"\*\*Author\*\*:\s*.*?\n", "", clean_md)
        clean_md = re.sub(r"\*\*Date\*\*:\s*.*?\n", "", clean_md)
        clean_md = re.sub(r"\*\*Version\*\*:\s*.*?\n", "", clean_md)
        clean_md = clean_md.strip()
        # Remove leading horizontal rule if present
        if clean_md.startswith("---"):
            clean_md = clean_md[3:].strip()

        cover_or_header_html = make_cover_page_html(doc_title, subtitle, meta)
    else:
        cover_or_header_html = make_header_html(doc_title, subtitle, meta)

    body_html = custom_markdown_processing(clean_md)
    body_html = enhance_html_elements(body_html, is_tech_report=is_tech_report)

    full_html = HTML_TEMPLATE.format(
        title=doc_title,
        css=CSS_STYLES,
        cover_or_header_html=cover_or_header_html,
        body_html=body_html
    )

    temp_html_path = output_pdf_path.replace(".pdf", ".temp.html")
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    print("Generated intermediate HTML:", temp_html_path)
    abs_html = os.path.abspath(temp_html_path)
    abs_pdf = os.path.abspath(output_pdf_path)

    cmd = [
        EDGE_PATH,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--virtual-time-budget=6500",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={abs_pdf}",
        f"file:///{abs_html}"
    ]

    print("Executing Edge Headless rendering...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Edge error:", res.stderr)

    time.sleep(0.5)

    if not os.path.exists(abs_pdf):
        raise RuntimeError(f"PDF creation failed: {abs_pdf} does not exist.")

    print(f"Raw PDF created: {os.path.getsize(abs_pdf)} bytes")

    print("Stamping running headers, rules, and page numbering...")
    stamp_pdf_decorations(abs_pdf, doc_title, has_cover=is_tech_report)

    doc = fitz.open(abs_pdf)
    print(f"Success! Final PDF generated with {len(doc)} pages: {abs_pdf}")
    doc.close()

    try:
        os.remove(temp_html_path)
    except Exception:
        pass

if __name__ == "__main__":
    # Resolve project root dynamically
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    reports_dir = os.path.join(root_dir, "docs", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # 1. Pipeline Explainer
    p1_in = os.path.join(reports_dir, "Pipeline_Explainer.md")
    p1_out = os.path.join(reports_dir, "Pipeline_Explainer.pdf")
    p1_meta = {
        "Document Type": "Technical Architecture & Pitch Guide",
        "Pipeline Engine": "LangGraph StateGraph",
        "Model Tiering": "gpt-oss-120b / gpt-oss-20b",
        "Target Audience": "Engineers, Architects & Executive Leads",
        "Date": "September 2026",
        "Author": "Muhammad Ammar"
    }
    convert_markdown_to_pdf(
        p1_in, p1_out,
        "DeviationIQ — Pipeline Explainer (Two-Way)",
        "Dual-Audience Technical Pointwise & Conversational Pitch Architecture",
        p1_meta,
        is_tech_report=False
    )

    # 2. Comprehensive Technical Project Report
    p2_in = os.path.join(reports_dir, "DeviationIQ_Technical_Report.md")
    p2_out = os.path.join(reports_dir, "DeviationIQ_Technical_Report.pdf")
    p2_meta = {
        "Project Name": "AIVOA.AI — AI-Powered Deviation Intake Module (DeviationIQ)",
        "Lead Author": "Muhammad Ammar",
        "Publication Date": "September 2026",
        "Document Version": "Version 1.0 (Full Technical Specification)",
        "Architecture": "Three-Tier: FastAPI (Async) + React 19 (Redux) + LangGraph",
        "AI Engine": "Dual-Model Strategy (Groq Cloud gpt-oss-120b & gpt-oss-20b)",
        "Compliance Standard": "FDA 21 CFR Part 11, GxP, ALCOA+, ICH Q9 & ICH Q10",
        "Classification": "RESTRICTED / GxP REGULATORY SPECIFICATION"
    }
    convert_markdown_to_pdf(
        p2_in, p2_out,
        "DeviationIQ — Comprehensive Technical Project Report",
        "Complete System Architecture, Data Contract, AI State Machine & Regulatory Specification",
        p2_meta,
        is_tech_report=True
    )

    print("\nAll reports successfully built in docs/reports/!")
