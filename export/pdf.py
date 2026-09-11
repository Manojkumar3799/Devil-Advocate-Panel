"""PDF report generation for Devil's Advocate Panel using ReportLab."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)


def generate_panel_pdf(
    pitch_text: str,
    intensity: str,
    transcript: list[dict[str, Any]],
    verdict: list[dict[str, Any]],
    session_id: str | None = None,
) -> bytes:
    """Generate a clean, high-design PDF executive summary report of the panel grilling."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6,
    )
    
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=15,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
    )

    reasoning_style = ParagraphStyle(
        "ReasoningText",
        parent=styles["Italic"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
    )

    elements = []

    # 1. Title Banner
    elements.append(Paragraph("DEVIL'S ADVOCATE PANEL", title_style))
    date_str = datetime.utcnow().strftime("%B %d, %Y - %H:%M UTC")
    elements.append(Paragraph(f"Executive Stress-Test Report | Intensity: <b>{intensity.upper()}</b> | Generated: {date_str}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#E2E8F0"), spaceAfter=15))

    # 2. Pitch Overview
    elements.append(Paragraph("1. THE PITCH UNDER SCRUTINY", section_heading))
    pitch_box = [
        [Paragraph(f"<b>Founder Pitch:</b><br/>{pitch_text}", body_style)]
    ]
    t_pitch = Table(pitch_box, colWidths=[532])
    t_pitch.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(t_pitch)
    elements.append(Spacer(1, 15))

    # 3. Final Verdict / Weaknesses (Ranked by Severity)
    elements.append(Paragraph("2. KEY RISKS & FATAL FLAWS (VERDICT)", section_heading))
    
    if verdict:
        # Table headers
        table_data = [
            [
                Paragraph("<b>Sev</b>", body_style),
                Paragraph("<b>Identified Weakness / Risk</b>", body_style),
                Paragraph("<b>Required Remediation / Fix</b>", body_style),
            ]
        ]
        
        # Sort verdict by severity desc
        sorted_verdict = sorted(verdict, key=lambda x: int(x.get("severity", 3)), reverse=True)
        for w in sorted_verdict:
            sev = int(w.get("severity", 3))
            sev_color = "#EF4444" if sev >= 4 else ("#F59E0B" if sev == 3 else "#10B981")
            sev_badge = f"<font color='{sev_color}'><b>{sev}/5</b></font>"
            
            table_data.append([
                Paragraph(sev_badge, body_style),
                Paragraph(w.get("issue", ""), body_style),
                Paragraph(w.get("fix", ""), body_style),
            ])

        v_table = Table(table_data, colWidths=[40, 246, 246])
        v_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.HexColor("#94A3B8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(v_table)
    else:
        elements.append(Paragraph("No critical weaknesses flagged by the panel.", body_style))

    elements.append(Spacer(1, 20))

    # 4. Detailed Interrogation Transcript
    elements.append(Paragraph("3. PANEL INTERROGATION TRANSCRIPT", section_heading))
    
    persona_names = {
        "vc": "Venture Capitalist (Moat & Founder Pedigree)",
        "analyst": "Financial Analyst (Unit Economics & Margins)",
        "realist": "Market Realist (Competitors & Distribution)",
    }

    for entry in transcript:
        p_key = entry.get("persona", "").lower()
        p_name = persona_names.get(p_key, p_key.upper())
        rnd = entry.get("round", 1)
        question = entry.get("question", "")
        thinking = entry.get("thinking", "")
        reply = entry.get("user_reply")

        card_content = [
            Paragraph(f"<b>{p_name} — Round {rnd}</b>", body_style),
        ]
        if thinking:
            card_content.append(Spacer(1, 4))
            card_content.append(Paragraph(f"<b>Internal Reasoning:</b> {thinking}", reasoning_style))
        if question:
            card_content.append(Spacer(1, 4))
            card_content.append(Paragraph(f"<b>Challenge:</b> {question}", body_style))
        if reply:
            card_content.append(Spacer(1, 4))
            card_content.append(Paragraph(f"<b>Founder Response:</b> <i>{reply}</i>", body_style))

        t_card = Table([[c] for c in card_content], colWidths=[532])
        t_card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))

        elements.append(KeepTogether([t_card, Spacer(1, 10)]))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
