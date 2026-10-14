"""Intermediate representation: assembles every content module, assigns
chapter-relative numbers to figures, tables and listings, and collects the
entries for the table of contents, list of figures and list of tables."""

from content_c1 import CH1_5
from content_c2 import CH6_10
from content_c3 import CH11_END
from content_front import FRONT_BLOCKS, TITLE_PAGE

BLOCKS = list(FRONT_BLOCKS) + list(CH1_5) + list(CH6_10) + list(CH11_END)

TOC = []      # (level, text, page-placeholder)
LOF = []      # (num_label, caption)
LOT = []      # (num_label, caption)
LOL = []      # listings

_chapter = None
_fig_n = _tab_n = _lst_n = 0


def _chap_label(c):
    return str(c) if isinstance(c, int) else str(c)


for i, blk in enumerate(BLOCKS):
    kind = blk[0]
    if kind == "chapter":
        _chapter = blk[1]
        _fig_n = _tab_n = _lst_n = 0
        if isinstance(_chapter, int):
            TOC.append((0, f"{_chapter}. {blk[2]}", None))
        else:
            TOC.append((0, f"APPENDIX {_chapter} — {blk[2]}", None))
        BLOCKS[i] = (kind, blk[1], blk[2], None)
    elif kind == "front_heading":
        TOC.append((0, blk[1].title() if blk[1].isupper() else blk[1], None))
    elif kind == "h2":
        TOC.append((1, blk[1], None))
    elif kind == "h3":
        TOC.append((2, blk[1], None))
    elif kind == "fig":
        _fig_n += 1
        num = f"{_chap_label(_chapter)}.{_fig_n}"
        d = dict(blk[1])
        d["num"] = num
        BLOCKS[i] = (kind, d)
        LOF.append((f"Figure {num}", d["caption"]))
    elif kind == "table":
        d = dict(blk[1])
        if d.get("caption"):
            _tab_n += 1
            num = f"{_chap_label(_chapter)}.{_tab_n}"
            d["num"] = num
            LOT.append((f"Table {num}", d["caption"]))
        else:
            d["num"] = None
        BLOCKS[i] = (kind, d)
    elif kind == "code":
        _lst_n += 1
        d = dict(blk[1])
        d["num"] = f"{_chap_label(_chapter)}.{_lst_n}"
        BLOCKS[i] = (kind, d)
        LOL.append((f"Listing {d['num']}", d["caption"]))
    elif kind == "refs":
        BLOCKS[i] = (kind, list(blk[1]))

REF_COUNT = len(BLOCKS[-1][1]) if BLOCKS[-1][0] == "refs" else 0
for i, blk in enumerate(BLOCKS):
    if blk[0] == "refs":
        TOC.append((0, "REFERENCES", None))
    if blk[0] == "chapter" and isinstance(blk[1], str):
        pass

# References and appendices appear after chapter 15; make sure TOC order is right:
# the loop above already appended in document order, except REFERENCES which is
# appended where the refs block occurs (correct) and appendices which are chapters
# with string numbers (handled by the 'chapter' branch).
