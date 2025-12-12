from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from io import BytesIO
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

app = FastAPI()

DISCLAIMER = (
    "This RAMS document is generated for guidance only and does not constitute legal advice. "
    "The user is responsible for reviewing and approving the document before use."
)

def _lines(text: str):
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

def build_pdf(data: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>RISK ASSESSMENT & METHOD STATEMENT (RAMS)</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    details = [
        ["Company", data["company"]],
        ["Job title", data["job_title"]],
        ["Location", data["location"]],
        ["Date", data["job_date"]],
        ["Workers", data["workers"]],
        ["Supervisor", data["supervisor"]],
    ]

    table = Table(details, colWidths=[150, 350])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Method Statement</b>", styles["Heading2"]))
    for step in _lines(data["method_steps"]):
        story.append(Paragraph(f"- {step}", styles["BodyText"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Hazards & Controls</b>", styles["Heading2"]))
    for hz in _lines(data["hazards"]):
        story.append(Paragraph(f"- {hz}", styles["BodyText"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Disclaimer</b>", styles["Heading2"]))
    story.append(Paragraph(DISCLAIMER, styles["BodyText"]))

    doc.build(story)
    return buf.getvalue()

@app.get("/", response_class=HTMLResponse)
def home():
    today = date.today().isoformat()
    return f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>QuickRAMS</title>
  <style>
    body {{ font-family: Arial; max-width: 900px; margin: 40px auto; }}
    input, textarea {{ width: 100%; padding: 10px; margin-bottom: 15px; }}
    button {{ padding: 12px 20px; font-weight: bold; }}
  </style>
</head>
<body>

<h1>QuickRAMS</h1>

<p>
  <a href="https://buy.stripe.com/4gM6oJda49hP9Ie8kh7Zu00" target="_blank">
    <strong>Pay £25/month to generate RAMS</strong>
  </a>
</p>

<p><em>Please complete payment before generating your RAMS.</em></p>

<form method="post" action="/generate">
  <label>Company</label>
  <input name="company" required>

  <label>Job title</label>
  <input name="job_title" required>

  <label>Location</label>
  <input name="location" required>

  <label>Date</label>
  <input name="job_date" value="{today}">

  <label>Workers</label>
  <input name="workers">

  <label>Supervisor</label>
  <input name="supervisor">

  <label>Method steps (one per line)</label>
  <textarea name="method_steps" rows="5"></textarea>

  <label>Hazards & controls (one per line)</label>
  <textarea name="hazards" rows="5"></textarea>

  <button type="submit">Generate RAMS PDF</button>
</form>

</body>
</html>
"""

@app.post("/generate")
def generate(
    company: str = Form(""),
    job_title: str = Form(""),
    location: str = Form(""),
    job_date: str = Form(""),
    workers: str = Form(""),
    supervisor: str = Form(""),
    method_steps: str = Form(""),
    hazards: str = Form(""),
):
    data = {
        "company": company,
        "job_title": job_title,
        "location": location,
        "job_date": job_date,
        "workers": workers,
        "supervisor": supervisor,
        "method_steps": method_steps,
        "hazards": hazards,
    }

    pdf = build_pdf(data)
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=RAMS.pdf"}
    )
