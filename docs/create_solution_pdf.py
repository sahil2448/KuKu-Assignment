from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether, Preformatted,
)

OUT = Path(__file__).with_name("Kuku_Problem1_Solution_Draft.pdf")
NAVY = colors.HexColor("#16243A")
BLUE = colors.HexColor("#1D6E8A")
TEAL = colors.HexColor("#DDF2F0")
PALE = colors.HexColor("#F2F5F8")
INK = colors.HexColor("#202B38")
MUTED = colors.HexColor("#5C6B7A")
AMBER = colors.HexColor("#FFF1D6")
WHITE = colors.white

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=25, textColor=NAVY, alignment=TA_LEFT, spaceAfter=4))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontName="Helvetica", fontSize=9.2, leading=13, textColor=BLUE))
styles.add(ParagraphStyle(name="H1x", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=NAVY, spaceBefore=7, spaceAfter=5))
styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=9.3, leading=11, textColor=BLUE, spaceBefore=4, spaceAfter=3))
styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.5, leading=11.3, textColor=INK, spaceAfter=4))
styles.add(ParagraphStyle(name="Smallx", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.3, leading=9.2, textColor=MUTED, spaceAfter=2))
styles.add(ParagraphStyle(name="Cellx", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.5, leading=9.5, textColor=INK))
styles.add(ParagraphStyle(name="CellBold", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.5, leading=9.5, textColor=NAVY))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10.5, textColor=colors.HexColor("#7A4B00")))
styles.add(ParagraphStyle(name="CodeX", parent=styles["Code"], fontName="Courier", fontSize=7.4, leading=9, textColor=INK, backColor=PALE, borderPadding=6))
styles.add(ParagraphStyle(name="Stat", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=18, leading=20, textColor=NAVY, alignment=TA_CENTER))


def P(text, style="Bodyx"):
    return Paragraph(text, styles[style])


def header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 34*mm, w, 34*mm, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, h - 35*mm, w, 1.2*mm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(WHITE)
    canvas.drawString(17*mm, h - 13*mm, "KUKU  |  PROBLEM 1: FIND THE PROMOS")
    canvas.setStrokeColor(colors.HexColor("#D7DEE6"))
    canvas.line(17*mm, 14*mm, w - 17*mm, 14*mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(17*mm, 9*mm, "Working draft - complete the AI-run and human-review fields before submission")
    canvas.drawRightString(w - 17*mm, 9*mm, f"Page {doc.page} of 2")
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    rightMargin=17*mm, leftMargin=17*mm,
    topMargin=40*mm, bottomMargin=19*mm,
    title="Kuku AI Generalist Assignment - Problem 1",
    author="",
)
story = []

# Page 1 - cover and solution
story.append(Spacer(1, -2*mm))
story.append(P("AI PROMO FINDER", "CoverTitle"))
story.append(P("Kuku AI Generalist Assignment | Problem 1: Find the Promos", "CoverSub"))
story.append(Spacer(1, 3*mm))
story.append(P("Candidate: [Your name]  |  Roll number: [Your roll number]  |  Branch: [Your branch]", "Smallx"))
story.append(P("<b>Problem framing</b>", "H1x"))
story.append(P(
    "Kuku editors currently inspect episodes manually to find 20-60 second promotional moments. "
    "This prototype reads the supplied timestamped screenplays and recommends moments that aim to "
    "(1) hook viewers in the first three seconds, (2) end on an unresolved beat, and (3) provide enough "
    "context for someone who has not watched the show.", "Bodyx"))

# Audit strip
stats = [
    [P("50", "Stat"), P("100", "Stat"), P("3,727", "Stat"), P("123.25s", "Stat")],
    [P("episodes", "Smallx"), P("scenes", "Smallx"), P("timed blocks", "Smallx"), P("average duration", "Smallx")],
]
t = Table(stats, colWidths=[42*mm, 42*mm, 48*mm, 49*mm], rowHeights=[11*mm, 7*mm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), PALE),
    ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#D7DEE6")),
    ("INNERGRID", (0,0), (-1,-1), 0.35, colors.HexColor("#D7DEE6")),
    ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
]))
story.append(t)
story.append(P("<b>Input audit:</b> all 50 files parsed; 1,754 camera, 1,487 dialogue, 372 action and 114 sound-effect blocks. Episode durations range from 70.50 to 200.75 seconds.", "Smallx"))

story.append(P("How the prototype works", "H1x"))
flow_data = [
    [P("1. Parse", "CellBold"), P("2. Understand", "CellBold"), P("3. Validate", "CellBold"), P("4. Rank", "CellBold")],
    [P("Read ZIP; extract episode, logline, continuity, scene and timed event data.", "Cellx"),
     P("The OpenRouter-selected language model reviews each episode and proposes candidate moments with hook, ending, explanation and evidence.", "Cellx"),
     P("Python checks duration, episode bounds, timestamp anchors and whether evidence occurs near the hook/end.", "Cellx"),
     P("Calculate a weighted score; deduplicate overlapping suggestions; export JSON and CSV.", "Cellx")]
]
flow = Table(flow_data, colWidths=[44*mm, 55*mm, 55*mm, 37*mm])
flow.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), TEAL),
    ("BACKGROUND", (0,1), (-1,1), colors.white),
    ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD7E1")),
    ("INNERGRID", (0,0), (-1,-1), 0.35, colors.HexColor("#CBD7E1")),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(flow)
story.append(P("Separation of responsibilities", "H2x"))
story.append(P("<b>AI:</b> semantic judgments about the dramatic hook, unresolved ending, standalone clarity and emotional potential. &nbsp; <b>Python:</b> file parsing, timestamp and duration checks, evidence checks, score calculation, ranking, deduplication and exports.", "Bodyx"))
story.append(P("Assumptions and outputs", "H2x"))
story.append(P("The first version recommends up to three continuous promo windows per episode. It does not attempt to stitch multiple excerpts together. The output includes the episode, exact start/end, total duration, hook, cliffhanger, reason, four scores, weighted score, evidence and validation warnings. The files are `promos.json`, `promos.csv`, a run report, an editor review template and per-episode raw model responses.", "Bodyx"))

# Page 2
story.append(PageBreak())
story.append(P("Scoring, quality checks and limitations", "H1x"))
score_data = [
    [P("Dimension", "CellBold"), P("Weight", "CellBold"), P("Question asked", "CellBold")],
    [P("Hook", "Cellx"), P("30%", "CellBold"), P("Does something attention-grabbing happen in the first three seconds?", "Cellx")],
    [P("Cliffhanger", "Cellx"), P("30%", "CellBold"), P("Does the clip stop before the question/conflict is resolved?", "Cellx")],
    [P("Standalone clarity", "Cellx"), P("25%", "CellBold"), P("Can a new viewer understand the situation without prior episodes?", "Cellx")],
    [P("Emotional intensity", "Cellx"), P("15%", "CellBold"), P("Does the scene create suspense, anger, surprise or emotion?", "Cellx")],
]
score_table = Table(score_data, colWidths=[40*mm, 20*mm, 131*mm], repeatRows=1)
score_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), TEAL),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, PALE]),
    ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD7E1")),
    ("INNERGRID", (0,0), (-1,-1), 0.3, colors.HexColor("#CBD7E1")),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
]))
story.append(score_table)
story.append(Spacer(1, 2*mm))
story.append(P("The weighted score is calculated in code: (30 x hook + 30 x cliffhanger + 25 x clarity + 15 x emotion) / 5. These weights are initial assumptions, not a proven measure of social-media performance.", "Bodyx"))

story.append(P("Quality checks", "H2x"))
story.append(P("The pipeline rejects clips outside 20-60 seconds or beyond the episode duration. It flags timestamps that do not align with a screenplay event/scene boundary, checks whether the hook evidence occurs in the first three seconds and whether the ending evidence appears near the end, and stores the original model response separately. The top recommendations must still be compared with the actual videos by a human editor.", "Bodyx"))

story.append(P("Limitations and human review", "H2x"))
story.append(P("A screenplay cannot verify acting quality, visual readability, pacing, music, shot composition or the final edit. Version 1 recommends one continuous segment per promo; multi-segment and cross-episode montages are a planned extension. The score is a ranking aid, not a guarantee that a clip will perform well. An offline keyword-based baseline is included for testing, but it is not used as a substitute for model editorial reasoning.", "Bodyx"))

story.append(P("Scale and model flexibility", "H2x"))
story.append(P("The prototype makes one model request per episode, saves per-episode checkpoints, records API errors and supports checkpoint-based resume, and combines candidates into one ranked list. The model name is configurable through an environment setting, while parsing and validation remain independent of the model provider. For a production workflow, the editor should approve or reject candidates and those decisions can later be used to tune scoring.", "Bodyx"))

story.append(P("Tools used and observed failure", "H2x"))
story.append(P("<b>Tools:</b> Python for the parser, validation, ranking and outputs; OpenRouter API is integrated for screenplay understanding; ChatGPT was used as a coding/design assistant. <b>Before submission:</b> run OpenRouter AI mode and add one real example where the model chose a weak promo or gave unsupported evidence, quoting the episode/timestamp and explaining how the human review caught it. Do not invent this example. The offline baseline itself can overrate a dramatic line that is not a true cliffhanger. <b>Data handling:</b> do not publish the screenplay pack; check the model provider's data-use terms before sending confidential scripts.", "Bodyx"))

story.append(P("Run it", "H2x"))
code = "python -m kukupromo --input \"data/your-screenplays.zip\" --mode ai --out \"outputs/ai_full\""
story.append(Preformatted(code, styles["CodeX"]))
story.append(Spacer(1, 2*mm))
story.append(P("Submission note: replace the candidate identity fields, run a real OpenRouter pass on the full 50-episode pack, inspect the top recommendations against the episode videos, and update the AI-failure example before submitting.", "Callout"))

doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
print(OUT)
