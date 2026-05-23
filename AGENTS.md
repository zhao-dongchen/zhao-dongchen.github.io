# Personal Site Codex Instructions

This is a static GitHub Pages academic personal website. Keep it build-free: plain HTML, CSS, PDFs, and image/assets only.

## Design Baseline

- The current system sans-serif typography, `DZ` mark/favicon, and icon-style profile/research links are intentional site-wide design choices from the May 23, 2026 request to change the font, make the site more elegant, and add icons.
- Future CV-only updates should not change `index.html`, `research.html`, `teaching.html`, or global styling unless the user also asks for a design/site-wide change.
- For visual changes, verify through the local HTTP server rather than `file://`, for example `http://localhost:8000/index.html`, `research.html`, `teaching.html`, `cv.html`, and `cv/`.

## CV Workflow

- Use the `$update-academic-cv` skill for any CV update, CV link update, CV PDF refresh, Dropbox CV sync, or website CV content change.
- Treat `/Users/zhaode/Desktop/Documents/Academic/CV/cv_260210.docx` as the controlling CV source unless the user provides a newer CV document.
- Treat `cv/cv-data.json` as the structured website/PDF copy of that Word CV, not an independent source of truth.
- Keep CV wording, section names, ordering, dates, and coauthor wording aligned with the source Word CV unless the user explicitly asks to revise the CV.
- Run `scripts/build_cv.py` after CV data or CV link changes so the same source regenerates:
  - `cv.html`
  - `cv/index.html`
  - `cv/dongchen-zhao-cv.pdf`
  - the optional Dropbox-synced PDF copy
- Do not manually patch only one CV page when the change belongs in `cv/cv-data.json` or the generator.
- `scripts/build_cv.py` uses `reportlab`. On this machine, run it with the bundled Codex Python runtime unless another Python environment already has `reportlab`.

## Fast CV Verification

Do not run an independent subagent/reviewer as part of the CV workflow.

- Verify locally by running the generator, checking the generated PDF and Dropbox copy exist, checking `cv.html` and `cv/index.html` point to the expected CV URL, and previewing through the local HTTP server when visual layout changes.
- If the user provides or references a Word CV, compare the generated CV content against that document with `textutil -convert txt -stdout`.
