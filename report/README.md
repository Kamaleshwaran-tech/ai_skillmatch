# SkillSync AI — Mini Project Report (build tooling)

This directory contains the complete, reproducible source of the submission
report for **SkillSync AI — AI-Driven Employment and Skill Matching Portal for
Youth Development** (KAMALESHWARAN R, 7376231CD120, B.E. Computer Science and
Design, IV Year / VII Semester, 2026–2027).

## Deliverables

| File | Description |
|------|-------------|
| `output/SkillSync_AI_Mini_Project_Report.pdf` | Typeset report (A4, Times New Roman 12 pt, 1.5 spacing) |
| `output/SkillSync_AI_Mini_Project_Report.docx` | Same content in editable Word format |

Both carry identical, *real* page numbers: lower-roman folios for the front
matter (certificate … abbreviations) and decimal folios restarting at 1 for
the body. The table of contents, list of figures and list of tables are static
lists numbered from the PDF build (`pagenums.json`), so the Word file needs no
field update after opening.

## Rebuilding

```bash
/home/user/.venv/bin/python report/build.py            # PDF + DOCX
/home/user/.venv/bin/python report/build.py --diagrams # also re-render all 17 figures
```

`build_pdf.py` runs a two-pass pagination (reserve → measure → fill) and writes
`pagenums.json`; `build_docx.py` consumes it. Python dependencies: `reportlab`,
`python-docx`, `matplotlib`, `pillow`, `pymupdf` (see `/home/user/.venv`).

## Source layout

| Path | Purpose |
|------|---------|
| `content_front.py` | Title-page data, certificate, declaration, acknowledgement, abstract, abbreviations |
| `content_c1.py` … `content_c3.py` | Chapters 1–5, 6–10, 11–appendices as a block IR (paragraphs, tables, figures, listings, equations, references) |
| `ir.py` | Assembles the block IR; derives TOC / LOF / LOT / LOL entries and all numbering |
| `dstyle.py`, `diagrams_a.py`, `diagrams_b.py`, `diagrams_c.py` | Original matplotlib artwork for the 17 diagrams (use-case, module, DFD-0/1, flows, ER, architecture, sequence, screenshots' companions) |
| `figures/` | Rendered diagram PNGs (210 dpi) |
| `screenshots/` | **You supply these** — seven real application captures, see `screenshots/README.md` |
| `assets/logo.png` | Institute logo (optional; a labelled frame is used until provided) |
| `observed_outputs.json` | Verbatim outputs produced by executing the project's own services in offline fixture mode (resume parse, market demand, deduplication) — the only quantitative evidence quoted in Chapter 13 |

## Integrity rules honoured by the text

* Every number quoted in Chapters 11–13 and Appendix C comes from
  `observed_outputs.json` or from the repository's automated test suites;
  nothing is estimated or invented.
* Market-demand figures are explicitly labelled as computed over the bundled
  fixture postings (`backend/app/taxonomy/sample_jobs.json`), never as live
  market data.
* No accuracy percentage is claimed anywhere: the system is a retrieval and
  rule-hybrid matcher, not a trained classifier.
* The semantic matcher is described exactly as implemented — an off-the-shelf
  Sentence-Transformer (`all-MiniLM-L6-v2`) used through
  `sentence-transformers`, not a custom-trained model.
* Screenshots and the institute logo are placeholders until the real assets
  are dropped in; placeholders are visibly labelled as such.

## Front-matter placeholders still to be filled

`content_front.py → TITLE_PAGE["institution_lines"]` holds
`[INSTITUTE NAME]`, the affiliating-university line and the city line taken
from the official example cover; replace them (and add `assets/logo.png`)
when the example document is available, then rebuild.
