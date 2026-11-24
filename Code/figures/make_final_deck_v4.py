"""
Final presentation deck (2026-11-25): cover + 30 slides in 8 sections.

1 Introduction (1-3) · 2 Grouping (4-9) · 3 Burn detection (10-18) · 4 Tehsil measurement (19-20)
5 Positive deviance (21-22) · 6 Validation (23-24) · 7 Public drivers (25-27) · 8 Impact and conclusion (28-30)
Every slide: one sentence title, one main visual, an "In short" line at the bottom, a section strip on top.
Figures are read from outputs/figures (built by the figure scripts in Code/figures).

Run:  python Code/figures/make_final_deck_v4.py
Out:  report/final_deck_v4.pptx   (git-ignored: embeds PlanetScope imagery)
"""
import json
from pathlib import Path

import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "outputs" / "figures"
FF = FIG / "final"
RAWF = FF / "raw"
OUT = ROOT / "report" / "final_deck_v4.pptx"

# Palette: charcoal text, one ember accent, green only for "positive deviant / good", red for "bad".
DARK = RGBColor(0x1F, 0x1A, 0x17)
EMBER = RGBColor(0xE4, 0x57, 0x2E)
GOOD = RGBColor(0x0F, 0x7B, 0x4A)
BAD = RGBColor(0xC0, 0x39, 0x2B)
TEXT = RGBColor(0x1F, 0x1A, 0x17)
MUTED = RGBColor(0x6B, 0x65, 0x60)
LIGHT = RGBColor(0xB5, 0xAE, 0xA8)
PANEL = RGBColor(0xF1, 0xF0, 0xEE)
TINT = RGBColor(0xFB, 0xE9, 0xE2)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ON_DARK_MUTED = RGBColor(0xC9, 0xC2, 0xBC)
GROUP = {"Central": RGBColor(0x2A, 0x78, 0xD6), "South-west": RGBColor(0xEB, 0x68, 0x34),
         "Foothills": RGBColor(0x1B, 0xAF, 0x7A)}
HEAD, BODY = "Cambria", "Calibri"

W, H = 13.333, 7.5
M = 0.6
TITLE_Y, TITLE_H = 0.4, 0.85
TOP = 1.45
SECTIONS = ["Introduction", "Grouping", "Burn detection", "Measurement", "Positive deviance", "Validation",
            "Drivers", "Impact"]

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]
PAGES = []

MASTER = pd.read_csv(ROOT / "Data" / "punjab_homogeneous_grouping_master_transformed.csv").set_index("lgd_tehsil_name")
GX = json.loads((FF / "f18_gower_example.json").read_text())


# ---------------------------------------------------------------- helpers

def fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def text(slide, x, y, w, h, runs, size=16, color=TEXT, font=BODY, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, italic=False, margin=0.05, space=0):
    """runs: str, or list of paragraphs; each paragraph a str or list of (text, {opts})."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", Inches(margin))
    paras = [runs] if isinstance(runs, str) else runs
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if space:
            p.space_after = Pt(space)
        parts = [(para, {})] if isinstance(para, str) else para
        for t, o in parts:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = o.get("font", font)
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", italic)
            f.color.rgb = o.get("color", color)
    return box


def bullets(slide, x, y, w, h, items, size=15, color=TEXT, gap=8):
    """items: list of str or (bold lead, rest)."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", Inches(0.05))
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(int(Inches(0.25))))
        pPr.set("indent", str(int(-Inches(0.25))))
        pPr.append(pPr.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}buChar", {"char": "•"}))
        lead, rest = (it, "") if isinstance(it, str) else it
        for t, b in ((lead, not isinstance(it, str)), (rest, False)):
            if t:
                r = p.add_run()
                r.text = t
                r.font.name, r.font.size, r.font.bold = BODY, Pt(size), b
                r.font.color.rgb = color
    return box


def panel(slide, x, y, w, h, color=PANEL, rounded=True):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    fill(shp, color)
    if rounded:
        shp.adjustments[0] = 0.06
    return shp


def image(slide, path, x, y, w, h, align="center"):
    iw, ih = Image.open(path).size
    s = min(w / iw, h / ih)
    pw, ph = iw * s, ih * s
    px = x + (w - pw) / 2 if align == "center" else (x if align == "left" else x + w - pw)
    return slide.shapes.add_picture(str(path), Inches(px), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))


def caption(slide, x, y, w, t):
    text(slide, x, y, w, 0.35, t, size=11, color=MUTED, italic=True, margin=0)


def stat(slide, x, y, w, big, label, color=EMBER, big_size=32):
    text(slide, x, y, w, 0.7, big, size=big_size, font=HEAD, bold=True, color=color, margin=0)
    text(slide, x, y + 0.68, w, 0.75, label, size=13, color=MUTED, margin=0)


def card(slide, x, y, w, h, head, body, head_color=TEXT, size=14):
    panel(slide, x, y, w, h)
    text(slide, x + 0.2, y + 0.13, w - 0.4, 0.45, head, size=16, bold=True, color=head_color, margin=0)
    if isinstance(body, list):
        bullets(slide, x + 0.15, y + 0.55, w - 0.3, h - 0.6, body, size=size, gap=4)
    else:
        text(slide, x + 0.2, y + 0.58, w - 0.4, h - 0.65, body, size=size, margin=0)


def table(slide, x, y, w, rows, col_w, size=13, row_h=0.4, first_bold=True):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    tb = shp.table
    for j, cw in enumerate(col_w):
        tb.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tb.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            cell = tb.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            color = None
            if isinstance(val, tuple):
                val, color = val
            tf = cell.text_frame
            tf.word_wrap = True
            tf.paragraphs[0].text = ""
            r = tf.paragraphs[0].add_run()
            r.text = str(val)
            r.font.name, r.font.size = BODY, Pt(size)
            cell.fill.solid()
            if i == 0:
                r.font.bold, r.font.color.rgb = True, WHITE
                cell.fill.fore_color.rgb = DARK
            else:
                r.font.bold = first_bold and j == 0
                r.font.color.rgb = color or TEXT
                cell.fill.fore_color.rgb = PANEL if i % 2 else WHITE
    return shp


def arrow(slide, x, y, w=0.35, h=0.35, color=MUTED, down=False):
    a = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW if down else MSO_SHAPE.RIGHT_ARROW,
                               Inches(x), Inches(y), Inches(w), Inches(h))
    fill(a, color)


def steps_col(slide, x, y, w, items, size=14, gap=0.12, h=0.78, start=1, color=EMBER):
    """Vertical numbered steps: items = list of (head, body)."""
    for i, (h_, b_) in enumerate(items):
        yy = y + i * (h + gap)
        c = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(yy + 0.03), Inches(0.4), Inches(0.4))
        fill(c, color)
        text(slide, x, yy + 0.03, 0.4, 0.4, str(i + start), size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE, margin=0)
        text(slide, x + 0.55, yy, w - 0.55, h, [[(h_, {"bold": True}), ("  " + b_, {})]], size=size, margin=0)


def note_bar(slide, y, lead, body, h=0.8, size=14, w=None, x=None):
    x = M if x is None else x
    w = W - 2 * M if w is None else w
    panel(slide, x, y, w, h)
    text(slide, x + 0.25, y, w - 0.5, h, [[(lead + " ", {"bold": True, "color": EMBER}), (body, {})]],
         size=size, anchor=MSO_ANCHOR.MIDDLE, margin=0)


def strip(slide, section):
    dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(M), Inches(0.22), Inches(0.14), Inches(0.14))
    fill(dot, EMBER)
    text(slide, M + 0.2, 0.12, 4, 0.32, section.upper(), size=11, color=MUTED, bold=True, margin=0)
    box = slide.shapes.add_textbox(Inches(4.3), Inches(0.1), Inches(W - M - 4.3), Inches(0.32))
    tf = box.text_frame
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", 0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    for i, st in enumerate(SECTIONS):
        r = p.add_run()
        r.text = st
        r.font.name, r.font.size = BODY, Pt(10.5)
        r.font.bold = st == section
        r.font.color.rgb = EMBER if st == section else LIGHT
        if i < len(SECTIONS) - 1:
            r = p.add_run()
            r.text = "  ›  "
            r.font.name, r.font.size = BODY, Pt(10.5)
            r.font.color.rgb = LIGHT


def short(slide, t):
    panel(slide, M, 6.38, W - 2 * M, 0.6, color=TINT)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(M), Inches(6.38), Inches(0.08), Inches(0.6))
    fill(bar, EMBER)
    text(slide, M + 0.25, 6.38, W - 2 * M - 0.4, 0.6, [[("In short:  ", {"bold": True, "color": EMBER}), (t, {})]],
         size=15, anchor=MSO_ANCHOR.MIDDLE, margin=0)


def notes(slide, t):
    slide.notes_slide.notes_text_frame.text = t


def S(section, t, sub=None):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = WHITE
    strip(s, section)
    text(s, M, TITLE_Y, W - 2 * M, TITLE_H, t, size=30 if len(t) <= 56 else 26, font=HEAD, bold=True,
         anchor=MSO_ANCHOR.BOTTOM, margin=0)
    if sub:
        text(s, M, TITLE_Y + TITLE_H + 0.05, W - 2 * M, 0.4, sub, size=15, color=MUTED, margin=0)
    PAGES.append(s)
    return s


# ================================================================ cover (not numbered)
s = prs.slides.add_slide(BLANK)
s.background.fill.solid()
s.background.fill.fore_color.rgb = DARK
image(s, RAWF / "s2_lehra.png", 7.6, 0.75, 5.73, 5.73, align="right")
shade = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(7.6), Inches(H))
fill(shade, DARK)
dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(M), Inches(1.55), Inches(0.22), Inches(0.22))
fill(dot, EMBER)
text(s, M + 0.35, 1.45, 6.5, 0.45, "COL7761 ICTD · FINAL PRESENTATION", size=13, color=ON_DARK_MUTED, bold=True,
     margin=0)
text(s, M, 2.1, 6.6, 2.4, "Finding Positive Deviants in Crop Residue Burning", size=44, font=HEAD, bold=True,
     color=WHITE, margin=0)
text(s, M, 4.35, 6.6, 0.9, "A Data-Powered Positive Deviance study of Punjab's 97 tehsils", size=20,
     color=ON_DARK_MUTED, margin=0)
text(s, M, 5.55, 6.6, 1.2, [[("Soham Malvadkar", {"bold": True, "color": WHITE})],
                            "Supervisor: Prof. Aaditeshwar Seth",
                            "Advisors: Basma Albanna, Andreas Pawelke"], size=15, color=ON_DARK_MUTED, margin=0)
text(s, 7.75, H - 0.45, 5.4, 0.3, "Sentinel-2, Lehra tehsil, 26 Oct 2022: harvested and burnt fields", size=10,
     color=ON_DARK_MUTED, italic=True, margin=0)

# ================================================================ SECTION 1 · INTRODUCTION
# 1 Research question
s = S("Introduction", "Which tehsils burn far less straw than places like them, and why?")
image(s, FIG / "fig_G_burn_map.png", M, TOP + 0.05, 3.9, 4.4, align="left")
caption(s, M, TOP + 4.5, 3.9, "Share of paddy burnt, mean 2020–24, by tehsil (our measure)")
stat(s, 4.85, TOP + 0.05, 2.5, "52–64%", "of paddy area burnt\nevery season")
stat(s, 7.45, TOP + 0.05, 2.5, "14–22 days", "between paddy harvest\nand wheat sowing")
stat(s, 10.05, TOP + 0.05, 2.7, "−91%", "drop in satellite fire counts\n2021→24, as farmers burn\nafter the satellite passes",
     color=BAD)
bullets(s, 4.85, TOP + 1.85, 7.9, 1.4, [
    ("Positive deviance: ", "some communities do better than peers with the same resources. Learn from them "
                            "instead of inventing a new solution."),
    ("Data-powered: ", "find those communities in public data (satellites, census), not by field survey."),
], size=15, gap=6)
panel(s, 4.85, TOP + 3.3, 7.88, 1.45)
text(s, 5.1, TOP + 3.3, 7.4, 1.45, [
    [("Our objective", {"bold": True, "color": EMBER, "size": 14})],
    [("Which of Punjab's 97 tehsils burn much less paddy straw than structurally similar tehsils, "
      "and what might explain it?", {"size": 18, "bold": True})]], anchor=MSO_ANCHOR.MIDDLE, margin=0)
short(s, "find places that already burn less than their peers, and learn what they do differently.")
notes(s, "Tehsil = sub-district; Punjab has 97. Farmers burn because the straw must go before wheat is sown and "
         "fire is the cheapest way. Fire counts (VIIRS) collapsed after 2021 because farmers time fires after the "
         "afternoon overpass, so we built our own measure from Sentinel-2.")

# 2 Pipeline
s = S("Introduction", "Our DPPD pipeline: compare like with like, then ask why")
pipe = [("1", "Problem–method fit", "Is burning measurable, does it vary, can some places do better?"),
        ("2a", "Peer groups", "Group tehsils by conditions they cannot change"),
        ("2b", "Burn measure", "Burnt share of paddy per tehsil, from satellites"),
        ("2c", "Find PDs", "Who burns far less than its own group?"),
        ("2d", "Validate", "Is the PD real, or noise and data errors?"),
        ("3", "Drivers", "What do PDs have that peers lack? (public data)"),
        ("4", "Impact", "How a partner would test and scale it")]
k, gap = len(pipe), 0.18
bw = (W - 2 * M - (k - 1) * gap) / k
for i, (num, h_, b_) in enumerate(pipe):
    x = M + i * (bw + gap)
    col = MUTED if num == "1" else (EMBER if num.startswith("2") else GOOD)
    hdr = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(TOP + 0.1), Inches(bw), Inches(0.6))
    fill(hdr, col)
    text(s, x, TOP + 0.1, bw, 0.6, f"{num} · {h_}", size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, margin=0.03)
    panel(s, x, TOP + 0.7, bw, 1.4, rounded=False)
    text(s, x + 0.1, TOP + 0.8, bw - 0.2, 1.25, b_, size=13, margin=0)
    if i < k - 1:
        arrow(s, x + bw + 0.02, TOP + 1.3, w=gap - 0.04, h=0.22)
text(s, M, TOP + 2.2, 3, 0.3, "Stage 1", size=11, color=MUTED, bold=True, margin=0)
text(s, M + bw + gap, TOP + 2.2, 6, 0.3, "Stage 2 · Determine positive deviants (PDs)", size=11, color=EMBER,
     bold=True, margin=0)
text(s, M + 5 * (bw + gap), TOP + 2.2, 3.6, 0.3, "Stage 3 · Discover drivers  ·  Impact", size=11, color=GOOD,
     bold=True, margin=0)
card(s, M, TOP + 2.7, 5.95, 2.0, "Rule 1 · Groups use only what a tehsil cannot change",
     "Rice share, rainfall, agro-ecological zone, groundwater, soil. Never things that could be the answer "
     "(machines, markets), and never burning itself.", size=14)
card(s, M + 6.18, TOP + 2.7, 5.95, 2.0, "Rule 2 · Groups first, burning second",
     "The groups were frozen on 7 Oct, before burning was measured, so knowing who burns could not shape "
     "who is compared with whom.", size=14)
short(s, "a PD is a tehsil that burns far less than tehsils facing the same conditions, not just a low burner.")
notes(s, "The talk follows this pipeline left to right; the strip at the top shows where we are.")

# 3 Midterm
s = S("Introduction", "What we completed by the midterm (17 Sep)")
card(s, M, TOP + 0.05, 3.9, 4.7, "Grouping data prepared", [
    "Five structural factors: rice, climate zone, groundwater, soil, cropping intensity",
    "Drivers (machines, mandis) kept out on purpose",
    "Unit = tehsil: finer than district, steadier than village",
    "Boundary bridge: 2011 Census villages mapped to today's 97 tehsils"], size=14, head_color=EMBER)
panel(s, M + 4.12, TOP + 0.05, 4.1, 4.7)
text(s, M + 4.32, TOP + 0.18, 3.7, 0.4, "Initial detector: BAIS2 + TCB", size=16, bold=True, color=EMBER, margin=0)
text(s, M + 4.32, TOP + 0.6, 3.7, 1.0, "BAIS2 = burn index from red-edge bands; TCB = brightness. "
     "Burnt fields score high on BAIS2 and go dark.", size=13, margin=0)
rows = [["380 fields, 5-fold CV", "NBR", "BAIS2+TCB"],
        ["Accuracy", "81.3%", ("95.5%", GOOD)],
        ["Burns caught", "82.3%", ("98.1%", GOOD)],
        ["Burns missed", ("47", BAD), ("5", GOOD)]]
table(s, M + 4.27, TOP + 1.65, 3.8, rows, [1.7, 0.9, 1.2], size=13, row_h=0.48)
text(s, M + 4.32, TOP + 3.7, 3.7, 0.9, "Preliminary result: chosen over NBR. Ground truth: CEEW field photos, "
     "Hoshiarpur/Jalandhar 2021, Sangrur 2020.", size=12, color=MUTED, margin=0)
card(s, M + 8.44, TOP + 0.05, 3.69, 4.7, "Still open", [
    "Grouping designed but not yet run",
    "Detector tested on one date only",
    "Never tested on ploughed fields",
    "No tehsil-level burning measure yet"], size=14, head_color=BAD)
short(s, "after the midterm we ran the grouping, and found the burn detector had a serious flaw.")
notes(s, "Everything after this slide is work done since 17 September.")

# ================================================================ SECTION 2 · GROUPING
# 4 Dataset
s = S("Grouping", "Our final grouping dataset: one row per tehsil, five dimensions")
AES = {"aesr_share_14_2": "14.2", "aesr_share_2_5": "2.5", "aesr_share_4_1": "4.1", "aesr_share_9_1": "9.1"}


def zone_str(r):
    parts = sorted([(v, r[c]) for c, v in AES.items() if r[c] > 0.05], key=lambda t: -t[1])
    return " + ".join(f"{v} ({sh:.0%})" for v, sh in parts)


rows = [["Tehsil", "Rice share", "Monsoon rain", "Agro-eco zone (AESR)", "Groundwater use", "Soil (3 of 8 classes)"]]
for nm in ["Phagwara", "Adampur", "Abohar", "Lehra", "Pathankot"]:
    r = MASTER.loc[nm]
    rows.append([nm, f"{r.rice_share_2022_cal:.0%}", f"{r.mean_monsoon_rainfall_mm:.0f} mm", zone_str(r),
                 f"{r.mean_extraction_pct_2022:.0f}%",
                 f"{r.dominant_soil_texture} · {r.dominant_particle_size} · {r.dominant_drainage}"])
rows.append([("… 92 more", MUTED), "", "", "", "", ""])
table(s, M, TOP + 0.05, W - 2 * M, rows, [1.8, 1.45, 1.6, 2.35, 1.75, 3.18], size=12, row_h=0.34)
rows = [["Dimension", "Why it matters for burning", "Unit", "Data type", "Source"],
        ["1 Rice share", "more paddy = more straw to clear", "% of tehsil area", "number", "Chen et al. 10 m map, 2022"],
        ["2 Monsoon rain", "wetter fields: later harvest, harder to burn", "mm, Jun–Sep", "number", "CHIRPS 2020–25"],
        ["3 Agro-eco zone", "climate and cropping system", "share in each zone", "shares", "NBSS&LUP AESR"],
        ["4 Groundwater use", "water rules shape paddy timing", "% of recharge", "number", "CGWB 2022"],
        ["5 Soil", "drainage and texture set field timing", "8 classes", "categories", "NBSS&LUP 1:250K"]]
table(s, M, TOP + 2.55, W - 2 * M, rows, [2.1, 4.33, 2.0, 1.5, 2.2], size=12, row_h=0.36)
short(s, "mm, %, shares and soil words cannot be compared directly, so we need a distance that handles mixed data.")
notes(s, "Rice share is calibrated to official district totals. Cropping intensity was dropped after the midterm: "
         "the satellite estimate did not match official figures (rho 0.18) and dropping it moved only 2 tehsils.")

# 5 Gower
s = S("Grouping", "Dimension-balanced Gower distance: every difference becomes 0–1")
steps_col(s, M, TOP + 0.05, 4.9, [
    ("Why Gower:", "the standard distance for mixed data; numbers, shares and categories each score 0–1."),
    ("Numbers:", "difference ÷ full range across tehsils."),
    ("Shares:", "same rule on each zone's share, then averaged."),
    ("Categories:", "same class = 0, different = 1."),
    ("Balanced:", "average inside each dimension, then the 5 dimensions with weight 1/5 each. "
                  "Soil's 8 columns get one vote, not eight.")], size=13, h=0.78, gap=0.1)
pa, pb, vv = GX["Phagwara|Adampur"], GX["Phagwara|Abohar"], GX["values"]
rows = [["Dimension", "Phagwara", "Adampur", "Abohar", "P ↔ Ad", "P ↔ Ab"],
        ["Rice share", f"{vv['Phagwara']['rice_share_2022_cal']:.0%}", f"{vv['Adampur']['rice_share_2022_cal']:.0%}",
         f"{vv['Abohar']['rice_share_2022_cal']:.0%}", f"{pa['rice']:.2f}", f"{pb['rice']:.2f}"],
        ["Monsoon rain", f"{vv['Phagwara']['mean_monsoon_rainfall_mm']:.0f}",
         f"{vv['Adampur']['mean_monsoon_rainfall_mm']:.0f}", f"{vv['Abohar']['mean_monsoon_rainfall_mm']:.0f}",
         f"{pa['rainfall']:.2f}", f"{pb['rainfall']:.2f}"],
        ["Agro-eco zone", vv['Phagwara']['aesr_dominant'], vv['Adampur']['aesr_dominant'],
         vv['Abohar']['aesr_dominant'], f"{pa['zone']:.2f}", f"{pb['zone']:.2f}"],
        ["Groundwater", f"{vv['Phagwara']['mean_extraction_pct_2022']:.0f}%",
         f"{vv['Adampur']['mean_extraction_pct_2022']:.0f}%", f"{vv['Abohar']['mean_extraction_pct_2022']:.0f}%",
         f"{pa['groundwater']:.2f}", f"{pb['groundwater']:.2f}"],
        ["Soil (8 classes)", "Loamy", "Sandy", "Sandy", f"{pa['soil']:.2f}", f"{pb['soil']:.2f}"],
        [("Distance (mean of 5)", EMBER), "", "", "", (f"{pa['distance']:.2f}", GOOD), (f"{pb['distance']:.2f}", BAD)]]
text(s, 5.75, TOP + 0.02, 7.0, 0.35, "Worked example with real tehsils", size=14, bold=True, color=MUTED, margin=0)
table(s, 5.75, TOP + 0.4, 6.98, rows, [1.9, 1.05, 1.05, 1.0, 1.0, 0.98], size=13, row_h=0.45)
text(s, 5.75, TOP + 3.7, 6.98, 1.0, [
    [("Phagwara ↔ Adampur 0.24: ", {"bold": True}), ("same zone, similar rain; differ mainly in soil.", {})],
    [("Phagwara ↔ Abohar 0.51: ", {"bold": True}), ("Abohar is drier, less rice, far less pumping.", {})]],
     size=13, margin=0, space=4)
short(s, "every pair of tehsils gets one number: 0 = identical conditions, 1 = as different as Punjab gets.")
notes(s, "Rice difference example: |share P − share A| ÷ range across tehsils. The hill outlier Dhar Kalan is left "
         "out when measuring ranges so it does not stretch the ruler. Equal weights are the neutral default; they "
         "are tested in the sensitivity check.")

# 6 Matrix
s = S("Grouping", "Comparing all 97 tehsils: a 97 × 97 distance matrix")
image(s, FF / "v3_distance_matrix.png", M, TOP, 6.6, 4.8, align="left")
text(s, 7.5, TOP + 0.05, 5.23, 0.35, "How it was generated", size=15, bold=True, color=EMBER, margin=0)
bullets(s, 7.5, TOP + 0.45, 5.23, 1.6, [
    "Code computes the 5 dimension scores for every pair and averages them.",
    "97 × 96 ÷ 2 = 4,656 pairs; the diagonal is 0 (a tehsil vs itself).",
], size=14, gap=4)
text(s, 7.5, TOP + 1.95, 5.23, 0.35, "How to read it", size=15, bold=True, color=EMBER, margin=0)
bullets(s, 7.5, TOP + 2.35, 5.23, 2.4, [
    ("Dark = alike, light = different.", ""),
    ("Rows sorted by final group: ", "dark squares on the diagonal mean tehsils inside a group are alike."),
    ("Foothills ", "are light against everyone: the most distinct region."),
    ("The only input to clustering: ", "it never sees maps or burning."),
], size=14, gap=4)
short(s, "the clustering's job is to find those dark blocks on its own, without being told where they are.")
notes(s, "Shown sorted for readability. The clustering receives the matrix in district order.")

# 7 HAC
s = S("Grouping", "Hierarchical clustering: merge the two closest, repeat")
image(s, FF / "f20_toy_merge.png", M, TOP + 0.05, 8.9, 3.3, align="left")
caption(s, M, TOP + 3.35, 8.9, "Six real tehsils, real distances. Blue = Central, orange = South-west.")
steps_col(s, 9.75, TOP + 0.05, 2.98, [("Start:", "every tehsil is its own group."),
                                      ("Merge", "the two closest groups."),
                                      ("Average linkage:", "group distance = mean of all pairs between them."),
                                      ("Repeat", "until all are in one tree.")], size=13, h=0.78, gap=0.06)
note_bar(s, TOP + 3.7, "Why hierarchical?", "it works directly on our Gower matrix (k-means needs numeric "
         "coordinates that soil classes do not have), and the tree shows every grouping, so the number of groups "
         "is chosen afterwards, not guessed.", h=1.05, size=14)
short(s, "average linkage does not force round, equal-size groups and is not pulled by one extreme pair.")
notes(s, "Worked step: Adampur to {Phagwara, Jalandhar-I} = (0.24 + 0.29) ÷ 2 = 0.27, the closest remaining pair, "
         "so they merge. Ward also assumes Euclidean space, so it is not used.")

# 8 Selecting and validating
s = S("Grouping", "Selecting and validating our groups")
image(s, FIG / "fig_B_dendrogram.png", M, TOP - 0.15, W - 2 * M, 3.05)
cw = (W - 2 * M - 0.45) / 4
items = [("Dendrogram cut", "k = 3", "Cut the tree into 3 groups: the lowest cut that separates the dry south-west."),
         ("Silhouette", "0.377", "Is each tehsil closer to its own group than the next? (k = 2: 0.409, but hides the south-west.)"),
         ("Bootstrap stability · ARI", "0.890", "Regroup random 80% samples 300 times; ARI = 1 means the same groups."),
         ("Weight sensitivity", "8 of 10", "Change one weight ±15% at a time: 8 of 10 changes keep ARI ≥ 0.83.")]
for i, (h_, big, b_) in enumerate(items):
    x = M + i * (cw + 0.15)
    panel(s, x, TOP + 2.95, cw, 1.8)
    text(s, x + 0.18, TOP + 3.02, cw - 0.36, 0.35, h_, size=14, bold=True, color=MUTED, margin=0)
    text(s, x + 0.18, TOP + 3.3, cw - 0.36, 0.6, big, size=28, font=HEAD, bold=True, color=EMBER, margin=0)
    text(s, x + 0.18, TOP + 3.9, cw - 0.36, 0.85, b_, size=12, margin=0)
short(s, "three groups are well separated and come back almost every time; only the south-west border is soft.")
notes(s, "Groups smaller than 5 tehsils are set aside. Bootstrap: 3 borderline tehsils (Firozpur, Faridkot, "
         "Dinanagar). Sensitivity weak point: more weight on rice or soil merges the south-west into Central, so "
         "every PD is also checked under the 2-group version.")

# 9 Final grouping
s = S("Grouping", "Final grouping: three peer regions, found without any location data")
image(s, FIG / "fig_A_group_map.png", M, TOP - 0.1, 4.6, 4.95, align="left")
rows = [["Group", "Tehsils", "Rice share", "Monsoon rain", "Groundwater", "Character"],
        [("Central", GROUP["Central"]), "63", "75%", "721 mm", "230%", "paddy plains, most over-pumped"],
        [("South-west", GROUP["South-west"]), "18", "59%", "467 mm", "118%", "dry cotton–paddy belt"],
        [("Foothills", GROUP["Foothills"]), "15", "28%", "981 mm", "117%", "wet, hilly Kandi belt"],
        [("Outlier", MUTED), "1", "7%", "1,604 mm", "27%", "Dhar Kalan hill tehsil, set aside"]]
table(s, 5.4, TOP + 0.05, 7.33, rows, [1.25, 0.8, 1.0, 1.2, 1.15, 1.93], size=12, row_h=0.55)
bullets(s, 5.4, TOP + 3.0, 7.33, 1.8, [
    ("Never saw a map, ", "yet each group is one connected region matching Punjab's known belts."),
    ("Frozen on 7 Oct, ", "before burning was measured."),
    ("Foothills: ", "measured but not ranked later, because the burn check is weakest there."),
], size=14, gap=6)
short(s, "from here on, each tehsil is compared only with tehsils in its own group.")
notes(s, "Group medians from the grouping dataset. Groundwater use above 100% means more is pumped than recharged.")

# ================================================================ SECTION 3 · BURN DETECTION
# 10 Why midterm detector failed
s = S("Burn detection", "Why our midterm detector failed: ploughed fields look burnt")
text(s, M, TOP + 0.0, W - 2 * M, 0.4, [[("Recap: ", {"bold": True, "color": EMBER}),
     ("BAIS2 + TCB was run on every clear Sentinel-2 image of the season; if any look scored burnt, the field burnt.",
      {})]], size=14, margin=0)
image(s, FF / "f05_planet_burnt_vs_ploughed.png", M, TOP + 0.45, W - 2 * M, 2.6)
caption(s, M, TOP + 3.08, W - 2 * M, "PlanetScope daily images, Jalandhar 2021. Top: burnt, goes black, then fades to "
        "soil colour. Bottom: ploughed, never black.")
stat(s, M, TOP + 3.45, 3.9, "81%", "of ploughed, NOT burnt fields called\nburnt (Walker et al. ground truth)", color=BAD)
stat(s, M + 4.12, TOP + 3.45, 3.9, "94.6%", "of random cropland points\ncalled burnt in 2022", color=BAD)
stat(s, M + 8.24, TOP + 3.45, 3.9, "92%", "of fields CEEW saw unburnt\nlater called burnt", color=BAD)
short(s, "after harvest, bare ploughed soil scores like ash, so a tehsil that ploughs straw in would look like a burner.")
notes(s, "Burns were still caught (98%), so the one-date accuracy was real; the problem is false alarms from tilled "
         "soil over a whole season of looks.")

# 11 Alternatives
s = S("Burn detection", "Alternative approaches we tested, and why each failed")
alts = [("Season restriction",
         "Ploughed fields might only be flagged after the burning season.",
         "Count flags only 15 Sep – 30 Nov (official ISRO/CAQM window); tried shorter windows.",
         "Wheat is sown by 7–15 Nov, so ploughing falls in the same weeks; ~95% of cropland points still flagged."),
        ("Thermal imagery",
         "Fresh ash should be hotter than soil.",
         "Landsat surface temperature on CEEW fields; MODIS heat peak to set each field's burn window.",
         "Ash was not warmer than ploughed soil. The heat window cut flags from 95% to ~56%, but about half of "
         "ploughed fields were still called burnt."),
        ("Radar (Sentinel-1)",
         "Ploughing roughens soil, so the radar signal should rise; burning should not.",
         "Radar before vs after each flag, on CEEW Jalandhar 2021 fields.",
         "Straw removal drops the signal either way: caught only 7% of ploughed fields, dropped 33% of real burns; "
         "12-day revisit.")]
cw = (W - 2 * M - 0.4) / 3
for i, (h_, mo, ex, fa) in enumerate(alts):
    x = M + i * (cw + 0.2)
    panel(s, x, TOP + 0.05, cw, 3.85)
    text(s, x + 0.2, TOP + 0.15, cw - 0.4, 0.4, h_, size=17, bold=True, color=EMBER, margin=0)
    text(s, x + 0.2, TOP + 0.6, cw - 0.4, 3.25, [
        [("Motivation  ", {"bold": True, "color": MUTED, "size": 12})], [(mo, {})],
        [("Experiment  ", {"bold": True, "color": MUTED, "size": 12})], [(ex, {})],
        [("Why it failed  ", {"bold": True, "color": BAD, "size": 12})], [(fa, {})]], size=13, margin=0, space=3)
note_bar(s, TOP + 4.05, "Common cause:", "each looks at one image or one sensor at a time; once the ash has faded, "
         "one look cannot tell burnt from ploughed.", h=0.7)
short(s, "the answer had to use time: how a field changed, not just how it looks on one day.")
notes(s, "Radar was B. Albanna's suggestion; kept as a documented negative result. Other indices and published "
         "thresholds (NBR, CEEW, Naeher & Ziulu) also failed to separate ash from tilled soil.")

# 12 PlanetScope
s = S("Burn detection", "What PlanetScope revealed: ash is black for only 2–3 days")
image(s, FF / "f06_planet_vs_s2.png", M, TOP + 0.05, W - 2 * M, 3.0)
caption(s, M, TOP + 3.1, W - 2 * M, "The same burnt field every day, 30 Oct – 9 Nov 2021 (PlanetScope, 3 m). Orange "
        "frame = a clear Sentinel-2 image that day: only 2 of 10.")
cw = (W - 2 * M - 0.4) / 3
card(s, M, TOP + 3.5, cw, 1.25, "Fading signature", "golden stubble → pure black for 2–3 days → fades to soil colour.",
     size=13)
card(s, M + cw + 0.2, TOP + 3.5, cw, 1.25, "Sentinel-2: every 5 days", "usually sees faded ash: ash vs soil "
     "AUC 0.51, a coin toss.", head_color=BAD, size=13)
card(s, M + 2 * (cw + 0.2), TOP + 3.5, cw, 1.25, "Planet: daily, small quota", "catches the black days (AUC 0.96), "
     "but 3,000 km²/month cannot cover Punjab.", head_color=GOOD, size=13)
short(s, "the index was not wrong; Sentinel-2 often arrives after the evidence has faded, so Planet can judge but not replace it.")
notes(s, "Planet Education & Research access. Used as an independent judge in Jalandhar 2021.")

# 13 Developing the new approach
s = S("Burn detection", "Developing our new approach: from observations to design")
obs = [("Burning is sudden.", "Drying and harvest change a field slowly; fire darkens it overnight.",
        "Sudden-change detection: find the biggest jump in the burn score."),
       ("Change says more than looks.", "Ash and soil differ more in how the field changed than in one image.",
        "Before/after comparison with the last clear image before the jump."),
       ("We need fields known to be ploughed.", "Walker et al. 2019: farmer-reported burnt and ploughed fields.",
        "Train on 2,204 burnt + 223 ploughed-not-burnt fields."),
       ("No single index is enough.", "Each band carries a little information.",
        "A random forest combines 14 bands and indices.")]
text(s, M, TOP + 0.02, 5.2, 0.35, "What we observed", size=14, bold=True, color=MUTED, margin=0)
text(s, 7.35, TOP + 0.02, 5.4, 0.35, "What we designed", size=14, bold=True, color=MUTED, margin=0)
for i, (h_, b_, d_) in enumerate(obs):
    y = TOP + 0.42 + i * 1.09
    panel(s, M, y, 6.2, 0.96)
    text(s, M + 0.2, y + 0.05, 5.9, 0.86, [[(h_ + " ", {"bold": True}), (b_, {})]], size=13,
         anchor=MSO_ANCHOR.MIDDLE, margin=0)
    arrow(s, M + 6.3, y + 0.33, w=0.35, h=0.3, color=EMBER)
    panel(s, 7.35, y, 5.38, 0.96, color=TINT)
    text(s, 7.55, y + 0.05, 5.0, 0.86, d_, size=13, bold=True, anchor=MSO_ANCHOR.MIDDLE, margin=0)
short(s, "look for a sudden darkening, compare before and after, and learn the difference from real ploughed fields.")
notes(s, "PlanetScope is then used as an independent judge in a new district and year (Jalandhar 2021).")

# 14 Final algorithm flowchart
s = S("Burn detection", "Our final burn detection algorithm, for one field in one season")
alg = [("1 · Flag events", "every clear Sentinel-2 image, 15 Sep – 30 Nov",
        "Score each image with BAIS2 + TCB; score > 0 = something happened",
        "flagged dates (burnt or ploughed)"),
       ("2 · Candidate date", "flagged dates",
        "Pick the flag with the largest rise in score since the previous clear image",
        "one candidate burn date"),
       ("3 · Before / after", "candidate image + last clear image in the 20 days before",
        "For 14 bands and indices: value after, and change after − before",
        "28 numbers describing the event"),
       ("4 · Classify", "28 numbers",
        "Random forest (500 trees) trained on Walker burnt vs ploughed fields",
        "p(burnt); burnt if p ≥ 0.79")]
k, gap = len(alg), 0.3
bw = (W - 2 * M - (k - 1) * gap) / k
for i, (h_, inp, do, out) in enumerate(alg):
    x = M + i * (bw + gap)
    panel(s, x, TOP + 0.05, bw, 1.1)
    text(s, x + 0.15, TOP + 0.1, bw - 0.3, 1.0, [[("INPUT", {"bold": True, "color": MUTED, "size": 11})], [(inp, {})]],
         size=13, margin=0)
    arrow(s, x + bw / 2 - 0.15, TOP + 1.2, w=0.3, h=0.3, color=LIGHT, down=True)
    hdr = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(TOP + 1.55), Inches(bw), Inches(1.6))
    fill(hdr, EMBER)
    hdr.adjustments[0] = 0.06
    text(s, x + 0.15, TOP + 1.62, bw - 0.3, 1.5, [[(h_, {"bold": True, "size": 17})], [(do, {})]], size=13,
         color=WHITE, margin=0, space=3)
    arrow(s, x + bw / 2 - 0.15, TOP + 3.2, w=0.3, h=0.3, color=LIGHT, down=True)
    panel(s, x, TOP + 3.55, bw, 1.15, color=TINT)
    text(s, x + 0.15, TOP + 3.6, bw - 0.3, 1.05, [[("OUTPUT", {"bold": True, "color": EMBER, "size": 11})],
                                                   [(out, {"bold": True})]], size=13, margin=0)
    if i < k - 1:
        arrow(s, x + bw + 0.04, TOP + 2.2, w=gap - 0.08, h=0.3, color=MUTED)
short(s, "steps 1–2 find when something happened; steps 3–4 decide whether it was fire or a plough.")
notes(s, "A point with no clear image, or no image before the candidate, is 'unknown' and not counted (< 3% of "
         "points). Clear = Sentinel-2 scene classes 2/4/5/7: the default mask threw away fresh char as 'dark area'.")

# 15 Candidate date
s = S("Burn detection", "Identifying the candidate burn date: the largest sudden jump")
image(s, FF / "f19_detector_series.png", M, TOP + 0.05, W - 2 * M, 3.55)
caption(s, M, TOP + 3.6, W - 2 * M, "Two real 20 m points in Lehra, 2022. Each dot = one clear Sentinel-2 look. "
        "Blue ring = 'before' image, orange ring = candidate.")
card(s, M, TOP + 3.95, 5.95, 0.85, "Left: burnt (p = 1.00)", "score jumps from −7 to +10 in one look.", size=13,
     head_color=BAD)
card(s, M + 6.18, TOP + 3.95, 5.95, 0.85, "Right: not burnt (p = 0.18)", "slow climb; crosses the flag line late.",
     size=13, head_color=GOOD)
short(s, "both points cross the flag line (score > 0), which fooled the old detector; only the sudden jump is a burn.")
notes(s, "Flag = BAIS2 + TCB score above 0. Candidate = flagged look with the largest rise from the previous look.")

# 16 Burning vs ploughing
s = S("Burn detection", "Distinguishing burning from ploughing")
cw = (W - 2 * M - 0.4) / 3
panel(s, M, TOP + 0.05, cw, 4.7)
text(s, M + 0.2, TOP + 0.15, cw - 0.4, 0.4, "14 bands and indices", size=16, bold=True, color=EMBER, margin=0)
rows = [["Input", "What it sees"],
        ["Blue, Green, Red", "colour, darkness"],
        ["Red-edge 1, 2, 3", "plant / residue"],
        ["NIR", "green vegetation"],
        ["SWIR 1, 2", "moisture, char"],
        ["NDVI", "greenness"],
        ["NBR, NBR2", "burn, residue"],
        ["BAIS2", "burn area"],
        ["TCB", "brightness"]]
table(s, M + 0.15, TOP + 0.6, cw - 0.3, rows, [1.7, cw - 2.0], size=12, row_h=0.43)
card(s, M + cw + 0.2, TOP + 0.05, cw, 4.7, "Before / after features", [
    "After: each of the 14 on the candidate date",
    "Change: after − before (last clear image in the 20 days before)",
    "14 × 2 = 28 features per event",
    "Fire: sudden drop in brightness and NIR, rise in BAIS2. Plough: brighter bare soil, smaller change"], size=15)
card(s, M + 2 * (cw + 0.2), TOP + 0.05, cw, 4.7, "Random forest", [
    "500 decision trees each vote burnt or not; p = share voting burnt",
    "Training: Walker et al. 2019, farmer-reported 2,204 burnt + 223 ploughed-not-burnt fields",
    "Threshold: burnt if p ≥ 0.79, which keeps 90% of burns while staying strict on ploughing",
    "p ≥ 0.5 rerun as a check"], size=15, head_color=GOOD)
short(s, "the forest learns what a real fire does to a field that a plough does not.")
notes(s, "Walker et al. 2019 is the only public ground truth with ploughed-not-burnt fields for Punjab.")

# 17 Evaluating
s = S("Burn detection", "Evaluating our improved detector on Walker ground truth")
image(s, FF / "f07_detector_bars.png", M, TOP + 0.05, 5.4, 4.35, align="left")
caption(s, M, TOP + 4.42, 5.4, "Walker et al. 2019, 5-fold cross-validation")
rows = [["Method", "Burns caught", "Ploughed called burnt"],
        ["Midterm detector", "98%", ("81%", BAD)],
        ["Daily Planet rule", "90%", "9%"],
        [("Our detector, p ≥ 0.79", GOOD), ("90%", GOOD), ("18%", GOOD)],
        ["Our detector, p ≥ 0.5", "97.5%", "51%"]]
table(s, 6.3, TOP + 0.1, 6.43, rows, [3.1, 1.5, 1.83], size=13, row_h=0.5)
bullets(s, 6.3, TOP + 2.75, 6.43, 2.0, [
    ("Cross-validation: ", "train on 4/5 of fields, test on the unseen 1/5, five times."),
    ("Threshold choice: ", "lower p catches more burns but lets ploughing back in; 0.79 is the strict point."),
    ("Model quality: ", "AUC 0.938."),
], size=13, gap=6)
short(s, "we give up 8 points of burns caught to cut ploughing false alarms by more than four times.")
notes(s, "Recall vs false-positive trade-off: for ranking tehsils, false alarms from ploughing are the bigger danger, "
         "because they would hide exactly the places that manage straw without burning.")

# 18 CEEW
s = S("Burn detection", "Independent validation: CEEW ground truth, Jalandhar 2021")
image(s, FF / "v3_ceew_test.png", M, TOP + 0.05, 7.6, 2.85, align="left")
caption(s, M, TOP + 2.95, 7.6, "CEEW visited 357 fields on 29 Oct 2021: 262 burnt, 95 unburnt. Model not retrained.")
stat(s, M, TOP + 3.3, 2.5, "28 → 2", "of 95 clean fields\ncalled burnt", color=GOOD, big_size=26)
stat(s, M + 2.6, TOP + 3.3, 2.5, "56 of 72", "fully burnt fields\nstill caught", color=GOOD, big_size=26)
stat(s, M + 5.2, TOP + 3.3, 2.5, "89 of 190", "partly burnt fields\nstill caught", color=BAD, big_size=26)
text(s, 8.5, TOP + 0.05, 4.23, 0.35, "PlanetScope judge", size=15, bold=True, color=EMBER, margin=0)
bullets(s, 8.5, TOP + 0.45, 4.23, 1.9, [
    "Daily 3 m images of the same fields",
    "Burnt if brightness falls to ≤ 0.765 of its 15-day median",
    ("Result: ", "false alarms 23/32 → 0–3/32"),
], size=13, gap=4)
text(s, 8.5, TOP + 2.45, 4.23, 0.35, "Limitations", size=15, bold=True, color=BAD, margin=0)
bullets(s, 8.5, TOP + 2.85, 4.23, 1.9, [
    "Under-counts partial burns",
    "One district, one year",
    "Ploughing tested on 2019 fields only",
], size=13, gap=4)
short(s, "in a new district and year, the detector rarely calls a clean field burnt; it under-counts partial burns.")
notes(s, "For ranking tehsils, an under-count hurts less than false alarms, provided it is similar across tehsils "
         "(assumption, not tested).")

# ================================================================ SECTION 4 · MEASUREMENT
# 19 Pixels to tehsil
s = S("Measurement", "From individual pixels to tehsil-level measurement")
image(s, FF / "f08_points_two_tehsils.png", M, TOP + 0.05, 7.8, 4.0, align="left")
mp = json.loads((RAWF / "tehsil_phagwara.json").read_text())
caption(s, M, TOP + 4.1, 7.8, f"Sentinel-2 true colour, cloud-free {mp['date']}, with each point's 2022 verdict")
steps_col(s, 8.7, TOP + 0.05, 4.03, [
    ("Rice pixels:", "100 random 20 m pixels that are rice in both the 2020 and 2022 maps."),
    ("Fixed points:", "the same 100 every season, so change is not sampling luck."),
    ("Seasonal classification:", "run the detector on each point, 15 Sep – 30 Nov, 2019–24."),
    ("Burnt share", "= burnt points ÷ points with a verdict.")], size=13, h=0.95, gap=0.08)
short(s, "each tehsil gets one number per season: the share of its paddy points that were burnt.")
notes(s, "15 Sep – 30 Nov is the ISRO protocol used by CAQM. ≥ 97% of points get a verdict each season.")

# 20 Measuring burning across Punjab
s = S("Measurement", "Measuring burning across Punjab, 2020–24")
image(s, FF / "f09_yearly_maps.png", M, TOP + 0.0, W - 2 * M, 2.7)
caption(s, M, TOP + 2.72, W - 2 * M, "Burnt share by tehsil: the same places stay low or high year after year")
cw = (W - 2 * M - 0.45) / 4
st = [("ρ 0.78–0.87", "same tehsil order as\nVIIRS fire counts, 2019–23"),
      ("ρ 0.82–0.91", "same order as the\nnext season"),
      ("ρ 0.87", "district order vs official\nCREAMS 2022"),
      ("ρ 0.84–0.98", "same order at\np ≥ 0.79 and p ≥ 0.5")]
for i, (b_, l_) in enumerate(st):
    x = M + i * (cw + 0.15)
    panel(s, x, TOP + 3.1, cw, 1.65)
    stat(s, x + 0.2, TOP + 3.2, cw - 0.4, b_, l_, big_size=24)
short(s, "ρ = rank correlation (1 = same order); DPPD needs the right order of tehsils, and every check agrees.")
notes(s, "VIIRS is biased by fire timing, so agreement is reassurance, not proof. 2024 is doubtful (72% of burns "
         "seen late Nov; agreement drops to 0.51), so every PD result is computed with 2020–24 and 2020–23. "
         "Ranked: 81 tehsils (Central 63, South-west 18); Foothills measured, not ranked.")

# ================================================================ SECTION 5 · POSITIVE DEVIANCE
# 21 How we identify PDs
s = S("Positive deviance", "How we identify positive deviants")
image(s, FF / "v3_fence.png", M, TOP + 0.0, W - 2 * M, 2.45)
cw = (W - 2 * M - 0.45) / 4
cards4 = [("Static PD", "burns least: 5-season mean beyond the fence, and in the group's lowest quarter in 4 of 5 "
                        "seasons", GOOD),
          ("Temporal PD", "cutting fastest: Theil–Sen trend 2020–24 minus the group's median trend, beyond the "
                          "fence", GOOD),
          ("Log transform", "halving burning counts the same at any level; without it the fence falls below zero",
           EMBER),
          ("IQR fence", "Q1 − 1.5 × IQR of the group: the handbook's standard outlier rule", EMBER)]
for i, (h_, b_, c_) in enumerate(cards4):
    card(s, M + i * (cw + 0.15), TOP + 2.6, cw, 2.15, h_, b_, head_color=c_, size=13)
short(s, "a PD is not just low: it is further below its own group than normal variation can explain.")
notes(s, "Theil–Sen = median of all pairwise slopes, so one odd year cannot drive the trend. Temporal deviance "
         "compares a tehsil with its own past, cancelling fixed differences we could not measure (suggested by "
         "Basma Albanna). Robust = flagged in both 2020–24 and 2020–23; negative deviants are the mirror image. "
         "No regression: every rule is a direct within-group comparison.")

# 22 Candidates
s = S("Positive deviance", "Initial positive deviance candidates")
image(s, FIG / "fig_I_pd_fences.png", M, TOP + 0.05, 6.1, 4.3, align="left")
caption(s, M, TOP + 4.4, 6.1, "Each dot = a tehsil, mean burnt share 2020–24 (log scale)")
rows = [["Tehsil", "Kind", "Burnt share"],
        [("Abohar (SW)", GOOD), "static + temporal", "0.34 (med 0.73)"],
        ["Dinanagar", "static", "0.21 (med 0.61)"],
        ["Gurdaspur · Phagwara · Adampur", "static", "0.29–0.30"],
        ["Jalandhar-I · Banga", "static", "0.31–0.34"],
        ["Talwandi Sabo (SW)", "static", "0.50"],
        ["Samana · Dirba", "temporal", "0.63 · 0.71"],
        [("NDs: Lehra · Zira · Moonak · Guruharsahai", BAD), "static", "0.79–0.90"]]
table(s, 6.9, TOP + 0.05, 5.83, rows, [3.0, 1.38, 1.45], size=12, row_h=0.5)
text(s, 6.9, TOP + 4.1, 5.83, 0.7, "Why they qualify: below their group's fence (Central 0.225, South-west 0.454) "
     "or reducing much faster than the group.", size=12, color=MUTED, margin=0)
short(s, "Abohar is the only tehsil that is both a low burner and a fast reducer; the Doaba tehsils form a low belt.")
notes(s, "Central unless marked SW. Dinanagar burns least of all but its burning is rising; Talwandi Sabo's rises "
         "fastest. Six of eight static PDs were also flagged by VIIRS fire counts.")

# ================================================================ SECTION 6 · VALIDATION
# 23 Six checks
s = S("Validation", "Our six validation checks, rules fixed before looking")
rows = [["Check", "Motivation", "Method", "Pass / fail"],
        ["V1 Resampling", "Is it luck of the 100 points?", "redraw points 1,000 times", "kept in ≥ 80% of redraws"],
        ["V2 Settings", "Does it hang on our choices?", "rerun with other cut-off, offset, 2 groups",
         "kept in all scenarios but one"],
        ["V3 Clear looks", "Did clouds hide the fires?", "share of points with no verdict",
         "≤ 2× group median"],
        ["V4 Rice", "Does it just grow less paddy?", "rice share vs group", "warning if below group Q1"],
        ["V4b Real paddy", "Do non-paddy points pull it down?", "re-score on harvest-confirmed points",
         "flag must survive"],
        ["V5 Timing", "Do fires fall outside the window?", "harvest date vs group", "warning if ≥ 10 days later"]]
table(s, M, TOP + 0.05, W - 2 * M, rows, [2.1, 3.5, 3.7, 2.83], size=13, row_h=0.52)
note_bar(s, TOP + 3.9, "Final label:", "any fail → dropped · at most one warning → validated PD · "
         "more warnings → PD with caveat", h=0.75, size=15)
short(s, "the handbook asks us to check a PD is real before anyone visits it; with no fieldwork, we check in the data.")
notes(s, "Triangulation with VIIRS and CREAMS is reported for information only.")

# 24 Final validated PDs
s = S("Validation", "Final validated positive deviants")
image(s, FF / "f11_validation_grid.png", M, TOP + 0.05, 7.4, 4.0, align="left")
groups4 = [("Strict PD", "Abohar: beyond the fence in every run", GOOD),
           ("Validated PDs", "Dinanagar, Phagwara, Jalandhar-I, Adampur, Talwandi Sabo", GOOD),
           ("PDs with caveat", "Gurdaspur, Banga (more than one warning)", MUTED),
           ("Rejected", "Samana, Dirba: kept in only 4 of 10 resamples", BAD),
           ("Negative deviants", "Lehra, Zira, Moonak, Guruharsahai", BAD)]
for i, (h_, b_, c_) in enumerate(groups4):
    y = TOP + 0.05 + i * 0.95
    panel(s, 8.25, y, 4.48, 0.85)
    text(s, 8.45, y + 0.05, 4.1, 0.75, [[(h_, {"bold": True, "color": c_})], [(b_, {"size": 12})]], size=14,
         anchor=MSO_ANCHOR.MIDDLE, margin=0)
short(s, "low burners hold up, fast reducers do not (except Abohar): a 5-season trend from 100 points is too noisy alone.")
notes(s, "Main warning is rice (V4), but on harvest-confirmed paddy (V4b) Abohar is 0.45 vs group 0.73 and "
         "Dinanagar 0.25 vs 0.62: still far below. All three temporal NDs fail V1 the same way.")

# ================================================================ SECTION 7 · DRIVERS
# 25 Drivers method
s = S("Drivers", "Investigating why positive deviants burn less")
rows = [["Driver (hypothesis)", "Public data", "Level"],
        ["Harvest-to-sowing days", "Sentinel-2 greenness", "Tehsil"],
        ["Early second crop", "points green again by 30 Nov", "Tehsil"],
        ["Farm labour; small farms", "Census 2011", "Tehsil"],
        ["Straw buyers", "14 biomass / biogas plants (news)", "Town"],
        ["Distance to state border", "district boundaries", "Tehsil"],
        ["Urban surroundings", "JRC settlement map 2020", "Tehsil"],
        ["Basmati share", "APEDA survey 2023", "District"],
        ["Livestock", "Livestock Census 2019", "Tehsil"]]
table(s, M, TOP + 0.05, 7.0, rows, [2.6, 3.4, 1.0], size=12, row_h=0.45)
steps_col(s, 7.95, TOP + 0.05, 4.78, [
    ("Profile comparison:", "are PDs above or below their group median, and NDs on the other side?"),
    ("Spearman:", "rank correlation with burning, inside each group."),
    ("Partial correlation:", "remove rice share's effect first, then correlate.")], size=13, h=0.85, gap=0.1)
note_bar(s, TOP + 2.95, "Result:", "only urban share holds on all three; turnaround days and small farms vanish once "
         "rice is held constant.", h=1.1, size=14, x=7.95, w=4.78)
text(s, 7.95, TOP + 4.2, 4.78, 0.5, "A driver counts only if all three agree.", size=14, bold=True, color=EMBER,
     margin=0)
short(s, "with 8 PDs and 4 NDs this is a search for leads, not proof of cause.")
notes(s, "CRM machine data were not available by district online, so that driver was dropped. 44 correlation "
         "tests in total, so about 2 would pass p < 0.05 by chance; we trust only patterns that repeat.")

# 26 Doaba
s = S("Drivers", "Understanding the Doaba region")
image(s, FF / "f14_doaba_far_fields.png", M, TOP + 0.05, 7.4, 4.1, align="left")
caption(s, M, TOP + 4.2, 7.4, "Burnt share: all fields vs only fields more than 5 km from any town")
bullets(s, 8.4, TOP + 0.05, 4.33, 4.7, [
    ("Urban share: ", "7 of 8 PDs above their group median, all 4 NDs below (Central ρ −0.61; −0.30 with rice held)."),
    ("Distance-from-town test: ", "far from towns, the Doaba PDs burn just as little."),
    ("Interpretation: ", "a regional trait, not town proximity: potato and vegetable rotations, off-farm and "
                         "overseas income."),
], size=14, gap=10)
short(s, "the lesson is inside Doaba farming itself; only fieldwork can say which practice it is.")
notes(s, "Fields within 2 km of a town burn 6–8 points less, but only 4% of fields are that close.")

# 27 Abohar
s = S("Drivers", "Understanding Abohar")
image(s, FF / "f15_abohar_profile.png", M, TOP + 0.05, 7.4, 4.1, align="left")
caption(s, M, TOP + 4.2, 7.4, "Abohar's percentile within the South-west group")
bullets(s, 8.4, TOP + 0.05, 4.33, 3.2, [
    ("Straw buyer: ", "a biomass power plant inside the tehsil."),
    ("Labour: ", "most farm labourers per cultivator in Punjab."),
    ("Livestock: ", "most cattle per cultivator in its group; straw is fodder."),
    ("Early second crop: ", "earliest in its group."),
], size=14, gap=8)
panel(s, 8.4, TOP + 3.3, 4.33, 1.45)
text(s, 8.6, TOP + 3.35, 3.95, 1.35, [[("Caveats ", {"bold": True, "color": BAD})],
     [("One tehsil cannot separate four levers. Rice map needed a 0.58 scaling; some cotton may pass as paddy.",
       {})]], size=14, margin=0)
short(s, "Abohar points to four levers worth testing; they are leads, not findings.")
notes(s, "Also a basmati-heavy district (Fazilka, 57% of rice) and 13 km from the Rajasthan border.")

# ================================================================ SECTION 8 · IMPACT
# 28 Theory of change + Phase 1
s = S("Impact", "Theory of change and field validation")
steps = [("PD leads", "where to look, candidate levers"),
         ("Phase 1", "confirm what PDs do differently"),
         ("Phase 2", "pilot the lever in matched villages"),
         ("Measure", "satellite burnt share + survey"),
         ("Scale", "through a partner if it holds")]
k, gap = len(steps), 0.3
bw = (W - 2 * M - (k - 1) * gap) / k
for i, (h_, b_) in enumerate(steps):
    x = M + i * (bw + gap)
    panel(s, x, TOP + 0.05, bw, 1.15, color=TINT if i == 1 else PANEL)
    text(s, x + 0.15, TOP + 0.12, bw - 0.3, 0.4, h_, size=16, bold=True, color=EMBER, margin=0)
    text(s, x + 0.15, TOP + 0.52, bw - 0.3, 0.65, b_, size=13, margin=0)
    if i < k - 1:
        arrow(s, x + bw + 0.04, TOP + 0.5, w=gap - 0.08, h=0.25)
card(s, M, TOP + 1.45, 5.95, 3.3, "Proposed interventions", [
    "Assured straw buyer near the field (Abohar's plant)",
    "Harvest-season labour and fodder links",
    "Doaba-style early second crop where suitable",
    "Target and monitor within peer groups, allowing for rice share"], size=16, head_color=GOOD)
card(s, M + 6.18, TOP + 1.45, 5.95, 3.3, "Phase 1 · field investigation (one season)", [
    "PD, ND and typical tehsils; ~6 villages each, chosen by satellite burning",
    "Farmer survey, focus groups, key informants",
    "Dated photos at our satellite points: new ground truth",
    "Tests assumptions: practices are real, and transferable"], size=16, head_color=EMBER)
short(s, "DPPD gives leads; Phase 1 checks them on the ground before anything is piloted.")
notes(s, "Assumptions: PD practices are real, not a data artefact; they transfer beyond Doaba/Abohar; farmers take "
         "up the lever; burning falls rather than moving in time or place.")

# 29 Randomized pilot
s = S("Impact", "Randomized pilot and impact measurement")
card(s, M, TOP + 0.05, 4.0, 3.4, "Phase 2 · design", [
    "Villages in non-PD tehsils of the same peer group",
    "Paired on past burning + rice share",
    "One village per pair gets the lever at random (treatment); the other is control"], size=15, head_color=EMBER)
card(s, M + 4.2, TOP + 0.05, 4.0, 3.4, "Outcome indicators", [
    "Satellite burnt share per village (our detector, 30 points)",
    "Straw sold or fed (survey)",
    "List experiment for burning: farmers report only how many statements are true"], size=15, head_color=GOOD)
image(s, FF / "f16_sample_size.png", 9.0, TOP + 0.05, 3.73, 3.0)
caption(s, 9.0, TOP + 3.1, 3.73, "Villages per arm to detect a 10-point drop")
note_bar(s, TOP + 3.65, "~30 villages per arm", "(35 pairs per lever) detect a 10-point drop at 80% power; the "
         "pessimistic case (52) still fits the 1,633-village south-west frame.", h=1.1, size=14)
short(s, "the same free satellite measure that found the PDs becomes the pilot's outcome measure.")
notes(s, "Sample size from our own tehsil data: ANCOVA on village baseline, 80% power, 5% two-sided. Burning is "
         "illegal, so the list experiment avoids direct questions.")

# 30 Limitations and conclusion
s = S("Impact", "Limitations and conclusion")
cw = (W - 2 * M - 0.4) / 3
card(s, M, TOP + 0.05, cw, 4.7, "Contributions", [
    "Reproducible DPPD grouping for 97 tehsils",
    "Free Sentinel-2 detector that separates burning from ploughing",
    "Tehsil burning measure that farmers cannot dodge by timing fires"], size=17, head_color=EMBER)
card(s, M + cw + 0.2, TOP + 0.05, cw, 4.7, "Key findings", [
    "Abohar: strict PD; four candidate levers",
    "Doaba belt burns little as a region",
    "Compare like with like and allow for rice share, or low paddy looks like good behaviour"], size=17,
     head_color=GOOD)
card(s, M + 2 * (cw + 0.2), TOP + 0.05, cw, 4.7, "Limitations · future work", [
    "No fieldwork: no practice confirmed on the ground",
    "Partial burns under-counted; 2024 doubtful",
    "8 PDs, 4 NDs; mixed-year public data; no CRM data",
    "Next: Phase 1 field visits, then the pilot"], size=17, head_color=BAD)
short(s, "thank you. Every number in this talk is reproducible from code in the repository.")

# ---------------------------------------------------------------- page numbers
for i, sl in enumerate(PAGES, start=1):
    text(sl, W - M - 1.0, H - 0.42 + 0.1, 1.0, 0.25, f"{i} / {len(PAGES)}", size=10, color=MUTED,
         align=PP_ALIGN.RIGHT, margin=0)

prs.save(OUT)
print(f"Saved {OUT}: cover + {len(PAGES)} slides")
