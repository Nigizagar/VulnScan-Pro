import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generate_pdf(scan_obj, ports_data):
    """Menghasilkan laporan PDF profesional menggunakan ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph(f"VulnScan Pro - Security Report", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Meta info
    elements.append(Paragraph(f"<b>Target:</b> {scan_obj.target_info.target}", styles['Normal']))
    elements.append(Paragraph(f"<b>Scan Date:</b> {scan_obj.scan_time.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph(f"<b>Total Open Ports:</b> {scan_obj.total_open_ports}", styles['Normal']))
    elements.append(Spacer(1, 24))

    # Table Data
    data = [['Port', 'Service', 'Banner', 'HTTP Server']]
    for p in ports_data:
        data.append([
            str(p.port), 
            p.service or 'N/A', 
            (p.banner[:30] + '...') if p.banner and len(p.banner) > 30 else (p.banner or 'N/A'),
            p.http_server or 'N/A'
        ])

    # Table styling
    t = Table(data, colWidths=[50, 100, 180, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#ECF0F1")),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()