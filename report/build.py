"""One-command build of the SkillSync AI mini-project report.

Usage (from the repository root or this directory):

    /home/user/.venv/bin/python report/build.py                # rebuild PDF + DOCX
    /home/user/.venv/bin/python report/build.py --diagrams     # also regenerate figures

Outputs
-------
report/output/SkillSync_AI_Mini_Project_Report.pdf
report/output/SkillSync_AI_Mini_Project_Report.docx
report/pagenums.json   (intermediate: page numbers shared by both formats)
"""

import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main(argv):
    if "--diagrams" in argv:
        for mod in ("diagrams_a.py", "diagrams_b.py", "diagrams_c.py"):
            print("rendering", mod)
            runpy.run_path(os.path.join(HERE, mod), run_name="__main__")
    import build_pdf
    import build_docx
    pdf = build_pdf.main()
    docx = build_docx.build()
    import pymupdf
    n = pymupdf.open(pdf).page_count
    print(f"\nPDF : {pdf}  ({n} pages)")
    print(f"DOCX: {docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
