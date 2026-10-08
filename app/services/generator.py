import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


def _fit_font_size(text, font, start, max_width, minimum=10):
    size = start
    while size > minimum and stringWidth(text, font, size) > max_width:
        size -= 1
    return size


def generate_certificate(name: str, event_name: str, issue_date: str, output_path: str) -> str:
    """Draw one landscape A4 certificate using the single predefined template."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    w, h = landscape(A4)
    max_w = w - 160
    navy = colors.HexColor("#1f3a5f")

    c = canvas.Canvas(output_path, pagesize=(w, h))
    c.setStrokeColor(navy)
    c.setLineWidth(6)
    c.rect(25, 25, w - 50, h - 50)
    c.setLineWidth(1.5)
    c.rect(40, 40, w - 80, h - 80)

    c.setFillColor(navy)
    c.setFont("Helvetica-Bold", 38)
    c.drawCentredString(w / 2, h - 120, "Certificate of Participation")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 16)
    c.drawCentredString(w / 2, h - 190, "This is to certify that")

    size = _fit_font_size(name, "Helvetica-Bold", 36, max_w)
    c.setFont("Helvetica-Bold", size)
    c.drawCentredString(w / 2, h / 2, name)
    c.line(w / 2 - 200, h / 2 - 10, w / 2 + 200, h / 2 - 10)

    c.setFont("Helvetica", 16)
    c.drawCentredString(w / 2, h / 2 - 50, "has successfully participated in")

    size = _fit_font_size(event_name, "Helvetica-Bold", 24, max_w)
    c.setFont("Helvetica-Bold", size)
    c.drawCentredString(w / 2, h / 2 - 90, event_name)

    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, 90, f"Issued on {issue_date}")
    c.save()
    return output_path