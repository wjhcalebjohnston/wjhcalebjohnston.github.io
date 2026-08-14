"""Build the seven public, one-page research briefs for caleb-johnston.com.

The source papers remain outside the public repository. This file intentionally
contains only public-safe summaries, publication boundaries, and the reusable
visual system used by every brief.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import KeepInFrame, Paragraph, Spacer
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
OUT.mkdir(parents=True, exist_ok=True)

FONT_DIR = Path("/System/Library/Fonts/Supplemental")
pdfmetrics.registerFont(TTFont("CJArial", str(FONT_DIR / "Arial.ttf")))
pdfmetrics.registerFont(TTFont("CJArialBold", str(FONT_DIR / "Arial Bold.ttf")))
pdfmetrics.registerFont(TTFont("CJTimes", str(FONT_DIR / "Times New Roman.ttf")))
pdfmetrics.registerFont(TTFont("CJTimesBold", str(FONT_DIR / "Times New Roman Bold.ttf")))
pdfmetrics.registerFont(TTFont("CJTimesBoldItalic", str(FONT_DIR / "Times New Roman Bold Italic.ttf")))

NAVY = colors.HexColor("#0E2A47")
NAVY_DARK = colors.HexColor("#071A2B")
GOLD = colors.HexColor("#A47C38")
GOLD_LIGHT = colors.HexColor("#E4CC9C")
IVORY = colors.HexColor("#F7F3EA")
CREAM = colors.HexColor("#FCFAF6")
INK = colors.HexColor("#202C36")
SLATE = colors.HexColor("#536575")
LINE = colors.HexColor("#D8D6CF")
PALE_BLUE = colors.HexColor("#E8EEF3")
WHITE = colors.white


def ascii_dashes(text: str) -> str:
    """Normalize all dash characters to the PDF-safe ASCII hyphen."""
    for char in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        text = text.replace(char, " - ")
    return " ".join(text.split())


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(ascii_dashes(text)), style)


EYEBROW = ParagraphStyle(
    "Eyebrow",
    fontName="CJArialBold",
    fontSize=7.6,
    leading=9,
    textColor=GOLD,
    spaceAfter=4,
    tracking=0.9,
)
SECTION = ParagraphStyle(
    "Section",
    fontName="CJArialBold",
    fontSize=8.1,
    leading=9.8,
    textColor=NAVY,
    spaceAfter=3,
    tracking=0.35,
)
BODY = ParagraphStyle(
    "Body",
    fontName="CJArial",
    fontSize=8.45,
    leading=11.05,
    textColor=INK,
    spaceAfter=3,
)
BULLET = ParagraphStyle(
    "Bullet",
    parent=BODY,
    leftIndent=10,
    firstLineIndent=-7,
    bulletIndent=0,
    fontSize=8.15,
    leading=10.55,
    spaceAfter=2,
)
OVERVIEW = ParagraphStyle(
    "Overview",
    fontName="CJTimesBoldItalic",
    fontSize=10.6,
    leading=13.2,
    textColor=NAVY,
)
NOTE = ParagraphStyle(
    "Note",
    fontName="CJArial",
    fontSize=7.55,
    leading=9.6,
    textColor=SLATE,
)
META = ParagraphStyle(
    "Meta",
    fontName="CJArial",
    fontSize=8.7,
    leading=10.5,
    textColor=GOLD_LIGHT,
)


@dataclass(frozen=True)
class Section:
    heading: str
    body: str = ""
    bullets: tuple[str, ...] = ()


@dataclass(frozen=True)
class Brief:
    filename: str
    category: str
    title: str
    metadata: str
    overview: str
    left: tuple[Section, ...]
    right: tuple[Section, ...]
    note: str
    subject: str


def title_style(title_text: str) -> ParagraphStyle:
    if len(title_text) > 118:
        size, leading = 17.0, 18.6
    elif len(title_text) > 88:
        size, leading = 18.6, 20.3
    else:
        size, leading = 21.5, 23.0
    return ParagraphStyle(
        "Title",
        fontName="CJTimesBold",
        fontSize=size,
        leading=leading,
        textColor=WHITE,
        alignment=TA_LEFT,
    )


def draw_paragraph(c, item: Paragraph, x: float, top: float, width: float, max_height: float = 1000) -> float:
    _, height = item.wrap(width, max_height)
    item.drawOn(c, x, top - height)
    return top - height


def section_flow(sections: tuple[Section, ...]):
    flow = []
    for index, item in enumerate(sections):
        if index:
            flow.append(Spacer(1, 10))
        flow.append(paragraph(item.heading.upper(), EYEBROW))
        if item.body:
            flow.append(paragraph(item.body, BODY))
        for bullet_text in item.bullets:
            flow.append(Paragraph("<bullet>&#8226;</bullet>" + escape(ascii_dashes(bullet_text)), BULLET))
    return flow


def draw_column(c, x: float, top: float, width: float, height: float, sections: tuple[Section, ...]):
    c.setFillColor(WHITE)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.65)
    c.roundRect(x, top - height, width, height, 10, stroke=1, fill=1)
    frame = KeepInFrame(width - 28, height - 28, section_flow(sections), mode="shrink")
    _, used_height = frame.wrapOn(c, width - 28, height - 28)
    frame.drawOn(c, x + 14, top - 14 - used_height)


def build_brief(brief: Brief):
    path = OUT / brief.filename
    c = pdfcanvas.Canvas(str(path), pagesize=letter, pageCompression=1)
    c.setTitle(brief.title)
    c.setAuthor("Caleb Johnston")
    c.setSubject(brief.subject)
    c.setKeywords("Caleb Johnston, research portfolio, public policy, selected research brief")

    page_w, page_h = letter
    c.setFillColor(CREAM)
    c.rect(0, 0, page_w, page_h, stroke=0, fill=1)

    # Branded header.
    header_bottom = 617
    c.setFillColor(NAVY_DARK)
    c.rect(0, header_bottom, page_w, page_h - header_bottom, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.rect(0, page_h - 8, page_w, 8, stroke=0, fill=1)
    c.setFont("CJArialBold", 7.6)
    c.setFillColor(GOLD_LIGHT)
    c.drawString(42, 758, ascii_dashes(brief.category.upper()))
    c.setFillColor(colors.HexColor("#C6D2DB"))
    c.drawRightString(570, 758, "SELECTED RESEARCH BRIEF")

    title_p = paragraph(brief.title, title_style(brief.title))
    draw_paragraph(c, title_p, 42, 744, 528, 92)
    meta_p = paragraph(brief.metadata, META)
    draw_paragraph(c, meta_p, 42, 646, 528, 28)

    # Overview callout.
    c.setFillColor(IVORY)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.7)
    c.roundRect(42, 529, 528, 67, 8, stroke=1, fill=1)
    c.setFillColor(GOLD)
    c.roundRect(42, 529, 5, 67, 2.5, stroke=0, fill=1)
    overview_p = paragraph(brief.overview, OVERVIEW)
    draw_paragraph(c, overview_p, 59, 579, 493, 46)

    # Two-column content grid.
    draw_column(c, 42, 510, 254, 389, brief.left)
    draw_column(c, 316, 510, 254, 389, brief.right)

    # Publication/status note.
    c.setFillColor(PALE_BLUE)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.65)
    c.roundRect(42, 64, 528, 43, 7, stroke=1, fill=1)
    c.setFont("CJArialBold", 7.6)
    c.setFillColor(NAVY)
    c.drawString(54, 92, "PORTFOLIO NOTE")
    note_p = paragraph(brief.note, NOTE)
    draw_paragraph(c, note_p, 136, 98, 420, 28)

    # Footer and live links.
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.7)
    c.line(42, 47, 570, 47)
    c.setFont("CJArial", 7.4)
    c.setFillColor(SLATE)
    c.drawString(42, 31, "Caleb Johnston")
    c.drawString(119, 31, "caleb-johnston.com")
    c.drawString(223, 31, "contact@caleb-johnston.com")
    c.drawRightString(570, 31, "ONE-PAGE BRIEF  |  1")
    c.linkURL("https://caleb-johnston.com", (117, 25, 216, 39), relative=0)
    c.linkURL("mailto:contact@caleb-johnston.com", (221, 25, 365, 39), relative=0)

    c.showPage()
    c.save()

    # ReportLab preserves selectable text and links; add the document language
    # explicitly so assistive technology does not need to guess it.
    reader = PdfReader(str(path))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.root_object[NameObject("/Lang")] = TextStringObject("en-US")
    temp_path = path.with_suffix(".tmp.pdf")
    with temp_path.open("wb") as stream:
        writer.write(stream)
    temp_path.replace(path)


BRIEFS = (
    Brief(
        filename="caleb-johnston-capstone-brief.pdf",
        category="Qualitative research | Reentry governance | 2026",
        title="Our Sacred Space: Governance of Reentry at Georgetown's Prisons and Justice Initiative",
        metadata="59 pages | Georgetown University | July 2026",
        overview="A case study of PJI - the organization where I was working while conducting the research - examining how frontline discretion shapes reentry governance in practice.",
        left=(
            Section(
                "Question and case",
                "How do PJI's frontline practices interrupt, soften, or reproduce punitive governance? The paper treats PJI as a single organizational case and does not claim to represent every reentry provider.",
            ),
            Section(
                "Evidence and approach",
                "Nine recorded interviews, 15 weekly field journals, six months of participant observation, and documentary evidence were triangulated with an explicit positionality analysis and no causal claims.",
            ),
            Section(
                "Learning from inside",
                "Working inside PJI made it possible to pair formal evidence with sustained observation of day-to-day governance. This methodological thinking was influenced in part by Richard Fenno's emphasis in Home Style on learning through presence, observation, and informal interaction; it was not a replication of Fenno's congressional research.",
            ),
        ),
        right=(
            Section(
                "Analytical contribution",
                "The paper develops a three-regime framework: domains an intermediary controls, domains that govern through it, and gatekeeping rules it authors itself. It treats translation across fragmented institutions as a form of governance.",
            ),
            Section(
                "Implications",
                bullets=(
                    "Make the location of discretion visible before prescribing more procedure.",
                    "Use selective structure - scenario-based onboarding, clear escalation paths, visible ownership, and feedback - to support judgment without bureaucratizing relational work.",
                ),
            ),
            Section(
                "Scope and limits",
                "The evidence is staff-weighted and drawn from one mission-driven organization. Corrections-side and currently incarcerated-student perspectives are incomplete, mechanisms are more visible than frequencies, and embedded research creates both access and positionality constraints.",
            ),
        ),
        note="The full paper contains interview, participant, and internal organizational material and remains private. This brief is the public-safe version.",
        subject="One-page public-safe brief for a qualitative case study of reentry governance",
    ),
    Brief(
        filename="caleb-johnston-public-safety-policy-brief.pdf",
        category="Policy analysis | Place-based safety | 2025",
        title="A Two-Tier Strategy for Public Safety around Banner Lane and Sursum Corda",
        metadata="10 pages | Georgetown University | October 2025 | Not commissioned by the D.C. Council",
        overview="An academic policy project pairing near-term environmental improvements with longer-term social investment, implementation ownership, and accountability.",
        left=(
            Section(
                "Problem",
                "Concentrated neighborhood safety concerns cannot be addressed through policing or redevelopment alone. The memo frames safety as both an immediate environmental challenge and a longer-term problem of opportunity, health, and community capacity.",
            ),
            Section(
                "Option analysis",
                "The paper compares the status quo, Crime Prevention Through Environmental Design alone, and a combined strategy using secondary evidence, place-based problem definition, implementation sequencing, and evaluation planning.",
            ),
            Section(
                "Recommendation",
                bullets=(
                    "Improve lighting, sightlines, maintenance, and greening.",
                    "Pair those measures with youth employment, treatment access, and community violence intervention.",
                ),
            ),
        ),
        right=(
            Section(
                "Implementation",
                "The proposed sequence assigns interagency ownership, creates a role for resident guidance, phases near- and longer-term actions, and uses public reporting to make progress and responsibility visible.",
            ),
            Section(
                "Evaluation and equity",
                bullets=(
                    "Track participation, safety indicators, delivery milestones, and unintended displacement effects.",
                    "Use independent evaluation and transparent reporting to support course correction.",
                ),
            ),
            Section(
                "Status and limits",
                "This is a proposed policy strategy, not an implemented intervention or an evaluation of observed Banner Lane outcomes. Local conditions and resident priorities would need current validation before use.",
            ),
        ),
        note="Coursework structured for a D.C. Council audience. It was not commissioned by, submitted to, or endorsed by the Council.",
        subject="One-page brief for an academic place-based public safety policy memo",
    ),
    Brief(
        filename="caleb-johnston-electoral-rhetoric-brief.pdf",
        category="Faculty-led research | U.S. elections | 2024",
        title="Winners and Losers: Electoral Rhetoric and Democratic Norms",
        metadata="Faculty-led research project | UT Austin (Department of Government) | August 2024",
        overview="A public account of my research-assistant contribution to a faculty-led project on how candidates communicate after electoral victory and defeat.",
        left=(
            Section(
                "Project context",
                "The broader project assembled structured evidence across U.S. presidential, congressional, and gubernatorial elections from 2000 through 2024. The research agenda, analysis, and eventual findings belong to the faculty-led project.",
            ),
            Section(
                "My role",
                bullets=(
                    "Built and quality-checked candidate-level election records.",
                    "Documented party, incumbency, vote share, margins, and winner or loser status.",
                    "Located and verified public victory and concession statements.",
                ),
            ),
            Section(
                "Coding contribution",
                "I coded approximately 100 statements for indicators including unity appeals, democratic legitimacy, fraud allegations, recounts, litigation, concession timing, and communication with opposing candidates.",
            ),
        ),
        right=(
            Section(
                "Research value",
                "The work turned dispersed election results, speeches, and news reporting into auditable research infrastructure with consistent definitions, source trails, and quality-control decisions.",
            ),
            Section(
                "Skills demonstrated",
                bullets=(
                    "Dataset construction and spreadsheet quality control",
                    "Election research, source verification, and qualitative coding",
                    "Documentation, deadline management, and confidentiality judgment",
                ),
            ),
            Section(
                "Ownership boundary",
                "This brief describes my contribution only. It does not claim ownership of the overall question or findings and does not release the project workbook, raw coding, or nonpublic research materials.",
            ),
        ),
        note="Unlike the six papers in this portfolio, this was a faculty-led research project; no standalone paper or page count is attributed to me.",
        subject="One-page brief describing a research assistant contribution to faculty-led elections research",
    ),
    Brief(
        filename="caleb-johnston-econometrics-brief.pdf",
        category="Quantitative analysis | Labor policy | 2024",
        title="Recreational Marijuana Legalization and Manufacturing Work Hours: A State-Level Econometric Analysis",
        metadata="15 pages | UT Austin (Department of Economics) | December 2024",
        overview="An exploratory 50-state analysis of whether recreational marijuana legalization is associated with average weekly payroll hours for manufacturing production employees.",
        left=(
            Section(
                "Question and data",
                "The project uses 2021 cross-sectional data for all 50 states. The outcome is sector-specific weekly manufacturing payroll hours - not productivity, employment, or work hours for all workers.",
            ),
            Section(
                "Model",
                "Ordinary least squares models include economic, demographic, education, health, and regional controls, along with diagnostic tests and a logged specification.",
            ),
            Section(
                "Observed association",
                "In the main specification, legalization status is associated with about 1.2 fewer weekly manufacturing payroll hours, holding selected controls constant. The estimate is statistically significant only at the 10 percent level; the logged model has the same direction.",
            ),
        ),
        right=(
            Section(
                "Interpretation",
                "The result is exploratory and does not establish that legalization changed work hours. A state-level cross-section can identify an association but cannot isolate policy timing or individual behavior.",
            ),
            Section(
                "Diagnostics",
                "The analysis does not detect heteroskedasticity, but multicollinearity and distributional concerns remain. Robustness checks help test specification sensitivity; they do not remove the design's structural limits.",
            ),
            Section(
                "Limitations",
                bullets=(
                    "Only 50 aggregate observations and a risk of ecological inference",
                    "Omitted confounders and a simplified binary policy measure",
                    "Pandemic-era data and no longitudinal or individual-level identification",
                ),
            ),
        ),
        note="Completed academic econometrics paper. The reported association is not presented as causal evidence.",
        subject="One-page brief for a state-level econometric analysis of marijuana policy and work hours",
    ),
    Brief(
        filename="caleb-johnston-identity-survey-design-brief.pdf",
        category="Research design | Political behavior | 2026",
        title="When Identity Becomes Political: Racial Identity Activation and Political Alignment Among Multiracial Americans",
        metadata="13 pages | Georgetown University | May 2026",
        overview="A proposed randomized survey experiment testing identity activation as a situational causal mechanism rather than treating multiracial identity only as a fixed demographic category.",
        left=(
            Section(
                "Question and theory",
                "Would temporarily activating different dimensions of racial identity change political attitudes among multiracial adults? Activation is distinguished from group membership, stable identity strength, and self-expression.",
            ),
            Section(
                "Competing hypotheses",
                bullets=(
                    "Minority solidarity",
                    "Assimilative alignment with dominant-group norms",
                    "An emergent multiracial political orientation",
                ),
            ),
            Section(
                "Proposed design",
                "The planned sample is 1,200 adults who identify as White and at least one non-White race, randomly assigned to a minority-identity prime, a White-identity prime, or a neutral control.",
            ),
        ),
        right=(
            Section(
                "Measures and analysis plan",
                "Planned outcomes include linked fate, group closeness, racial resentment, policy preferences, partisan identity, and affective evaluations. OLS with robust errors, standardized indices, balance and manipulation checks, covariates, and heterogeneous-effect tests would estimate treatment effects.",
            ),
            Section(
                "Theoretical contribution",
                "The design specifies identity activation as a testable causal mechanism and asks whether context changes the political meaning of multiple racial attachments.",
            ),
            Section(
                "Limits",
                "Prime strength and demand effects could threaten inference. A short treatment cannot establish durable real-world change, and the narrowed White and non-White multiracial sample limits generalizability.",
            ),
        ),
        note="Proposed design only. No respondents were recruited, no data were collected, and no empirical results are claimed.",
        subject="One-page brief for a proposed survey experiment on multiracial identity activation",
    ),
    Brief(
        filename="caleb-johnston-resident-power-brief.pdf",
        category="Nonviolent strategy | Resident power | 2025",
        title="Rebuilding Power from the Ground Up: A Nonviolent Strategy for Institutionalizing Resident Power in Sursum Corda",
        metadata="24 pages | Georgetown University | December 2025",
        overview="A conceptual movement strategy for converting resident legitimacy, coordination, culture, and documentation into durable influence over redevelopment and public-safety decisions.",
        left=(
            Section(
                "Movement goal",
                "Institutionalize resident authority beyond symbolic consultation by seeking transparent timelines, enforceable right-to-return commitments, and regular mechanisms for consequential resident input.",
            ),
            Section(
                "Power architecture",
                "Residents and returning families form the moral center; advocacy organizations, faith groups, legal clinics, and ANC representatives can amplify capacity; developers and city agencies hold formal authority but depend on legitimacy, procedural continuity, and limited scrutiny.",
            ),
            Section(
                "Strategic leverage",
                bullets=(
                    "Document the gap between public commitments and lived outcomes.",
                    "Build coalition and narrative power before escalating pressure.",
                    "Use targeted hearings, oversight, media, and public testimony rather than spectacle for its own sake.",
                ),
            ),
        ),
        right=(
            Section(
                "Accessible participation",
                "Modular, low-exposure roles, rotating leadership, familiar meeting spaces, collective representation, and digital documentation reduce barriers for residents facing disability, caregiving demands, surveillance, or economic precarity.",
            ),
            Section(
                "Durability and evaluation",
                "Material benchmarks are paired with measures of participation diversity, leadership development, coalition durability, and autonomous resident infrastructure. Institutional access is treated as a tool, not the endpoint.",
            ),
            Section(
                "Risks and scope",
                "The design anticipates co-optation, burnout, and internal fragmentation. It is a theory-informed academic strategy, not a resident-led campaign that was launched, adopted, or evaluated.",
            ),
        ),
        note="Completed academic strategy paper. The movement design is conceptual and should not be presented as resident authorization or an implemented campaign.",
        subject="One-page brief for a conceptual nonviolent strategy to institutionalize resident power",
    ),
    Brief(
        filename="caleb-johnston-institutional-political-learning-brief.pdf",
        category="Theory building | Political behavior | 2025",
        title="Why Similar Interests Produce Different Partisan Loyalties: Institutional Experience and Political Learning in the United States",
        metadata="14 pages | Georgetown University | December 2025",
        overview="A theoretical and synthetic account of how repeated encounters with public institutions shape political learning, trust, legitimacy, and durable partisan attachment.",
        left=(
            Section(
                "Puzzle",
                "Why do citizens with similar interests and backgrounds develop different partisan loyalties, and why does dissatisfaction with representation not reliably produce electoral punishment?",
            ),
            Section(
                "Core argument",
                "Routine interactions with welfare agencies, law enforcement, schools, health systems, and regulatory bodies teach citizens whom government serves and whether authority feels responsive, burdensome, or coercive.",
            ),
            Section(
                "Mechanism",
                "Institutional touchpoints create political predispositions; identity shapes interpretation, information environments shape attribution, and party coalitions mobilize the resulting trust or distrust.",
            ),
        ),
        right=(
            Section(
                "Contribution",
                "The framework moves the primary site of political learning from elections to everyday governance and connects policy-feedback reasoning to durable partisan attachment under weak electoral accountability.",
            ),
            Section(
                "Implication",
                "Administrative design affects democratic responsiveness, not just service delivery. Legible and empowering institutions may foster participation, while opaque or punitive systems can deepen distrust and unequal representation.",
            ),
            Section(
                "Scope and limitations",
                "The paper synthesizes existing research rather than presenting original data. Causal sequencing remains unresolved, institutional contexts vary, and cumulative experience is difficult to measure; longitudinal or experimental work would be needed to test the framework directly.",
            ),
        ),
        note="Completed theoretical and synthetic paper. It presents a framework and literature-based argument, not an original-data empirical study.",
        subject="One-page brief for a theoretical paper on institutional experience and partisan learning",
    ),
)


if __name__ == "__main__":
    for item in BRIEFS:
        build_brief(item)
        print(OUT / item.filename)
