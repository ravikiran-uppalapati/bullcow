from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "project_submission.pdf"


class ArchitectureFlow(Flowable):
    def __init__(self):
        super().__init__()
        self.width = 7.0 * inch
        self.height = 3.05 * inch

    def draw(self):
        c = self.canv
        c.setFont("Helvetica-Bold", 9)

        boxes = {
            "Human": (0.0, 1.15, 1.05, 0.5, colors.HexColor("#eef2ff")),
            "Streamlit UI": (1.35, 1.15, 1.15, 0.5, colors.HexColor("#f8fafc")),
            "Opponent Agent\nLangGraph": (2.85, 1.85, 1.4, 0.62, colors.HexColor("#ede9fe")),
            "Coach Agent": (2.85, 0.45, 1.4, 0.62, colors.HexColor("#dcfce7")),
            "Rules + Memory": (4.55, 1.15, 1.35, 0.68, colors.HexColor("#fef3c7")),
            "Ollama LLM": (6.2, 1.85, 1.15, 0.55, colors.HexColor("#e0f2fe")),
            "LangSmith": (6.2, 0.45, 1.15, 0.55, colors.HexColor("#fee2e2")),
        }

        for label, (x, y, w, h, fill) in boxes.items():
            self._box(c, x * inch, y * inch, w * inch, h * inch, label, fill)

        arrows = [
            ("Human", "Streamlit UI"),
            ("Streamlit UI", "Opponent Agent\nLangGraph"),
            ("Streamlit UI", "Coach Agent"),
            ("Opponent Agent\nLangGraph", "Rules + Memory"),
            ("Coach Agent", "Rules + Memory"),
            ("Rules + Memory", "Ollama LLM"),
            ("Ollama LLM", "Opponent Agent\nLangGraph"),
            ("Ollama LLM", "Coach Agent"),
            ("Rules + Memory", "LangSmith"),
        ]
        for start, end in arrows:
            self._arrow(c, boxes[start], boxes[end])

    def _box(self, c, x, y, w, h, text, fill):
        c.setStrokeColor(colors.HexColor("#334155"))
        c.setFillColor(fill)
        c.roundRect(x, y, w, h, 6, stroke=1, fill=1)
        c.setFillColor(colors.HexColor("#0f172a"))
        lines = text.split("\n")
        line_y = y + h / 2 + (len(lines) - 1) * 5
        for line in lines:
            c.drawCentredString(x + w / 2, line_y, line)
            line_y -= 10

    def _center(self, box):
        x, y, w, h, _ = box
        return (x * inch + w * inch / 2, y * inch + h * inch / 2)

    def _arrow(self, c, start, end):
        sx, sy = self._center(start)
        ex, ey = self._center(end)
        c.setStrokeColor(colors.HexColor("#475569"))
        c.line(sx, sy, ex, ey)
        dx = ex - sx
        dy = ey - sy
        length = max((dx * dx + dy * dy) ** 0.5, 1)
        ux, uy = dx / length, dy / length
        ah = 7
        aw = 3.5
        px, py = -uy, ux
        c.setFillColor(colors.HexColor("#475569"))
        c.line(ex, ey, ex - ux * ah + px * aw, ey - uy * ah + py * aw)
        c.line(ex, ey, ex - ux * ah - px * aw, ey - uy * ah - py * aw)


def p(text, style):
    return Paragraph(text, style)


def bullets(items, styles):
    return ListFlowable(
        [ListItem(Paragraph(item, styles["Body"]), leftIndent=12) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=18,
    )


def section(title, story, styles):
    story.append(Paragraph(title, styles["H1"]))
    story.append(Spacer(1, 0.08 * inch))


def add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "Bulls and Cows LangGraph Agent")
    canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build():
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.72 * inch,
        title="Bulls and Cows LangGraph Agent Project Submission",
    )
    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1e1b4b"),
            spaceAfter=12,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            alignment=TA_CENTER,
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#475569"),
            spaceAfter=18,
        ),
        "H1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#065f46"),
            spaceBefore=10,
            spaceAfter=5,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#7c2d12"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.2,
            textColor=colors.HexColor("#111827"),
            spaceAfter=6,
        ),
        "Small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.3,
            leading=11,
            textColor=colors.HexColor("#334155"),
        ),
        "Callout": ParagraphStyle(
            "Callout",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#064e3b"),
            backColor=colors.HexColor("#dcfce7"),
            borderColor=colors.HexColor("#22c55e"),
            borderWidth=1,
            borderPadding=8,
            spaceAfter=10,
        ),
    }

    story = []
    story.append(Spacer(1, 0.55 * inch))
    story.append(p("Bulls and Cows LangGraph Agent", styles["Title"]))
    story.append(p("Project Submission Document", styles["Subtitle"]))
    story.append(p("An interactive agent demo using LangGraph, Ollama, Streamlit, and LangSmith observability.", styles["Callout"]))
    story.append(Spacer(1, 0.25 * inch))
    story.append(ArchitectureFlow())
    story.append(Spacer(1, 0.2 * inch))
    story.append(p("<b>Repository:</b> github.com/ravikiran-uppalapati/bullcow", styles["Body"]))
    story.append(p("<b>Primary local LLM:</b> Ollama with gemma3:4b", styles["Body"]))
    story.append(p("<b>Observability:</b> LangSmith EU endpoint", styles["Body"]))
    story.append(PageBreak())

    section("1. Problem Statement", story, styles)
    story.append(p(
        "The project demonstrates how an agent can solve an iterative reasoning problem using memory, tools, state transitions, and observability. The selected problem is a 3-digit Bulls and Cows game where a human and an opponent agent take turns guessing secret numbers.",
        styles["Body"],
    ))
    story.append(p(
        "This is not a one-shot question-answer task. A player must guess, observe bulls/cows feedback, remember previous turns, eliminate impossible answers, and choose the next move. This makes it a good project for demonstrating an agentic reasoning loop.",
        styles["Body"],
    ))

    section("2. High-Level System Architecture", story, styles)
    story.append(p(
        "The system combines deterministic game tools with agent workflows and LLM-powered conversation. Streamlit provides the game interface, LangGraph manages the opponent workflow, the Coach Agent helps the human player, Ollama gives natural-language responses, and LangSmith records the internal reasoning trace.",
        styles["Body"],
    ))
    table = Table(
        [
            ["Component", "Role"],
            ["Streamlit UI", "Interactive game screen, forms, Coach panel, history notebook, and winner dialogs."],
            ["Rules Engine", "Validates numbers, generates 648 valid candidates, and scores bulls/cows."],
            ["LangGraph Opponent Agent", "Maintains candidate state, receives feedback, filters candidates, and chooses guesses."],
            ["Coach Agent", "Tracks human guesses, filters possible opponent secrets, suggests next moves, and explains why."],
            ["Session Memory", "Stores agent turns, human turns, Coach chat, candidate counts, and a merged timeline."],
            ["Ollama LLM", "Adds conversational personality and coaching using full game context."],
            ["LangSmith", "Traces agent steps, state changes, human turns, and LLM messages."],
        ],
        colWidths=[1.7 * inch, 5.1 * inch],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e1b4b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.2),
        ("LEADING", (0, 0), (-1, -1), 10.5),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)

    section("3. LLM Used", story, styles)
    story.append(p(
        "For the local demo, the project uses Ollama with the locally installed gemma3:4b model. Ollama is selected because it runs locally, avoids hosted quota limits, and makes the demo reliable even when internet-hosted model providers are unavailable.",
        styles["Body"],
    ))
    story.append(bullets([
        "Ollama is used for natural language only, not for hidden game logic.",
        "The strategic guess is produced by deterministic candidate filtering.",
        "Nebius and Gemini are supported as hosted fallbacks for Streamlit Cloud.",
        "A deterministic fallback remains available if no LLM provider is configured.",
    ], styles))

    section("4. Agents in the System", story, styles)
    story.append(KeepTogether([
        p("Opponent Agent", styles["H2"]),
        p("The Opponent Agent guesses the human player's secret number. LangGraph manages its workflow: initialize state, generate a guess, receive feedback, filter candidates, choose the next guess, detect win/conflict, and explain reasoning.", styles["Body"]),
        p("Coach Agent", styles["H2"]),
        p("The Coach Agent helps the human player. It remembers previous guesses, bulls/cows responses, digits tried, remaining possible secrets, suggested next guess, and reasoning for the suggestion.", styles["Body"]),
    ]))

    section("5. How the Problem Is Solved", story, styles)
    story.append(p(
        "The game is solved through candidate elimination. At the start there are 648 possible 3-digit secrets: 9 choices for the first digit, 9 choices for the second digit, and 8 choices for the third digit. After each feedback response, invalid candidates are removed.",
        styles["Body"],
    ))
    story.append(p(
        "For example, if the agent guesses 102 and receives 0 bulls and 1 cow, only numbers that would produce exactly that response against 102 remain in the candidate pool. This loop continues until the secret is solved or feedback becomes contradictory.",
        styles["Body"],
    ))

    section("6. Why These Design Decisions Were Made", story, styles)
    story.append(bullets([
        "LangGraph was chosen because the opponent requires an explicit reasoning workflow, not a single chatbot response.",
        "Ollama was chosen for local reliability, no hosted quota dependency, and simple laptop demonstrations.",
        "LangSmith was chosen to make the internal agent loop visible and debuggable.",
        "Streamlit was chosen for a fast interactive UI suitable for demos and project review.",
        "The rules engine remains deterministic so the game can be tested and explained.",
    ], styles))

    section("7. Observability With LangSmith", story, styles)
    story.append(p(
        "LangSmith is the observability layer. It records LangGraph node execution, human guesses, agent feedback turns, LLM messages, and the state passed into each step. This helps prove the agent was reasoning over memory and tools rather than guessing randomly.",
        styles["Body"],
    ))

    section("8. Testing and Validation", story, styles)
    story.append(p("The project includes 49 passing automated tests covering:", styles["Body"]))
    story.append(bullets([
        "Bulls/cows scoring and candidate generation.",
        "Candidate filtering and LangGraph state updates.",
        "Coach notes, possible-count reasoning, and notebook rendering.",
        "Session memory and LLM prompt construction.",
        "Settings for Ollama, Nebius, Gemini, and LangSmith.",
    ], styles))

    section("9. Demo Flow", story, styles)
    story.append(bullets([
        "Start the Streamlit app.",
        "Think of a valid 3-digit secret number.",
        "Let the Opponent Agent guess and provide bulls/cows feedback.",
        "Make human guesses and watch the Coach Agent track history.",
        "Ask the Coach a question and show that Ollama uses full game memory.",
        "Open LangSmith to show traces for LangGraph, turns, and LLM messages.",
    ], styles))

    section("10. Limitations and Future Improvements", story, styles)
    story.append(bullets([
        "Local Ollama works only where Ollama is running; Streamlit Cloud needs Nebius or Gemini.",
        "The guessing strategy is explainable but not optimized for the absolute fewest guesses.",
        "Future work could add minimax-style guessing, richer trace links, and UI controls for provider selection.",
    ], styles))

    section("11. Conclusion", story, styles)
    story.append(p(
        "This project demonstrates a complete agent pattern: LangGraph controls the reasoning workflow, deterministic tools provide reliable game logic, the Coach Agent supports the human with memory and explanation, Ollama adds conversational intelligence, Streamlit provides interaction, and LangSmith makes the process observable.",
        styles["Body"],
    ))

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)


if __name__ == "__main__":
    build()
    print(OUT)
