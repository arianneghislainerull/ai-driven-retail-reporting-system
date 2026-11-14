from datetime import datetime
import os
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from utils import money, pct
from theme import CT_RED, CT_GREEN, CT_BLACK, CT_DARK_GREY, CT_LIGHT_GREY


def _header_footer(c: canvas.Canvas, doc, title: str, generated_at: str):
    c.saveState()
    w, h = letter

    # Top red bar
    c.setFillColor(CT_RED)
    c.rect(0, h - 32, w, 32, stroke=0, fill=1)

    # Title in bar
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(36, h - 22, title)

    # Footer line + page number
    c.setStrokeColor(CT_LIGHT_GREY)
    c.setLineWidth(1)
    c.line(36, 40, w - 36, 40)

    c.setFillColor(CT_DARK_GREY)
    c.setFont("Helvetica", 9)
    c.drawString(36, 26, f"Generated on: {generated_at}")
    c.drawRightString(w - 36, 26, f"Page {doc.page}")

    c.restoreState()


def df_to_table(df_in: pd.DataFrame, max_rows=12):
    df_show = df_in.head(max_rows).copy()
    data = [df_show.columns.tolist()] + df_show.values.tolist()

    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CT_BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),

        ("GRID", (0, 0), (-1, -1), 0.25, CT_LIGHT_GREY),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),

        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def kpi_table(snapshot: dict):
    data = [
        ["Total Sales", money(snapshot["total_sales"]), "Total COGS", money(snapshot["total_cogs"])],
        ["Total Margin", money(snapshot["total_margin"]), "Margin Rate", pct(snapshot["margin_rate"])],
    ]
    t = Table(data, colWidths=[1.35 * inch, 1.25 * inch, 1.35 * inch, 1.25 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
        ("BOX", (0, 0), (-1, -1), 1, CT_LIGHT_GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, CT_LIGHT_GREY),

        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (-1, -1), CT_BLACK),

        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def build_pdf(
    pdf_path: str,
    snapshot: dict,
    insights: list,
    charts: list,          # list of dicts: title/path/caption/takeaway
    dim_tables: list,      # list[(title, top_sales_df, worst_mr_df)]
    anom_table: pd.DataFrame | None,
    driver_table: pd.DataFrame | None,
    generated_at: str | None = None,
    logo_path: str | None = "ct_logo.png"
):
    if generated_at is None:
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CTTitle", parent=styles["Title"],
        fontSize=24, leading=28, textColor=CT_BLACK, spaceAfter=10
    )
    subtitle_style = ParagraphStyle(
        "CTSubtitle", parent=styles["BodyText"],
        fontSize=11, leading=15, textColor=CT_DARK_GREY, spaceAfter=8
    )
    h_style = ParagraphStyle(
        "CTH2", parent=styles["Heading2"],
        fontSize=14.5, leading=18, textColor=CT_BLACK, spaceBefore=10, spaceAfter=6
    )
    h_style_green = ParagraphStyle(
        "CTH2Green", parent=styles["Heading2"],
        fontSize=14.5, leading=18, textColor=CT_GREEN, spaceBefore=10, spaceAfter=6
    )
    chart_title_style = ParagraphStyle(
        "CTH3", parent=styles["Heading3"],
        fontSize=12.5, leading=16, textColor=CT_BLACK, spaceBefore=8, spaceAfter=4
    )
    body_style = ParagraphStyle(
        "CTBody", parent=styles["BodyText"],
        fontSize=11, leading=15, textColor=CT_BLACK
    )
    small_style = ParagraphStyle(
        "CTSmall", parent=styles["BodyText"],
        fontSize=9.8, leading=13, textColor=CT_DARK_GREY
    )

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=36, leftMargin=36,
        topMargin=54, bottomMargin=54
    )

    title = "Retail Performance & AI Insights Report"

    elements = []

    # --- Cover
    # Red banner block
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(f"<b>Generated on:</b> {generated_at}", subtitle_style))
    elements.append(Paragraph(
        "Purpose: summarize performance KPIs, diagnose margin drivers, highlight anomalies, and recommend action areas.",
        body_style
    ))
    elements.append(Spacer(1, 14))

    # Optional logo
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=1.1 * inch, height=1.1 * inch))
        elements.append(Spacer(1, 10))

    elements.append(Paragraph("Executive KPI Summary", h_style))
    elements.append(kpi_table(snapshot))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Executive Insights", h_style_green))
    if insights:
        bullet_text = "<br/>".join([f"• {t}" for t in insights[:10]])
        elements.append(Paragraph(bullet_text, body_style))
    else:
        elements.append(Paragraph("No auto-generated insights available.", body_style))

    elements.append(PageBreak())

    # --- Charts section
    elements.append(Paragraph("Key Visualizations & Interpretation", h_style))
    if not charts:
        elements.append(Paragraph("No charts available.", body_style))
    else:
        for c in charts:
            block = []
            block.append(Paragraph(c["title"], chart_title_style))
            block.append(Image(c["path"], width=6.8 * inch, height=3.2 * inch))
            block.append(Spacer(1, 6))
            block.append(Paragraph(f"<b>What this shows:</b> {c.get('caption','')}", small_style))
            block.append(Paragraph(f"<b>Why it matters:</b> {c.get('takeaway','')}", small_style))
            block.append(Spacer(1, 10))
            elements.append(KeepTogether(block))

    elements.append(PageBreak())

    # --- Breakdown tables
    elements.append(Paragraph("Performance Breakdown Tables", h_style))
    for title_dim, top_sales, worst_mr in dim_tables:
        elements.append(Paragraph(f"{title_dim}: Top by Sales", chart_title_style))
        elements.append(df_to_table(top_sales))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph(f"{title_dim}: Worst by Margin Rate (Sales ≥ 25th percentile)", chart_title_style))
        elements.append(df_to_table(worst_mr))
        elements.append(Spacer(1, 16))

    elements.append(PageBreak())

    # --- AI findings
    elements.append(Paragraph("AI-Based Findings", h_style))

    if anom_table is not None and len(anom_table) > 0:
        elements.append(Paragraph("Anomaly Detection: Highest-Risk Margin Records", chart_title_style))
        elements.append(Paragraph(
            "These rows are statistically unusual and may indicate data quality issues (bad cost/price) or true business outliers (promo, returns, shrink).",
            body_style
        ))
        elements.append(Spacer(1, 6))
        elements.append(df_to_table(anom_table))
        elements.append(Spacer(1, 12))

    if driver_table is not None and len(driver_table) > 0:
        elements.append(Paragraph("Driver Model: Top Signals Associated with Margin Rate", chart_title_style))
        elements.append(Paragraph(
            "These are the strongest signals correlated with margin rate. Treat as hypotheses to investigate (correlation ≠ causation).",
            body_style
        ))
        elements.append(Spacer(1, 6))
        elements.append(df_to_table(driver_table))

    doc.build(
        elements,
        onFirstPage=lambda c, d: _header_footer(c, d, title, generated_at),
        onLaterPages=lambda c, d: _header_footer(c, d, title, generated_at),
    )