"""
Report Generation Utility
Creates PDF reports for deal summaries
"""

import io
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


DISCLAIMER_TEXT = """
IMPORTANT DISCLAIMER: This is an indicative early-look demand tool. It is not an offering document, 
not investment advice, and not a solicitation. All Indications of Interest (IOIs) are non-binding 
and subject to further diligence and documentation. This summary is confidential and intended 
solely for the issuer's internal use.
"""


def generate_deal_report(
    deal_data: Dict[str, Any],
    bands_data: List[Dict],
    demand_summary: Dict[str, Any],
    iois_data: List[Dict],
    selected_range: Dict[str, Any] = None
) -> bytes:
    """
    Generate a PDF report for a deal
    
    Args:
        deal_data: Deal information dict
        bands_data: List of band dicts with label, value, multiples
        demand_summary: Aggregated demand data
        iois_data: List of IOI dicts (investor name, amount, band, etc.)
        selected_range: Selected indicative range info
    
    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        textColor=colors.HexColor('#1a1a2e'),
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        textColor=colors.HexColor('#4a4a6a'),
        alignment=TA_CENTER
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=15,
        textColor=colors.HexColor('#1a1a2e'),
        borderPadding=5
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        textColor=colors.HexColor('#333333')
    )
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        alignment=TA_LEFT,
        spaceBefore=20
    )
    
    # Build content
    story = []
    
    # Title
    story.append(Paragraph("Early-Look Bookbuilding Summary", title_style))
    story.append(Paragraph(deal_data.get('name', 'Unnamed Deal'), subtitle_style))
    story.append(Spacer(1, 10))
    
    # Horizontal line
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
    story.append(Spacer(1, 15))
    
    # Deal Overview
    story.append(Paragraph("Deal Overview", section_style))
    
    deal_type = deal_data.get('deal_type', 'N/A')
    if hasattr(deal_type, 'value'):
        deal_type = deal_type.value.capitalize()
    
    currency = deal_data.get('currency', 'AED')
    target = deal_data.get('target_amount', 0)
    
    overview_data = [
        ['Deal Type:', deal_type],
        ['Currency:', currency],
        ['Target Raise:', f"{currency} {target:,.0f}"],
        ['Status:', deal_data.get('status', 'N/A')],
        ['Book Opened:', deal_data.get('start_at', 'N/A')],
        ['Book Closed:', deal_data.get('closed_at', 'N/A')],
    ]
    
    overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
    overview_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 15))
    
    # Pricing Bands Table
    story.append(Paragraph("Valuation/Yield Bands", section_style))
    
    band_headers = ['Band', 'Value', 'Total Demand', '# Investors', 'Coverage']
    band_rows = [band_headers]
    
    for band in bands_data:
        band_id = band.get('id')
        band_demand = demand_summary.get('demand_by_band', {}).get(band_id, {})
        
        value_str = f"{currency} {band.get('band_value', 0):,.0f}"
        demand_str = f"{currency} {band_demand.get('demand', 0):,.0f}"
        coverage = band_demand.get('coverage', 0)
        coverage_str = f"{coverage:.1%}"
        
        band_rows.append([
            band.get('label', ''),
            value_str,
            demand_str,
            str(band_demand.get('bid_count', 0)),
            coverage_str
        ])
    
    band_table = Table(band_rows, colWidths=[1.2*inch, 1.3*inch, 1.5*inch, 1*inch, 1*inch])
    band_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d44')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    story.append(band_table)
    story.append(Spacer(1, 15))
    
    # Demand Summary
    story.append(Paragraph("Demand Summary", section_style))
    
    total_demand = demand_summary.get('total_demand', 0)
    total_bids = demand_summary.get('total_bids', 0)
    overall_coverage = demand_summary.get('overall_coverage', 0)
    
    summary_data = [
        ['Total Demand:', f"{currency} {total_demand:,.0f}"],
        ['Total IOIs:', str(total_bids)],
        ['Overall Coverage:', f"{overall_coverage:.1%}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # Selected Indicative Range
    if selected_range:
        story.append(Paragraph("Selected Indicative Range", section_style))
        
        range_text = f"<b>{selected_range.get('low_label', '')} – {selected_range.get('high_label', '')}</b>"
        range_value = f"{currency} {selected_range.get('low_value', 0):,.0f} – {currency} {selected_range.get('high_value', 0):,.0f}"
        
        story.append(Paragraph(range_text, body_style))
        story.append(Paragraph(range_value, body_style))
        
        if selected_range.get('description'):
            story.append(Spacer(1, 5))
            story.append(Paragraph(f"<i>{selected_range.get('description')}</i>", body_style))
        
        story.append(Spacer(1, 15))
    
    # IOI Details Table (for issuer only)
    if iois_data:
        story.append(Paragraph("IOI Details (Confidential)", section_style))
        
        ioi_headers = ['Investor', 'Type', 'Amount', 'Band', 'Strength', 'Anchor']
        ioi_rows = [ioi_headers]
        
        for ioi in iois_data:
            ioi_rows.append([
                ioi.get('investor_name', 'Unknown'),
                ioi.get('investor_type', 'N/A'),
                f"{currency} {ioi.get('amount', 0):,.0f}",
                ioi.get('band_label', 'N/A'),
                ioi.get('strength', 'N/A'),
                '✓' if ioi.get('anchor_flag') else ''
            ])
        
        ioi_table = Table(ioi_rows, colWidths=[1.5*inch, 1*inch, 1.3*inch, 0.8*inch, 0.7*inch, 0.7*inch])
        ioi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d2d44')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        story.append(ioi_table)
    
    # Disclaimer
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
    story.append(Paragraph(DISCLAIMER_TEXT, disclaimer_style))
    
    # Report generation timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<i>Report generated: {timestamp}</i>", disclaimer_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def format_datetime(dt) -> str:
    """Format datetime for display"""
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        return dt
    return dt.strftime("%Y-%m-%d %H:%M")
