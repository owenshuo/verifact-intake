from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf"

NAVY = colors.HexColor("#10243E")
TEAL = colors.HexColor("#1D8A8A")
INK = colors.HexColor("#1E293B")
MUTED = colors.HexColor("#64748B")
PALE = colors.HexColor("#EAF5F4")
LINE = colors.HexColor("#CBD5E1")


@dataclass(frozen=True)
class Section:
    title: str
    paragraphs: tuple[str, ...] = ()
    bullets: tuple[str, ...] = ()
    rows: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class DocumentSpec:
    filename: str
    title: str
    subtitle: str
    metadata: tuple[tuple[str, str], ...]
    summary: str
    sections: tuple[Section, ...]


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=4 * mm,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=TEAL,
            spaceAfter=6 * mm,
        ),
        "summary": ParagraphStyle(
            "Summary",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            textColor=INK,
            backColor=PALE,
            borderColor=TEAL,
            borderWidth=0.7,
            borderPadding=10,
            spaceBefore=3 * mm,
            spaceAfter=7 * mm,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=NAVY,
            spaceBefore=5 * mm,
            spaceAfter=2.5 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=INK,
            spaceAfter=2.5 * mm,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            leftIndent=5 * mm,
            firstLineIndent=-3 * mm,
            bulletIndent=1 * mm,
            textColor=INK,
            spaceAfter=1.5 * mm,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
        ),
    }


def _header_footer(canvas: Canvas, doc: SimpleDocTemplate, title: str) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, height - 14 * mm, width - 18 * mm, height - 14 * mm)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(NAVY)
    canvas.drawString(18 * mm, height - 10.5 * mm, "VERIFACT INTAKE - SYNTHETIC DEMO")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(width - 18 * mm, height - 10.5 * mm, title)
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.drawString(18 * mm, 9.5 * mm, "Public synthetic data - no real product information")
    canvas.drawRightString(width - 18 * mm, 9.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _metadata_table(items: Iterable[tuple[str, str]], style: ParagraphStyle) -> Table:
    data = [[Paragraph(f"<b>{key}</b>", style), Paragraph(value, style)] for key, value in items]
    table = Table(data, colWidths=[40 * mm, 112 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
                ("TEXTCOLOR", (0, 0), (-1, -1), INK),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def build_pdf(spec: DocumentSpec) -> Path:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / spec.filename
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=21 * mm,
        bottomMargin=20 * mm,
        title=spec.title,
        author="VeriFact Intake",
        subject="Public synthetic hackathon demonstration document",
    )
    s = styles()
    story = [
        Spacer(1, 6 * mm),
        Paragraph(spec.title, s["title"]),
        Paragraph(spec.subtitle, s["subtitle"]),
        _metadata_table(spec.metadata, s["small"]),
        Paragraph(spec.summary, s["summary"]),
    ]
    for section in spec.sections:
        content: list[Flowable] = [Paragraph(section.title, s["h2"])]
        content.extend(Paragraph(text, s["body"]) for text in section.paragraphs)
        content.extend(Paragraph(text, s["bullet"], bulletText="-") for text in section.bullets)
        if section.rows:
            table_data = [
                [Paragraph(f"<b>{left}</b>", s["small"]), Paragraph(right, s["small"])]
                for left, right in section.rows
            ]
            table = Table(table_data, colWidths=[51 * mm, 101 * mm], hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        (
                            "ROWBACKGROUNDS",
                            (0, 0),
                            (-1, -1),
                            [colors.white, colors.HexColor("#F8FAFC")],
                        ),
                        ("LEFTPADDING", (0, 0), (-1, -1), 7),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            content.append(table)
        story.append(KeepTogether(content))
    doc.build(
        story,
        onFirstPage=lambda canvas, current: _header_footer(canvas, current, spec.title),
        onLaterPages=lambda canvas, current: _header_footer(canvas, current, spec.title),
    )
    return path


DOCUMENTS = (
    DocumentSpec(
        filename="atlas-api-reference.pdf",
        title="Atlas Change Service API Reference",
        subtitle="Normative API contract for version 2.1",
        metadata=(
            ("Version", "2.1"),
            ("Authority", "Product API specification"),
            ("Effective", "2026-07-15"),
        ),
        summary=(
            "This document is the authoritative contract for Atlas Change Service endpoints. "
            "The service base path is <b>/change-api</b>."
        ),
        sections=(
            Section(
                title="Service identity",
                rows=(
                    ("Service", "Atlas Change Service"),
                    ("Base path", "/change-api"),
                    ("API version", "v2"),
                ),
            ),
            Section(
                title="Create change",
                paragraphs=("<b>POST /v2/changes</b> creates a new change request.",),
                bullets=(
                    "The <b>Idempotency-Key</b> header is required.",
                    "Synchronous validation timeout is <b>30 seconds</b>.",
                    "A successful request returns HTTP 202.",
                ),
            ),
            Section(
                title="Get change",
                paragraphs=(
                    "<b>GET /v2/changes/{changeId}</b> returns the latest workflow state.",
                ),
                rows=(
                    ("States", "DRAFT, PENDING_APPROVAL, SCHEDULED, RUNNING, SUCCEEDED, FAILED"),
                    ("Not found", "HTTP 404 when the identifier is unknown"),
                ),
            ),
        ),
    ),
    DocumentSpec(
        filename="atlas-operations-guide.pdf",
        title="Atlas Operations Guide",
        subtitle="Operating guidance published before API 2.1 and the 2026-Q3 policy",
        metadata=(
            ("Version", "2.0"),
            ("Authority", "Operations guidance"),
            ("Published", "2026-04-02"),
        ),
        summary=(
            "This guide provides ownership and operating context. It predates newer normative "
            "materials, so API and policy claims require cross-source validation."
        ),
        sections=(
            Section(
                title="Ownership",
                paragraphs=(
                    "The Atlas Change Service is operated by the <b>Network Operations</b> team.",
                ),
            ),
            Section(
                title="Creating a change",
                paragraphs=(
                    "Operators create a change with <b>PUT /v2/changes</b>. "
                    "The client retries once if the request times out.",
                ),
            ),
            Section(
                title="High-risk workflow",
                paragraphs=(
                    "<b>One</b> duty manager approval is sufficient before a high-risk "
                    "change is scheduled.",
                ),
            ),
            Section(
                title="Evidence retention",
                paragraphs=(
                    "Execution evidence is retained for <b>90 days</b> after the change completes.",
                ),
            ),
            Section(
                title="Supersession notice",
                paragraphs=(
                    "This guide predates the API 2.1 release and the 2026-Q3 quality policy. "
                    "Newer normative sources take precedence for API and policy facts.",
                ),
            ),
        ),
    ),
    DocumentSpec(
        filename="atlas-quality-policy.pdf",
        title="Atlas Change Quality Policy",
        subtitle="Normative governance controls for 2026-Q3",
        metadata=(
            ("Policy version", "2026-Q3"),
            ("Authority", "Quality governance policy"),
            ("Effective", "2026-07-01"),
        ),
        summary=(
            "This policy defines mandatory approval, evidence, verification, and audit controls "
            "for Atlas changes."
        ),
        sections=(
            Section(
                title="Approval control",
                paragraphs=(
                    "Every high-risk change requires <b>two independent approvals</b> "
                    "before scheduling.",
                    "The requester cannot approve the same change.",
                ),
            ),
            Section(
                title="Evidence retention",
                paragraphs=(
                    "Change plans, approvals, execution logs, and verification results must be "
                    "retained for <b>180 days</b> after completion.",
                ),
            ),
            Section(
                title="Verification",
                paragraphs=(
                    "A change can enter <b>SUCCEEDED</b> only after the post-change "
                    "verification suite passes.",
                    "A failed verification moves the change to FAILED and requires an "
                    "incident reference.",
                ),
            ),
            Section(
                title="Audit",
                paragraphs=(
                    "Approval and promotion decisions are append-only. A later correction creates "
                    "a new decision and never overwrites the original record.",
                ),
            ),
        ),
    ),
)


def main() -> None:
    for document in DOCUMENTS:
        path = build_pdf(document)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
