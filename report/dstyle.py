"""Shared drawing primitives for all SkillSync AI report diagrams.

Every diagram is generated programmatically with matplotlib so that the figures
in the report are original artwork (not copied from any external source) and can
be regenerated at any resolution.

Coordinate convention
---------------------
`new_ax(w_in, h_in)` returns an axes whose x-range is always 0..100 and whose
y-range is 0..(100 * h_in / w_in).  Because the aspect ratio of the data window
matches the aspect ratio of the figure, one unit is square in both directions,
so rounded corners, diamonds and circles render undistorted.
"""

import os
import textwrap

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import (  # noqa: E402
    Circle,
    Ellipse,
    FancyArrowPatch,
    FancyBboxPatch,
    Polygon,
    Rectangle,
)

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
INK = "#263238"
ARROW = "#455A64"

COLORS = {
    "ui": ("#E3F2FD", "#1565C0"),
    "api": ("#E8F5E9", "#2E7D32"),
    "service": ("#FFF3E0", "#E65100"),
    "ai": ("#FCE4EC", "#AD1457"),
    "data": ("#EDE7F6", "#4527A0"),
    "ext": ("#ECEFF1", "#37474F"),
    "decision": ("#FFF8E1", "#EF6C00"),
    "start": ("#E0F2F1", "#00695C"),
    "end": ("#FFEBEE", "#B71C1C"),
    "store": ("#F1F8E9", "#33691E"),
    "note": ("#FAFAFA", "#90A4AE"),
    "band": ("#FBFCFE", "#B0BEC5"),
    "actor": ("#E1F5FE", "#01579B"),
}

FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")

# Points per data-unit for a figure whose x-range is 0..100.
_PT_PER_UNIT_X = 72.0 / 100.0  # placeholder; recomputed per figure


def new_ax(w_in, h_in):
    """Create a borderless axes with square data units."""
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    y_max = 100.0 * h_in / w_in
    ax.set_xlim(0, 100)
    ax.set_ylim(0, y_max)
    ax.axis("off")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    ax._pt_per_unit = (w_in * 72.0) / 100.0
    return fig, ax


def _chars_per_line(width_units, fs, pt_per_unit):
    """Estimate how many characters fit on one line inside a box."""
    avg_char_pt = fs * 0.50
    avail_pt = (width_units - 1.4) * pt_per_unit
    return max(6, int(avail_pt / avg_char_pt))


def wrap(text, width_units, fs, pt_per_unit):
    """Word-wrap text to the width of its container box."""
    if not text:
        return ""
    n = _chars_per_line(width_units, fs, pt_per_unit)
    out = []
    for para in str(text).split("\n"):
        out.append(textwrap.fill(para, n) if para.strip() else "")
    return "\n".join(out)


def box(
    ax,
    cx,
    cy,
    w,
    h,
    text="",
    kind="service",
    fs=None,
    bold=False,
    lw=1.1,
    radius=1.4,
    align="center",
    color=None,
    zorder=3,
):
    """Draw a rounded rectangle centred at (cx, cy) with wrapped text."""
    fc, ec = COLORS[kind]
    if color:
        fc, ec = color
    fs = fs or (7.6 if w < 22 else 8.4)
    patch = FancyBboxPatch(
        (cx - w / 2.0, cy - h / 2.0),
        w,
        h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=lw,
        edgecolor=ec,
        facecolor=fc,
        mutation_aspect=1.0,
        zorder=zorder,
    )
    ax.add_patch(patch)
    if text:
        ppu = getattr(ax, "_pt_per_unit", 7.2)
        ha = "center" if align == "center" else ("left" if align == "left" else "right")
        tx = cx if align == "center" else (cx - w / 2.0 + 0.9 if align == "left" else cx + w / 2.0 - 0.9)
        ax.text(
            tx,
            cy,
            wrap(text, w, fs, ppu),
            ha=ha,
            va="center",
            fontsize=fs,
            color=INK,
            linespacing=1.32,
            fontweight="bold" if bold else "normal",
            zorder=zorder + 1,
        )
    return patch


def rect(ax, x0, y0, w, h, kind="band", lw=1.0, ls="-", zorder=1, alpha=1.0):
    """Plain (square-cornered) rectangle, mainly for swim-lane bands."""
    fc, ec = COLORS[kind]
    patch = Rectangle(
        (x0, y0), w, h, linewidth=lw, edgecolor=ec, facecolor=fc,
        linestyle=ls, zorder=zorder, alpha=alpha,
    )
    ax.add_patch(patch)
    return patch


def band(ax, x0, y0, w, h, label, kind="band", fs=8.2):
    """A labelled swim-lane band with a left-hand title gutter."""
    rect(ax, x0, y0, w, h, kind=kind, lw=1.0, zorder=1)
    ax.text(
        x0 + 1.2, y0 + h - 1.5, label, ha="left", va="top", fontsize=fs,
        fontweight="bold", color=COLORS[kind][1], zorder=2,
    )


def diamond(ax, cx, cy, w, h, text="", kind="decision", fs=7.4, lw=1.1):
    """Decision diamond centred at (cx, cy)."""
    fc, ec = COLORS[kind]
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3))
    if text:
        ppu = getattr(ax, "_pt_per_unit", 7.2)
        ax.text(
            cx, cy, wrap(text, w * 0.62, fs, ppu), ha="center", va="center",
            fontsize=fs, color=INK, linespacing=1.25, zorder=4,
        )


def store(ax, cx, cy, w, h, text="", kind="store", fs=7.6):
    """Cylinder shape used for data stores in DFDs and database design."""
    fc, ec = COLORS[kind]
    ry = h * 0.18
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2 + ry), w, h - 2 * ry,
                           facecolor=fc, edgecolor=ec, linewidth=1.1, zorder=3))
    ax.add_patch(Ellipse((cx, cy + h / 2 - ry), w, 2 * ry, facecolor=fc,
                         edgecolor=ec, linewidth=1.1, zorder=4))
    ax.add_patch(Ellipse((cx, cy - h / 2 + ry), w, 2 * ry, facecolor=fc,
                         edgecolor=ec, linewidth=1.1, zorder=3))
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2 + ry), w, h - 2 * ry,
                           facecolor=fc, edgecolor="none", zorder=4))
    if text:
        ppu = getattr(ax, "_pt_per_unit", 7.2)
        ax.text(cx, cy, wrap(text, w, fs, ppu), ha="center", va="center",
                fontsize=fs, color=INK, linespacing=1.28, zorder=5)


def arrow(ax, p1, p2, label="", fs=6.9, color=ARROW, lw=1.15, rad=0.0,
          style="-|>", label_offset=(0, 0), label_bg=True, zorder=6,
          label_color=None, ms=11, ls="-"):
    """Directed connector with an optional mid-point label."""
    patch = FancyArrowPatch(
        p1, p2, arrowstyle=style, mutation_scale=ms, linewidth=lw,
        color=color, connectionstyle=f"arc3,rad={rad}", zorder=zorder,
        shrinkA=0, shrinkB=0, linestyle=ls,
    )
    ax.add_patch(patch)
    if label:
        mx = (p1[0] + p2[0]) / 2.0 + label_offset[0]
        my = (p1[1] + p2[1]) / 2.0 + label_offset[1]
        ax.text(
            mx, my, label, ha="center", va="center", fontsize=fs,
            color=label_color or color, zorder=zorder + 1,
            bbox=(dict(boxstyle="round,pad=0.16", fc="white", ec="none", alpha=0.88)
                  if label_bg else None),
        )
    return patch


def elbow(ax, pts, label="", fs=6.9, color=ARROW, lw=1.15, label_at=None,
          label_offset=(0, 0), zorder=6, ms=11):
    """Orthogonal connector through a list of waypoints; arrowhead on last leg."""
    for i in range(len(pts) - 1):
        last = i == len(pts) - 2
        arrow(ax, pts[i], pts[i + 1], label="" , color=color, lw=lw,
              style="-|>" if last else "-", fs=fs, zorder=zorder, ms=ms)
    if label and label_at is not None:
        ax.text(label_at[0] + label_offset[0], label_at[1] + label_offset[1], label,
                ha="center", va="center", fontsize=fs, color=color, zorder=zorder + 1,
                bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="none", alpha=0.88))


def note(ax, cx, cy, w, h, text, fs=7.0, kind="note", title=None):
    """Small annotation box, optionally with a bold lead-in title."""
    fc, ec = COLORS[kind]
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0,rounding_size=1.0",
                                linewidth=0.9, edgecolor=ec, facecolor=fc,
                                linestyle=(0, (3, 2)), zorder=3))
    ppu = getattr(ax, "_pt_per_unit", 7.2)
    if title:
        ax.text(cx, cy + h / 2 - 0.9, title, ha="center", va="top", fontsize=fs + 0.2,
                color=COLORS[kind][1], fontweight="bold", zorder=4)
        ax.text(cx, cy - 0.9, wrap(text, w, fs, ppu), ha="center", va="center",
                fontsize=fs, color=INK, linespacing=1.34, zorder=4)
    else:
        ax.text(cx, cy, wrap(text, w, fs, ppu), ha="center", va="center", fontsize=fs,
                color=INK, linespacing=1.34, zorder=4)


def actor(ax, cx, cy, scale=1.0, label="", fs=7.4, kind="actor"):
    """Stick-figure actor for use-case diagrams."""
    _, ec = COLORS[kind]
    r = 1.5 * scale
    ax.add_patch(Circle((cx, cy + 4.2 * scale), r, fill=False, edgecolor=ec, lw=1.4, zorder=4))
    ax.plot([cx, cx], [cy + 2.7 * scale, cy - 1.6 * scale], color=ec, lw=1.4, zorder=4)
    ax.plot([cx - 2.6 * scale, cx + 2.6 * scale], [cy + 1.2 * scale, cy + 1.2 * scale],
            color=ec, lw=1.4, zorder=4)
    ax.plot([cx, cx - 2.2 * scale], [cy - 1.6 * scale, cy - 4.6 * scale], color=ec, lw=1.4, zorder=4)
    ax.plot([cx, cx + 2.2 * scale], [cy - 1.6 * scale, cy - 4.6 * scale], color=ec, lw=1.4, zorder=4)
    if label:
        ax.text(cx, cy - 6.4 * scale, label, ha="center", va="top", fontsize=fs,
                color=INK, fontweight="bold", zorder=5)


def save(fig, name, dpi=210):
    """Write the figure to report/figures/<name>.png and close it."""
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.10, facecolor="white")
    plt.close(fig)
    return path
