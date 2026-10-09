from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from xml.sax.saxutils import escape

def write_pdf(document: dict, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    body = styles["BodyText"]
    body.leading = 14
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    story = [Paragraph("DocFusion AI Report", styles["Title"]), Paragraph(escape(str(document.get("title", "Untitled document"))), styles["Heading2"]), Spacer(1, 8), Paragraph(f"Document ID: {escape(str(document.get('document_id', 'Unknown')))} | Version: {escape(str(document.get('version', 1)))}", body), Paragraph(f"SHA-256: {escape(str(document.get('document_hash', 'generated after signing')))}", body), Paragraph(f"Classification: {escape(str(document.get('classification', 'INTERNAL')))} | Redacted items: {escape(str(document.get('redaction_count', 0)))}", body), Spacer(1, 12), Paragraph("Executive Summary", styles["Heading2"]), Paragraph(escape(str(document.get("summary", ""))), body), Spacer(1, 10)]
    story += [Paragraph("Sources", styles["Heading2"])]
    rows = [["ID", "Name", "Type", "SHA-256"]] + [[escape(str(source.get("source_id", "—"))), escape(str(source.get("name", "Unknown source"))), escape(str(source.get("source_type", "unknown"))), escape(str(source.get("content_hash", "—")))] for source in document.get("sources", [])]
    table = Table(rows, colWidths=[24*mm, 45*mm, 25*mm, 75*mm], repeatRows=1)
    table.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.4, colors.grey), ("BACKGROUND", (0,0), (-1,0), colors.lightgrey), ("FONTSIZE", (0,0), (-1,-1), 7)]))
    story += [table, Spacer(1, 12), Paragraph("Consolidated Facts", styles["Heading2"])]
    for c in document.get("claims", []):
        story += [Paragraph(escape(str(c.get("claim", ""))), body), Paragraph(escape(f"Sources: {', '.join(c.get('sources', []))} | Confidence: {c.get('confidence', 0):.2f}"), body), Spacer(1, 5)]
    story += [Paragraph("Conflicts", styles["Heading2"])]
    if document.get("conflicts"):
        for c in document["conflicts"]:
            values = "; ".join(f"{v['source']}: {v['value']}" for v in c.get("values", []))
            story += [Paragraph(escape(f"{c.get('field', 'Unknown field')}: {values} — {c.get('status', 'unresolved').upper()}"), body), Spacer(1, 5)]
    else:
        story.append(Paragraph("No conflicts detected.", body))
    story += [Paragraph("Provenance", styles["Heading2"])]
    for p in document.get("provenance", []):
        story += [Paragraph(escape(f"{p.get('claim', '')} — {p.get('source_id', '')}"), body), Paragraph(escape(f"Evidence: {p.get('evidence', '')}"), body), Spacer(1, 5)]
    doc.build(story)
