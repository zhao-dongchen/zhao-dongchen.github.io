#!/usr/bin/env python3
"""Build the website CV page and PDF from cv/cv-data.json."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "cv" / "cv-data.json"
DEFAULT_HTML = ROOT / "cv" / "index.html"
DEFAULT_LANDING = ROOT / "cv.html"
DEFAULT_DROPBOX_PDF = Path("/Users/zhaode/Library/CloudStorage/Dropbox/Personal Site/CV/dongchen-zhao-cv.pdf")


def load_data(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def register_fonts() -> tuple[str, str]:
    return "Times-Roman", "Times-Bold"


def paragraph_text(text: str) -> str:
    return xml_escape(text.replace("\u00a0", " ").strip())


def format_inline(text: str, *, html: bool = False) -> str:
    """Preserve the Word CV's italic coauthor notes in generated outputs."""
    cleaned = text.replace("\u00a0", " ").strip()
    escaped = escape(cleaned) if html else paragraph_text(cleaned)
    open_tag, close_tag = ("<em>", "</em>") if html else ("<i>", "</i>")
    if cleaned.startswith("* presented by coauthor"):
        return f"{open_tag}{escaped}{close_tag}"
    return re.sub(
        r"(\((?:joint|Joint) with [^)]+\))",
        lambda match: f"{open_tag}{match.group(1)}{close_tag}",
        escaped,
    )


def item_kind(section_title: str, index: int, text: str) -> str:
    if text.startswith("* presented by coauthor"):
        return "note"
    if section_title == "Education" and index in {0, 2}:
        return "institution"
    return "indent"


def render_pdf(data: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    font, _ = register_fonts()
    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "CVTitle",
        parent=styles["Title"],
        fontName=font,
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=3
    )
    contact = ParagraphStyle(
        "CVContact",
        parent=styles["Normal"],
        fontName=font,
        fontSize=14,
        leading=16,
        spaceAfter=3
    )
    section = ParagraphStyle(
        "CVSection",
        parent=styles["Heading2"],
        fontName=font,
        fontSize=12,
        leading=14,
        textColor=colors.black,
        spaceBefore=3,
        spaceAfter=0
    )
    item_indent = ParagraphStyle(
        "CVItem",
        parent=styles["Normal"],
        fontName=font,
        fontSize=14,
        leading=16,
        leftIndent=0.5 * inch,
        spaceAfter=0
    )
    item_institution = ParagraphStyle(
        "CVInstitution",
        parent=item_indent,
        fontSize=16,
        leading=18,
    )
    item_note = ParagraphStyle(
        "CVNote",
        parent=styles["Normal"],
        fontName=font,
        fontSize=10,
        leading=12,
        firstLineIndent=0.5 * inch,
        spaceAfter=0
    )

    story = [
        Paragraph(paragraph_text(data["name"]), title),
        HRFlowable(width="100%", thickness=0.25, color=colors.HexColor("#a0a0a0"), spaceBefore=0, spaceAfter=5),
        *[Paragraph(paragraph_text(line), contact) for line in data.get("contact", [])],
        HRFlowable(width="100%", thickness=0.25, color=colors.HexColor("#a0a0a0"), spaceBefore=2, spaceAfter=1),
    ]

    for section_data in data.get("sections", []):
        entries = []
        for index, entry in enumerate(section_data.get("items", [])):
            kind = item_kind(section_data["title"], index, entry)
            style = {"institution": item_institution, "note": item_note}.get(kind, item_indent)
            entries.append(Paragraph(format_inline(entry), style))
        story.append(KeepTogether([Paragraph(paragraph_text(section_data["title"]), section), *entries[:2]]))
        story.extend(entries[2:])

    doc = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        rightMargin=1 * inch,
        leftMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
        title=f"{data['name']} CV",
        author=data["name"]
    )
    doc.build(story)


def render_pdf_previews(pdf_path: Path, output_dir: Path) -> list[str]:
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return []

    reader = PdfReader(str(pdf_path))
    preview_names: list[str] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cv-pdf-preview-") as tmp_name:
        tmp_dir = Path(tmp_name)
        for index, page in enumerate(reader.pages, start=1):
            page_pdf = tmp_dir / f"cv-page-{index}.pdf"
            thumb_dir = tmp_dir / f"thumb-{index}"
            thumb_dir.mkdir()

            writer = PdfWriter()
            writer.add_page(page)
            with page_pdf.open("wb") as handle:
                writer.write(handle)

            subprocess.run(
                ["qlmanage", "-t", "-s", "1600", "-o", str(thumb_dir), str(page_pdf)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            thumbnail = thumb_dir / f"{page_pdf.name}.png"
            if not thumbnail.exists():
                continue
            target_name = f"cv-page-{index}.png"
            shutil.copy2(thumbnail, output_dir / target_name)
            preview_names.append(target_name)

    for stale in output_dir.glob("cv-page-*.png"):
        if stale.name not in preview_names:
            stale.unlink()
    return preview_names


def render_html(data: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf_href = escape(data.get("pdf_url") or data.get("pdf_filename", "dongchen-zhao-cv.pdf"))
    pdf_preview_href = escape(data.get("pdf_filename", "dongchen-zhao-cv.pdf"))
    pdf_attrs = ' target="_blank" rel="noopener"' if data.get("pdf_url") else ""
    section_html = []
    for section_data in data.get("sections", []):
        items = []
        for index, item in enumerate(section_data.get("items", [])):
            kind = item_kind(section_data["title"], index, item)
            items.append(f'          <p class="cv-entry cv-entry-{kind}">{format_inline(item, html=True)}</p>')
        section_html.append(
            f"""        <section class="cv-section">
          <h2>{escape(section_data["title"])}</h2>
{chr(10).join(items)}
        </section>"""
        )

    preview_images = data.get("_preview_images", [])
    if preview_images:
        preview_html = "\n".join(
            f'      <img src="{escape(image)}" alt="{escape(data["name"])} CV page {index}">'
            for index, image in enumerate(preview_images, start=1)
        )
        preview_html = f"""    <div class="cv-image-preview" aria-label="CV PDF preview">
{preview_html}
    </div>"""
    else:
        preview_html = f"""    <object class="cv-pdf-viewer" data="{pdf_preview_href}" type="application/pdf" aria-label="PDF preview of {escape(data['name'])}'s CV">
      <p><a href="{pdf_preview_href}">Open the CV PDF</a></p>
    </object>"""

    contact_html = "\n".join(f"          <p>{escape(line)}</p>" for line in data.get("contact", []))
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Curriculum vitae for {escape(data['name'])}.">
  <title>CV | {escape(data['name'])}</title>
  <link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../style.css?v=3">
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <a class="site-title" href="../index.html">
        <span class="site-mark" aria-hidden="true">∂</span>
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

  <main class="container page cv-page">
    <div class="cv-tools" aria-label="CV actions">
      <a class="button" href="{pdf_href}"{pdf_attrs}><span aria-hidden="true">PDF</span>Download PDF</a>
    </div>
{preview_html}
    <details class="cv-text-version">
      <summary>Text version</summary>
    <article class="cv-document cv-word">
      <header class="cv-heading">
        <h1>{escape(data['name'])}</h1>
        <div class="cv-rule" aria-hidden="true"></div>
        <div class="cv-contact">
{contact_html}
        </div>
      </header>

{chr(10).join(section_html)}
    </article>
    </details>
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
  <link rel="stylesheet" href="style.css?v=3">
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <a class="site-title" href="index.html">
        <span class="site-mark" aria-hidden="true">∂</span>
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

  <main class="container site-layout page-layout">
    <aside class="profile-card" aria-label="Profile">
      <img class="profile-photo" src="assets/profile.jpg" alt="{escape(data['name'])}">
      <h2>{escape(data['name'])}</h2>
      <p class="profile-role">Assistant Professor of Economics</p>
      <p class="profile-fields">Macroeconomics · Finance · Macro Labor</p>
      <div class="profile-links" aria-label="Profile links">
        <p>Follow</p>
        <a href="mailto:dongchen.zhao@uc.edu">Email</a>
        <a href="cv.html">CV</a>
        <a href="https://github.com/dczhaozach" target="_blank" rel="noopener">GitHub</a>
        <a href="https://www.linkedin.com/in/dongchen-zhao/" target="_blank" rel="noopener">LinkedIn</a>
      </div>
    </aside>

    <div class="content-column">
      <header class="page-header">
        <h1>Curriculum Vitae</h1>
        <p>
          A current PDF version of my curriculum vitae and a web version are available below.
        </p>
        <p class="button-row">
          <a class="button" href="{pdf_href}"{pdf_attrs}><span aria-hidden="true">PDF</span>Download CV</a>
          <a class="icon-link" href="cv/"><span aria-hidden="true">CV</span>View Web CV</a>
        </p>
      </header>
    </div>
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
    parser.add_argument(
        "--build-pdf-from-data",
        action="store_true",
        help="Ignore source_pdf and rebuild the site PDF from cv/cv-data.json.",
    )
    args = parser.parse_args()

    data = load_data(args.data)
    pdf_path = args.pdf or args.html.parent / data.get("pdf_filename", "dongchen-zhao-cv.pdf")

    source_pdf = data.get("source_pdf")
    if source_pdf and not args.build_pdf_from_data:
        source_pdf_path = Path(source_pdf).expanduser()
        if not source_pdf_path.exists():
            raise FileNotFoundError(f"source_pdf does not exist: {source_pdf_path}")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_pdf_path, pdf_path)
    else:
        render_pdf(data, pdf_path)

    data["_preview_images"] = render_pdf_previews(pdf_path, args.html.parent)
    render_html(data, args.html)
    render_landing_html(data, args.landing)

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
