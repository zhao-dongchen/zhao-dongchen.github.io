#!/usr/bin/env python3
"""Build the website CV page and PDF from cv/cv-data.json."""

from __future__ import annotations

import argparse
import json
import shutil
from html import escape
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "cv" / "cv-data.json"
DEFAULT_HTML = ROOT / "cv" / "index.html"
DEFAULT_LANDING = ROOT / "cv.html"
DEFAULT_DROPBOX_PDF = Path("/Users/zhaode/Library/CloudStorage/Dropbox/Personal Site/CV/dongchen-zhao-cv.pdf")


def load_data(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def register_fonts() -> tuple[str, str]:
    regular_candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    ]
    bold_candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        Path("/Library/Fonts/Arial Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    ]

    regular = next((path for path in regular_candidates if path.exists()), None)
    bold = next((path for path in bold_candidates if path.exists()), None)
    if regular and bold:
        pdfmetrics.registerFont(TTFont("CVSans", str(regular)))
        pdfmetrics.registerFont(TTFont("CVSans-Bold", str(bold)))
        return "CVSans", "CVSans-Bold"
    return "Helvetica", "Helvetica-Bold"


def paragraph_text(text: str) -> str:
    return xml_escape(text.replace("\u00a0", " ").strip())


def render_pdf(data: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    font, font_bold = register_fonts()
    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "CVTitle",
        parent=styles["Title"],
        fontName=font_bold,
        fontSize=17,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=6
    )
    contact = ParagraphStyle(
        "CVContact",
        parent=styles["Normal"],
        fontName=font,
        fontSize=8.8,
        leading=11,
        alignment=TA_CENTER,
        spaceAfter=8
    )
    section = ParagraphStyle(
        "CVSection",
        parent=styles["Heading2"],
        fontName=font_bold,
        fontSize=10.7,
        leading=13,
        textColor=colors.HexColor("#171717"),
        spaceBefore=7,
        spaceAfter=3
    )
    item = ParagraphStyle(
        "CVItem",
        parent=styles["Normal"],
        fontName=font,
        fontSize=9.2,
        leading=11.5,
        spaceAfter=2.8
    )

    story = [
        Paragraph(paragraph_text(data["name"]), title),
        Paragraph("<br/>".join(paragraph_text(line) for line in data.get("contact", [])), contact),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d9dde3"), spaceAfter=5)
    ]

    for section_data in data.get("sections", []):
        story.append(Paragraph(paragraph_text(section_data["title"]), section))
        for entry in section_data.get("items", []):
            story.append(Paragraph(paragraph_text(entry), item))

    doc = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
        title=f"{data['name']} CV",
        author=data["name"]
    )
    doc.build(story)


def render_html(data: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf_href = escape(data.get("pdf_url") or data.get("pdf_filename", "dongchen-zhao-cv.pdf"))
    pdf_attrs = ' target="_blank" rel="noopener"' if data.get("pdf_url") else ""
    section_html = []
    for section_data in data.get("sections", []):
        items = "\n".join(f"            <li>{escape(item)}</li>" for item in section_data.get("items", []))
        section_html.append(
            f"""        <section class="cv-section">
          <h2>{escape(section_data["title"])}</h2>
          <ul>
{items}
          </ul>
        </section>"""
        )

    contact_html = "\n".join(f"          <p>{escape(line)}</p>" for line in data.get("contact", []))
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Curriculum vitae for {escape(data['name'])}.">
  <title>CV | {escape(data['name'])}</title>
  <link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../style.css?v=2">
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <a class="site-title" href="../index.html">
        <span class="site-mark" aria-hidden="true">DZ</span>
        <span>{escape(data['name'])}</span>
      </a>
      <nav class="site-nav" aria-label="Main navigation">
        <a href="../index.html">Home</a>
        <a href="../research.html">Research</a>
        <a href="../teaching.html">Teaching</a>
        <a href="../cv.html" aria-current="page">CV</a>
      </nav>
    </div>
  </header>

  <main class="container page">
    <article class="cv-document">
      <header class="cv-heading">
        <p class="eyebrow">{escape(data.get("role", "Curriculum Vitae"))}</p>
        <h1>{escape(data['name'])}</h1>
        <div class="cv-contact">
{contact_html}
        </div>
        <p class="button-row">
          <a class="button" href="{pdf_href}"{pdf_attrs}><span aria-hidden="true">PDF</span>Download PDF</a>
        </p>
      </header>

{chr(10).join(section_html)}
    </article>
  </main>

  <footer class="site-footer">
    <div class="container">
      <p>&copy; 2026 {escape(data['name'])}</p>
    </div>
  </footer>
</body>
</html>
"""
    output.write_text(html, encoding="utf-8")


def render_landing_html(data: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf_href = escape(data.get("pdf_url") or f"cv/{data.get('pdf_filename', 'dongchen-zhao-cv.pdf')}")
    pdf_attrs = ' target="_blank" rel="noopener"' if data.get("pdf_url") else ""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Curriculum vitae for {escape(data['name'])}.">
  <title>CV | {escape(data['name'])}</title>
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="style.css?v=2">
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <a class="site-title" href="index.html">
        <span class="site-mark" aria-hidden="true">DZ</span>
        <span>{escape(data['name'])}</span>
      </a>
      <nav class="site-nav" aria-label="Main navigation">
        <a href="index.html">Home</a>
        <a href="research.html">Research</a>
        <a href="teaching.html">Teaching</a>
        <a href="cv.html" aria-current="page">CV</a>
      </nav>
    </div>
  </header>

  <main class="container page">
    <header class="page-header">
      <h1>Curriculum Vitae</h1>
      <p class="lead narrow">
        A current PDF version of my curriculum vitae and a web version are available below.
      </p>
      <p class="button-row">
        <a class="button" href="{pdf_href}"{pdf_attrs}><span aria-hidden="true">PDF</span>Download CV</a>
        <a class="icon-link" href="cv/"><span aria-hidden="true">CV</span>View Web CV</a>
      </p>
    </header>
  </main>

  <footer class="site-footer">
    <div class="container">
      <p>&copy; 2026 {escape(data['name'])}</p>
    </div>
  </footer>
</body>
</html>
"""
    output.write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CV website page and PDF.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--landing", type=Path, default=DEFAULT_LANDING)
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument("--dropbox-pdf", type=Path, default=None, help="Optional Dropbox-synced copy target.")
    args = parser.parse_args()

    data = load_data(args.data)
    pdf_path = args.pdf or args.html.parent / data.get("pdf_filename", "dongchen-zhao-cv.pdf")

    render_html(data, args.html)
    render_landing_html(data, args.landing)
    render_pdf(data, pdf_path)

    if args.dropbox_pdf:
        args.dropbox_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_path, args.dropbox_pdf)

    print(f"Wrote {args.html}")
    print(f"Wrote {args.landing}")
    print(f"Wrote {pdf_path}")
    if args.dropbox_pdf:
        print(f"Copied {pdf_path} to {args.dropbox_pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
