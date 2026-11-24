"""
Final presentation deck, version 3 (2026-11-25): 42 main slides + 4 backup.

Structure set by Soham (2026-11-25): research question -> DPPD pipeline -> till midterm -> grouping
(final table, Gower, 97x97 matrix, clustering, cut, stability, sensitivity, result) -> burn detector (midterm
index, how it failed, what we tried, how we got to the algorithm, algorithm, results, CEEW test) -> tehsil
measure -> PD identification -> validation -> public drivers -> impact assessment.
Every slide: one sentence title, one visual, and an "In short" line at the bottom; a progress strip on top.
Helpers and style copied from make_final_deck_v2.py.

Run:  python Code/figures/make_v2_figures.py
      python Code/figures/make_v3_figures.py
      python Code/figures/make_final_deck_v3.py
Out:  report/final_deck_v3.pptx
"""
import json
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "outputs" / "figures"
PLANET = ROOT / "outputs" / "planet"
OUT = ROOT / "report" / "final_deck_v3.pptx"

# Smoke and ember: charcoal base, one ember accent, green only for "positive deviant".
DARK = RGBColor(0x1F, 0x1A, 0x17)
EMBER = RGBColor(0xE4, 0x57, 0x2E)
GOOD = RGBColor(0x0F, 0x7B, 0x4A)
BAD = RGBColor(0xC0, 0x39, 0x2B)
TEXT = RGBColor(0x1F, 0x1A, 0x17)
MUTED = RGBColor(0x6B, 0x65, 0x60)
PANEL = RGBColor(0xF1, 0xF0, 0xEE)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ON_DARK_MUTED = RGBColor(0xC9, 0xC2, 0xBC)
GROUP = {"Central": RGBColor(0x2A, 0x78, 0xD6), "South-west": RGBColor(0xEB, 0x68, 0x34),
         "Foothills": RGBColor(0x1B, 0xAF, 0x7A)}
HEAD, BODY = "Cambria", "Calibri"

W, H = 13.333, 7.5
M = 0.6  # side margin
TITLE_Y, TITLE_H = 0.4, 0.85
TOP = 1.45  # content starts here

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]


# ---------- helpers ----------

def fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def background(slide, color):
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = color


def text(slide, x, y, w, h, runs, size=16, color=TEXT, font=BODY, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, italic=False, margin=0.05):
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


def bullets(slide, x, y, w, h, items, size=16, color=TEXT, gap=8):
    """items: list of str or (bold lead, rest). Real bullets via XML buChar."""
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
        bu = pPr.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}buChar",
                             {"char": "•"})
        pPr.append(bu)
        lead, rest = (it, "") if isinstance(it, str) else it
        for t, b in ((lead, not isinstance(it, str)), (rest, False)):
            if not t:
                continue
            r = p.add_run()
            r.text = t
            r.font.name, r.font.size, r.font.bold = BODY, Pt(size), b
            r.font.color.rgb = color
    return box


def title(slide, t, sub=None):
    text(slide, M, TITLE_Y, W - 2 * M, TITLE_H, t, size=34, font=HEAD, bold=True,
         anchor=MSO_ANCHOR.BOTTOM, margin=0)
    if sub:
        text(slide, M, TITLE_Y + TITLE_H + 0.02, W - 2 * M, 0.4, sub, size=15, color=MUTED, margin=0)


def tag(slide, label):
    """Small section tag top-left, the deck's one repeated motif (ember dot + label)."""
    dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(M), Inches(0.22), Inches(0.14), Inches(0.14))
    fill(dot, EMBER)
    text(slide, M + 0.2, 0.12, 6, 0.32, label.upper(), size=11, color=MUTED, bold=True, margin=0)


def image(slide, path, x, y, w, h, align="center"):
    iw, ih = Image.open(path).size
    s = min(w / iw, h / ih)
    pw, ph = iw * s, ih * s
    px = x + (w - pw) / 2 if align == "center" else (x if align == "left" else x + w - pw)
    py = y + (h - ph) / 2
    return slide.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(pw), Inches(ph))


def caption(slide, x, y, w, t):
    text(slide, x, y, w, 0.35, t, size=11, color=MUTED, italic=True, margin=0)


def panel(slide, x, y, w, h, color=PANEL, rounded=True):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    fill(shp, color)
    if rounded:
        shp.adjustments[0] = 0.06
    return shp


def stat(slide, x, y, w, big, label, color=EMBER, big_size=40):
    text(slide, x, y, w, 0.8, big, size=big_size, font=HEAD, bold=True, color=color, margin=0)
    text(slide, x, y + 0.8, w, 0.7, label, size=13, color=MUTED, margin=0)


def card(slide, x, y, w, h, head, body, head_color=TEXT, size=14):
    panel(slide, x, y, w, h)
    text(slide, x + 0.2, y + 0.15, w - 0.4, 0.45, head, size=17, bold=True, color=head_color, margin=0)
    if isinstance(body, list):
        bullets(slide, x + 0.15, y + 0.62, w - 0.3, h - 0.7, body, size=size, gap=4)
    else:
        text(slide, x + 0.2, y + 0.62, w - 0.4, h - 0.7, body, size=size, margin=0)


def table(slide, x, y, w, rows, col_w, size=13, head_fill=DARK, row_h=0.4, first_bold=True):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w),
                                 Inches(row_h * len(rows)))
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
            if i == 0:
                r.font.bold, r.font.color.rgb = True, WHITE
                cell.fill.solid()
                cell.fill.fore_color.rgb = head_fill
            else:
                r.font.bold = first_bold and j == 0
                r.font.color.rgb = color or TEXT
                cell.fill.solid()
                cell.fill.fore_color.rgb = PANEL if i % 2 else WHITE
    return shp


def arrow(slide, x, y, w=0.35, h=0.35, color=MUTED):
    a = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    fill(a, color)


def new(label=None, dark=False):
    s = prs.slides.add_slide(BLANK)
    background(s, DARK if dark else WHITE)
    if label:
        tag(s, label)
    return s


def notes(slide, t):
    slide.notes_slide.notes_text_frame.text = t


FF = ROOT / "outputs" / "figures" / "final"
RAWF = FF / "raw"
TOTAL = 25


def meta(name):
    return json.loads((RAWF / name).read_text())


def foot(slide, i, dark=False):
    text(slide, W - M - 1.0, H - 0.42, 1.0, 0.3, f"{i} / {TOTAL}", size=10,
         color=ON_DARK_MUTED if dark else MUTED, align=PP_ALIGN.RIGHT, margin=0)


def big_title(slide, t, sub=None):
    """Sentence title: the slide's one message."""
    text(slide, M, TITLE_Y, W - 2 * M, TITLE_H, t, size=30, font=HEAD, bold=True,
         anchor=MSO_ANCHOR.BOTTOM, margin=0)
    if sub:
        text(slide, M, TITLE_Y + TITLE_H + 0.05, W - 2 * M, 0.4, sub, size=15, color=MUTED, margin=0)


n = 0


def S(label, t, sub=None, dark=False):
    global n
    n += 1
    s = new(label, dark=dark)
    if t:
        big_title(s, t, sub)
    foot(s, n, dark)
    return s


def flow_steps(slide, y, items, h=1.3, gap=0.32, size=13, head_color=EMBER):
    """Row of panels joined by arrows. items: list of (head, body)."""
    k = len(items)
    bw = (W - 2 * M - (k - 1) * gap) / k
    for i, (h_, b_) in enumerate(items):
        x = M + i * (bw + gap)
        panel(slide, x, y, bw, h)
        text(slide, x + 0.15, y + 0.1, bw - 0.3, 0.4, h_, size=size + 3, bold=True, color=head_color, margin=0)
        text(slide, x + 0.15, y + 0.52, bw - 0.3, h - 0.6, b_, size=size, margin=0)
        if i < k - 1:
            arrow(slide, x + bw + 0.03, y + h / 2 - 0.13, w=gap - 0.06, h=0.26)



# =====================================================================================
# Version 3 additions: progress strip, "In short" strip, deferred page numbers.
# =====================================================================================
import pandas as pd

STAGES = ["Question", "Peer groups", "Burn detector", "Tehsil measure", "PDs", "Validation", "Why", "Impact"]
LIGHT = RGBColor(0xB5, 0xAE, 0xA8)
TINT = RGBColor(0xFB, 0xE9, 0xE2)
PAGES = []
BOTTOM = 6.25  # content must end above this


def progress(slide, stage):
    box = slide.shapes.add_textbox(Inches(4.9), Inches(0.1), Inches(W - M - 4.9), Inches(0.32))
    tf = box.text_frame
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", 0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    for i, st in enumerate(STAGES):
        r = p.add_run()
        r.text = st
        r.font.name, r.font.size = BODY, Pt(10.5)
        r.font.bold = st == stage
        r.font.color.rgb = EMBER if st == stage else LIGHT
        if i < len(STAGES) - 1:
            r = p.add_run()
            r.text = "   ›   "
            r.font.name, r.font.size = BODY, Pt(10.5)
            r.font.color.rgb = LIGHT


def short(slide, t):
    """The slide's message in one plain sentence, always in the same place."""
    panel(slide, M, 6.38, W - 2 * M, 0.6, color=TINT)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(M), Inches(6.38), Inches(0.08), Inches(0.6))
    fill(bar, EMBER)
    text(slide, M + 0.25, 6.38, W - 2 * M - 0.4, 0.6, [[("In short:  ", {"bold": True, "color": EMBER}), (t, {})]],
         size=15, anchor=MSO_ANCHOR.MIDDLE, margin=0)


def big_title(slide, t, sub=None):
    """Sentence title: the slide's one message. Long titles drop to 26 pt so they stay on one line."""
    text(slide, M, TITLE_Y, W - 2 * M, TITLE_H, t, size=30 if len(t) <= 56 else 26, font=HEAD, bold=True,
         anchor=MSO_ANCHOR.BOTTOM, margin=0)
    if sub:
        text(slide, M, TITLE_Y + TITLE_H + 0.05, W - 2 * M, 0.4, sub, size=15, color=MUTED, margin=0)


def S(stage, t, sub=None, dark=False):
    s = prs.slides.add_slide(BLANK)
    background(s, DARK if dark else WHITE)
    tag(s, stage)
    progress(s, stage)
    if t:
        big_title(s, t, sub)
    PAGES.append((s, dark))
    return s


def steps_col(slide, x, y, w, items, num_color=EMBER, size=14, gap=0.12, h=0.78, head_size=None, start=1):
    """Vertical numbered steps: items = list of (head, body)."""
    for i, (h_, b_) in enumerate(items):
        yy = y + i * (h + gap)
        c = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(yy + 0.05), Inches(0.42), Inches(0.42))
        fill(c, num_color)
        text(slide, x, yy + 0.05, 0.42, 0.42, str(i + start), size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE, margin=0)
        text(slide, x + 0.58, yy, w - 0.58, h, [[(h_, {"bold": True, "size": head_size or size + 1}),
                                                 ("  " + b_, {"color": TEXT})]], size=size, margin=0)


MASTER = pd.read_csv(ROOT / "Data" / "punjab_homogeneous_grouping_master_transformed.csv").set_index("lgd_tehsil_name")
GX = json.loads((FF / "f18_gower_example.json").read_text())

# =====================================================================================
# 1. Title
# =====================================================================================
s = new(dark=True)
PAGES.append((s, True))
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

# =====================================================================================
# 2. Research question
# =====================================================================================
s = S("Question", "Which tehsils burn far less straw than places like them, and why?")
image(s, FIG / "fig_G_burn_map.png", M, TOP + 0.05, 3.9, 4.4, align="left")
caption(s, M, TOP + 4.5, 3.9, "Share of paddy burnt, mean 2020–24, by tehsil (our measure)")
stat(s, 4.85, TOP + 0.05, 2.5, "52–64%", "of paddy area burnt\nevery season", big_size=34)
stat(s, 7.45, TOP + 0.05, 2.5, "14–22 days", "between paddy harvest\nand wheat sowing", big_size=34)
stat(s, 10.05, TOP + 0.05, 2.7, "−91%", "drop in satellite fire counts\n2021→24: farmers burn after\nthe satellite passes",
     color=BAD, big_size=34)
bullets(s, 4.85, TOP + 1.95, 7.9, 1.4, [
    ("Why farmers burn: ", "the straw must go before wheat is sown, and fire is the cheapest way."),
    ("The puzzle: ", "places that look alike burn very differently. Some may already have an answer."),
], size=15, gap=6)
panel(s, 4.85, TOP + 3.3, 7.88, 1.45, color=PANEL)
text(s, 5.1, TOP + 3.3, 7.4, 1.45, [
    [("Research question", {"bold": True, "color": EMBER, "size": 14})],
    [("Which of Punjab's 97 tehsils burn much less paddy straw than structurally similar tehsils, "
      "and what might explain it?", {"size": 18, "bold": True})]], anchor=MSO_ANCHOR.MIDDLE, margin=0)
short(s, "instead of inventing a new solution, find places that already burn less, and learn from them.")
notes(s, "Tehsil = sub-district; Punjab has 97. 'Structurally similar' means same rice share, rainfall, zone, "
         "groundwater and soil. Fire counts (VIIRS) collapsed after 2021 because farmers time fires after the "
         "afternoon overpass, so we had to build our own measure from Sentinel-2.")

# =====================================================================================
# 3. DPPD pipeline
# =====================================================================================
s = S("Question", "Our DPPD pipeline: compare like with like, then ask why")
pipe = [("1", "Problem–method fit", "Is burning measurable, does it vary, can some places do better?"),
        ("2a", "Peer groups", "Group tehsils by conditions they cannot change"),
        ("2b", "Burn measure", "Burnt share of paddy per tehsil, from satellites"),
        ("2c", "Find PDs", "Who burns far less than its own group?"),
        ("2d", "Validate", "Is the PD real, or noise and data errors?"),
        ("3", "Why?", "What do PDs have that peers lack? (public data)")]
k = len(pipe)
gap = 0.22
bw = (W - 2 * M - (k - 1) * gap) / k
for i, (num, h_, b_) in enumerate(pipe):
    x = M + i * (bw + gap)
    stage_col = MUTED if num == "1" else (EMBER if num.startswith("2") else GOOD)
    hdr = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(TOP + 0.1), Inches(bw), Inches(0.55))
    fill(hdr, stage_col)
    text(s, x, TOP + 0.1, bw, 0.55, f"{num} · {h_}", size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, margin=0.03)
    panel(s, x, TOP + 0.65, bw, 1.35, rounded=False)
    text(s, x + 0.12, TOP + 0.75, bw - 0.24, 1.2, b_, size=13, margin=0)
    if i < k - 1:
        arrow(s, x + bw + 0.02, TOP + 1.2, w=gap - 0.04, h=0.22)
text(s, M, TOP + 2.1, 3, 0.3, "Stage 1", size=11, color=MUTED, bold=True, margin=0)
text(s, M + bw + gap, TOP + 2.1, 6, 0.3, "Stage 2 · Determine positive deviants (PDs)", size=11, color=EMBER,
     bold=True, margin=0)
text(s, M + 5 * (bw + gap), TOP + 2.1, 2.2, 0.3, "Stage 3", size=11, color=GOOD, bold=True, margin=0)
card(s, M, TOP + 2.6, 5.95, 2.1, "Rule 1 · Groups use only what a tehsil cannot change",
     "Rice share, rainfall, agro-ecological zone, groundwater, soil. Never things that could be the answer "
     "(machines, markets), and never burning itself.", size=14)
card(s, M + 6.18, TOP + 2.6, 5.95, 2.1, "Rule 2 · Groups first, burning second",
     "We froze the groups on 7 Oct before measuring burning, so knowing who burns could not shape the groups. "
     "Then we added an impact-assessment plan for what to do with the PDs.", size=14)
short(s, "a PD is a tehsil that burns far less than tehsils facing the same conditions, not just a low burner.")
notes(s, "Positive deviance: some members of a community do better than peers with the same resources. "
         "Data-powered: we find them in data instead of by field survey. The talk follows this pipeline left to right.")

# =====================================================================================
# 4. Till the midterm
# =====================================================================================
s = S("Question", "Till the midterm (17 Sep): burn index chosen, groups designed")
text(s, M, TOP + 0.05, 6.0, 0.4, "A · Burn measure: chosen", size=18, bold=True, color=EMBER, margin=0)
rows = [["380 ground-truth fields, 5-fold CV", "NBR", "BAIS2 + TCB"],
        ["Accuracy", "81.3%", ("95.5%", GOOD)],
        ["Burns caught (recall)", "82.3%", ("98.1%", GOOD)],
        ["Burns missed", ("47", BAD), ("5", GOOD)]]
table(s, M, TOP + 0.55, 6.0, rows, [3.2, 1.3, 1.5], size=14, row_h=0.5)
text(s, M, TOP + 2.7, 6.0, 1.3, "BAIS2 = a burn index from Sentinel-2's red-edge bands. TCB = brightness. "
     "Burnt fields score high on BAIS2 and go dark. Fields: CEEW photos, Hoshiarpur/Jalandhar 2021, Sangrur 2020.",
     size=13, color=MUTED, margin=0)
text(s, 7.0, TOP + 0.05, 5.73, 0.4, "B · Grouping: designed, not run", size=18, bold=True, color=EMBER, margin=0)
bullets(s, 7.0, TOP + 0.55, 5.73, 2.9, [
    ("Five structural factors: ", "rice, climate zone, groundwater, soil, cropping intensity."),
    ("Kept out on purpose: ", "machines, mandi access (possible answers, saved for Stage 3)."),
    ("Unit = tehsil: ", "finer than district, steadier than village."),
    ("Boundary bridge: ", "2011 Census villages mapped to today's 97 tehsils, so old and new data line up."),
], size=14, gap=6)
panel(s, M, TOP + 3.85, W - 2 * M, 0.85, color=PANEL)
text(s, M + 0.25, TOP + 3.85, W - 2 * M - 0.5, 0.85, [[("Still open at the midterm: ", {"bold": True, "color": BAD}),
     ("the grouping had not been run, and the burn index had been tested on one date only, never on ploughed fields.",
      {})]], size=15, anchor=MSO_ANCHOR.MIDDLE, margin=0)
short(s, "after the midterm we ran the grouping, and found the burn index had a serious flaw.")
notes(s, "This is the starting point. Everything after this slide is work done since 17 September.")

# =====================================================================================
# 5. Final table
# =====================================================================================
s = S("Peer groups", "Our final input: one row per tehsil, five structural dimensions")
names = ["Phagwara", "Adampur", "Abohar", "Lehra", "Dinanagar", "Pathankot"]
AES = {"aesr_share_14_2": "14.2", "aesr_share_2_5": "2.5", "aesr_share_4_1": "4.1", "aesr_share_9_1": "9.1"}


def zone_str(r):
    parts = [(v, r[c]) for c, v in AES.items() if r[c] > 0.05]
    parts.sort(key=lambda t: -t[1])
    return " + ".join(f"{v} ({sh:.0%})" for v, sh in parts)


rows = [["Tehsil", "1 Rice share", "2 Monsoon rain", "3 Agro-eco zone (AESR)", "4 Groundwater use",
         "5 Soil (3 of 8 classes)"]]
for nm in names:
    r = MASTER.loc[nm]
    rows.append([nm, f"{r.rice_share_2022_cal:.0%}", f"{r.mean_monsoon_rainfall_mm:.0f} mm", zone_str(r),
                 f"{r.mean_extraction_pct_2022:.0f}%",
                 f"{r.dominant_soil_texture} · {r.dominant_particle_size} · {r.dominant_drainage}"])
rows.append([("… 91 more", MUTED), "", "", "", "", ""])
table(s, M, TOP + 0.05, W - 2 * M, rows, [1.8, 1.45, 1.6, 2.35, 1.75, 3.18], size=13, row_h=0.42)
cards3 = [("Numbers", "rice share, rain (mm), groundwater use (% of recharge): different units"),
          ("Shares", "zone: a tehsil can be split across zones, so we keep the share in each"),
          ("Categories", "soil: texture, drainage, depth … words, not numbers")]
cw = (W - 2 * M - 0.4) / 3
for i, (h_, b_) in enumerate(cards3):
    card(s, M + i * (cw + 0.2), TOP + 3.55, cw, 1.2, h_, b_, size=13)
short(s, "mm, %, shares and soil words cannot be compared directly, so we need a distance that handles mixed data.")
notes(s, "Sources: rice share = Chen et al. 10 m rice map 2022, calibrated to official district totals; rain = "
         "CHIRPS Jun–Sep 2020–25; zones = NBSS&LUP AESR 2018 polygons; groundwater = CGWB stage of extraction 2022; "
         "soil = NBSS&LUP 1:250K, 8 descriptors. Cropping intensity was dropped after the midterm: the satellite "
         "estimate did not match official figures (rho 0.18) and dropping it moved only 2 tehsils.")

# =====================================================================================
# 6. Gower rules
# =====================================================================================
s = S("Peer groups", "Step 1 · Gower distance: every difference becomes a 0–1 score")
vP, vA = MASTER.loc["Phagwara"], MASTER.loc["Adampur"]
rng = MASTER.drop("Dhar Kalan").rice_share_2022_cal
rr = rng.max() - rng.min()
card(s, M, TOP + 0.1, 3.9, 2.45, "Numbers", [
    "difference ÷ full range across tehsils",
    f"Rice: |{vP.rice_share_2022_cal:.0%} − {vA.rice_share_2022_cal:.0%}| ÷ {rr:.0%} = "
    f"{GX['Phagwara|Adampur']['rice']:.2f}"], size=14)
card(s, M + 4.12, TOP + 0.1, 3.9, 2.45, "Shares (zone)", [
    "same rule on each zone's share, then averaged",
    "Phagwara and Adampur: both 100% zone 9.1 → 0.00"], size=14)
card(s, M + 8.24, TOP + 0.1, 3.89, 2.45, "Categories (soil)", [
    "same class = 0, different = 1",
    f"7 of 8 soil classes differ → {GX['Phagwara|Adampur']['soil']:.2f}"], size=14)
panel(s, M, TOP + 2.75, W - 2 * M, 1.95, color=PANEL)
text(s, M + 0.3, TOP + 2.85, W - 2 * M - 0.6, 0.4, "Dimension-balanced: one equal vote per dimension", size=17,
     bold=True, color=EMBER, margin=0)
text(s, M + 0.3, TOP + 3.3, W - 2 * M - 0.6, 1.4, [
    "Average the columns inside each dimension first, then average the 5 dimensions, each with weight 1/5.",
    "Why: soil has 8 columns and rainfall has 1. Plain Gower would give soil 8 votes and let it outvote everything.",
    "The hill outlier Dhar Kalan is left out when measuring ranges, so it does not stretch the ruler for everyone."],
    size=14, margin=0)
short(s, "every pair of tehsils gets one number: 0 = identical conditions, 1 = as different as Punjab gets.")
notes(s, "Gower (1971) is the standard distance for mixed data. Equal weights are the neutral default when there "
         "is no evidence that one condition matters more; we test this choice later (sensitivity).")

# =====================================================================================
# 7. Worked example
# =====================================================================================
s = S("Peer groups", "Worked example: Phagwara is close to Adampur, far from Abohar")
pa, pb = GX["Phagwara|Adampur"], GX["Phagwara|Abohar"]
vv = GX["values"]
rows = [["Dimension", "Phagwara", "Adampur", "Abohar", "Phagwara ↔ Adampur", "Phagwara ↔ Abohar"],
        ["1 Rice share", f"{vv['Phagwara']['rice_share_2022_cal']:.0%}", f"{vv['Adampur']['rice_share_2022_cal']:.0%}",
         f"{vv['Abohar']['rice_share_2022_cal']:.0%}", f"{pa['rice']:.2f}", f"{pb['rice']:.2f}"],
        ["2 Monsoon rain", f"{vv['Phagwara']['mean_monsoon_rainfall_mm']:.0f} mm",
         f"{vv['Adampur']['mean_monsoon_rainfall_mm']:.0f} mm", f"{vv['Abohar']['mean_monsoon_rainfall_mm']:.0f} mm",
         f"{pa['rainfall']:.2f}", f"{pb['rainfall']:.2f}"],
        ["3 Agro-eco zone", f"AESR {vv['Phagwara']['aesr_dominant']}", f"AESR {vv['Adampur']['aesr_dominant']}",
         f"AESR {vv['Abohar']['aesr_dominant']}", f"{pa['zone']:.2f}", f"{pb['zone']:.2f}"],
        ["4 Groundwater use", f"{vv['Phagwara']['mean_extraction_pct_2022']:.0f}%",
         f"{vv['Adampur']['mean_extraction_pct_2022']:.0f}%", f"{vv['Abohar']['mean_extraction_pct_2022']:.0f}%",
         f"{pa['groundwater']:.2f}", f"{pb['groundwater']:.2f}"],
        ["5 Soil (8 classes)", "Loamy", "Sandy", "Sandy", f"{pa['soil']:.2f}", f"{pb['soil']:.2f}"],
        [("Distance = average of 5", EMBER), "", "", "", (f"{pa['distance']:.2f}", GOOD), (f"{pb['distance']:.2f}", BAD)]]
table(s, M, TOP + 0.1, W - 2 * M, rows, [2.9, 1.6, 1.6, 1.6, 2.2, 2.23], size=15, row_h=0.52)
bullets(s, M, TOP + 3.95, W - 2 * M, 0.9, [
    ("Phagwara ↔ Adampur 0.24: ", "same zone, similar rain, rice and groundwater; they differ mainly in soil."),
    ("Phagwara ↔ Abohar 0.51: ", "Abohar is drier, grows less rice and uses far less groundwater: different on every dimension."),
], size=14, gap=4)
short(s, "the distance agrees with common sense: neighbours in the Doaba are close, the dry south-west is far.")
notes(s, "All numbers are real values from the grouping master; scores computed by Code/grouping/gower.py.")

# =====================================================================================
# 8. 97 x 97 matrix
# =====================================================================================
s = S("Peer groups", "Repeat for every pair: a 97 × 97 table of distances")
image(s, FF / "v3_distance_matrix.png", M, TOP, 6.6, 4.8, align="left")
bullets(s, 7.5, TOP + 0.15, 5.23, 4.5, [
    ("Each cell ", "is the distance between two tehsils: dark = alike, light = different."),
    ("4,656 pairs ", "(97 × 96 ÷ 2); the diagonal is 0, a tehsil compared with itself."),
    ("Here the rows are already sorted ", "by the final groups, so dark squares appear on the diagonal: "
                                          "tehsils inside a group are alike."),
    ("The Foothills ", "are light against everyone else: the most distinct region."),
    ("This table is the only input ", "to the clustering. It never sees maps or burning."),
], size=15, gap=10)
short(s, "the clustering's job is to find those dark blocks on its own, without being told where they are.")
notes(s, "Shown sorted for readability. The clustering receives the table in district order.")

# =====================================================================================
# 9. HAC
# =====================================================================================
s = S("Peer groups", "Step 2 · Hierarchical clustering: merge the two closest, repeat")
image(s, FF / "f20_toy_merge.png", M, TOP + 0.05, 8.9, 3.6, align="left")
caption(s, M, TOP + 3.65, 8.9, "Six real tehsils, real distances. Blue = Central, orange = South-west.")
steps_col(s, 9.75, TOP + 0.05, 2.98, [("Start:", "every tehsil is its own group."),
                                      ("Merge", "the two closest groups."),
                                      ("Group distance", "= average of all pairs between them."),
                                      ("Repeat", "until all are in one tree.")], size=13, h=0.82, gap=0.08)
panel(s, M, TOP + 4.0, W - 2 * M, 0.78, color=PANEL)
text(s, M + 0.25, TOP + 4.0, W - 2 * M - 0.5, 0.78, [[("Worked step 3: ", {"bold": True, "color": EMBER}),
     ("Adampur to {Phagwara, Jalandhar-I} = (0.24 + 0.29) ÷ 2 = 0.27, the closest remaining pair, so they merge.", {})]],
     size=14, anchor=MSO_ANCHOR.MIDDLE, margin=0)
short(s, "we used average linkage because it works on any distance table and does not force round, equal-size groups.")
notes(s, "Why not k-means: it needs coordinates and averages, which soil words do not have. Ward also assumes "
         "Euclidean space. Average linkage is endorsed by Prof. Seth.")

# =====================================================================================
# 10. Full tree
# =====================================================================================
s = S("Peer groups", "On all 97 tehsils this gives a tree (dendrogram)")
image(s, FIG / "fig_B_dendrogram.png", M, TOP + 0.05, W - 2 * M, 3.75)
bullets(s, M, TOP + 3.95, W - 2 * M, 0.9, [
    ("How to read it: ", "tehsils sit at the bottom; the height where two branches join is how different they are."),
    ("Cutting ", "the tree with a horizontal line gives groups; a lower cut gives more, smaller groups."),
], size=14, gap=4)
short(s, "the tree gives every possible grouping; the next two slides decide where to cut and whether to trust it.")
notes(s, "Colours show the final groups for reference. Dhar Kalan joins last of all, so it is set aside as an outlier.")

# =====================================================================================
# 11. Silhouette
# =====================================================================================
s = S("Peer groups", "Where to cut? Silhouette: is each tehsil closer to its own group?")
image(s, FF / "v3_silhouette.png", M, TOP + 0.05, 5.6, 4.4, align="left")
panel(s, 6.5, TOP + 0.05, 6.23, 1.55, color=PANEL)
text(s, 6.75, TOP + 0.1, 5.8, 1.45, [
    [("For each tehsil:  ", {"bold": True}), ("a = average distance to its own group", {})],
    [("", {}), ("                              b = average distance to the nearest other group", {})],
    [("silhouette = (b − a) ÷ larger of a, b", {"bold": True, "color": EMBER})],
    [("+1 clearly placed · 0 on a border · below 0 in the wrong group", {"color": MUTED, "size": 13})]],
     size=14, anchor=MSO_ANCHOR.MIDDLE, margin=0)
rows = [["Cut", "Groups", "Silhouette", "Verdict"],
        ["k = 2", "Plains 81 / Foothills 15", "0.409", "dry south-west hidden inside Plains"],
        [("k = 3", GOOD), "63 / 18 / 15", "0.377", ("chosen: separates the south-west", GOOD)],
        ["k = 4, 5", "same 3 groups", "0.377", "extra pieces < 5 tehsils"],
        ["k = 6", "Central splits", "0.348", "less stable (next slide)"]]
table(s, 6.5, TOP + 1.8, 6.23, rows, [0.9, 2.0, 1.1, 2.23], size=12, row_h=0.5)
short(s, "k = 3 is almost as well separated as k = 2 and keeps Bathinda from being judged against Ludhiana.")
notes(s, "Groups smaller than 5 tehsils are set aside: a peer group needs enough members to compare against. "
         "Silhouette around 0.38 means moderate structure, normal for gradual agro-climatic gradients.")

# =====================================================================================
# 12. Bootstrap
# =====================================================================================
s = S("Peer groups", "Stability: do the groups survive if we leave out 20% of tehsils?")
image(s, FF / "v3_bootstrap.png", M, TOP + 0.05, 5.6, 4.4, align="left")
steps_col(s, 6.5, TOP + 0.1, 6.23, [
    ("Resample:", "pick 80% of tehsils at random and regroup them."),
    ("Compare", "with the full grouping using ARI (1 = same groups, 0 = chance)."),
    ("Repeat 300 times", "and average."),
    ("Final label", "= the group a tehsil lands in most often.")], size=14, h=0.6, gap=0.1)
stat(s, 6.5, TOP + 2.95, 1.8, "0.890", "mean ARI at k = 3", big_size=28)
stat(s, 8.4, TOP + 2.95, 2.5, "94–100%", "of resamples find\neach group again", big_size=28)
stat(s, 11.0, TOP + 2.95, 1.73, "3", "borderline tehsils\n(switch > 20%)", big_size=28)
short(s, "the three groups come back almost every time; only Firozpur, Faridkot and Dinanagar sit on a border.")
notes(s, "Group survival: Central 100%, Foothills 100%, South-west 93.7%. Freeze rule: mean ARI >= 0.8. "
         "k = 2 is even more stable (0.981), which is why every PD is also checked under the 2-group version.")

# =====================================================================================
# 13. Sensitivity
# =====================================================================================
s = S("Peer groups", "Sensitivity: change one design choice at a time")
image(s, FIG / "fig_E_sensitivity.png", M, TOP + 0.05, 7.3, 4.75, align="left")
bullets(s, 8.15, TOP + 0.1, 4.58, 4.6, [
    ("What we changed: ", "each dimension's weight ±15%, or drop one dimension entirely."),
    ("Mostly stable: ", "8 of 10 weight changes keep ARI ≥ 0.83, moving at most 5 tehsils."),
    ("Weak point: ", "the South-west / Central border. More weight on rice or soil, or dropping any dimension, "
                     "merges the south-west back into Central."),
    ("Never moves: ", "the Foothills vs Plains split."),
], size=14, gap=8)
short(s, "because the south-west border is soft, every PD must also hold when Central and South-west are merged.")
notes(s, "The south-west is real (rainfall, zone and groundwater all say so) but shades gradually into the centre "
         "across Malwa rather than meeting it at a sharp line.")

# =====================================================================================
# 14. Grouping result
# =====================================================================================
s = S("Peer groups", "Result: three peer regions, found without any location data")
image(s, FIG / "fig_A_group_map.png", M, TOP - 0.05, 4.1, 4.85, align="left")
rows = [["Group", "Tehsils", "Rice share", "Monsoon rain", "Groundwater use", "Character"],
        [("Central", GROUP["Central"]), "63", "75%", "721 mm", "230%", "paddy plains, most over-pumped"],
        [("South-west", GROUP["South-west"]), "18", "59%", "467 mm", "118%", "dry cotton–paddy belt"],
        [("Foothills", GROUP["Foothills"]), "15", "28%", "981 mm", "117%", "wet, hilly Kandi belt"],
        [("Outlier", MUTED), "1", "7%", "1,604 mm", "27%", "Dhar Kalan hill tehsil, set aside"]]
table(s, 5.0, TOP + 0.05, 7.73, rows, [1.25, 0.85, 1.0, 1.25, 1.35, 2.03], size=12, row_h=0.55)
bullets(s, 5.0, TOP + 3.0, 7.73, 1.8, [
    ("The method never saw a map, ", "yet each group is one connected region matching Punjab's known belts."),
    ("Frozen on 7 Oct, ", "before burning was measured."),
    ("Foothills are measured but not ranked ", "later: the burn check is weakest there."),
], size=14, gap=6)
short(s, "from here on, each tehsil is compared only with tehsils in its own group.")
notes(s, "Medians per group from the transformed master. Groundwater use above 100% means more is pumped than recharged.")

# =====================================================================================
# 15. BAIS2+TCB fixed at midterm
# =====================================================================================
s = S("Burn detector", "At the midterm, BAIS2 + TCB was fixed as our burn measure")
image(s, FF / "f01_season_field.png", M, TOP + 0.1, W - 2 * M, 2.5)
caption(s, M, TOP + 2.65, W - 2 * M, "One Sentinel-2 point through the 2022 season: green paddy → harvest → bare → wheat")
card(s, M, TOP + 3.05, 3.9, 1.7, "The index", "BAIS2 + brightness, combined by a simple model trained on 380 fields: "
     "95.5% accurate on one date.", size=13)
card(s, M + 4.12, TOP + 3.05, 3.9, 1.7, "The plan", "run it on every clear Sentinel-2 image of the season; "
     "if any look scores as burnt, the field burnt.", size=13)
card(s, M + 8.24, TOP + 3.05, 3.89, 1.7, "The hidden question", "after harvest, fields are bare for weeks. Does a "
     "ploughed field also score as burnt?", head_color=BAD, size=13)
short(s, "a one-date test said the index works; the real use is a whole season of looks, and that had never been tested.")
notes(s, "Sentinel-2 passes every 5 days, so each field has about 10–15 clear looks in the 15 Sep–30 Nov window.")

# =====================================================================================
# 16. How it failed
# =====================================================================================
s = S("Burn detector", "How it failed: ploughed fields look burnt too")
image(s, FF / "f05_planet_burnt_vs_ploughed.png", M, TOP + 0.05, W - 2 * M, 3.0)
caption(s, M, TOP + 3.1, W - 2 * M, "PlanetScope daily images, Jalandhar 2021. Top: burnt, goes black, then fades to "
        "soil colour. Bottom: ploughed, never black.")
stat(s, M, TOP + 3.5, 3.9, "81%", "of ploughed, NOT burnt fields called\nburnt (Walker et al. ground truth, 2019)",
     color=BAD, big_size=34)
stat(s, M + 4.12, TOP + 3.5, 3.9, "94.6%", "of random cropland points\ncalled burnt in 2022", color=BAD, big_size=34)
stat(s, M + 8.24, TOP + 3.5, 3.9, "92%", "of fields CEEW saw unburnt\nlater called burnt", color=BAD, big_size=34)
short(s, "a tehsil that ploughs straw in instead of burning would look like a burner, hiding exactly the PDs we want.")
notes(s, "Burns were still caught (98%), so the one-date accuracy was real; the problem is false alarms from tilled soil.")

# =====================================================================================
# 17. Why
# =====================================================================================
s = S("Burn detector", "Why: ash is black for 2–3 days; Sentinel-2 visits every 5")
image(s, FF / "f06_planet_vs_s2.png", M, TOP + 0.05, W - 2 * M, 3.1)
caption(s, M, TOP + 3.2, W - 2 * M, "The same burnt field every day, 30 Oct – 9 Nov 2021 (PlanetScope). Orange frame "
        "= a clear Sentinel-2 image that day: only 2 of 10.")
card(s, M, TOP + 3.6, 5.95, 1.15, "Sentinel-2 (free, every 5 days)", "usually sees faded ash: ash vs fresh soil "
     "AUC 0.51 = a coin toss.", head_color=BAD, size=13)
card(s, M + 6.18, TOP + 3.6, 5.95, 1.15, "PlanetScope (daily, limited quota)", "catches the black days: "
     "ash vs soil AUC 0.96.", head_color=GOOD, size=13)
short(s, "the index was not wrong; it simply arrives after the evidence has faded.")
notes(s, "Planet Education & Research quota is 3,000 km² a month, far too little for Punjab, so Planet can judge "
         "but cannot replace Sentinel-2.")

# =====================================================================================
# 18. What we tried
# =====================================================================================
s = S("Burn detector", "What we tried first, and why each did not work")
rows = [["Tried", "Idea", "Why it did not work"],
        ["Other indices and thresholds", "NBR, CEEW's and Naeher & Ziulu's thresholds", "none separates ash from tilled soil"],
        ["Tighter season window", "count only 15 Sep – 30 Nov", "ploughing for wheat happens in the same weeks"],
        ["Heat (Landsat, MODIS)", "fresh ash should be hotter than soil", "about half of ploughed fields still called burnt"],
        ["Radar (Sentinel-1)", "ploughing roughens soil; radar sees roughness", "12-day revisit; dropped 33% of real burns"],
        ["Hand-labelling images", "label burnt vs ploughed by eye", "10 m chips too coarse: 1 clear case in 60 points"]]
table(s, M, TOP + 0.1, W - 2 * M, rows, [3.0, 4.4, 4.73], size=14, row_h=0.6)
panel(s, M, TOP + 3.85, W - 2 * M, 0.9, color=PANEL)
text(s, M + 0.25, TOP + 3.85, W - 2 * M - 0.5, 0.9, [[("Common cause: ", {"bold": True, "color": EMBER}),
     ("all of these look at one image at a time. One image after the ash has faded cannot tell the two apart.", {})]],
     size=15, anchor=MSO_ANCHOR.MIDDLE, margin=0)
short(s, "the answer had to use time: how the field changed, not just how it looks on one day.")
notes(s, "Radar was B. Albanna's suggestion, tested on CEEW 2021 fields; kept as a documented negative result.")

# =====================================================================================
# 19. How we got to the algorithm
# =====================================================================================
s = S("Burn detector", "How we arrived at our algorithm: four observations")
obs = [("Burning is sudden.", "Drying and harvest change a field slowly; a fire darkens it overnight.",
        "Look for the biggest jump in the burn score."),
       ("Compare with just before.", "Ash and soil differ more in how the field changed than in how it looks.",
        "Compare the jump image with the last clear image before it."),
       ("We need fields known to be ploughed.", "Walker et al. 2019: farmer-reported burnt and ploughed fields.",
        "Train on 2,204 burnt + 223 ploughed-not-burnt fields."),
       ("No single index is enough.", "Each band carries a little information.",
        "Let a random forest combine 14 bands and indices.")]
text(s, M, TOP + 0.05, 5.2, 0.35, "What we noticed", size=14, bold=True, color=MUTED, margin=0)
text(s, 7.35, TOP + 0.05, 5.4, 0.35, "What we built", size=14, bold=True, color=MUTED, margin=0)
for i, (h_, b_, d_) in enumerate(obs):
    y = TOP + 0.45 + i * 1.08
    panel(s, M, y, 6.2, 0.95)
    text(s, M + 0.2, y + 0.06, 5.9, 0.85, [[(h_ + " ", {"bold": True}), (b_, {})]], size=13,
         anchor=MSO_ANCHOR.MIDDLE, margin=0)
    arrow(s, M + 6.3, y + 0.33, w=0.35, h=0.3, color=EMBER)
    panel(s, 7.35, y, 5.38, 0.95, color=TINT)
    text(s, 7.55, y + 0.06, 5.0, 0.85, d_, size=13, bold=True, anchor=MSO_ANCHOR.MIDDLE, margin=0)
short(s, "the detector looks for a sudden darkening, compares before and after, and learns from real ploughed fields.")
notes(s, "PlanetScope is then used as an independent judge in a new district and year (Jalandhar 2021).")

# =====================================================================================
# 20. Algorithm
# =====================================================================================
s = S("Burn detector", "Our algorithm, step by step, for one field in one season")
alg = [("1 · Flag", "Score every clear Sentinel-2 image with BAIS2 + TCB. Score > 0 = something happened "
                    "(burnt or ploughed)."),
       ("2 · Candidate", "Pick the flagged image with the largest rise in score since the previous image."),
       ("3 · Before", "Take the last clear image in the 20 days before the candidate."),
       ("4 · Describe", "14 numbers: bands and indices after, and how much each changed."),
       ("5 · Decide", "Random forest (500 trees) → probability burnt. Burnt if p ≥ 0.79.")]
k = len(alg)
gap = 0.2
bw = (W - 2 * M - (k - 1) * gap) / k
for i, (h_, b_) in enumerate(alg):
    x = M + i * (bw + gap)
    panel(s, x, TOP + 0.15, bw, 2.55)
    text(s, x + 0.15, TOP + 0.25, bw - 0.3, 0.4, h_, size=17, bold=True, color=EMBER, margin=0)
    text(s, x + 0.15, TOP + 0.75, bw - 0.3, 1.9, b_, size=14, margin=0)
    if i < k - 1:
        arrow(s, x + bw + 0.02, TOP + 1.3, w=gap - 0.04, h=0.24)
card(s, M, TOP + 2.95, 5.95, 1.75, "Why cut-off 0.79?", "It keeps 90% of real burns. Ploughing false alarms are the "
     "bigger danger for DPPD, so we chose a strict cut. 0.5 is run as a check.", size=13)
card(s, M + 6.18, TOP + 2.95, 5.95, 1.75, "No verdict = left out", "A point with no clear image, or no image before "
     "the candidate, is 'unknown' and not counted (< 3% of points).", size=13)
short(s, "steps 1–2 find when something happened; steps 3–5 decide whether it was fire or a plough.")
notes(s, "Clear = Sentinel-2 scene classes 2/4/5/7 (the default mask threw away fresh char as 'dark area'). "
         "Code: Code/planet/jalandhar_walker_model_test.py and Code/burn/tehsil_metric_rf.py.")

# =====================================================================================
# 21. Example
# =====================================================================================
s = S("Burn detector", "Example: two real points in Lehra, 2022")
image(s, FF / "f19_detector_series.png", M, TOP + 0.05, W - 2 * M, 3.75)
card(s, M, TOP + 3.9, 5.95, 0.85, "Left: burnt (p = 1.00)", "score jumps from −7 to +10 in one look.", size=13,
     head_color=BAD)
card(s, M + 6.18, TOP + 3.9, 5.95, 0.85, "Right: not burnt (p = 0.18)", "slow climb; crosses the flag line late.",
     size=13, head_color=GOOD)
short(s, "both fields cross the flag line, which fooled the old index; only the sudden jump is judged a burn.")
notes(s, "Each dot is one clear Sentinel-2 look at a single 20 m pixel. Blue ring = 'before', orange ring = candidate.")

# =====================================================================================
# 22. Result on Walker
# =====================================================================================
s = S("Burn detector", "Result: ploughing false alarms fall from 81% to 18%")
image(s, FF / "f07_detector_bars.png", M, TOP + 0.05, 5.4, 4.45, align="left")
caption(s, M, TOP + 4.5, 5.4, "Walker et al. ground truth 2019, 5-fold cross-validation")
rows = [["Method", "Burns caught", "Ploughed called burnt"],
        ["Old index (midterm)", "98%", ("81%", BAD)],
        ["Daily Planet rule", "90%", "9%"],
        ["Sentinel-2 trained on Planet labels", "89%", "22%"],
        [("Our detector, cut-off 0.79", GOOD), ("90%", GOOD), ("18%", GOOD)],
        ["Our detector, cut-off 0.5", "97.5%", "51%"]]
table(s, 6.3, TOP + 0.1, 6.43, rows, [3.3, 1.45, 1.68], size=13, row_h=0.52)
text(s, 6.3, TOP + 3.35, 6.43, 1.3, "Model quality AUC 0.938. Sentinel-2 trained only on Planet labels comes close "
     "(22%), so Planet can teach Sentinel-2 where no field survey exists.", size=13, color=MUTED, margin=0)
short(s, "we give up 8 points of burns caught to cut ploughing false alarms by more than four times.")
notes(s, "Walker et al. 2019 is the only public ground truth with ploughed-not-burnt fields for Punjab.")

# =====================================================================================
# 23. Improvement ladder
# =====================================================================================
s = S("Burn detector", "How we improved it, one change at a time")
image(s, FF / "v3_dev_ladder.png", M, TOP + 0.05, 7.6, 3.3, align="left")
caption(s, M, TOP + 3.4, 7.6, "Jalandhar 2021, burns judged by daily PlanetScope; cut-off 0.5")
panel(s, M, TOP + 3.85, 7.6, 0.9, color=PANEL)
text(s, M + 0.25, TOP + 3.85, 7.2, 0.9, [[("Read it as: ", {"bold": True, "color": EMBER}),
     ("taller bar = more real burns kept; the number inside = clean fields wrongly called burnt (of 32).", {})]],
     size=13, anchor=MSO_ANCHOR.MIDDLE, margin=0)
bullets(s, 8.45, TOP + 0.1, 4.28, 4.6, [
    ("Old index: ", "catches all burns but calls 23 of 32 unburnt fields burnt."),
    ("Forest added: ", "false alarms fall to 2–3, but too many burns lost."),
    ("Better 'before': ", "the last clear image, not a 20-day average: 36 → 47."),
    ("Better candidate: ", "the largest jump: 47 → 51."),
    ("No gain from: ", "other cloud masks, extra local training fields, automatic cut-offs."),
], size=13, gap=6)
short(s, "each change kept false alarms near zero while winning back real burns.")
notes(s, "Judge A: an automatic Planet rule calls a field burnt if its brightness falls to <= 0.765 of its median "
         "over the previous 15 days. No manual labels, no retraining on Jalandhar.")

# =====================================================================================
# 24. CEEW test
# =====================================================================================
s = S("Burn detector", "Tested on new ground truth: CEEW field visits, Jalandhar 2021")
image(s, FF / "v3_ceew_test.png", M, TOP + 0.05, 8.1, 2.95, align="left")
caption(s, M, TOP + 3.05, 8.1, "CEEW visited 357 fields on 29 Oct 2021: 262 burnt, 95 unburnt. Model trained on "
        "Walker 2019, not retrained.")
stat(s, M, TOP + 3.35, 2.6, "28 → 2", "of 95 clean fields\ncalled burnt", color=GOOD, big_size=26)
stat(s, M + 2.75, TOP + 3.35, 2.6, "56 of 72", "fully burnt fields\nstill caught", color=GOOD, big_size=26)
stat(s, M + 5.5, TOP + 3.35, 2.6, "89 of 190", "partly burnt fields\nstill caught", color=BAD, big_size=26)
bullets(s, 9.0, TOP + 0.1, 3.73, 4.6, [
    ("New district, new year, ", "never seen in training."),
    ("False alarms: ", "28/95 → 2/95. The Planet judge agrees: 23/32 → 0–3/32."),
    ("Cost: ", "missed burns, mostly partial ones. Fully burnt fields: 56 of 72 kept; partly burnt: 89 of 190."),
], size=13, gap=8)
short(s, "the detector now rarely calls a clean field burnt; it under-counts partial burns, which we state as a limit.")
notes(s, "For ranking tehsils, an under-count hurts less than false alarms, provided the under-count is similar "
         "across tehsils (assumption, not tested). AUC 0.94 vs 0.89 for the old index on judge A.")

# =====================================================================================
# 25. Fields -> tehsils
# =====================================================================================
s = S("Tehsil measure", "From fields to tehsils: 100 fixed rice points per tehsil")
image(s, FF / "f08_points_two_tehsils.png", M, TOP + 0.05, 7.8, 4.0, align="left")
mp = meta("tehsil_phagwara.json")
caption(s, M, TOP + 4.1, 7.8, f"Sentinel-2 true colour, cloud-free {mp['date']}, with each point's 2022 verdict")
steps_col(s, 8.7, TOP + 0.1, 4.03, [
    ("Pick", "100 random 20 m pixels that are rice in both the 2020 and 2022 maps."),
    ("Keep them fixed", "every season, so year-to-year change is not sampling luck."),
    ("Run the detector", "on each point, 15 Sep – 30 Nov, 2019–24."),
    ("Burnt share", "= burnt points ÷ points with a verdict.")], size=13, h=0.95, gap=0.08)
short(s, "each tehsil gets one number per season: the share of its paddy points that were burnt.")
notes(s, "15 Sep – 30 Nov is the ISRO protocol used by CAQM. >= 97% of points get a verdict each season.")

# =====================================================================================
# 26. Tehsil values and decisions
# =====================================================================================
s = S("Tehsil measure", "Burnt share by tehsil, 2020–24, and the choices we made")
image(s, FF / "f09_yearly_maps.png", M, TOP + 0.05, W - 2 * M, 2.9)
caption(s, M, TOP + 3.0, W - 2 * M, "Burnt share by tehsil: the same places stay low or high year after year")
cards4 = [("Seasons for PDs", "2020–24; 2019 only for the official check"),
          ("Ranked", "81 tehsils: Central 63, South-west 18"),
          ("Foothills", "measured, not ranked: burn check weakest"),
          ("2024 flagged", "72% of burns seen late Nov: rerun without it")]
cw = (W - 2 * M - 0.45) / 4
for i, (h_, b_) in enumerate(cards4):
    card(s, M + i * (cw + 0.15), TOP + 3.45, cw, 1.3, h_, b_, size=12)
short(s, "every PD result is computed twice, with 2020–24 and with 2020–23, so the odd 2024 season cannot decide it.")
notes(s, "VIIRS fire counts are kept as a backup measure only, because they collapse after 2021.")

# =====================================================================================
# 27. Trust
# =====================================================================================
s = S("Tehsil measure", "Can we trust it? It ranks tehsils like independent sources do")
image(s, FIG / "fig_H_burn_vs_viirs.png", M, TOP + 0.05, 5.6, 4.0, align="left")
caption(s, M, TOP + 4.1, 5.6, "Our burnt share vs VIIRS fires per 1,000 ha rice, 2021")
stat(s, 6.6, TOP + 0.05, 3.0, "ρ 0.78–0.87", "same order as VIIRS\nfire counts, 2019–23", big_size=28)
stat(s, 9.75, TOP + 0.05, 3.0, "ρ 0.82–0.91", "same order as the\nnext season", big_size=28)
stat(s, 6.6, TOP + 1.75, 3.0, "ρ 0.87", "district order vs official\nCREAMS 2022", big_size=28)
stat(s, 9.75, TOP + 1.75, 3.0, "ρ 0.84–0.98", "same order at cut-off\n0.79 and 0.5", big_size=28)
text(s, 6.6, TOP + 3.5, 6.1, 1.2, "ρ = rank correlation: 1 means the same order. The old season index agreed with "
     "VIIRS at only 0.10–0.27.", size=13, color=MUTED, margin=0)
short(s, "DPPD needs a correct order of tehsils, and on order the measure agrees with every check we have.")
notes(s, "VIIRS is biased by fire timing, so agreement is reassurance, not proof. Weak spots: 2020 district order 0.50; "
         "2024 agreement drops to 0.51.")

# =====================================================================================
# 28. PD definition
# =====================================================================================
s = S("PDs", "A positive deviant lies beyond its own group's fence")
image(s, FF / "v3_fence.png", M, TOP + 0.05, W - 2 * M, 2.9)
steps_col(s, M, TOP + 3.1, 6.0, [
    ("Middle half:", "the box holds the middle 50% of the group (Q1 to Q3); its width is the IQR."),
    ("Fence", "= Q1 − 1.5 × IQR, the handbook's standard outlier rule.")], size=13, h=0.75, gap=0.05)
steps_col(s, 6.8, TOP + 3.1, 5.93, [
    ("Log scale:", "halving burning counts the same at any level; without it the fence falls below zero."),
    ("Within group only:", "Abohar is compared with the 17 other south-west tehsils.")], size=13, h=0.75, gap=0.05,
          start=3)
short(s, "a PD is not just low: it is further below its peers than normal variation can explain.")
notes(s, "Log(value + c), c = 10% of the group median. An earlier 'bottom 10%' rule always flags someone; the fence "
         "flags only clear outliers.")

# =====================================================================================
# 29. Static / temporal / robust
# =====================================================================================
s = S("PDs", "Two kinds of positive deviance, and a robustness rule")
card(s, M, TOP + 0.1, 3.9, 2.6, "Static PD · burns least", [
    "5-season average beyond the fence",
    "and in the group's lowest quarter in 4 of 5 seasons (one lucky year is not enough)"], size=16,
     head_color=GOOD)
card(s, M + 4.12, TOP + 0.1, 3.9, 2.6, "Temporal PD · cut fastest", [
    "trend 2020–24 (Theil–Sen, resists one odd year)",
    "minus the group's median trend, beyond the same kind of fence"], size=16, head_color=GOOD)
card(s, M + 8.24, TOP + 0.1, 3.89, 2.6, "Robust · holds twice", [
    "flagged in both 2020–24 and 2020–23",
    "strict = beyond the fence in both runs",
    "negative deviants (NDs) = the mirror image"], size=16, head_color=EMBER)
panel(s, M, TOP + 2.95, W - 2 * M, 1.8, color=PANEL)
text(s, M + 0.25, TOP + 2.95, W - 2 * M - 0.5, 1.8, [
    [("Why temporal? ", {"bold": True, "color": EMBER}),
     ("A tehsil compared with its own past cancels fixed differences we could not measure (farm size, local "
      "enforcement). Suggested by Basma Albanna.", {})],
    [("No regression: ", {"bold": True, "color": EMBER}),
     ("every rule is a direct comparison inside the group (supervisor's constraint).", {})]],
     size=14, anchor=MSO_ANCHOR.MIDDLE, margin=0)
short(s, "the strongest PD is low on both: it burns least and is also cutting fastest.")
notes(s, "Code: Code/pd/pd_identify.py and pd_robust.py; outputs/pd/robust/robust_deviants.csv.")

# =====================================================================================
# 30. PD result
# =====================================================================================
s = S("PDs", "Result: Abohar, and a low-burning Doaba belt")
image(s, FIG / "fig_I_pd_fences.png", M, TOP + 0.05, 7.4, 3.7, align="left")
caption(s, M, TOP + 3.8, 7.4, "Each dot = a tehsil, mean burnt share 2020–24 (log scale)")
image(s, FF / "f03_pd_map.png", 8.2, TOP + 0.05, 4.53, 3.4, align="right")
bullets(s, 8.2, TOP + 3.55, 4.53, 1.2, [
    ("Abohar: ", "the only strict PD (0.34 vs median 0.73)."),
    ("Doaba: ", "6 tehsils at half the Central median."),
], size=13, gap=4)
short(s, "the Doaba tehsils sit together, so the fence sees them as a low-burning region, not lone outliers.")
notes(s, "Fences: Central 0.225 (median 0.61), South-west 0.454 (median 0.73). Six of eight static PDs were also "
         "flagged by VIIRS fire counts, so the list does not hang on one sensor.")

# =====================================================================================
# 31. Candidate list
# =====================================================================================
s = S("PDs", "The candidate list going into validation")
rows = [["Tehsil", "Group", "Kind", "Burnt share 2020–24", "Trend vs group (%/yr)"],
        [("Abohar", GOOD), "South-west", "static + temporal", "0.34 (median 0.73)", "−11.1"],
        ["Dinanagar", "Central", "static", "0.21 (median 0.61)", "+6.5"],
        ["Gurdaspur · Phagwara · Adampur", "Central", "static", "0.29–0.30", "+2.3 · +6.0 · −4.9"],
        ["Jalandhar-I · Banga", "Central", "static", "0.31–0.34", "−1.4 · +5.6"],
        ["Talwandi Sabo", "South-west", "static", "0.50", "+14.5"],
        ["Samana · Dirba", "Central", "temporal", "0.63 · 0.71", "−9.1 · −8.2"],
        [("NDs: Lehra · Zira · Moonak · Guruharsahai", BAD), "C / SW", "static", "0.79–0.90", ""]]
table(s, M, TOP + 0.1, W - 2 * M, rows, [4.3, 1.6, 2.0, 2.4, 1.83], size=14, row_h=0.52)
short(s, "low burners and fast reducers are mostly different tehsils; only Abohar is both.")
notes(s, "Dinanagar burns least of all but its burning is rising; Talwandi Sabo's is rising fastest.")

# =====================================================================================
# 32. Validation design
# =====================================================================================
s = S("Validation", "Validation: six checks, rules fixed before looking")
rows = [["Check", "Question it answers", "Pass rule"],
        ["V1 Resampling", "Is the flag luck of which 100 points were drawn?", "kept in ≥ 80% of 1,000 redraws"],
        ["V2 Settings", "Does it depend on our choices (cut-off, offset, grouping)?", "kept in all scenarios but one"],
        ["V3 Clear looks", "Did clouds hide the fires?", "unknown share ≤ 2× group median"],
        ["V4 Rice", "Does it just grow less paddy?", "warning if below group Q1"],
        ["V4b Real paddy", "Do non-paddy points pull the score down?", "flag must survive on harvest-confirmed points"],
        ["V5 Timing", "Is harvest so late that fires fall outside the window?", "warning if ≥ 10 days later"]]
table(s, M, TOP + 0.1, W - 2 * M, rows, [2.3, 5.9, 3.93], size=14, row_h=0.52)
text(s, M, TOP + 3.95, W - 2 * M, 0.6, [[("Final label: ", {"bold": True, "color": EMBER}),
     ("any fail → dropped · at most one warning → validated PD · more → PD with caveat", {})]], size=15, margin=0)
short(s, "the handbook asks us to check a PD is a real signal before anyone visits it; with no fieldwork, we check in the data.")
notes(s, "V6 triangulation (VIIRS, CREAMS) is information only. A blind visual check (V7) was built but not labelled; "
         "stated as a limitation.")

# =====================================================================================
# 33. Validation result
# =====================================================================================
s = S("Validation", "Result: low burners hold up, fast reducers do not (except Abohar)")
image(s, FF / "f11_validation_grid.png", M, TOP + 0.05, 7.6, 4.0, align="left")
bullets(s, 8.45, TOP + 0.1, 4.28, 4.6, [
    ("Validated PDs: ", "Abohar, Dinanagar, Phagwara, Jalandhar-I, Adampur, Talwandi Sabo."),
    ("With caveat: ", "Gurdaspur, Banga."),
    ("Dropped: ", "Samana, Dirba (kept in only 4 of 10 resamples)."),
    ("Lesson: ", "a 5-season trend from 100 points is too noisy to name a deviant on its own."),
], size=14, gap=8)
short(s, "six validated PDs and two with a caveat go forward to Stage 3; the four heavy burners are the contrast.")
notes(s, "All three temporal NDs fail V1 the same way (Batala 0.14, Majitha 0.23, Malout 0.30).")

# =====================================================================================
# 34. Rice warning
# =====================================================================================
s = S("Validation", "The main warning is rice, but PDs burn little on real paddy too")
image(s, FF / "f12_burn_vs_rice.png", M, TOP + 0.05, 6.9, 4.25, align="left")
bullets(s, 7.8, TOP + 0.1, 4.93, 4.6, [
    ("Inside a group, ", "more rice still means more burning (ρ 0.70 Central, 0.63 South-west)."),
    ("Most PDs ", "have less rice than three-quarters of their group (V4 warning)."),
    ("So we re-scored ", "using only points where a paddy harvest was seen (V4b):"),
    ("Abohar ", "0.45 vs group 0.73; Dinanagar 0.25 vs 0.62. Still far below."),
], size=14, gap=8)
short(s, "the PDs are not just places with less paddy: on fields that really grew paddy, they still burn far less.")
notes(s, "Abohar's rice map needed a 0.58 scaling and a paddy harvest is seen at only 82% of its points (group 98%). "
         "Cotton fields that pass the harvest test cannot be ruled out without a visual check.")

# =====================================================================================
# 35. Drivers method
# =====================================================================================
s = S("Why", "Why do they burn less? Nine public drivers, tested three ways")
rows = [["Driver", "Public data", "Level"],
        ["Harvest-to-sowing days", "Sentinel-2 greenness (checked vs CIMMYT survey)", "Tehsil"],
        ["Early second crop", "points green again by 30 Nov (potato, vegetables)", "Tehsil"],
        ["Farm labour; small farms", "Census 2011", "Tehsil"],
        ["Straw buyers", "14 biomass / biogas plants, from news", "Town"],
        ["Distance to state border", "district boundaries", "Tehsil"],
        ["Urban surroundings", "JRC settlement map 2020", "Tehsil"],
        ["Basmati share", "APEDA survey 2023", "District"],
        ["Livestock", "Livestock Census 2019", "Tehsil"],
        [("CRM machines", BAD), ("no district data online → dropped", BAD), "—"]]
table(s, M, TOP + 0.05, 7.3, rows, [2.5, 3.8, 1.0], size=12, row_h=0.46)
steps_col(s, 8.2, TOP + 0.1, 4.53, [
    ("Profiles:", "are PDs above or below their group's median, and NDs on the other side?"),
    ("Rank correlation", "with burning, inside each group."),
    ("Rice held constant:", "remove rice share's effect first, then correlate.")], size=13, h=1.0, gap=0.1)
text(s, 8.2, TOP + 3.5, 4.53, 1.0, "A driver counts only if all three agree.", size=14, bold=True, color=EMBER,
     margin=0)
short(s, "with 8 PDs and 4 NDs this is a search for leads, not proof of cause.")
notes(s, "Online data only, no fieldwork (academic scope; the handbook allows a desk study when fieldwork is not "
         "possible). Drivers are things that could change; grouping variables are never reused as drivers.")

# =====================================================================================
# 36. Doaba
# =====================================================================================
s = S("Why", "Doaba burns little as a region, not because it is near towns")
image(s, FF / "f14_doaba_far_fields.png", M, TOP + 0.05, 7.4, 4.1, align="left")
caption(s, M, TOP + 4.2, 7.4, "Burnt share: all fields vs only fields more than 5 km from any town")
bullets(s, 8.4, TOP + 0.1, 4.33, 4.6, [
    ("Only urban share holds: ", "7 of 8 PDs above their group median, all 4 NDs below."),
    ("But far from towns ", "the Doaba PDs burn just as little."),
    ("So it is a regional trait: ", "potato and vegetable rotations, off-farm and overseas income."),
], size=14, gap=10)
short(s, "the lesson is inside Doaba farming itself; only fieldwork can say which practice it is.")
notes(s, "Central rho -0.61, still -0.30 with rice held constant. Fields within 2 km of a town burn 6–8 points less, "
         "but only 4% of fields are that close.")

# =====================================================================================
# 37. Abohar
# =====================================================================================
s = S("Why", "Abohar: straw buyer, labourers, livestock, early second crop")
image(s, FF / "f15_abohar_profile.png", M, TOP + 0.05, 7.6, 4.1, align="left")
caption(s, M, TOP + 4.2, 7.6, "Abohar's percentile within the South-west group")
bullets(s, 8.6, TOP + 0.1, 4.13, 4.6, [
    ("A biomass power plant ", "inside the tehsil: an assured straw buyer."),
    ("Most farm labourers per cultivator ", "in Punjab."),
    ("Most cattle per cultivator ", "in its group: straw is fodder."),
    ("Earliest second crop ", "in its group."),
], size=14, gap=8)
short(s, "one tehsil cannot separate these four levers; they are leads to test, not findings.")
notes(s, "Also a basmati-heavy district (Fazilka, 57% of rice) and 13 km from the Rajasthan border.")

# =====================================================================================
# 38. What did not hold
# =====================================================================================
s = S("Why", "What looked like a driver, but was really rice share")
image(s, FF / "f13_drivers.png", M, TOP + 0.05, 7.6, 4.0, align="left")
bullets(s, 8.6, TOP + 0.1, 4.13, 4.6, [
    ("Turnaround days, small farms: ", "linked to burning, but the link vanishes once rice share is held constant."),
    ("State border: ", "south-west tehsils near the border burn less (cotton belt), the opposite of past studies."),
    ("No pattern: ", "straw buyers within 30 km, livestock, basmati share."),
], size=14, gap=10)
short(s, "a programme that targets 'small farms' or 'short turnaround' without allowing for rice share would miss.")
notes(s, "44 correlation tests in total, so about 2 would pass p < 0.05 by chance; we only trust patterns that repeat.")

# =====================================================================================
# 39. What to do
# =====================================================================================
s = S("Impact", "Who to learn from, and what to do with it")
rows = [["Role", "Tehsils"],
        [("Positive deviants", GOOD), "Abohar (strict); Dinanagar, Phagwara, Jalandhar-I, Adampur, Talwandi Sabo"],
        [("With caveat", MUTED), "Gurdaspur, Banga"],
        [("Heavy burners (contrast)", BAD), "Lehra, Zira, Moonak, Guruharsahai"]]
table(s, M, TOP + 0.05, W - 2 * M, rows, [3.0, 9.13], size=14, row_h=0.45)
acts = [("Where to look", "Abohar and the Doaba tehsils first, with the heavy burners as comparison."),
        ("What to test", "Abohar's levers in other south-west tehsils: straw buyer, harvest labour, fodder link."),
        ("How to target", "Rank tehsils within peer groups and allow for rice share."),
        ("How to monitor", "Rerun the free Sentinel-2 detector each December: farmers cannot dodge it by timing fires.")]
cw = (W - 2 * M - 0.25) / 2
for i, (h_, b_) in enumerate(acts):
    x = M + (i % 2) * (cw + 0.25)
    y = TOP + 2.0 + (i // 2) * 1.4
    card(s, x, y, cw, 1.28, h_, b_, head_color=GOOD, size=13)
short(s, "the PDs tell an NGO or government where to look first and which levers are worth a pilot.")
notes(s, "For the Doaba belt the fieldwork question is what farmers do with straw before an October potato or "
         "vegetable crop, and whether that works in wheat-only areas.")

# =====================================================================================
# 40. Theory of change
# =====================================================================================
s = S("Impact", "Impact assessment: theory of change")
flow_steps(s, TOP + 0.1, [("PD leads", "this study: where to look, candidate levers"),
                          ("Phase 1", "confirm in the field what PDs do differently"),
                          ("Phase 2", "pilot confirmed levers in matched villages"),
                          ("Measure", "satellite burnt share + farmer survey"),
                          ("Scale", "through the partner, if the effect holds")], h=1.45, size=13)
rows = [["Assumption that must hold", "Where it is tested"],
        ["PD practices are real, not a data artefact", "Phase 1: field visits to our satellite points"],
        ["Practices transfer (not tied to Doaba or Abohar's plant)", "Phase 1 interviews; Phase 2 pilot"],
        ["Farmers take up the lever when offered", "Phase 2 take-up"],
        ["Burning falls, not just moves in time or place", "Phase 2 satellite outcome, incl. neighbours"]]
table(s, M, TOP + 1.85, W - 2 * M, rows, [7.0, 5.13], size=14, row_h=0.5)
short(s, "DPPD gives leads; the impact plan turns them into a tested lever before anyone scales it.")
notes(s, "DPPD stops at candidate explanations. The handbook's next step is to check them and test transfer.")

# =====================================================================================
# 41. Phases + sample size
# =====================================================================================
s = S("Impact", "Two phases: confirm in the field, then a randomised pilot")
card(s, M, TOP + 0.05, 3.85, 3.55, "Phase 1 · one season", [
    "PD, ND and typical tehsils; ~6 villages each, chosen by satellite burning",
    "Farmer survey, focus groups, key informants",
    "Dated photos at our satellite points: new ground truth"], size=13)
card(s, M + 4.05, TOP + 0.05, 3.85, 3.55, "Phase 2 · pilot", [
    "Villages in non-PD tehsils of the same peer group",
    "Paired on past burning + rice share; one per pair gets the lever at random",
    "Outcome: satellite burnt share + survey with a list experiment"], size=13)
image(s, FF / "f16_sample_size.png", 8.7, TOP + 0.05, 4.03, 3.2)
caption(s, 8.7, TOP + 3.3, 4.03, "Villages per arm to detect a 10-point drop")
panel(s, M, TOP + 3.8, W - 2 * M, 0.95, color=PANEL)
text(s, M + 0.3, TOP + 3.8, W - 2 * M - 0.6, 0.95, [[("~30 villages per arm ", {"bold": True, "color": EMBER}),
     ("(35 pairs per lever) detect a 10-point drop with 30 satellite points per village; the pessimistic case (52) "
      "still fits the 1,633-village south-west frame.", {})]], size=14, anchor=MSO_ANCHOR.MIDDLE, margin=0)
short(s, "the same free satellite measure that found the PDs becomes the pilot's outcome measure.")
notes(s, "Sample size from our own tehsil data: ANCOVA on village baseline, 80% power, 5% two-sided. List experiment: "
         "burning is illegal, so farmers report only how many statements in a list are true.")

# =====================================================================================
# 42. Limits + takeaways
# =====================================================================================
s = S("Impact", "Limits, and three takeaways")
text(s, M, TOP + 0.05, 5.8, 0.4, "Limits", size=20, bold=True, color=BAD, margin=0)
bullets(s, M, TOP + 0.55, 5.8, 4.2, [
    "No fieldwork: no practice confirmed on the ground.",
    "Detector under-counts partial burns; ploughing tested on 2019 fields only; 2024 doubtful.",
    "8 PDs and 4 NDs; public data of mixed years; no district CRM machine data.",
    "South-west / Central border is soft (checked with the 2-group version).",
], size=15, gap=8)
text(s, 6.95, TOP + 0.05, 5.78, 0.4, "Takeaways", size=20, bold=True, color=GOOD, margin=0)
bullets(s, 6.95, TOP + 0.55, 5.78, 4.2, [
    ("Compare like with like ", "and allow for rice share, or low paddy looks like good behaviour."),
    ("Burning can be told from ploughing ", "with free Sentinel-2, if you look at the sudden change."),
    ("Abohar and the Doaba belt ", "are where to look; their levers are leads for a pilot."),
], size=15, gap=10)
short(s, "thank you. Every number in this talk is reproducible from code in the repository.")

# =====================================================================================
# Backup
# =====================================================================================


def backup(t):
    s = prs.slides.add_slide(BLANK)
    background(s, WHITE)
    tag(s, "Backup")
    title(s, t)
    PAGES.append((s, False))
    return s


s = backup("B1 · Data sources")
rows = [["Variable", "Source", "Level", "Year(s)", "Use"],
        ["Boundaries", "SHRUG v2.2 villages; LGD tehsils; own crosswalk", "Village / tehsil", "2011, 2024", "Base"],
        ["Rice area", "Chen et al. 10 m map, calibrated to Statistical Abstract", "Pixel → tehsil", "2022", "Grouping"],
        ["Rainfall", "CHIRPS daily (Earth Engine)", "~5 km", "2020–25", "Grouping"],
        ["Agro-ecological zones", "NBSS&LUP AESR 2018", "Polygon", "2018", "Grouping"],
        ["Groundwater", "CGWB Ground Water Resources of Punjab", "Block", "2022", "Grouping"],
        ["Soil", "NBSS&LUP 1:250K soil map", "Map unit", "static", "Grouping"],
        ["Burn imagery", "Sentinel-2 SR Harmonized", "10–20 m", "2019–24", "Measure"],
        ["Ground truth", "Walker et al.; CEEW fields; CIMMYT survey", "Field", "2019–22", "Measure"],
        ["Daily imagery", "PlanetScope (Education & Research)", "3 m", "Oct–Nov 2021", "Judge"],
        ["Drivers", "Census 2011, Livestock Census 2019, plant lists, JRC urban", "Tehsil / district", "mixed", "Stage 3"],
        ["Checks", "CREAMS (official), VIIRS / FIRMS fire counts", "District / 375 m", "2019–25", "Validation"]]
table(s, M, TOP, W - 2 * M, rows, [2.3, 5.2, 1.9, 1.5, 1.23], size=13, row_h=0.44)

s = backup("B2 · Detector cut-off 0.79 vs 0.5")
stat(s, M, TOP + 0.3, 4, "0.84–0.98", "tehsil rank agreement between\nthe two cut-offs, by year", big_size=44)
bullets(s, 5.2, TOP + 0.3, 7.5, 4.5, [
    ("The cut-off changes the level, not the order: ", "at 0.5 every tehsil burns more but keeps its rank."),
    ("PDs depend on order within a group, ", "and survive the 0.5 rerun (validation V2)."),
    ("Walker trade-off: ", "0.79 → 90% burns caught, 18% ploughed called burnt; 0.5 → 97.5% and 51%."),
], size=16, gap=10)

s = backup("B3 · Drivers vs burning within groups")
rows = [["Driver", "Central ρ (partial)", "South-west ρ (partial)", "PDs / NDs on expected side"],
        ["Urban area share", "−0.61** (−0.30*)", "+0.45 (+0.52*)", "7/8, 4/4"],
        ["Turnaround (days)", "−0.38** (−0.20)", "+0.40 (+0.04)", "4/8, 2/4"],
        ["Cultivators per 100 ha rice", "−0.28* (−0.19)", "−0.49* (−0.05)", "5/8, 2/4"],
        ["Early second crop share", "−0.16 (+0.05)", "−0.56* (−0.47)", "5/8, 2/4"],
        ["km to inter-state border", "+0.11 (+0.07)", "+0.83** (+0.75**)", "0/8, 2/4"],
        ["km to nearest straw buyer", "−0.20 (−0.26*)", "0.00 (+0.17)", "5/8, 3/4"],
        ["Straw buyers within 30 km", "+0.06 (+0.16)", "+0.27 (+0.04)", "1/8, 2/4"],
        ["Labourers per cultivator", "+0.08 (+0.18)", "+0.16 (+0.21)", "4/8, 1/4"],
        ["Basmati share (district)", "+0.01 (−0.05)", "+0.14 (+0.01)", "4/8, 1/4"],
        ["Cattle + buffalo per cultivator", "−0.18 (−0.02)", "−0.19 (+0.06)", "4/8, 3/4"]]
table(s, M, TOP, W - 2 * M, rows, [3.6, 2.8, 2.9, 2.83], size=13, row_h=0.46)
caption(s, M, 6.65, W - 2 * M, "Spearman with 2020–24 mean burnt share; partial = rice share held constant; "
        "* p < 0.05, ** p < 0.01")

s = backup("B4 · Survey modules and logframe")
rows = [["#", "Survey module", "#", "Survey module"],
        ["1", "Household and farm", "6", "Labour and livestock"],
        ["2", "Paddy season (variety, harvest, combine)", "7", "Next crop and timing"],
        ["3", "Residue handling per plot", "8", "Norms and enforcement"],
        ["4", "Machines (own / hire, cost, waiting)", "9", "Barriers and preferences"],
        ["5", "Straw market (buyer, price, distance)", "10", "List experiment (burning)"]]
table(s, M, TOP, W - 2 * M, rows, [0.6, 5.47, 0.6, 5.46], size=14, row_h=0.5)
bullets(s, M, TOP + 3.3, W - 2 * M, 2.2, [
    ("Impact: ", "less burning in south-west villages (satellite burnt share, peer-group adjusted)."),
    ("Outcome: ", "farmers manage straw without burning (list experiment; straw sold / fed)."),
    ("Outputs: ", "lever delivered on time (villages served, tonnes collected, labour days)."),
], size=15, gap=6)

# page numbers, now that the total is known
TOTAL = len(PAGES)
for i, (sl, dk) in enumerate(PAGES, start=1):
    if i > 1:
        foot(sl, i, dk)

prs.save(OUT)
print(f"Saved {OUT} ({len(prs.slides)} slides)")
