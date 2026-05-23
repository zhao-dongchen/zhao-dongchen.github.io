# Personal Site Codex Instructions

This is a static GitHub Pages academic personal website. Keep it build-free: plain HTML, CSS, PDFs, and image/assets only.

## Design Baseline

- The current system sans-serif typography, `DZ` mark/favicon, and icon-style profile/research links are intentional site-wide design choices from the May 23, 2026 request to change the font, make the site more elegant, and add icons.
- Future CV-only updates should not change `index.html`, `research.html`, `teaching.html`, or global styling unless the user also asks for a design/site-wide change.
- For visual changes, verify through the local HTTP server rather than `file://`, for example `http://localhost:8000/index.html`, `research.html`, `teaching.html`, `cv.html`, and `cv/`.

## CV Workflow

- Use the `$update-academic-cv` skill for any CV update, CV link update, CV PDF refresh, Dropbox CV sync, or website CV content change.
- Treat `cv/cv-data.json` as the editable CV source.
- Run `scripts/build_cv.py` after CV data or CV link changes so the same source regenerates:
  - `cv.html`
  - `cv/index.html`
  - `cv/dongchen-zhao-cv.pdf`
  - the optional Dropbox-synced PDF copy
- Do not manually patch only one CV page when the change belongs in `cv/cv-data.json` or the generator.
- `scripts/build_cv.py` uses `reportlab`. On this machine, run it with the bundled Codex Python runtime unless another Python environment already has `reportlab`.

## Mandatory Review

After every CV workflow update, run an independent read-only critical reviewer before final completion claims.

- Use the project `critical_reviewer` subagent when available.
- If only generic subagents are available, spawn a read-only critical reviewer using the prompt in `/Users/zhaode/.codex/skills/update-academic-cv/references/critical-review-prompt.md`.
- The reviewer must not be restricted by the scope, directions, file list, commands, or claims supplied by the main agent.
- The reviewer must treat anything from the main agent as starting context only, never as an inspection boundary, and must independently decide how and where to evaluate within the user request, reviewer role, and read-only limits.
- Fix blocker or major findings that are within the user-authorized work, then re-run verification.
- If a subagent cannot be run, state that the mandatory review did not run and do not claim the CV update is fully complete.
