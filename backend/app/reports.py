"""
DeviationIQ â€” Regulatory Report Generators (PDF & DOCX)

Produces publication-grade, GxP-compliant deviation investigation reports
and 21 CFR Part 11 audit records.

Features:
- Strict typographical hierarchy with zero text overlap (explicit leading/cell wrapping).
- Explicit column geometry matching standard letter page boundaries.
- Formal pharmaceutical QA headers, executive triage assessment, and audit trail diffs.
- Clean vector styling adhering to GxP documentation standards (no informal styling).
"""

from __future__ import annotations

import html
import io
import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

# ReportLab (PDF Generation)
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Register High-Fidelity TrueType Unicode Fonts if available
FONT_NORMAL = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

try:
    windir = os.environ.get("WINDIR", "C:\\Windows")
    arial_path = os.path.join(windir, "Fonts", "arial.ttf")
    arial_bold_path = os.path.join(windir, "Fonts", "arialbd.ttf")
    liberation_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    liberation_bold_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

    if os.path.exists(arial_path) and os.path.exists(arial_bold_path):
        pdfmetrics.registerFont(TTFont("Arial-GxP", arial_path))
        pdfmetrics.registerFont(TTFont("Arial-GxP-Bold", arial_bold_path))
        FONT_NORMAL = "Arial-GxP"
        FONT_BOLD = "Arial-GxP-Bold"
    elif os.path.exists(liberation_path) and os.path.exists(liberation_bold_path):
        pdfmetrics.registerFont(TTFont("Liberation-GxP", liberation_path))
        pdfmetrics.registerFont(TTFont("Liberation-GxP-Bold", liberation_bold_path))
        FONT_NORMAL = "Liberation-GxP"
        FONT_BOLD = "Liberation-GxP-Bold"
except Exception:
    pass


# python-docx (DOCX Generation)
import docx
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor


# ===========================================================================
# REPORTLAB NUMBERED CANVAS (PAGE X OF Y & FORMAL FOOTER)
# ===========================================================================

class GxPReportCanvas(canvas.Canvas):
    """Two-pass canvas that computes total page count and renders running headers/footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()

        # Running Top Rule & Header (on page 2 and later)
        if self._pageNumber > 1:
            self.setFont(FONT_BOLD, 7.5)
            self.setFillColor(colors.HexColor("#374151"))
            self.drawString(36, 756, "DEVIATION INVESTIGATION & REGULATORY AUDIT REPORT")
            self.setFont(FONT_NORMAL, 7.5)
            self.setFillColor(colors.HexColor("#6B7280"))
            self.drawRightString(576, 756, "21 CFR PART 11 SEALED")
            self.setStrokeColor(colors.HexColor("#E5E7EB"))
            self.setLineWidth(0.6)
            self.line(36, 750, 576, 750)

        # Running Bottom Rule & Footer (all pages)
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.6)
        self.line(36, 42, 576, 42)

        self.setFont(FONT_NORMAL, 7.5)
        self.setFillColor(colors.HexColor("#6B7280"))
        self.drawString(36, 30, "CONFIDENTIAL â€” Good Manufacturing Practice (GMP) Record â€” DeviationIQ QMS")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(576, 30, page_str)

        self.restoreState()


# ===========================================================================
# HELPER UTILITIES & UNICODE NORMALIZATION
# ===========================================================================

def _sanitize_gxp_text(text: Any) -> str:
    """Thoroughly sanitize text to eliminate unrenderable glyphs, non-breaking hyphens,

    and special Unicode characters that cause black box / tofu (â– ) artifacts in PDFs and documents.
    """
    if text is None:
        return ""
    s = str(text)

    # 1. Normalize unicode compatibility forms (NFKC)
    s = unicodedata.normalize("NFKC", s)

    # 2. Replace all variants of non-breaking hyphens, em/en-dashes, minus signs with standard hyphens
    s = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212\u00ad]", "-", s)

    # 3. Replace typographic / smart quotes with standard ASCII quotes
    s = re.sub(r"[\u2018\u2019\u201a\u201b]", "'", s)
    s = re.sub(r"[\u201c\u201d\u201e\u201f]", '"', s)

    # 4. Replace mathematical and comparison symbols
    s = s.replace("\u2248", "~")      # approximately equal (â‰ˆ -> ~)
    s = s.replace("\u2264", "<=")     # less than or equal (â‰¤ -> <=)
    s = s.replace("\u2265", ">=")     # greater than or equal (â‰¥ -> >=)
    s = s.replace("\u00b1", "+/-")    # plus-minus (Â± -> +/-)
    s = s.replace("\u00b7", " - ")    # middle dot (Â· -> -)
    s = s.replace("\u2026", "...")    # ellipsis (â€¦ -> ...)

    # 5. Replace arrows and bullets
    s = re.sub(r"[\u2192\u2794\u21d2]", "->", s)
    s = re.sub(r"[\u2190\u21d0]", "<-", s)
    s = re.sub(r"[\u2022\u2023\u25cf\u25aa\u25ab]", "* ", s)

    # 6. Normalize whitespace, remove zero-width and invisible control characters
    s = re.sub(r"[\u200b\u200c\u200d\ufeff\x7f-\x9f]", "", s)
    s = re.sub(r"[\u00a0\u202f\u2007\u2008\u2009\u200a]", " ", s)

    return s


def _escape_pdf(text: Any) -> str:
    """Safely escape text for ReportLab Paragraphs, sanitize glyphs, and preserve linebreaks."""
    if text is None:
        return "â€”"
    cleaned = _sanitize_gxp_text(text).strip()
    if not cleaned:
        return "â€”"
    escaped = html.escape(cleaned)
    return escaped.replace("\r\n", "<br/>").replace("\n", "<br/>")


def _format_dt(val: Any) -> str:
    """Format timestamps cleanly."""
    if not val:
        return "N/A"
    if isinstance(val, str):
        try:
            val = datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            return val
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M UTC")
    return str(val)


# ===========================================================================
# PDF GENERATOR (REPORTLAB)
# ===========================================================================

def generate_deviation_pdf(
    deviation: Any,
    messages: list[Any],
    events: list[Any],
    session_summary: str | None = None,
) -> io.BytesIO:
    """Generate a publication-grade, GxP-compliant PDF report."""
    buffer = io.BytesIO()

    # Page Geometry: Letter is 612 x 792 pt.
    # Margins: 36 pt (0.5 in) left/right. Usable width = 540 pt.
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=54,
    )

    # Palette
    color_teal = colors.HexColor("#0F766E")
    color_dark = colors.HexColor("#111827")
    color_slate = colors.HexColor("#374151")
    color_muted = colors.HexColor("#6B7280")
    color_border = colors.HexColor("#D1D5DB")
    color_light_bg = colors.HexColor("#F9FAFB")
    color_header_bg = colors.HexColor("#F3F4F6")

    sev = getattr(deviation, "initial_severity", "") or "Unspecified"
    if sev.lower() == "critical":
        color_sev = colors.HexColor("#991B1B")
        bg_sev = colors.HexColor("#FEF2F2")
    elif sev.lower() == "major":
        color_sev = colors.HexColor("#92400E")
        bg_sev = colors.HexColor("#FEF3C7")
    elif sev.lower() == "minor":
        color_sev = colors.HexColor("#1E40AF")
        bg_sev = colors.HexColor("#EFF6FF")
    else:
        color_sev = color_slate
        bg_sev = color_light_bg

    # Typography Styles with Mathematically Proportional Leading (No Overlapping)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        fontName=FONT_BOLD,
        fontSize=15,
        leading=19,
        textColor=color_teal,
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        fontName=FONT_NORMAL,
        fontSize=8.5,
        leading=12,
        textColor=color_muted,
        spaceAfter=12,
    )
    sec_heading_style = ParagraphStyle(
        "SecHeading",
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=14,
        textColor=color_teal,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    label_style = ParagraphStyle(
        "FieldLabel",
        fontName=FONT_BOLD,
        fontSize=8,
        leading=11,
        textColor=color_muted,
    )
    val_style = ParagraphStyle(
        "FieldValue",
        fontName=FONT_NORMAL,
        fontSize=8.5,
        leading=12,
        textColor=color_dark,
    )
    body_text_style = ParagraphStyle(
        "BodyTextBlock",
        fontName=FONT_NORMAL,
        fontSize=8.5,
        leading=13,
        textColor=color_slate,
    )
    chat_author_style = ParagraphStyle(
        "ChatAuthor",
        fontName=FONT_BOLD,
        fontSize=8,
        leading=11,
        textColor=color_dark,
    )
    chat_text_style = ParagraphStyle(
        "ChatText",
        fontName=FONT_NORMAL,
        fontSize=8,
        leading=12,
        textColor=color_slate,
    )

    story = []

    # 1. Institutional Header Banner
    dev_id = str(getattr(deviation, "id", "UNKNOWN"))
    ref_code = f"DEV-{dev_id[:8].upper()}"
    site_name = getattr(deviation, "site_plant", "API Manufacturing Unit 01") or "API Manufacturing Unit 01"

    header_table_data = [
        [
            Paragraph(f"<b>{site_name.upper()}</b><br/><font color='#6B7280'>Quality Assurance & Regulatory Compliance Department</font>", val_style),
            Paragraph(f"<font color='#0F766E'><b>DOCUMENT REF: {ref_code}</b></font><br/><font color='#6B7280'>Status: COMMITTED (21 CFR Part 11)</font>", ParagraphStyle("RightH", parent=val_style, alignment=2)),
        ]
    ]
    t_header = Table(header_table_data, colWidths=[340, 200])
    t_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_header)

    story.append(HRFlowable(width="100%", thickness=1.5, color=color_teal, spaceBefore=4, spaceAfter=8))

    # Document Title
    dev_title = getattr(deviation, "title", "Untitled Deviation") or "Untitled Deviation"
    story.append(Paragraph("DEVIATION INVESTIGATION & INITIAL TRIAGE REPORT", title_style))
    story.append(Paragraph(f"Title: <b>{_escape_pdf(dev_title)}</b>", ParagraphStyle("TitleP", fontName=FONT_NORMAL, fontSize=11, leading=15, textColor=color_dark)))
    story.append(Spacer(1, 8))

    # Executive Metadata Summary Table (Width = 540 pt)
    comm_at = getattr(deviation, "committed_at", None)
    doc_meta_data = [
        [
            Paragraph("Deviation ID", label_style),
            Paragraph(f"<b>{ref_code}</b>", val_style),
            Paragraph("Initial Severity", label_style),
            Paragraph(f"<b><font color='{color_sev.hexval()}'>{sev.upper()}</font></b>", val_style),
        ],
        [
            Paragraph("Date of Occurrence", label_style),
            Paragraph(_escape_pdf(getattr(deviation, "date_of_occurrence", None)), val_style),
            Paragraph("Committed At", label_style),
            Paragraph(_format_dt(comm_at), val_style),
        ],
        [
            Paragraph("Facility / Plant", label_style),
            Paragraph(_escape_pdf(site_name), val_style),
            Paragraph("Reviewed By", label_style),
            Paragraph(f"<b>{_escape_pdf(getattr(deviation, 'reviewed_by', 'Quality Officer'))}</b>", val_style),
        ],
        [
            Paragraph("Classification / Source", label_style),
            Paragraph(_escape_pdf(getattr(deviation, "source", None)), val_style),
            Paragraph("Related Product", label_style),
            Paragraph(_escape_pdf(getattr(deviation, "related_product", None)), val_style),
        ],
        [
            Paragraph("Batch / Lot Number", label_style),
            Paragraph(_escape_pdf(getattr(deviation, "batch_lot", None)), val_style),
            Paragraph("Source File", label_style),
            Paragraph(_escape_pdf(getattr(deviation, "filename", "Direct Form Input")), val_style),
        ],
    ]
    t_meta = Table(doc_meta_data, colWidths=[105, 165, 105, 165])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), color_header_bg),
        ("BACKGROUND", (2, 0), (2, -1), color_header_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, color_border),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # 2. Executive Triage & Risk Rationale Callout Box
    ai_reasoning = getattr(deviation, "ai_reasoning", None)
    summary_text = session_summary or getattr(deviation, "session_summary", None)

    story.append(Paragraph("1. REGULATORY TRIAGE & RISK ASSESSMENT", sec_heading_style))
    triage_box_content = []
    triage_box_content.append(Paragraph(f"<b>Assigned Severity:</b> <font color='{color_sev.hexval()}'><b>{sev}</b></font> &nbsp;|&nbsp; <b>AI Suggested:</b> {getattr(deviation, 'ai_suggested_severity', 'N/A')}", val_style))
    if ai_reasoning:
        triage_box_content.append(Spacer(1, 3))
        triage_box_content.append(Paragraph(f"<b>Triage Justification & Regulatory Rationale:</b><br/>{_escape_pdf(ai_reasoning)}", body_text_style))
    if summary_text:
        triage_box_content.append(Spacer(1, 3))
        triage_box_content.append(Paragraph(f"<b>Pipeline Outcome Summary:</b> {_escape_pdf(summary_text)}", val_style))

    t_triage = Table([[triage_box_content]], colWidths=[540])
    t_triage.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_sev),
        ("BOX", (0, 0), (-1, -1), 1, color_sev),
        ("LINEBEFORE", (0, 0), (0, -1), 3.5, color_sev),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_triage)
    story.append(Spacer(1, 10))

    # 3. Detailed Description & Containment Action
    story.append(Paragraph("2. DEVIATION DESCRIPTION & CONTAINMENT ACTIONS", sec_heading_style))
    desc = getattr(deviation, "detailed_description", "")
    impact = getattr(deviation, "initial_impact", "")
    sugg_action = getattr(deviation, "ai_suggested_action", "")

    desc_table_data = [
        [Paragraph("<b>Detailed Description of Event</b>", label_style)],
        [Paragraph(_escape_pdf(desc), body_text_style)],
        [Paragraph("<b>Immediate Action Taken / Containment</b>", label_style)],
        [Paragraph(_escape_pdf(impact), body_text_style)],
    ]
    if sugg_action and sugg_action != impact:
        desc_table_data.extend([
            [Paragraph("<b>Secondary / AI Recommended Corrective Containment</b>", label_style)],
            [Paragraph(_escape_pdf(sugg_action), body_text_style)],
        ])

    t_desc = Table(desc_table_data, colWidths=[540])
    t_desc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), color_header_bg),
        ("BACKGROUND", (0, 2), (0, 2), color_header_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, color_border),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_desc)
    story.append(Spacer(1, 10))

    # 4. 21 CFR Part 11 Append-Only Audit Trail
    story.append(Paragraph(f"3. 21 CFR PART 11 AUDIT TRAIL LOG ({len(events)} EVENTS)", sec_heading_style))
    if not events:
        story.append(Paragraph("<i>No incremental field modification events logged for this record.</i>", body_text_style))
    else:
        audit_headers = [
            Paragraph("<b>Timestamp (UTC)</b>", label_style),
            Paragraph("<b>Actor</b>", label_style),
            Paragraph("<b>Field / Attribute</b>", label_style),
            Paragraph("<b>Audit Diff (Old &rarr; New Value)</b>", label_style),
        ]
        audit_rows = [audit_headers]
        for evt in events:
            actor_str = getattr(evt, "actor", "user") or "user"
            field_str = getattr(evt, "field", "") or ""
            old_v = getattr(evt, "old_value", None)
            new_v = getattr(evt, "new_value", None)
            ts_str = _format_dt(getattr(evt, "created_at", None))

            diff_str = f"<b>New:</b> {_escape_pdf(new_v)}"
            if old_v:
                diff_str = f"<font color='#BE123C'><strike>{_escape_pdf(old_v)}</strike></font> &rarr; {diff_str}"

            audit_rows.append([
                Paragraph(ts_str, val_style),
                Paragraph(f"<b>{actor_str.upper()}</b>", val_style),
                Paragraph(_escape_pdf(field_str), val_style),
                Paragraph(diff_str, val_style),
            ])

        t_audit = Table(audit_rows, colWidths=[95, 55, 110, 280], repeatRows=1)
        t_audit.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), color_header_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, color_border),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t_audit)

    story.append(Spacer(1, 10))

    # 5. AI Copilot Chat Conversation Transcript
    story.append(Paragraph(f"4. AI COPILOT INTERACTIVE SESSION TRANSCRIPT ({len(messages)} MESSAGES)", sec_heading_style))
    if not messages:
        story.append(Paragraph("<i>Deviation committed directly through regulatory form intake. No dialogue transcript.</i>", body_text_style))
    else:
        chat_rows = []
        for msg in messages:
            role = getattr(msg, "role", "assistant") if hasattr(msg, "role") else msg.get("role", "assistant")
            content = getattr(msg, "content", "") if hasattr(msg, "content") else msg.get("content", "")
            ts = getattr(msg, "timestamp", None) if hasattr(msg, "timestamp") else msg.get("timestamp", None)

            is_user = role == "user"
            author_label = "Operator / Intake Author" if is_user else "DeviationIQ AI Assistant"
            author_color = "#111827" if is_user else "#0F766E"
            bg_chat = "#F9FAFB" if is_user else "#F0FDF4"

            header_text = f"<font color='{author_color}'><b>{author_label}</b></font>"
            if ts:
                header_text += f" &nbsp;|&nbsp; <font color='#6B7280'>{_format_dt(ts)}</font>"

            cell_content = [
                Paragraph(header_text, chat_author_style),
                Spacer(1, 2),
                Paragraph(_escape_pdf(content), chat_text_style),
            ]
            chat_rows.append([cell_content])

        t_chat = Table(chat_rows, colWidths=[540])
        t_chat.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, color_border),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_chat)

    story.append(Spacer(1, 12))

    # 6. Formal 21 CFR Part 11 Electronic Signature Stamp (KeepTogether)
    sig_content = [
        Paragraph("5. 21 CFR PART 11 ELECTRONIC SIGNATURE & QUALITY APPROVAL", sec_heading_style),
        Spacer(1, 3),
    ]

    sig_reviewer = getattr(deviation, "reviewed_by", "Quality Officer") or "Quality Officer"
    sig_date = _format_dt(getattr(deviation, "committed_at", datetime.now(timezone.utc)))

    sig_table_data = [
        [
            Paragraph("<b>Signer Name:</b>", label_style),
            Paragraph(f"<b>{_escape_pdf(sig_reviewer)}</b>", val_style),
            Paragraph("<b>Signature Meaning:</b>", label_style),
            Paragraph("Formally Reviewed & Approved (21 CFR Part 11)", val_style),
        ],
        [
            Paragraph("<b>Timestamp:</b>", label_style),
            Paragraph(sig_date, val_style),
            Paragraph("<b>Record Hash / Seal:</b>", label_style),
            Paragraph(f"<font color='#0F766E'><b>{dev_id}</b></font>", val_style),
        ],
    ]
    t_sig = Table(sig_table_data, colWidths=[90, 180, 110, 160])
    t_sig.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color_light_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, color_teal),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    sig_content.append(t_sig)

    story.append(KeepTogether(sig_content))

    # Build Document
    doc.build(story, canvasmaker=GxPReportCanvas)
    buffer.seek(0)
    return buffer


# ===========================================================================
# DOCX GENERATOR (PYTHON-DOCX)
# ===========================================================================

def _set_cell_background(cell, color_hex: str):
    """Set background shading on a docx cell."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set internal padding on a docx cell in twips."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def generate_deviation_docx(
    deviation: Any,
    messages: list[Any],
    events: list[Any],
    session_summary: str | None = None,
) -> io.BytesIO:
    """Generate a clean, professional GxP DOCX deviation dossier."""
    doc = docx.Document()

    # Page Margins: 0.5 inches all around (clean width = 7.5 in = 540 pt)
    sections = doc.sections
    for sec in sections:
        sec.top_margin = Inches(0.5)
        sec.bottom_margin = Inches(0.5)
        sec.left_margin = Inches(0.5)
        sec.right_margin = Inches(0.5)

    # Base Colors
    c_teal = RGBColor(15, 118, 110)
    c_dark = RGBColor(17, 24, 39)
    c_muted = RGBColor(107, 114, 128)

    dev_id = str(getattr(deviation, "id", "UNKNOWN"))
    ref_code = f"DEV-{dev_id[:8].upper()}"
    site_name = getattr(deviation, "site_plant", "API Manufacturing Unit 01") or "API Manufacturing Unit 01"
    sev = getattr(deviation, "initial_severity", "") or "Unspecified"

    # Header / Title Block
    h_p = doc.add_paragraph()
    h_p.paragraph_format.space_before = Pt(0)
    h_p.paragraph_format.space_after = Pt(2)
    run_inst = h_p.add_run(site_name.upper())
    run_inst.font.bold = True
    run_inst.font.size = Pt(11)
    run_inst.font.color.rgb = c_teal

    h_sub = doc.add_paragraph()
    h_sub.paragraph_format.space_after = Pt(6)
    r_sub = h_sub.add_run("Quality Assurance & Regulatory Compliance Department | 21 CFR Part 11 Electronic Record")
    r_sub.font.size = Pt(8.5)
    r_sub.font.color.rgb = c_muted

    t_p = doc.add_paragraph()
    t_p.paragraph_format.space_after = Pt(2)
    r_title = t_p.add_run("DEVIATION INVESTIGATION & INITIAL TRIAGE REPORT")
    r_title.font.bold = True
    r_title.font.size = Pt(14)
    r_title.font.color.rgb = c_teal

    p_dev_title = doc.add_paragraph()
    p_dev_title.paragraph_format.space_after = Pt(10)
    r_dt = p_dev_title.add_run(f"Title: {getattr(deviation, 'title', 'Untitled Deviation')}")
    r_dt.font.bold = True
    r_dt.font.size = Pt(10.5)

    # Table 1: Core Metadata Table
    table_meta = doc.add_table(rows=5, cols=4)
    table_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_meta.autofit = False

    meta_rows = [
        ("Deviation ID", ref_code, "Initial Severity", sev.upper()),
        ("Date of Occurrence", _sanitize_gxp_text(str(getattr(deviation, "date_of_occurrence", "N/A"))), "Committed At", _format_dt(getattr(deviation, "committed_at", None))),
        ("Facility / Site", _sanitize_gxp_text(site_name), "Reviewed By", _sanitize_gxp_text(str(getattr(deviation, "reviewed_by", "Quality Officer")))),
        ("Classification", _sanitize_gxp_text(str(getattr(deviation, "source", "N/A"))), "Related Product", _sanitize_gxp_text(str(getattr(deviation, "related_product", "N/A")))),
        ("Batch / Lot", _sanitize_gxp_text(str(getattr(deviation, "batch_lot", "N/A"))), "Source File", _sanitize_gxp_text(str(getattr(deviation, "filename", "Direct Form Input")))),
    ]

    col_widths = [Inches(1.4), Inches(2.35), Inches(1.4), Inches(2.35)]
    for r_idx, row_data in enumerate(meta_rows):
        row = table_meta.rows[r_idx]
        for c_idx in range(4):
            cell = row.cells[c_idx]
            cell.width = col_widths[c_idx]
            _set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.15
            run = p.add_run(row_data[c_idx])
            run.font.size = Pt(8.5)
            if c_idx in (0, 2):
                _set_cell_background(cell, "F3F4F6")
                run.font.bold = True
                run.font.color.rgb = c_muted
            else:
                if c_idx == 3 and r_idx == 0:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(180, 83, 9) if sev.lower() == "major" else RGBColor(190, 18, 60)
                else:
                    run.font.color.rgb = c_dark

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Section 1: Triage Risk Assessment
    p_sec1 = doc.add_paragraph()
    p_sec1.paragraph_format.space_before = Pt(8)
    p_sec1.paragraph_format.space_after = Pt(4)
    r_s1 = p_sec1.add_run("1. REGULATORY TRIAGE & RISK ASSESSMENT")
    r_s1.font.bold = True
    r_s1.font.size = Pt(10.5)
    r_s1.font.color.rgb = c_teal

    t_triage = doc.add_table(rows=1, cols=1)
    t_triage.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_tr = t_triage.rows[0].cells[0]
    c_tr.width = Inches(7.5)
    _set_cell_background(c_tr, "F8FAFC")
    _set_cell_margins(c_tr, top=100, bottom=100, left=140, right=140)

    p_tr = c_tr.paragraphs[0]
    p_tr.paragraph_format.space_before = Pt(2)
    p_tr.paragraph_format.space_after = Pt(3)
    r_t1 = p_tr.add_run(f"Severity Classification: {sev} (AI Suggested: {getattr(deviation, 'ai_suggested_severity', 'N/A')})\n")
    r_t1.font.bold = True
    r_t1.font.size = Pt(9)

    ai_reas = getattr(deviation, "ai_reasoning", None)
    if ai_reas:
        r_t2 = p_tr.add_run(f"Justification Rationale:\n{_sanitize_gxp_text(ai_reas)}\n")
        r_t2.font.size = Pt(8.5)
    if session_summary:
        r_t3 = p_tr.add_run(f"Pipeline Summary:\n{_sanitize_gxp_text(session_summary)}")
        r_t3.font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Section 2: Narrative & Containment
    p_sec2 = doc.add_paragraph()
    p_sec2.paragraph_format.space_before = Pt(8)
    p_sec2.paragraph_format.space_after = Pt(4)
    r_s2 = p_sec2.add_run("2. DEVIATION DESCRIPTION & CONTAINMENT ACTIONS")
    r_s2.font.bold = True
    r_s2.font.size = Pt(10.5)
    r_s2.font.color.rgb = c_teal

    t_desc = doc.add_table(rows=4, cols=1)
    t_desc.alignment = WD_TABLE_ALIGNMENT.CENTER
    sections_desc = [
        ("DETAILED DESCRIPTION OF EVENT", _sanitize_gxp_text(str(getattr(deviation, "detailed_description", "N/A")))),
        ("IMMEDIATE ACTION TAKEN / CONTAINMENT", _sanitize_gxp_text(str(getattr(deviation, "initial_impact", "N/A")))),
    ]
    for idx, (label, val) in enumerate(sections_desc):
        cell_lbl = t_desc.rows[idx * 2].cells[0]
        cell_lbl.width = Inches(7.5)
        _set_cell_background(cell_lbl, "F3F4F6")
        _set_cell_margins(cell_lbl, top=40, bottom=40, left=100, right=100)
        p_l = cell_lbl.paragraphs[0]
        p_l.paragraph_format.space_before = Pt(1)
        p_l.paragraph_format.space_after = Pt(1)
        r_l = p_l.add_run(label)
        r_l.font.bold = True
        r_l.font.size = Pt(8)
        r_l.font.color.rgb = c_muted

        cell_val = t_desc.rows[idx * 2 + 1].cells[0]
        cell_val.width = Inches(7.5)
        _set_cell_margins(cell_val, top=60, bottom=60, left=100, right=100)
        p_v = cell_val.paragraphs[0]
        p_v.paragraph_format.space_before = Pt(2)
        p_v.paragraph_format.space_after = Pt(2)
        p_v.paragraph_format.line_spacing = 1.15
        r_v = p_v.add_run(str(val))
        r_v.font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Section 3: Audit Trail
    p_sec3 = doc.add_paragraph()
    p_sec3.paragraph_format.space_before = Pt(8)
    p_sec3.paragraph_format.space_after = Pt(4)
    r_s3 = p_sec3.add_run(f"3. 21 CFR PART 11 AUDIT TRAIL LOG ({len(events)} EVENTS)")
    r_s3.font.bold = True
    r_s3.font.size = Pt(10.5)
    r_s3.font.color.rgb = c_teal

    if events:
        t_aud = doc.add_table(rows=len(events) + 1, cols=4)
        t_aud.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers = ["Timestamp (UTC)", "Actor", "Field / Attribute", "Audit Diff (Old â†’ New Value)"]
        aud_widths = [Inches(1.3), Inches(0.8), Inches(1.5), Inches(3.9)]

        hdr_row = t_aud.rows[0]
        for c_i, h_txt in enumerate(headers):
            cell = hdr_row.cells[c_i]
            cell.width = aud_widths[c_i]
            _set_cell_background(cell, "F3F4F6")
            _set_cell_margins(cell, top=40, bottom=40, left=80, right=80)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(h_txt)
            r.font.bold = True
            r.font.size = Pt(8)
            r.font.color.rgb = c_muted

        for r_i, evt in enumerate(events, start=1):
            row = t_aud.rows[r_i]
            ts = _format_dt(getattr(evt, "created_at", None))
            actor = (getattr(evt, "actor", "user") or "user").upper()
            fld = _sanitize_gxp_text(str(getattr(evt, "field", "") or ""))
            ov = _sanitize_gxp_text(str(getattr(evt, "old_value", "") or "")) if getattr(evt, "old_value", None) else None
            nv = _sanitize_gxp_text(str(getattr(evt, "new_value", "") or "")) if getattr(evt, "new_value", None) else None

            diff = f"New: {nv}"
            if ov:
                diff = f"Old: {ov}  â†’  {diff}"

            for c_i, val in enumerate([ts, actor, fld, diff]):
                cell = row.cells[c_i]
                cell.width = aud_widths[c_i]
                _set_cell_margins(cell, top=40, bottom=40, left=80, right=80)
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.line_spacing = 1.15
                r = p.add_run(val)
                r.font.size = Pt(8)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Section 4: Chat Transcript
    p_sec4 = doc.add_paragraph()
    p_sec4.paragraph_format.space_before = Pt(8)
    p_sec4.paragraph_format.space_after = Pt(4)
    r_s4 = p_sec4.add_run(f"4. AI COPILOT INTERACTIVE TRANSCRIPT ({len(messages)} MESSAGES)")
    r_s4.font.bold = True
    r_s4.font.size = Pt(10.5)
    r_s4.font.color.rgb = c_teal

    if messages:
        t_chat = doc.add_table(rows=len(messages), cols=1)
        t_chat.alignment = WD_TABLE_ALIGNMENT.CENTER
        for idx, msg in enumerate(messages):
            cell = t_chat.rows[idx].cells[0]
            cell.width = Inches(7.5)
            role = getattr(msg, "role", "assistant") if hasattr(msg, "role") else msg.get("role", "assistant")
            content = _sanitize_gxp_text(str(getattr(msg, "content", "") if hasattr(msg, "content") else msg.get("content", "")))
            ts = getattr(msg, "timestamp", None) if hasattr(msg, "timestamp") else msg.get("timestamp", None)

            is_user = role == "user"
            author = "Operator / Intake Author" if is_user else "DeviationIQ AI Assistant"
            _set_cell_background(cell, "F9FAFB" if is_user else "F0FDF4")
            _set_cell_margins(cell, top=60, bottom=60, left=100, right=100)

            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.15

            r_hdr = p.add_run(f"{author}  [{_format_dt(ts)}]\n")
            r_hdr.font.bold = True
            r_hdr.font.size = Pt(8)
            r_hdr.font.color.rgb = c_dark if is_user else c_teal

            r_cnt = p.add_run(content)
            r_cnt.font.size = Pt(8)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Section 5: Signature Stamp
    p_sec5 = doc.add_paragraph()
    p_sec5.paragraph_format.space_before = Pt(8)
    p_sec5.paragraph_format.space_after = Pt(4)
    r_s5 = p_sec5.add_run("5. 21 CFR PART 11 ELECTRONIC SIGNATURE & QUALITY APPROVAL")
    r_s5.font.bold = True
    r_s5.font.size = Pt(10.5)
    r_s5.font.color.rgb = c_teal

    t_sig = doc.add_table(rows=2, cols=4)
    t_sig.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_data = [
        ("Signer Name:", str(getattr(deviation, "reviewed_by", "Quality Officer")), "Signature Meaning:", "Formally Reviewed & Approved (21 CFR Part 11)"),
        ("Timestamp:", _format_dt(getattr(deviation, "committed_at", None)), "Record Hash / Seal:", dev_id),
    ]
    sig_widths = [Inches(1.4), Inches(2.35), Inches(1.4), Inches(2.35)]
    for r_i, s_row in enumerate(sig_data):
        row = t_sig.rows[r_i]
        for c_i in range(4):
            cell = row.cells[c_i]
            cell.width = sig_widths[c_i]
            _set_cell_background(cell, "F9FAFB")
            _set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(s_row[c_i])
            r.font.size = Pt(8)
            if c_i in (0, 2):
                r.font.bold = True
                r.font.color.rgb = c_muted
            else:
                r.font.color.rgb = c_dark

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
