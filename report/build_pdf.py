"""PDF renderer for the SkillSync AI mini-project report (reportlab platypus).

Page numbering is resolved with a two-pass build: the first pass reserves a
fixed number of pages for the table of contents, list of figures and list of
tables while recording the physical page of every heading, figure, table and
listing; the second pass fills those reserved pages with the recorded numbers.
"""

import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, Image, KeepTogether, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from PIL import Image as PILImage

import ir

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(HERE, "figures")
SHOT_DIR = os.path.join(HERE, "screenshots")
OUT = os.path.join(HERE, "output", "SkillSync_AI_Mini_Project_Report.pdf")

FIG_ALIASES = {"dfd0": "dfd_level0", "dfd1": "dfd_level1", "er": "er_diagram"}

PAGE_W, PAGE_H = A4
M_LEFT, M_RIGHT, M_TOP, M_BOT = 3.0 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm
TEXT_W = PAGE_W - M_LEFT - M_RIGHT

TOC_PAGES, LOF_PAGES, LOT_PAGES = 3, 1, 1

_ss = getSampleStyleSheet()
S = {}
S["body"] = ParagraphStyle("body", parent=_ss["Normal"], fontName="Times-Roman",
                           fontSize=12, leading=19.5, alignment=TA_JUSTIFY,
                           spaceAfter=7, firstLineIndent=0)
S["bodyc"] = ParagraphStyle("bodyc", parent=S["body"], alignment=TA_CENTER,
                            firstLineIndent=0)
S["chap"] = ParagraphStyle("chap", parent=_ss["Normal"], fontName="Times-Bold",
                           fontSize=16, leading=22, alignment=TA_CENTER,
                           spaceBefore=6, spaceAfter=18)
S["front"] = ParagraphStyle("front", parent=S["chap"], fontSize=15, leading=21,
                            spaceAfter=16)
S["h2"] = ParagraphStyle("h2", parent=_ss["Normal"], fontName="Times-Bold",
                         fontSize=13.5, leading=19, spaceBefore=14, spaceAfter=7)
S["h3"] = ParagraphStyle("h3", parent=_ss["Normal"], fontName="Times-BoldItalic",
                         fontSize=12, leading=17, spaceBefore=10, spaceAfter=6)
S["bullet"] = ParagraphStyle("bullet", parent=S["body"], leftIndent=20,
                             bulletIndent=8, spaceAfter=5)
S["num"] = ParagraphStyle("num", parent=S["body"], leftIndent=24, bulletIndent=8,
                          spaceAfter=5)
S["caption"] = ParagraphStyle("caption", parent=_ss["Normal"], fontName="Times-Bold",
                              fontSize=10.5, leading=14, alignment=TA_CENTER,
                              spaceBefore=6, spaceAfter=12)
S["tabcap"] = ParagraphStyle("tabcap", parent=S["caption"], spaceBefore=10,
                             spaceAfter=6)
S["th"] = ParagraphStyle("th", parent=_ss["Normal"], fontName="Times-Bold",
                         fontSize=9.5, leading=12.5, alignment=TA_LEFT)
S["td"] = ParagraphStyle("td", parent=_ss["Normal"], fontName="Times-Roman",
                         fontSize=9.5, leading=12.5, alignment=TA_LEFT)
S["code"] = ParagraphStyle("code", parent=_ss["Normal"], fontName="Courier",
                           fontSize=8.2, leading=11.0)
S["eq"] = ParagraphStyle("eq", parent=_ss["Normal"], fontName="Times-Italic",
                         fontSize=12, leading=18, alignment=TA_CENTER,
                         spaceBefore=8, spaceAfter=8)
S["ref"] = ParagraphStyle("ref", parent=S["body"], leftIndent=26,
                          firstLineIndent=-26, spaceAfter=6, fontSize=11,
                          leading=17)
S["toc0"] = ParagraphStyle("toc0", parent=_ss["Normal"], fontName="Times-Bold",
                           fontSize=11.5, leading=17, spaceBefore=4)
S["toc1"] = ParagraphStyle("toc1", parent=_ss["Normal"], fontName="Times-Roman",
                           fontSize=11.5, leading=16.5, leftIndent=16)
S["toc2"] = ParagraphStyle("toc2", parent=_ss["Normal"], fontName="Times-Roman",
                           fontSize=11, leading=16, leftIndent=32)
S["sig"] = ParagraphStyle("sig", parent=_ss["Normal"], fontName="Times-Roman",
                          fontSize=11.5, leading=16, alignment=TA_LEFT)
S["ph"] = ParagraphStyle("ph", parent=_ss["Normal"], fontName="Times-Italic",
                         fontSize=10, leading=14, alignment=TA_CENTER,
                         textColor=colors.HexColor("#546E7A"))


def _roman(n):
    vals = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"),
            (90, "xc"), (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"),
            (4, "iv"), (1, "i")]
    out = ""
    for v, sym in vals:
        while n >= v:
            out += sym
            n -= v
    return out


class Marker(Flowable):
    """Zero-height flowable used to record the page of a numbered element."""

    def __init__(self, key):
        Flowable.__init__(self)
        self.key = key
        self.width = 0
        self.height = 0

    def draw(self):
        pass


class Doc(BaseDocTemplate):
    def __init__(self, path, **kw):
        BaseDocTemplate.__init__(self, path, pagesize=A4, **kw)
        self.markers = {}
        frame = Frame(M_LEFT, M_BOT, TEXT_W, PAGE_H - M_TOP - M_BOT, id="main",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="title", frames=[frame], onPage=self._on_title),
            PageTemplate(id="front", frames=[frame], onPage=self._on_front),
            PageTemplate(id="body", frames=[frame], onPage=self._on_body),
        ])
        self.front_count = 0
        self.body_count = 0
        self._body_started = False

    def afterFlowable(self, flowable):
        if isinstance(flowable, Marker):
            self.markers[flowable.key] = self.page

    def _on_title(self, canv, doc):
        pass

    def _on_front(self, canv, doc):
        self.front_count += 1
        canv.saveState()
        canv.setFont("Times-Roman", 11)
        canv.drawCentredString(PAGE_W / 2, 1.4 * cm, _roman(self.front_count + 1))
        canv.restoreState()

    def _on_body(self, canv, doc):
        self.body_count += 1
        canv.saveState()
        canv.setFont("Times-Roman", 10)
        canv.setStrokeColor(colors.HexColor("#90A4AE"))
        canv.setLineWidth(0.6)
        canv.line(M_LEFT, PAGE_H - 1.7 * cm, PAGE_W - M_RIGHT, PAGE_H - 1.7 * cm)
        canv.drawString(M_LEFT, PAGE_H - 1.55 * cm,
                        "AI-Driven Employment and Skill Matching Portal for Youth Development")
        canv.drawRightString(PAGE_W - M_RIGHT, PAGE_H - 1.55 * cm, "SkillSync AI")
        canv.line(M_LEFT, 1.8 * cm, PAGE_W - M_RIGHT, 1.8 * cm)
        canv.setFont("Times-Roman", 11)
        canv.drawCentredString(PAGE_W / 2, 1.3 * cm, str(self.body_count))
        canv.restoreState()


# ---------------------------------------------------------------------------
# story construction
# ---------------------------------------------------------------------------
def _table_flow(d):
    headers, rows, widths = d["headers"], d["rows"], d.get("widths")
    data = [[Paragraph(str(h), S["th"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), S["td"]) for c in r])
    colw = [TEXT_W * w for w in widths] if widths else None
    t = Table(data, colWidths=colw, repeatRows=1, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#78909C")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EAF6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _figure_flow(d):
    key = d["key"]
    target_w = TEXT_W * d.get("width", 0.95)
    max_h = PAGE_H - M_TOP - M_BOT - 3.2 * cm
    path = None
    if d.get("kind") == "screenshot":
        path = None
        for ext in ("png", "jpg", "jpeg"):
            cand = os.path.join(SHOT_DIR, f"{key}.{ext}")
            if os.path.exists(cand):
                path = cand
                break
    else:
        path = None
        base = FIG_ALIASES.get(key, key)
        for cand in (os.path.join(FIG_DIR, f"fig_{base}.png"),
                     os.path.join(FIG_DIR, f"{base}.png")):
            if os.path.exists(cand):
                path = cand
                break

    if path:
        with PILImage.open(path) as im:
            pw, ph = im.size
        w = target_w
        h = w * ph / pw
        if h > max_h:
            h = max_h
            w = h * pw / ph
        img = Image(path, width=w, height=h)
        img.hAlign = "CENTER"
        inner = [img]
    else:
        if d.get("kind") == "screenshot":
            note = "[ SCREENSHOT TO BE INSERTED ]"
            help_txt = (f"Figure {d['num']} placeholder — capture this screen from the running "
                        f"application and save it as screenshots/{key}.png (or .jpg), then rebuild "
                        f"the report; the image is embedded automatically.")
        else:
            note = "[ DIAGRAM ASSET MISSING ]"
            help_txt = (f"Figure {d['num']} placeholder — regenerate the diagram assets with "
                        f"'python make_diagrams.py'; expected file figures/fig_{key}.png.")
        inner = [Table([[Paragraph(note, S["ph"])],
                        [Paragraph(help_txt, S["ph"])]],
                       colWidths=[target_w], rowHeights=[6.5 * cm, None]) ]
        inner[0].setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#90A4AE")),
            ("LINEBELOW", (0, 0), (0, 0), 0.6, colors.HexColor("#B0BEC5")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
    cap = Paragraph(f"Figure {d['num']}: {d['caption']}", S["caption"])
    if d.get("page"):
        return inner + [cap]
    return [KeepTogether(inner + [cap])]


def _titlepage(tp):
    st = []
    logo = os.path.join(HERE, tp["logo"])
    if os.path.exists(logo):
        with PILImage.open(logo) as im:
            pw, ph = im.size
        w = 3.4 * cm
        img = Image(logo, width=w, height=w * ph / pw)
        img.hAlign = "CENTER"
        st.append(img)
    else:
        st.append(Table([[Paragraph("[ INSTITUTE LOGO ]", S["ph"])]],
                        colWidths=[4.0 * cm], rowHeights=[2.2 * cm]))
        st[-1].setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#90A4AE")),
                                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        st[-1].hAlign = "CENTER"
    st.append(Spacer(1, 0.5 * cm))
    for line in tp["institution_lines"]:
        st.append(Paragraph(line, ParagraphStyle("inst", parent=S["chap"], fontSize=14,
                                                  leading=20, spaceAfter=2)))
    st.append(Spacer(1, 0.9 * cm))
    st.append(Paragraph(tp["report_label"], S["chap"]))
    st.append(Paragraph(tp["title"], ParagraphStyle("t", parent=S["chap"], fontSize=17,
                                                    leading=24, spaceAfter=6)))
    st.append(Paragraph(tp["subtitle"], ParagraphStyle("s", parent=S["chap"], fontSize=12.5,
                                                       leading=17, fontName="Times-Italic",
                                                       spaceAfter=14)))
    st.append(Paragraph(tp["purpose"], ParagraphStyle("p", parent=S["body"], alignment=TA_CENTER,
                                                      fontSize=11.5, leading=17)))
    st.append(Spacer(1, 0.9 * cm))
    st.append(Paragraph("Submitted by", ParagraphStyle("sb", parent=S["body"], alignment=TA_CENTER,
                                                       fontSize=11.5, fontName="Times-Italic")))
    rows = [[Paragraph(f"<b>{name}</b>", S["bodyc"]), Paragraph(f"({reg})", S["bodyc"])]
            for name, reg in tp["student"]]
    t = Table(rows, colWidths=[8 * cm, 5 * cm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    t.hAlign = "CENTER"
    st.append(t)
    st.append(Spacer(1, 0.35 * cm))
    st.append(Paragraph(tp["degree_line"], ParagraphStyle("d", parent=S["chap"], fontSize=12.5,
                                                          leading=17, spaceAfter=2)))
    st.append(Paragraph(tp["year_sem"], ParagraphStyle("y", parent=S["body"], alignment=TA_CENTER,
                                                       fontSize=11.5)))
    st.append(Spacer(1, 0.9 * cm))
    rows_n = max(len(tp["guide"]), len(tp["hod"]))
    guide = []
    for i in range(rows_n):
        gl = tp["guide"][i] if i < len(tp["guide"]) else ""
        hl = tp["hod"][i] if i < len(tp["hod"]) else ""
        if i == 0:
            gl, hl = f"<b>{gl}</b>", f"<b>{hl}</b>"
        guide.append([Paragraph(gl, S["sig"]), Paragraph(hl, S["sig"])])
    t2 = Table(guide, colWidths=[TEXT_W / 2, TEXT_W / 2])
    t2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (0, -1), "LEFT"),
                            ("ALIGN", (1, 0), (1, -1), "RIGHT")]))
    st.append(t2)
    st.append(Spacer(1, 0.9 * cm))
    st.append(Paragraph(tp["department"], ParagraphStyle("dep", parent=S["chap"], fontSize=13,
                                                         leading=18, spaceAfter=3)))
    st.append(Paragraph(tp["place_date"], ParagraphStyle("pd", parent=S["body"],
                                                         alignment=TA_CENTER, fontSize=11.5)))
    return st


def _toc_block(entries, pages_by_key, kind, heading, style_map):
    st = [Paragraph(heading, S["front"])]
    for level, text, _ in entries:
        pg = pages_by_key.get(_toc_key(kind, level, text), "")
        st.append(Paragraph(f"{text}"
                            f"<font face='Times-Roman'>{'.' * max(2, 60 - len(text))}</font>"
                            f"<b>&nbsp;{pg}</b>", style_map[level]))
    return st


def _toc_key(kind, level, text):
    return f"{kind}:{level}:{text}"


def build_story(pages):
    """pages: dict mapping toc/lof/lot keys to display page strings, or None."""
    st = []
    tp = ir.TITLE_PAGE
    st += _titlepage(tp)
    st.append(NextPageTemplate("front"))
    st.append(PageBreak())

    for blk in ir.BLOCKS:
        kind = blk[0]
        if kind == "titlepage":
            continue
        if kind == "front_heading":
            st.append(Paragraph(blk[1], S["front"]))
        elif kind == "p":
            st.append(Paragraph(blk[1], S["body"]))
        elif kind == "sig_two":
            rows = [[Paragraph("<br/>".join(blk[1]["left"]), S["sig"]),
                     Paragraph("<br/>".join(blk[1]["right"]), S["sig"])]]
            t = Table(rows, colWidths=[TEXT_W / 2, TEXT_W / 2])
            t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("ALIGN", (1, 0), (1, -1), "RIGHT")]))
            st.append(Spacer(1, 1.6 * cm))
            st.append(t)
        elif kind == "sig_one":
            st.append(Spacer(1, 1.6 * cm))
            st.append(Paragraph("<br/>".join(blk[1]["lines"]), S["sig"]))
        elif kind == "table":
            d = blk[1]
            if d.get("num"):
                st.append(Marker(_toc_key("lot", 0, d["num"])))
                st.append(Paragraph(f"Table {d['num']}: {d['caption']}", S["tabcap"]))
            st.append(_table_flow(d))
            st.append(Spacer(1, 0.3 * cm))
        elif kind == "chapter":
            st.append(NextPageTemplate("body"))
            st.append(PageBreak())
            num, title = blk[1], blk[2]
            label = f"{num}. {title}" if isinstance(num, int) else f"APPENDIX {num}<br/>{title}"
            st.append(Marker(_toc_key("toc", 0,
                                      f"{num}. {title}" if isinstance(num, int)
                                      else f"APPENDIX {num} — {title}")))
            st.append(Paragraph(label, S["chap"]))
        elif kind == "h2":
            st.append(Marker(_toc_key("toc", 1, blk[1])))
            st.append(Paragraph(blk[1], S["h2"]))
        elif kind == "h3":
            st.append(Marker(_toc_key("toc", 2, blk[1])))
            st.append(Paragraph(blk[1], S["h3"]))
        elif kind == "bullets":
            for b in blk[1]:
                st.append(Paragraph(b, S["bullet"], bulletText="•"))
        elif kind == "nums":
            for i, b in enumerate(blk[1], 1):
                st.append(Paragraph(b, S["num"], bulletText=f"{i}."))
        elif kind == "fig":
            d = blk[1]
            if d.get("page"):
                st.append(PageBreak())
            st.append(Marker(_toc_key("lof", 0, d["num"])))
            st += _figure_flow(d)
        elif kind == "code":
            d = blk[1]
            st.append(Paragraph(f"Listing {d['num']}: {d['caption']}", S["tabcap"]))
            pre = Table([[Paragraph(d["text"].replace("&", "&amp;").replace("<", "&lt;")
                                    .replace(">", "&gt;").replace("\n", "<br/>"), S["code"])]],
                        colWidths=[TEXT_W])
            pre.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#90A4AE")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            st.append(pre)
            st.append(Spacer(1, 0.3 * cm))
        elif kind == "eq":
            text, n = blk[1], blk[2]
            st.append(Paragraph(f"{text}&nbsp;&nbsp;&nbsp;({n})", S["eq"]))
        elif kind == "refs":
            st.append(Paragraph("REFERENCES", S["chap"]))
            st.append(Marker(_toc_key("toc", 0, "REFERENCES")))
            for i, r in enumerate(blk[1], 1):
                st.append(Paragraph(f"[{i}]&nbsp;&nbsp;{r}", S["ref"]))
        elif kind == "pagebreak":
            st.append(PageBreak())

    # ---- front-matter lists are inserted after building; see assemble() ----
    return st


def _front_lists_story(pages):
    """TOC / LOF / LOT / abbreviations pages are part of the front matter; they
    must appear before the body.  Because the story is linear, assemble()
    splits construction: front blocks, lists, body blocks."""
    raise NotImplementedError


PAGE_TEXT_H = PAGE_H - M_TOP - M_BOT


def _reserve(st, pages_n):
    """Fill the reserved list pages with blank space so that pass 1 and pass 2
    paginate identically."""
    total = pages_n * PAGE_TEXT_H * 0.97 - 45
    n = max(1, int(total / 12.2))
    for _ in range(n):
        st.append(Spacer(1, 12.2))


def assemble(pages):
    """Build the complete story: title page, certificate..abstract, the three
    front-matter lists, the abbreviations table, then the body."""
    st = []
    st += _titlepage(ir.TITLE_PAGE)
    st.append(NextPageTemplate("front"))

    front_blocks, body_blocks = [], []
    seen_body = False
    for blk in ir.BLOCKS:
        if blk[0] == "chapter":
            seen_body = True
        (body_blocks if seen_body else front_blocks).append(blk)

    # split front matter around the abbreviations list
    cut = next(i for i, b in enumerate(front_blocks)
               if b[0] == "front_heading" and b[1] == "LIST OF ABBREVIATIONS")
    pre, post = front_blocks[:cut], front_blocks[cut:]

    for blk in pre:
        st += _render_front(blk)

    # ---- table of contents -------------------------------------------------
    st.append(PageBreak())
    st.append(Marker("frontpage:toc"))
    st.append(Paragraph("TABLE OF CONTENTS", S["front"]))
    if pages:
        for level, text, _ in ir.TOC:
            pg = pages["toc"].get(text, "")
            st.append(Paragraph(
                f"{text}<font color='#90A4AE'>{'.' * max(3, 80 - len(text))}</font> {pg}",
                S[f"toc{level}"]))
    else:
        _reserve(st, TOC_PAGES)

    # ---- list of figures ---------------------------------------------------
    st.append(PageBreak())
    st.append(Marker("frontpage:lof"))
    st.append(Paragraph("LIST OF FIGURES", S["front"]))
    if pages:
        for label, cap in ir.LOF:
            st.append(Paragraph(
                f"{label}: {cap}<font color='#90A4AE'>{'.' * max(3, 62 - len(cap))}</font> "
                f"{pages['lof'].get(label, '')}", S["toc1"]))
    else:
        _reserve(st, LOF_PAGES)

    # ---- list of tables ----------------------------------------------------
    st.append(PageBreak())
    st.append(Marker("frontpage:lot"))
    st.append(Paragraph("LIST OF TABLES", S["front"]))
    if pages:
        for label, cap in ir.LOT:
            st.append(Paragraph(
                f"{label}: {cap}<font color='#90A4AE'>{'.' * max(3, 62 - len(cap))}</font> "
                f"{pages['lot'].get(label, '')}", S["toc1"]))
    else:
        _reserve(st, LOT_PAGES)

    # ---- abbreviations then body -------------------------------------------
    for blk in post:
        st += _render_front(blk)
    for blk in body_blocks:
        st += _render_body(blk)
    return st


def _render_front(blk):
    kind = blk[0]
    if kind == "titlepage":
        return []
    if kind == "front_heading":
        return [PageBreak(),
                Marker(_toc_key("toc", 0, blk[1].title() if blk[1].isupper() else blk[1])),
                Paragraph(blk[1], S["front"])]
    if kind == "p":
        return [Paragraph(blk[1], S["body"])]
    if kind == "sig_two":
        rows = [[Paragraph("<br/>".join(blk[1]["left"]), S["sig"]),
                 Paragraph("<br/>".join(blk[1]["right"]), S["sig"])]]
        t = Table(rows, colWidths=[TEXT_W / 2, TEXT_W / 2])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("ALIGN", (1, 0), (1, -1), "RIGHT")]))
        return [Spacer(1, 1.4 * cm), t]
    if kind == "sig_one":
        return [Spacer(1, 1.4 * cm), Paragraph("<br/>".join(blk[1]["lines"]), S["sig"])]
    if kind == "table":
        d = blk[1]
        out = []
        if d.get("num"):
            out.append(Paragraph(f"Table {d['num']}: {d['caption']}", S["tabcap"]))
        out.append(_table_flow(d))
        return out
    return []


def _render_body(blk):
    kind = blk[0]
    if kind == "chapter":
        num, title = blk[1], blk[2]
        label = f"{num}. {title}" if isinstance(num, int) else f"APPENDIX {num}<br/>{title}"
        key = f"{num}. {title}" if isinstance(num, int) else f"APPENDIX {num} — {title}"
        return [NextPageTemplate("body"), PageBreak(), Marker(_toc_key("toc", 0, key)),
                Paragraph(label, S["chap"])]
    if kind == "h2":
        return [Marker(_toc_key("toc", 1, blk[1])), Paragraph(blk[1], S["h2"])]
    if kind == "h3":
        return [Marker(_toc_key("toc", 2, blk[1])), Paragraph(blk[1], S["h3"])]
    if kind == "p":
        return [Paragraph(blk[1], S["body"])]
    if kind == "bullets":
        return [Paragraph(b, S["bullet"], bulletText="•") for b in blk[1]]
    if kind == "nums":
        return [Paragraph(b, S["num"], bulletText=f"{i}.") for i, b in enumerate(blk[1], 1)]
    if kind == "table":
        d = blk[1]
        out = []
        if d.get("num"):
            out.append(Marker(_toc_key("lot", 0, d["num"])))
            out.append(Paragraph(f"Table {d['num']}: {d['caption']}", S["tabcap"]))
        out.append(_table_flow(d))
        out.append(Spacer(1, 0.25 * cm))
        return out
    if kind == "fig":
        d = blk[1]
        out = []
        if d.get("page"):
            out.append(PageBreak())
        out.append(Marker(_toc_key("lof", 0, d["num"])))
        out += _figure_flow(d)
        return out
    if kind == "code":
        d = blk[1]
        pre = Table([[Paragraph(d["text"].replace("&", "&amp;").replace("<", "&lt;")
                                .replace(">", "&gt;").replace("\n", "<br/>"), S["code"])]],
                    colWidths=[TEXT_W])
        pre.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#90A4AE")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return [Paragraph(f"Listing {d['num']}: {d['caption']}", S["tabcap"]), pre,
                Spacer(1, 0.25 * cm)]
    if kind == "eq":
        return [Paragraph(f"{blk[1]}&nbsp;&nbsp;&nbsp;({blk[2]})", S["eq"])]
    if kind == "refs":
        out = [PageBreak(), Marker(_toc_key("toc", 0, "REFERENCES")),
               Paragraph("REFERENCES", S["chap"])]
        for i, r in enumerate(blk[1], 1):
            out.append(Paragraph(f"[{i}]&nbsp;&nbsp;{r}", S["ref"]))
        return out
    return []


def run_pass(pages):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc = Doc(OUT)
    story = assemble(pages)
    doc.build(story)
    return doc


def compute_pages(doc):
    """Convert recorded physical pages into display page strings."""
    body_start = doc.markers.get(_toc_key("toc", 0, "1. INTRODUCTION"))
    front_count = body_start - 1
    pages = {"toc": {}, "lof": {}, "lot": {}}
    for key, phys in doc.markers.items():
        if key.startswith("frontpage:"):
            continue
        kind, level, text = key.split(":", 2)
        disp = _roman(phys) if phys <= front_count else str(phys - front_count)
        if kind == "toc":
            pages["toc"][text] = disp
        elif kind == "lof":
            pages["lof"][f"Figure {text}"] = disp
        elif kind == "lot":
            pages["lot"][f"Table {text}"] = disp
    return pages, front_count


def main():
    pages = None
    for attempt in range(4):
        doc = run_pass(pages)
        new_pages, front_count = compute_pages(doc)
        if pages == new_pages:
            break
        pages = new_pages
    os.makedirs(HERE, exist_ok=True)
    with open(os.path.join(HERE, "pagenums.json"), "w") as f:
        json.dump({"pages": pages, "front_count": front_count}, f, indent=2)
    print("PDF written:", OUT)
    print("front-matter pages:", front_count)
    return OUT


if __name__ == "__main__":
    main()
