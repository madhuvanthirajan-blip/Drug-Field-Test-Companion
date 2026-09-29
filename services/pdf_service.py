from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from PIL import Image as PILImage

def build_pdf(test, image_bytes):
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=18*mm,leftMargin=18*mm,topMargin=16*mm,bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8.5, leading=11)
    story = [Paragraph("FIELD TEST COMPANION", styles["Title"]),
             Paragraph("Digital Field Drug Testing — Prototype Report", styles["Heading2"]),
             Spacer(1,5*mm)]
    gps = "Not recorded"
    if test.get("latitude") is not None:
        gps = f'{test["latitude"]:.6f}, {test["longitude"]:.6f}'
    rows = [
        ["Record ID",test["record_id"]],["Officer ID",test["officer_id"]],
        ["Suspected drug",test["drug"]],["Kit batch / lot",test["batch"]],
        ["Classification",test["result"]],["Confidence",f'{test["confidence"]:.1f}%'],
        ["Timestamp",test["timestamp"]],["GPS",gps],
        ["Image SHA-256",test["image_hash"]],["Record SHA-256",test["record_hash"]]]
    table=Table(rows,colWidths=[42*mm,130*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#EAF2F5")),
        ("GRID",(0,0),(-1,-1),.4,colors.HexColor("#B7C6CC")),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.5),
        ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),
        ("RIGHTPADDING",(0,0),(-1,-1),5)]))
    story += [table,Spacer(1,7*mm),Paragraph("Captured image",styles["Heading3"])]
    try:
        pil=PILImage.open(BytesIO(image_bytes)).convert("RGB")
        ib=BytesIO(); pil.thumbnail((1500,1000)); pil.save(ib,format="JPEG",quality=88); ib.seek(0)
        story.append(Image(ib,width=145*mm,height=96*mm))
    except Exception:
        story.append(Paragraph("Captured image could not be embedded.",small))
    story += [Spacer(1,5*mm),Paragraph("CV explanation: "+test["explanation"],small),
              Spacer(1,4*mm),Paragraph(
              "Prototype disclaimer: This is a presumptive field-test result and supporting digital record. "
              "It is not laboratory confirmation and has not been chemically validated.",small)]
    doc.build(story)
    return out.getvalue()
