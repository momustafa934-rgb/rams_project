from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from io import BytesIO
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

app = FastAPI()

DISCLAIMER = (
    "This Risk Assessment & Method Statement (RAMS) document has been generated for guidance purposes only. "
    "It does not constitute legal advice. The contractor/company is responsible for reviewing, amending, and "
    "ensuring the document is suitable for the specific task, site conditions, client requirements, and "
    "current UK health and safety legislation before use."
)

UK_COMPLIANCE = (
    "This RAMS has been prepared with reference to relevant UK legislation including, but not limited to: "
    "The Health and Safety at Work etc. Act 1974, Management of Health and Safety at Work Regulations 1999, "
    "Personal Protective Equipment at Work Regulations 2022, COSHH Regulations 2002 (where applicable), "
    "and the Work at Height Regulations 2005 (where applicable)."
)

def _lines(text: str):
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

def build_pdf(data: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    story = []

    # TITLE
    story.append(Paragraph("<b>RISK ASSESSMENT & METHOD STATEMENT (RAMS)</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    # JOB DETAILS TABLE
    details = [
        ["Company Name", data["company"]],
        ["Job Title / Description", data["job_title"]],
        ["Site Location", data["location"]],
        ["Date", data["job_date"]],
        ["Number of Workers", data["workers"]],
        ["Supervisor / Responsible Person", data["supervisor"]],
    ]

    table = Table([["Project Details", ""]] + details, colWidths=[180, 320])
    table.setStyle(TableStyle([
        ("SPAN", (0,0), (1,0)),
        ("BACKGROUND", (0,0), (1,0), colors.black),
        ("TEXTCOLOR", (0,0), (1,0), colors.white),
        ("FONTNAME", (0,0), (1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("PADDING", (0,0), (1,-1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 14))

    # SCOPE OF WORKS
    story.append(Paragraph("<b>Scope of Works</b>", styles["Heading2"]))
    story.append(Paragraph(
        "The works covered by this RAMS include the completion of the described task in a controlled and "
        "safe manner, ensuring risks to workers, site personnel, and the public are minimised at all times.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 10))

    # PPE
    story.append(Paragraph("<b>Personal Protective Equipment (PPE)</b>", styles["Heading2"]))
    story.append(Paragraph(
        "As a minimum, operatives shall wear suitable PPE appropriate to the task, including safety footwear, "
        "gloves, high-visibility clothing, and eye protection. Additional PPE shall be used where required "
        "by site rules or specific hazards.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 10))

    # TOOLS
    story.append(Paragraph("<b>Tools, Equipment & Materials</b>", styles["Heading2"]))
    story.append(Paragraph(
        "All tools and equipment used shall be suitable for purpose, in good condition, and subject to "
        "pre-use checks. Defective equipment must not be used and shall be removed from service immediately.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 10))

    # METHOD STATEMENT
    story.append(Paragraph("<b>Method Statement</b>", styles["Heading2"]))
    steps = _lines(data["method_steps"]) or [
        "Arrive on site and sign in accordance with site procedures.",
        "Review site-specific rules, emergency arrangements, and relevant permits.",
        "Inspect the work area and implement barriers or signage where required.",
        "Carry out the task using safe systems of work and appropriate PPE.",
        "Maintain good housekeeping throughout the works.",
        "Complete works, clear the area, and sign out of site."
    ]

    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"{i}. {step}", styles["BodyText"]))

    story.append(Spacer(1, 12))

    # RISK ASSESSMENT
    story.append(Paragraph("<b>Risk Assessment</b>", styles["Heading2"]))
    hazards = _lines(data["hazards"]) or [
        "Slips, trips and falls | Operatives / others | Maintain good housekeeping and clear access routes.",
        "Manual handling | Operatives | Use correct lifting techniques and mechanical aids where required.",
        "Use of tools and equipment | Operatives | Pre-use checks, correct training, and PPE.",
    ]

    rows = [["Hazard", "Who May Be Harmed", "Control Measures"]]
    for h in hazards:
        parts = [p.strip() for p in h.split("|")]
        while len(parts) < 3:
            parts.append("Controls to be reviewed and implemented as appropriate.")
        rows.append(parts[:3])

    ra_table = Table(rows, colWidths=[160, 140, 200])
    ra_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.black),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(ra_table)
    story.append(Spacer(1, 12))

    # EMERGENCY
    story.append(Paragraph("<b>Emergency Arrangements</b>", styles["Heading2"]))
    story.append(Paragraph(
        "In the event of an emergency, all operatives shall follow site emergency procedures. "
        "First aid facilities and trained first aiders shall be identified prior to works commencing. "
        "All accidents, incidents, or near misses must be reported immediately.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 10))

    # COMPLIANCE
    story.append(Paragraph("<b>Legal Compliance</b>", styles["Heading2"]))
    story.append(Paragraph(UK_COMPLIANCE, styles["BodyText"]))
    story.append(Spacer(1, 10))

    # DISCLAIMER
    story.append(Paragraph("<b>Disclaimer</b>", styles["Heading2"]))
    story.append(Paragraph(DISCLAIMER, styles["BodyText"]))
    story.append(Spacer(1, 14))

    # SIGN OFF
    sign = Table([
        ["Prepared By", data["supervisor"]],
        ["Signature", "____________________________"],
        ["Date", data["job_date"]],
    ], colWidths=[200, 300])
    sign.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("PADDING", (0,0), (-1,-1), 6),
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
<title>QuickRAMS</title>
<style>
body {{ font-family: Arial; max-width: 900px; margin: 40px auto; }}
input, textarea {{ width: 100%; padding: 10px; margin-bottom: 14px; }}
button {{ padding: 12px 18px; font-weight: bold; }}
.note {{ font-size: 0.95em; color: #444; }}
</style>
</head>
<body>

<h1>QuickRAMS</h1>

<p>
<a href="https://buy.stripe.com/4gM6oJda49hP9Ie8kh7Zu00" target="_blank">
<strong>Pay £35 to generate a professional RAMS (one-off)</strong>
</a>
</p>

<p class="note">
£35 covers the generation of one RAMS document. A new payment is required for each additional RAMS.
</p>

<label><input type="checkbox" id="paidCheck"> I confirm I have paid £35</label><br><br>

<form method="post" action="/generate">
<input name="company" placeholder="Company name" required>
<input name="job_title" placeholder="Job title / description" required>
<input name="location" placeholder="Site location" required>
<input name="job_date" value="{today}">
<input name="workers" placeholder="Number of workers">
<input name="supervisor" placeholder="Supervisor / responsible person">
<textarea name="method_steps" rows="5" placeholder="Method steps (one per line)"></textarea>
<textarea name="hazards" rows="5" placeholder="Hazards | Who | Controls (one per line)"></textarea>

<button type="submit" id="generateBtn" disabled>Generate RAMS PDF</button>
</form>

<script>
const c=document.getElementById("paidCheck");
const b=document.getElementById("generateBtn");
c.addEventListener("change",()=>{{b.disabled=!c.checked;}});
</script>

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
    pdf = build_pdf(locals())
    return StreamingResponse(BytesIO(pdf), media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=RAMS.pdf"})
