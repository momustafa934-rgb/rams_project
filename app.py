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
    "Disclaimer: This RAMS document is generated for guidance only and does not constitute legal advice. "
    "The contractor/company is responsible for reviewing, amending, and ensuring the RAMS is suitable for the "
    "specific job, site rules, client requirements, and UK legislation before use."
)

UK_NOTES = (
    "Typical UK context (review for your job): Health & Safety at Work etc. Act 1974, "
    "Management of Health and Safety at Work Regulations 1999, "
    "Personal Protective Equipment at Work Regulations 2022, "
    "COSHH 2002 (if chemicals), Work at Height Regulations 2005 (if applicable)."
)

def _lines(text: str):
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

def _parse_hazards(text: str):
    """
    Format (one per line):
      Hazard | Who might be harmed | Controls
    Example:
      Slips/trips | Staff & public | Keep area tidy; cable mats; signage
    If user enters plain lines, we auto-fill columns.
    """
    rows = []
    for ln in _lines(text):
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) >= 3:
            rows.append(parts[:3])
        elif len(parts) == 2:
            rows.append([parts[0], parts[1], "Review and add suitable controls for this site/task."])
        else:
            rows.append([ln, "Workers/others", "Review and add suitable controls for this site/task."])
    return rows

def build_pdf(data: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=36, rightMargin=36,
        topMargin=36, bottomMargin=36
    )
    styles = getSampleStyleSheet()
    story = []

    title = f"RAMS – Risk Assessment & Method Statement"
    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 10))

    # --- Job details table ---
    job_rows = [
        ["Company", data["company"]],
        ["Job title", data["job_title"]],
        ["Location", data["location"]],
        ["Date", data["job_date"]],
        ["No. of workers", data["workers"]],
        ["Supervisor / Responsible person", data["supervisor"]],
        ["Client / Site contact (optional)", data["site_contact"]],
    ]
    t = Table([["Job Details", ""]] + job_rows, colWidths=[160, 340])
    t.setStyle(TableStyle([
        ("SPAN", (0,0), (1,0)),
        ("BACKGROUND", (0,0), (1,0), colors.black),
        ("TEXTCOLOR", (0,0), (1,0), colors.white),
        ("FONTNAME", (0,0), (1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("GRID", (0,0), (1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (1,-1), "TOP"),
        ("PADDING", (0,0), (1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # --- Scope / description ---
    story.append(Paragraph("<b>Scope of Works / Description</b>", styles["Heading2"]))
    story.append(Paragraph(data["description"] or "N/A", styles["BodyText"]))
    story.append(Spacer(1, 10))

    # --- PPE / Equipment ---
    story.append(Paragraph("<b>PPE Required</b>", styles["Heading2"]))
    story.append(Paragraph(data["ppe"] or "Safety boots, gloves, eye protection (edit as required).", styles["BodyText"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Tools / Equipment / Materials</b>", styles["Heading2"]))
    story.append(Paragraph(data["equipment"] or "N/A", styles["BodyText"]))
    story.append(Spacer(1, 12))

    # --- Method statement steps ---
    story.append(Paragraph("<b>Method Statement (How the work will be done safely)</b>", styles["Heading2"]))
    steps = _lines(data["method_steps"])
    if not steps:
        steps = [
            "Arrive on site, sign in, review site rules, emergency arrangements, and permits (if required).",
            "Complete a site-specific check: access/egress, work area condition, nearby hazards and public interface.",
            "Set up work area: barriers/signage if needed; keep walkways clear; maintain good housekeeping.",
            "Inspect tools/equipment before use; do not use damaged equipment; follow manufacturer instructions.",
            "Carry out the work as described, communicate with others on site, and manage waste safely.",
            "Leave area clean, remove barriers when safe, sign out, and report any incidents/near misses."
        ]
    for i, s in enumerate(steps, start=1):
        story.append(Paragraph(f"{i}. {s}", styles["BodyText"]))
    story.append(Spacer(1, 12))

    # --- Risk assessment table ---
    story.append(Paragraph("<b>Risk Assessment (Hazards & Control Measures)</b>", styles["Heading2"]))
    hazard_rows = _parse_hazards(data["hazards"])
    if not hazard_rows:
        hazard_rows = [
            ["Slips/trips/falls", "Workers / others", "Good housekeeping; clear walkways; suitable footwear; signage if needed."],
            ["Manual handling", "Workers", "Use safe lifting technique; team lift; use trolleys; avoid overloading."],
            ["Tools/equipment", "Workers", "Pre-use checks; correct tool for job; PPE; trained/competent users."],
            ["Electric shock (if applicable)", "Workers / others", "Isolate where required; competent person; test equipment; keep area dry."],
            ["Working at height (if applicable)", "Workers / others", "Suitable access equipment; secure footing; do not overreach; exclusion zone below."],
        ]

    ra_table = Table(
        [["Hazard", "Who might be harmed", "Controls / precautions"]] + hazard_rows,
        colWidths=[140, 140, 220]
    )
    ra_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (2,0), colors.black),
        ("TEXTCOLOR", (0,0), (2,0), colors.white),
        ("FONTNAME", (0,0), (2,0), "Helvetica-Bold"),
        ("GRID", (0,0), (2,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (2,-1), "TOP"),
        ("PADDING", (0,0), (2,-1), 6),
    ]))
    story.append(ra_table)
    story.append(Spacer(1, 12))

    # --- Emergency info ---
    story.append(Paragraph("<b>Emergency Arrangements</b>", styles["Heading2"]))
    emergency = data["emergency"] or "Follow site/client emergency plan. Call 999 in an emergency. Identify assembly point and first aid arrangements."
    story.append(Paragraph(emergency, styles["BodyText"]))
    story.append(Spacer(1, 10))

    # --- Compliance notes + disclaimer ---
    story.append(Paragraph("<b>Compliance Notes</b>", styles["Heading2"]))
    story.append(Paragraph(UK_NOTES, styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Disclaimer</b>", styles["Heading2"]))
    story.append(Paragraph(DISCLAIMER, styles["BodyText"]))
    story.append(Spacer(1, 12))

    # --- Sign-off (basic) ---
    sign = Table([
        ["Sign-off", ""],
        ["Prepared by (name)", data["prepared_by"]],
        ["Signature", "______________________________"],
        ["Date", data["job_date"]],
        ["Reviewed by (client/site)", "______________________________"],
    ], colWidths=[160, 340])
    sign.setStyle(TableStyle([
        ("SPAN", (0,0), (1,0)),
        ("BACKGROUND", (0,0), (1,0), colors.black),
        ("TEXTCOLOR", (0,0), (1,0), colors.white),
        ("FONTNAME", (0,0), (1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("GRID", (0,0), (1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (1,-1), "TOP"),
        ("PADDING", (0,0), (1,-1), 6),
    ]))
    story.append(sign)

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
  <title>RAMS Generator</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 30px; max-width: 900px; }}
    input, textarea {{ width: 100%; padding: 10px; margin: 6px 0 16px; }}
    label {{ font-weight: bold; }}
    button {{ padding: 12px 16px; font-weight: bold; cursor: pointer; }}
    .row {{ display:flex; gap:12px; }}
    .col {{ flex:1; }}
    .hint {{ font-size: 0.95em; color:#444; }}
    code {{ background:#f2f2f2; padding:2px 6px; }}
  </style>
</head>
<body>
  <h1>RAMS Generator (Business-ready MVP)</h1>
  <p class="hint">
    Tip: For hazards use format <code>Hazard | Who might be harmed | Controls</code> (one per line).
  </p>

  <form method="post" action="/generate">
    <label>Company</label>
    <input name="company" placeholder="e.g., Costa Coffee Ltd" required>

    <label>Job title</label>
    <input name="job_title" placeholder="e.g., Replace lighting in office" required>

    <div class="row">
      <div class="col">
        <label>Location</label>
        <input name="location" placeholder="e.g., Milton Keynes" required>
      </div>
      <div class="col">
        <label>Date</label>
        <input name="job_date" value="{today}">
      </div>
      <div class="col">
        <label>Workers</label>
        <input name="workers" placeholder="e.g., 2">
      </div>
    </div>

    <div class="row">
      <div class="col">
        <label>Supervisor / Responsible person</label>
        <input name="supervisor" placeholder="e.g., J. Smith">
      </div>
      <div class="col">
        <label>Client / Site contact (optional)</label>
        <input name="site_contact" placeholder="e.g., Site manager name">
      </div>
    </div>

    <label>Scope / Description</label>
    <textarea name="description" rows="4" placeholder="Describe the work clearly..."></textarea>

    <label>PPE required</label>
    <input name="ppe" placeholder="e.g., Safety boots, gloves, eye protection, hi-vis">

    <label>Tools / Equipment / Materials</label>
    <textarea name="equipment" rows="3" placeholder="e.g., Step ladder, cordless drill, cable ties..."></textarea>

    <label>Method steps (one per line)</label>
    <textarea name="method_steps" rows="6" placeholder="Arrive and sign in...&#10;Set up work area..."></textarea>

    <label>Hazards (one per line: Hazard | Who | Controls)</label>
    <textarea name="hazards" rows="6" placeholder="Slips/trips | Workers/public | Keep area tidy; signage&#10;Manual handling | Workers | Use trolleys; team lift"></textarea>

    <label>Emergency arrangements (site specific if known)</label>
    <textarea name="emergency" rows="3" placeholder="Assembly point: ... First aid: ... Nearest A&E: ..."></textarea>

    <div class="row">
      <div class="col">
        <label>Prepared by (name)</label>
        <input name="prepared_by" placeholder="Your name / company rep">
      </div>
    </div>

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
    site_contact: str = Form(""),
    description: str = Form(""),
    ppe: str = Form(""),
    equipment: str = Form(""),
    method_steps: str = Form(""),
    hazards: str = Form(""),
    emergency: str = Form(""),
    prepared_by: str = Form(""),
):
    data = dict(
        company=company.strip(),
        job_title=job_title.strip(),
        location=location.strip(),
        job_date=(job_date.strip() or date.today().isoformat()),
        workers=workers.strip() or "N/A",
        supervisor=supervisor.strip() or "N/A",
        site_contact=site_contact.strip() or "N/A",
        description=description.strip(),
        ppe=ppe.strip(),
        equipment=equipment.strip(),
        method_steps=method_steps.strip(),
        hazards=hazards.strip(),
        emergency=emergency.strip(),
        prepared_by=prepared_by.strip() or "N/A",
    )

    pdf = build_pdf(data)
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="RAMS.pdf"'}
    )
