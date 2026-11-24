"""
Final presentation deck, version 2 (2026-11-25, 15 min): 25 main slides + 6 backup.

Content follows report/final_deck_outline_version2.md: problem -> midterm (17 Sep) -> six pieces of work
since -> how each works -> PDs, why, what to do -> impact assessment.
Helpers and style are copied from make_final_deck.py. New figure f20 from make_v2_figures.py.

Run:  python Code/figures/make_v2_figures.py
      python Code/figures/make_final_deck_v2.py
Out:  report/final_deck_v2.pptx
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
OUT = ROOT / "report" / "final_deck_v2.pptx"

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


# ---------- 1. Title ----------
n += 1
s = new(dark=True)
image(s, RAWF / "s2_lehra.png", 7.6, 0.75, 5.73, 5.73, align="right")
shade = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(7.6), Inches(H))
fill(shade, DARK)
dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(M), Inches(1.55), Inches(0.22), Inches(0.22))
fill(dot, EMBER)
text(s, M + 0.35, 1.45, 6.5, 0.45, "COL7761 ICTD · FINAL PRESENTATION", size=13, color=ON_DARK_MUTED,
     bold=True, margin=0)
text(s, M, 2.1, 6.6, 2.4, "Finding Positive Deviants in Crop Residue Burning", size=44, font=HEAD,
     bold=True, color=WHITE, margin=0)
text(s, M, 4.35, 6.6, 0.9, "A Data-Powered Positive Deviance study of Punjab's 97 tehsils", size=20,
     color=ON_DARK_MUTED, margin=0)
text(s, M, 5.55, 6.6, 1.2, [[("Soham Malvadkar", {"bold": True, "color": WHITE})],
                            "Supervisor: Prof. Aaditeshwar Seth",
                            "Advisors: Basma Albanna, Andreas Pawelke"], size=15, color=ON_DARK_MUTED, margin=0)
text(s, 7.75, H - 0.45, 5.4, 0.3, "Sentinel-2, Lehra tehsil, 26 Oct 2022: harvested and burnt fields",
     size=10, color=ON_DARK_MUTED, italic=True, margin=0)
notes(s, "Plan: the problem, where we were at the midterm, what we did since, how each piece works, "
         "who the positive deviants are and why, and how we would test it in the field.")

# ---------- 2. Problem ----------
s = S("The problem", "Punjab burns over half its paddy straw every autumn")
image(s, FIG / "fig_G_burn_map.png", M, TOP + 0.1, 5.4, 5.3, align="left")
caption(s, M, 6.95, 5.4, "Our measure: share of sample rice points burnt, mean 2020–24, by tehsil")
stat(s, 6.6, TOP + 0.1, 3.0, "52–64%", "of paddy area burnt each\nseason, 2019–23", big_size=40)
stat(s, 9.75, TOP + 0.1, 3.0, "14–22 days", "median gap from paddy\nharvest to wheat sowing", big_size=40)
bullets(s, 6.6, TOP + 1.95, 6.1, 1.9, [
    ("Why burn: ", "the straw must go before wheat is sown; fire is the cheapest way."),
    ("Same window: ", "farmers who do not burn plough the straw in, in the same weeks."),
    ("Uneven: ", "places that look alike burn very differently. Some may already have an answer."),
], size=15, gap=6)
image(s, FF / "f01_season_field.png", 6.6, TOP + 3.95, 6.1, 1.5)
caption(s, 6.6, 6.95, 6.1, "One Sentinel-2 point through the 2022 season: paddy → harvest → wheat")
notes(s, "Despite CRM machine subsidies since 2018, custom hiring centres and short-duration varieties, "
         "burning stays high. Turnaround checked against the CIMMYT farmer survey.")

# ---------- 3. Fire counts + question ----------
s = S("The problem", "Fire counts fail; so who burns less than its peers?")
image(s, FF / "f02_viirs_collapse.png", M, TOP + 0.05, 7.2, 2.55, align="left")
caption(s, M, TOP + 2.62, 7.2, "VIIRS active fires over our 97 tehsils vs our Sentinel-2 measure")
stat(s, 8.2, TOP + 0.05, 4.5, "−91%", "VIIRS fires 2021 → 2024: farmers burn after\nthe satellite's afternoon pass",
     color=BAD, big_size=40)
text(s, 8.2, TOP + 1.75, 4.5, 1.3, [[("Question: ", {"bold": True, "color": EMBER}),
     ("which of Punjab's 97 tehsils burn much less paddy straw than structurally similar peers, and why?", {})]],
     size=15, margin=0)
flow_steps(s, 4.9, [("1 · Fit", "Is DPPD right for this problem?"),
                    ("2 · Peer groups", "Group tehsils by conditions they cannot change"),
                    ("3 · Measure", "Burnt share per tehsil from satellites"),
                    ("4 · Find + validate", "Who lies beyond its group's spread?"),
                    ("5 · Why", "What do the deviants have in common?")], h=1.5, size=13)
text(s, M, 4.5, W - 2 * M, 0.35, "Data-Powered Positive Deviance (DPPD) pipeline", size=13, bold=True,
     color=MUTED, margin=0)
notes(s, "Fire counts also missed about 3 of 4 burns that Sentinel-2 sees, even before the collapse.")

# ---------- 4. Midterm: burn proxy ----------
s = S("Midterm · 17 Sep", "At the midterm: a burn index chosen on 380 ground fields")
rows = [["Metric (5-fold CV, 380 fields)", "NBR", "BAIS2 + TCB"],
        ["Accuracy", "81.3%", ("95.5%", GOOD)],
        ["Precision (burnt)", "90.1%", ("95.6%", GOOD)],
        ["Recall (burnt)", "82.3%", ("98.1%", GOOD)],
        ["F1", "0.860", ("0.968", GOOD)],
        ["Missed burns", ("47", BAD), ("5", GOOD)]]
table(s, M, TOP + 0.2, 7.0, rows, [3.6, 1.6, 1.8], size=15, row_h=0.55)
caption(s, M, TOP + 3.6, 7.0, "Ground truth: 438 hand-labelled field polygons (Hoshiarpur/Jalandhar 2021, Sangrur 2020)")
card(s, 8.1, TOP + 0.2, 4.63, 1.7, "BAIS2", "red-edge burn index for Sentinel-2", size=14)
card(s, 8.1, TOP + 2.05, 4.63, 1.7, "TCB", "Tasseled Cap brightness: charred fields go dark", size=14)
text(s, 8.1, TOP + 3.95, 4.63, 1.5, "Open at the midterm: this was a single look after harvest. It had not been "
     "tested on ploughed fields.", size=14, color=MUTED, italic=True, margin=0)
notes(s, "Logistic regression on BAIS2 + TCB, stratified 5-fold cross-validation. This is the starting point "
         "for the detector work after the midterm.")

# ---------- 5. Midterm: grouping design ----------
s = S("Midterm · 17 Sep", "At the midterm: the grouping was designed, not yet run")
rows = [["Midterm design", "What we finally used"],
        ["Rice area (Chen et al. 10 m)", "Rice share of tehsil, calibrated to official totals"],
        ["Cropping intensity", ("Dropped: satellite estimate did not match official (ρ 0.18)", MUTED)],
        ["Agro-climatic zone (NARP, district)", "AESR zones (polygons) + monsoon rainfall"],
        ["Groundwater (block)", "Groundwater extraction 2022"],
        ["Soil type (NBSS&LUP)", "Soil, 8 descriptors"]]
table(s, M, TOP + 0.2, 7.6, rows, [3.4, 4.2], size=14, row_h=0.56)
card(s, 8.7, TOP + 0.2, 4.03, 1.6, "Kept out on purpose", "CRM machines, mandi access: possible drivers, kept "
     "for Stage 3", size=14)
card(s, 8.7, TOP + 1.95, 4.03, 1.6, "Unit", "tehsil: finer than district, steadier than village. "
     "Punjab: 97 tehsils", size=14)
card(s, 8.7, TOP + 3.7, 4.03, 1.6, "Boundary bridge", "2011 Census villages → current tehsils, so old and new "
     "data line up", size=14)
notes(s, "Rule from the DPPD handbook: groups use only conditions a tehsil cannot change, never burning itself.")

# ---------- 6. Since the midterm ----------
s = S("Since the midterm", "Since the midterm: six pieces of work")
items = [("1", "Peer groups", "built and frozen: 3 regions"),
         ("2", "Burn detector", "now separates burning from ploughing"),
         ("3", "Tehsil measure", "100 points per tehsil, 2019–24, checked"),
         ("4", "Positive deviants", "found within each group"),
         ("5", "Validation", "six checks, fixed in advance"),
         ("6", "Why, and what to do", "drivers, actions, pilot design")]
for i, (k, h_, b_) in enumerate(items):
    y = TOP + 0.05 + i * 0.9
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(M), Inches(y + 0.12), Inches(0.55), Inches(0.55))
    fill(c, EMBER)
    text(s, M, y + 0.12, 0.55, 0.55, k, size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, margin=0)
    text(s, M + 0.75, y + 0.05, 5.6, 0.4, h_, size=19, bold=True, margin=0)
    text(s, M + 0.75, y + 0.45, 5.6, 0.4, b_, size=14, color=MUTED, margin=0)
image(s, FF / "f03_pd_map.png", 6.7, TOP - 0.05, 6.03, 5.6, align="right")
caption(s, 6.7, 7.0, 6.03, "Result first: Abohar and a Doaba belt burn far less than their peers")
notes(s, "The rest of the talk takes these six in order: how each works, what it found.")

# ---------- 7. Gower ----------
s = S("1 · Peer groups", "Step 1: how alike are two tehsils? (dimension-balanced Gower)")
gx = json.loads((FF / "f18_gower_example.json").read_text())
pa, pb = gx["Phagwara|Adampur"], gx["Phagwara|Abohar"]
vv = gx["values"]
rows = [["Dimension", "Phagwara", "Adampur", "Abohar", "Phagwara–Adampur", "Phagwara–Abohar"],
        ["Rice share", f"{vv['Phagwara']['rice_share_2022_cal']:.0%}", f"{vv['Adampur']['rice_share_2022_cal']:.0%}",
         f"{vv['Abohar']['rice_share_2022_cal']:.0%}", f"{pa['rice']:.2f}", f"{pb['rice']:.2f}"],
        ["Monsoon rain", f"{vv['Phagwara']['mean_monsoon_rainfall_mm']:.0f} mm",
         f"{vv['Adampur']['mean_monsoon_rainfall_mm']:.0f} mm", f"{vv['Abohar']['mean_monsoon_rainfall_mm']:.0f} mm",
         f"{pa['rainfall']:.2f}", f"{pb['rainfall']:.2f}"],
        ["Agro-ecological zone", f"AESR {vv['Phagwara']['aesr_dominant']}", f"AESR {vv['Adampur']['aesr_dominant']}",
         f"AESR {vv['Abohar']['aesr_dominant']}", f"{pa['zone']:.2f}", f"{pb['zone']:.2f}"],
        ["Groundwater use", f"{vv['Phagwara']['mean_extraction_pct_2022']:.0f}%",
         f"{vv['Adampur']['mean_extraction_pct_2022']:.0f}%", f"{vv['Abohar']['mean_extraction_pct_2022']:.0f}%",
         f"{pa['groundwater']:.2f}", f"{pb['groundwater']:.2f}"],
        ["Soil (8 descriptors)", "", "", "", f"{pa['soil']:.2f}", f"{pb['soil']:.2f}"],
        [("Distance = mean of 5", EMBER), "", "", "", (f"{pa['distance']:.2f}", GOOD), (f"{pb['distance']:.2f}", BAD)]]
table(s, M, TOP + 0.1, 8.3, rows, [2.2, 1.15, 1.15, 1.15, 1.35, 1.3], size=13, row_h=0.5)
caption(s, M, TOP + 3.65, 8.3, "Real values from the grouping master; scores from Code/grouping/gower.py")
card(s, 9.2, TOP + 0.1, 3.53, 1.75, "Numbers", "difference ÷ range across tehsils → 0 to 1", size=14)
card(s, 9.2, TOP + 2.0, 3.53, 1.75, "Shares and categories", "zone shares compared like numbers; soil classes: "
     "same = 0, different = 1", size=14)
card(s, 9.2, TOP + 3.9, 3.53, 1.75, "Balanced", "average inside each dimension first, so soil's 8 columns get 1 vote, "
     "not 8", size=14)
text(s, M, TOP + 4.2, 8.3, 1.2, "Phagwara and Adampur differ mainly in soil, so they are close (0.24). Abohar differs "
     "on every dimension (0.51). Doing this for every pair gives a 97 × 97 distance table.", size=15, margin=0)
notes(s, "Why Gower: the variables mix numbers, shares and categories. Why balanced: plain Gower would let soil "
         "(8 columns) outvote rainfall (1). Each of the 5 dimensions gets weight 1/5.")

# ---------- 8. Merging ----------
s = S("1 · Peer groups", "Step 2: merge the closest tehsils, again and again")
image(s, FF / "f20_toy_merge.png", M, TOP + 0.05, 9.1, 3.75, align="left")
caption(s, M, TOP + 3.8, 9.1, "Six real tehsils, real Gower distances. Blue = Central group, orange = South-west.")
bullets(s, 9.9, TOP + 0.05, 2.83, 3.9, [
    ("Start: ", "every tehsil is its own group."),
    ("Merge: ", "join the two closest groups."),
    ("Group distance: ", "the average of all pairs across the two groups."),
    ("Repeat ", "until one tree remains; cut it into groups."),
], size=15, gap=8)
panel(s, M, 5.7, W - 2 * M, 1.2)
text(s, M + 0.25, 5.7, W - 2 * M - 0.5, 1.2, [
    [("Worked step 3: ", {"bold": True, "color": EMBER}),
     ("Adampur to {Phagwara, Jalandhar-I} = (0.24 + 0.29) / 2 = 0.27, the closest remaining pair, so they merge. "
      "Abohar and Fazilka (0.17) merged first; the two sides join last (0.43).", {})]],
    size=15, anchor=MSO_ANCHOR.MIDDLE, margin=0)
notes(s, "Why average linkage: works on any distance table, and does not force round or equal-sized groups "
         "(unlike k-means or Ward). The same procedure runs on all 97 tehsils.")

# ---------- 9. Cut + trust ----------
s = S("1 · Peer groups", "Step 3: where to cut the tree, and can we trust the groups?")
image(s, FIG / "fig_B_dendrogram.png", M, TOP + 0.05, 6.4, 2.6, align="left")
caption(s, M, TOP + 2.65, 6.4, "All 97 tehsils; dashed line = cut into 3 groups + 1 hill outlier")
stat(s, M, TOP + 3.1, 2.0, "0.377", "silhouette at k = 3", big_size=30)
stat(s, M + 2.15, TOP + 3.1, 2.1, "0.890", "bootstrap ARI\n(300 × 80% samples)", big_size=30)
stat(s, M + 4.4, TOP + 3.1, 2.1, "±15%", "weights changed: groups hold", big_size=30)
text(s, M, TOP + 4.6, 6.4, 0.9, "Silhouette: is each tehsil closer to its own group than to the next? "
     "Bootstrap: regroup random 80% samples; 1 = same groups every time.", size=13, color=MUTED, margin=0)
image(s, FIG / "fig_A_group_map.png", 7.2, TOP - 0.05, 5.53, 4.1)
rows = [["Group", "Tehsils", "Rice share", "Rain"],
        [("Central", GROUP["Central"]), "63", "75%", "721 mm"],
        [("South-west", GROUP["South-west"]), "18", "59%", "467 mm"],
        [("Foothills", GROUP["Foothills"]), "15", "28%", "981 mm"]]
table(s, 7.4, TOP + 4.1, 5.33, rows, [1.6, 1.1, 1.3, 1.33], size=13, row_h=0.36)
notes(s, "No location was given to the clustering, yet the groups are real belts: Central plains, dry Malwa "
         "south-west, Kandi foothills. Each tehsil is compared only with its own group. "
         "Weak point: the South-west / Central border, so PDs are also checked under a 2-group split.")

# ---------- 10. Burnt vs ploughed ----------
s = S("2 · Burn detector", "The midterm index called 81% of ploughed fields burnt")
image(s, FF / "f05_planet_burnt_vs_ploughed.png", M, TOP + 0.2, W - 2 * M, 4.3)
caption(s, M, TOP + 4.6, W - 2 * M, "PlanetScope 3 m daily images, Jalandhar 2021, CEEW fields (cyan outline). "
        "Top: goes black, then fades to soil colour. Bottom: ploughed, never black.")
text(s, M, 6.5, W - 2 * M, 0.6, [[("Why it matters: ", {"bold": True, "color": BAD}),
     ("a tehsil that ploughs straw in instead of burning would look like a burner, and its deviance would be hidden.",
      {})]], size=16, margin=0)
notes(s, "Walker et al. ground truth (2019): 98% of burns caught but 81% of ploughed-not-burnt fields flagged "
         "within 10 days.")

# ---------- 11. Tried & failed ----------
s = S("2 · Burn detector", "What we tried first, and why it did not work")
rows = [["Tried", "Idea", "Why it failed"],
        ["Tighter season window", "count only 15 Sep–30 Nov (official season)", "ploughing for wheat happens in the same weeks"],
        ["Heat (Landsat, MODIS)", "fresh ash should be hotter than soil", "ash is not hotter than ploughed soil; heat gives timing only"],
        ["Radar (Sentinel-1)", "ploughing roughens the soil, radar should see it", "recognised only 7% of ploughed fields and dropped 33% of real burns"]]
table(s, M, TOP + 0.3, W - 2 * M, rows, [2.9, 4.4, 4.83], size=15, row_h=0.75)
panel(s, M, 5.0, W - 2 * M, 1.5)
text(s, M + 0.3, 5.05, W - 2 * M - 0.6, 1.4, [
    [("Root cause: ", {"bold": True, "color": EMBER}),
     ("Sentinel-2 passes every 5 days, often after the ash has faded. Then char and fresh soil look the same "
      "(AUC 0.51). We needed something that sees the field every day.", {})]],
    size=16, anchor=MSO_ANCHOR.MIDDLE, margin=0)
notes(s, "Radar was the advisor's suggestion (Basma Albanna), tested on CEEW 2021 fields; kept as a documented "
         "negative result. MODIS heat peak is still used to time the burn window.")

# ---------- 12. Planet ----------
s = S("2 · Burn detector", "PlanetScope sees every day; Sentinel-2 saw this field on 2 of 10")
image(s, FF / "f06_planet_vs_s2.png", M, TOP + 0.05, W - 2 * M, 3.2)
caption(s, M, TOP + 3.3, W - 2 * M, "Same burnt field, every PlanetScope day 30 Oct – 9 Nov 2021. "
        "Orange frame = a clear Sentinel-2 pass that day.")
card(s, M, 5.05, 3.9, 1.75, "Sentinel-2", "free, 10 m, every 5 days. Covers all of Punjab, but misses the dark days.",
     size=14)
card(s, M + 4.12, 5.05, 3.9, 1.75, "PlanetScope", "daily, 3 m, limited quota. Separates ash from soil (AUC 0.96).",
     size=14)
card(s, M + 8.24, 5.05, 3.89, 1.75, "So", "Sentinel-2 does the work everywhere; Planet is the independent judge "
     "on a sample area.", head_color=GOOD, size=14)
notes(s, "Planet Education & Research quota: 3,000 km² per month, so it cannot cover the state. "
         "It is used to check the Sentinel-2 detector, not to replace it.")

# ---------- 13. Detector ----------
s = S("2 · Burn detector", "The detector: flag, find the sudden jump, let a forest judge")
image(s, FF / "f19_detector_series.png", M, TOP + 0.05, W - 2 * M, 3.6)
caption(s, M, TOP + 3.7, W - 2 * M, "Two real sample points in Lehra, 2022. Both cross the flag line; only the "
        "sudden jump is judged a burn.")
steps = [("1 · Flag", "score each clear look with BAIS2 + TCB; > 0 = possible burn"),
         ("2 · Candidate", "the largest jump in the score: burning darkens a field overnight"),
         ("3 · Before / after", "compare 14 bands and indices with the last clear look ≤ 20 days before"),
         ("4 · Decide", "random forest (500 trees) trained on 2,204 burnt + 223 ploughed fields; burnt if p ≥ 0.79")]
cw = (W - 2 * M - 3 * 0.15) / 4
for i, (h_, b_) in enumerate(steps):
    card(s, M + i * (cw + 0.15), 5.6, cw, 1.4, h_, b_, size=12)
notes(s, "Drying and harvest change a field gradually; a burn is sudden. The before/after comparison is what "
         "separates ash from ploughed soil. Cut-off 0.79 keeps 90% of burns; 0.5 is the sensitivity check.")

# ---------- 14. Detector result ----------
s = S("2 · Burn detector", "Ploughing false alarms fall from 81% to 18%")
image(s, FF / "f07_detector_bars.png", M, TOP + 0.1, 7.2, 4.7, align="left")
caption(s, M, TOP + 4.85, 7.2, "Walker et al. ground truth, 5-fold cross-validation")
stat(s, 8.2, TOP + 0.1, 4.5, "81% → 18%", "ploughed fields called burnt", color=GOOD, big_size=36)
stat(s, 8.2, TOP + 1.6, 4.5, "90%", "of real burns still caught", color=GOOD, big_size=36)
stat(s, 8.2, TOP + 3.1, 4.5, "23 → 0–3 of 32", "false alarms on a new district and year\n(Jalandhar 2021, judged by Planet)",
     color=GOOD, big_size=30)
notes(s, "Cost: partial burns are under-counted. Fine for DPPD if the miss rate is similar across tehsils "
         "(stated assumption).")

# ---------- 15. Tehsil measure ----------
s = S("3 · Tehsil measure", "From fields to tehsils: 100 fixed rice points per tehsil")
image(s, FF / "f08_points_two_tehsils.png", M, TOP + 0.05, 7.8, 5.4, align="left")
mp = meta("tehsil_phagwara.json")
caption(s, M, 6.95, 7.8, f"Sentinel-2 true colour, cloud-free {mp['date']}, with each point's 2022 verdict")
bullets(s, 8.7, TOP + 0.1, 4.03, 3.0, [
    ("100 rice pixels ", "per tehsil, the same points every season."),
    ("Each point ", "run through the detector, 15 Sep–30 Nov, 2019–24."),
    ("Tehsil value ", "= share of its points burnt."),
], size=15, gap=8)
card(s, 8.7, TOP + 3.15, 4.03, 2.4, "Decisions along the way", [
    "VIIRS fire counts: backup only (collapse 2024–25)",
    "Foothills: measured, not ranked (weakest check)",
    "2024: flagged (most burns seen late)"], size=13)
notes(s, "Points are pixels that are rice in both the 2020 and 2022 maps. Same panel every season, so year-to-year "
         "change is not sampling noise. ≥ 97% of points get a verdict each season.")

# ---------- 16. Tehsil result ----------
s = S("3 · Tehsil measure", "The tehsil measure matches fire counts and is stable")
image(s, FIG / "fig_H_burn_vs_viirs.png", M, TOP + 0.05, 5.2, 3.7, align="left")
caption(s, M, TOP + 3.8, 5.2, "Our burnt share vs VIIRS fires per 1,000 ha rice, 2021")
stat(s, 6.3, TOP + 0.05, 3.0, "ρ 0.78–0.87", "rank agreement with VIIRS,\n2019–23", big_size=28)
stat(s, 9.6, TOP + 0.05, 3.1, "ρ 0.82–0.91", "same ranks year after year", big_size=28)
image(s, FF / "f09_yearly_maps.png", 6.2, TOP + 1.7, 6.5, 2.3)
caption(s, 6.2, TOP + 4.0, 6.5, "Burnt share by tehsil, 2020–24: the same places stay low or high")
text(s, M, 6.3, W - 2 * M, 0.6, "Official CREAMS 2022: district ρ 0.87. Every result is also checked on 2020–23.",
     size=14, color=MUTED, margin=0)
notes(s, "Agreement with VIIRS is reassuring but not proof, since farmers time fires to dodge the overpass.")

# ---------- 17. PD rule ----------
s = S("4 · Positive deviants", "A positive deviant lies beyond its own group's fence")
image(s, FIG / "fig_I_pd_fences.png", M, TOP + 0.05, 6.2, 3.7, align="left")
caption(s, M, TOP + 3.8, 6.2, "Each dot = a tehsil, mean burnt share 2020–24 (log scale)")
image(s, FF / "f10_abohar_vs_group.png", 7.0, TOP + 0.05, 5.73, 3.7, align="right")
caption(s, 7.0, TOP + 3.8, 5.73, "Abohar 0.34 vs South-west median 0.73, every season")
steps = [("Log scale", "log(share + c): halving counts the same at any level"),
         ("Static PD", "5-season mean below Q1 − 1.5 × IQR of its group"),
         ("Temporal PD", "Theil–Sen trend vs group's median trend, same fence"),
         ("Robust", "flagged in both 2020–24 and 2020–23")]
cw = (W - 2 * M - 3 * 0.15) / 4
for i, (h_, b_) in enumerate(steps):
    card(s, M + i * (cw + 0.15), 5.75, cw, 1.3, h_, b_, size=12)
notes(s, "c = 10% of the group median. An earlier bottom-10% rule was too loose: it always flags someone. "
         "The IQR fence flags only clear outliers. Abohar is the only strict PD on level and trend.")

# ---------- 18. Validation ----------
s = S("5 · Validation", "Six checks: low burners survive, fast reducers do not")
rows = [["Check", "Question"],
        ["V1 Resampling", "luck of the 100 points?"],
        ["V2 Settings", "depends on our choices?"],
        ["V3 Clear looks", "do clouds hide fires?"],
        ["V4 Rice map", "just less paddy?"],
        ["V4b Real paddy", "non-paddy points pulling it down?"],
        ["V5 Timing", "harvest after the window?"]]
table(s, M, TOP + 0.05, 5.0, rows, [1.9, 3.1], size=13, row_h=0.5)
text(s, M, TOP + 3.7, 5.0, 1.8, [[("Rule: ", {"bold": True, "color": EMBER}),
     ("any fail → dropped; at most one warning → validated PD.", {})],
     [("Dropped: ", {"bold": True, "color": BAD}), ("Samana, Dirba (kept in 4 of 10 resamples).", {})],
     [("On real paddy: ", {"bold": True, "color": GOOD}), ("Abohar 0.45 vs 0.73; Dinanagar 0.25 vs 0.62.", {})]],
     size=14, margin=0)
image(s, FF / "f11_validation_grid.png", 5.9, TOP + 0.05, 6.83, 5.5, align="right")
notes(s, "Handbook pp. 67–68: check a deviant is a real signal before fieldwork. Trends from 5 seasons × 100 points "
         "are too noisy, so only Abohar holds as a temporal PD. A blind visual check (V7) was not done; stated as "
         "a limitation.")

# ---------- 19. Driver method ----------
s = S("6 · Why they burn less", "Stage 3: nine public drivers, tested three ways")
rows = [["Driver", "Data", "Level"],
        ["Harvest-to-sowing days", "Sentinel-2 NDVI (checked vs CIMMYT survey)", "Tehsil 2020–24"],
        ["Early second crop", "points green by 30 Nov (potato, vegetables)", "Tehsil 2020–24"],
        ["Farm labour; small farms", "Census 2011 village abstract", "Tehsil"],
        ["Straw buyers", "14 biomass / biogas plants from news", "Town"],
        ["Distance to state border", "SHRUG district polygons", "Tehsil"],
        ["Urban surroundings", "JRC GHS-SMOD 2020 settlement map", "Tehsil"],
        ["Basmati share", "APEDA survey 2023 ÷ rice area", "District"],
        ["Livestock", "Livestock Census 2019, village", "Tehsil"],
        [("CRM machines", BAD), ("no district data online → dropped", BAD), "—"]]
table(s, M, TOP + 0.05, 7.4, rows, [2.5, 3.5, 1.4], size=12, row_h=0.47)
card(s, 8.3, TOP + 0.05, 4.43, 1.45, "1 · Profiles", "Are PDs on the expected side of their group median, NDs on "
     "the other?", size=13)
card(s, 8.3, TOP + 1.65, 4.43, 1.45, "2 · Rank correlation", "Spearman ρ with 2020–24 burning, inside each "
     "group", size=13)
card(s, 8.3, TOP + 3.25, 4.43, 1.45, "3 · Rice held constant", "partial ρ: remove rice share from both, "
     "then correlate", size=13)
text(s, 8.3, TOP + 4.85, 4.43, 0.8, "8 PDs vs 4 heavy burners (NDs). A driver counts only if all three readings "
     "agree.", size=13, color=MUTED, margin=0)
notes(s, "Online data only, no fieldwork (academic scope). Why hold rice constant: more rice means more burning "
         "even inside a group (ρ 0.70 Central), so many drivers just restate rice share.")

# ---------- 20. Doaba ----------
s = S("6 · Why they burn less", "Doaba burns little as a region, not because it is near towns")
image(s, FF / "f14_doaba_far_fields.png", M, TOP + 0.05, 7.4, 4.3, align="left")
caption(s, M, TOP + 4.4, 7.4, "Share of points burnt, 2020–24: all fields vs fields more than 5 km from any town")
bullets(s, 8.4, TOP + 0.1, 4.33, 5.3, [
    ("Only urban share holds: ", "Central ρ −0.61, still −0.30 with rice held constant; 7 of 8 PDs above "
     "median, all 4 NDs below."),
    ("But far from towns, ", "the Doaba PDs burn just as little."),
    ("So: ", "a marker of the Doaba region (potato and vegetable rotations, off-farm and overseas income), "
     "not a town effect."),
    ("Others ", "(turnaround, small farms) vanish once rice is held constant."),
], size=14, gap=8)
notes(s, "Fields within 2 km of a town burn 6–8 points less, but only 4% of fields are that close. "
         "In the South-west, tehsils near the state border burn less (cotton belt), the opposite of Dipoppa & Gulzar.")

# ---------- 21. Abohar ----------
s = S("6 · Why they burn less", "Abohar: straw buyer, labour, livestock, early second crop")
image(s, FF / "f15_abohar_profile.png", M, TOP + 0.05, 7.6, 4.6, align="left")
caption(s, M, TOP + 4.7, 7.6, "Percentile of Abohar within the South-west group")
bullets(s, 8.6, TOP + 0.2, 4.13, 5, [
    ("A biomass power plant ", "inside the tehsil: an assured straw buyer."),
    ("Most farm labourers per cultivator ", "in Punjab: hands for straw handling."),
    ("Most cattle per cultivator ", "in its group: straw is fodder."),
    ("Earliest second crop ", "in its group."),
    ("One tehsil: ", "these cannot be separated. A lead for fieldwork, not a finding."),
], size=14, gap=8)
notes(s, "Also basmati-heavy district (Fazilka, 57% of rice) and 13 km from the Rajasthan border.")

# ---------- 22. What to do ----------
s = S("What to do", "The positive deviants, and what to do with them")
rows = [["Role", "Tehsils"],
        [("Positive deviants", GOOD), "Abohar (SW, strict); Dinanagar, Phagwara, Jalandhar-I, Adampur, Talwandi Sabo"],
        [("With caveat", MUTED), "Gurdaspur, Banga"],
        [("Heavy burners (ND)", BAD), "Lehra, Zira, Moonak, Guruharsahai"]]
table(s, M, TOP + 0.05, W - 2 * M, rows, [2.6, 9.53], size=14, row_h=0.45)
acts = [("Where to look", "Abohar and the Doaba tehsils first, with the heavy burners as comparison."),
        ("What to test", "Abohar's levers in other South-west tehsils: assured straw buyer, harvest labour, fodder link."),
        ("How to target", "Rank tehsils within peer groups and allow for rice share, or programmes reward places "
                          "that just grow less paddy."),
        ("How to monitor", "Rerun the free Sentinel-2 detector each December: farmers cannot dodge it by timing fires.")]
cw = (W - 2 * M - 0.25) / 2
for i, (h_, b_) in enumerate(acts):
    x = M + (i % 2) * (cw + 0.25)
    y = TOP + 2.0 + (i // 2) * 1.75
    card(s, x, y, cw, 1.6, h_, b_, head_color=GOOD, size=14)
notes(s, "For the Doaba belt the question for fieldwork is what farmers do with straw before an October potato "
         "or vegetable crop, and whether that works in wheat-only areas.")

# ---------- 23. Theory of change ----------
s = S("Impact assessment", "Theory of change: from leads to a tested lever")
flow_steps(s, TOP + 0.1, [("PD leads", "this study: where, and candidate levers"),
                          ("Phase 1", "confirm in the field what PDs do differently"),
                          ("Phase 2", "pilot confirmed levers in matched villages"),
                          ("Measure", "satellite burnt share + farmer survey"),
                          ("Scale", "through the partner, if the effect holds")], h=1.55, size=13)
rows = [["Assumption that must hold", "Tested in"],
        ["PD practices are real, not a data artefact", "Phase 1: field visits to satellite points"],
        ["Practices transfer (not tied to Doaba's region or Abohar's plant)", "Phase 1 interviews; Phase 2 pilot"],
        ["Farmers take up the lever when offered", "Phase 2 take-up indicators"],
        ["Burning falls, not just moves in time or place", "Phase 2 satellite outcome incl. neighbour villages"]]
table(s, M, TOP + 2.0, W - 2 * M, rows, [7.2, 4.93], size=14, row_h=0.55)
notes(s, "DPPD stops at candidate explanations (Stage 3). The handbook's next step is to check them and test "
         "whether they transfer.")

# ---------- 24. Phases + sample size ----------
s = S("Impact assessment", "Two phases: confirm in the field, then a randomised pilot")
card(s, M, TOP + 0.05, 3.85, 3.7, "Phase 1 · one season", [
    "PD, ND and typical tehsils; ~6 villages each, picked by satellite burning",
    "Farmer survey, focus groups, key informants",
    "Dated photos at our satellite points: ground truth"], size=13)
card(s, M + 4.05, TOP + 0.05, 3.85, 3.7, "Phase 2 · pilot", [
    "Villages in non-PD tehsils of the same peer group",
    "Paired on past burning + rice share; one per pair gets the lever at random",
    "Outcome: satellite burnt share; survey with a list experiment"], size=13)
image(s, FF / "f16_sample_size.png", 8.7, TOP + 0.05, 4.03, 3.3)
caption(s, 8.7, TOP + 3.4, 4.03, "Villages per arm to detect a 10-point drop")
panel(s, M, 5.75, W - 2 * M, 1.15)
text(s, M + 0.3, 5.8, W - 2 * M - 0.6, 1.05, [
    [("~30 villages per arm ", {"bold": True, "color": EMBER}),
     ("(35 pairs per lever) to detect a 10-point drop, 30 satellite points per village. The pessimistic case (52) "
      "still fits in the 1,633-village South-west frame.", {})]], size=15, anchor=MSO_ANCHOR.MIDDLE, margin=0)
notes(s, "Sample size from our own tehsil data: ANCOVA on the village baseline, 80% power, 5% two-sided. "
         "List experiment: burning is illegal, so farmers only report how many of a list of statements are true.")

# ---------- 25. Limits + takeaways ----------
s = S("Limits and takeaways", "Limits, and three takeaways")
image(s, FF / "f17_ground_truth_coverage.png", M, TOP + 0.05, 4.6, 4.6, align="left")
caption(s, M, TOP + 4.7, 4.6, "Where our ground truth comes from")
text(s, 5.5, TOP + 0.05, 3.3, 0.4, "Limits", size=18, bold=True, color=BAD, margin=0)
bullets(s, 5.5, TOP + 0.5, 3.3, 4.5, [
    "No fieldwork: no practice confirmed on the ground.",
    "8 PDs, 4 NDs; public data of mixed years.",
    "Ploughing tested on 2019 fields only; partial burns under-counted; 2024 doubtful.",
    "No district CRM machine data online.",
], size=14, gap=6)
text(s, 9.1, TOP + 0.05, 3.65, 0.4, "Takeaways", size=18, bold=True, color=GOOD, margin=0)
bullets(s, 9.1, TOP + 0.5, 3.65, 4.6, [
    ("Compare like with like ", "and allow for rice share."),
    ("Separate burning from ploughing: ", "possible with free Sentinel-2."),
    ("Abohar and Doaba ", "are where to look; their levers are leads to test."),
], size=15, gap=10)
text(s, 5.5, 6.55, 7.2, 0.4, "Thank you. Every number is reproducible from code in the repository.",
     size=14, color=MUTED, italic=True, margin=0)


# ---------- Backup ----------
def backup(t):
    s = new("Backup")
    title(s, t)
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
        ["Drivers", "Census 2011, Livestock Census 2019, biomass plant lists, urban areas", "Tehsil / district",
         "mixed", "Stage 3"],
        ["Checks", "CREAMS (official), VIIRS / FIRMS fire counts", "District / 375 m", "2019–25", "Validation"]]
table(s, M, TOP, W - 2 * M, rows, [2.3, 5.2, 1.9, 1.5, 1.23], size=13, row_h=0.44)

s = backup("B2 · Grouping: choice of k and sensitivity")
image(s, FIG / "fig_D_choosing_k.png", M, TOP, 6.2, 5.4, align="left")
image(s, FIG / "fig_E_sensitivity.png", 7.0, TOP, 5.73, 5.6)
caption(s, M, 7.0, W - 2 * M, "k = 3: silhouette 0.377, bootstrap ARI 0.890 (300 × 80%); Plains/Foothills split ARI 0.981.")

s = backup("B3 · Detector cut-off 0.79 vs 0.5")
stat(s, M, TOP + 0.3, 4, "0.84–0.98", "tehsil rank agreement between\nthe two cut-offs, by year", big_size=44)
bullets(s, 5.2, TOP + 0.3, 7.5, 4.5, [
    ("The cut-off changes the level, not the order: ", "at 0.5 every tehsil burns more but keeps its rank."),
    ("PDs depend on order within a group, ", "and survive the 0.5 rerun (validation V2)."),
    ("Walker trade-off: ", "0.79 → 90% burns caught, 18% ploughed called burnt; 0.5 → 97.5% and 51%."),
], size=16, gap=10)

s = backup("B4 · Robust deviants and validation")
rows = [["Tehsil", "Group", "Burnt share", "%/yr vs group", "Bootstrap", "Label"],
        ["Abohar", "SW", "0.34", "−11.1", "0.92", ("validated PD (strict)", GOOD)],
        ["Dinanagar", "C", "0.21", "+6.5", "1.00", ("validated PD", GOOD)],
        ["Phagwara", "C", "0.30", "+6.0", "0.99", ("validated PD", GOOD)],
        ["Jalandhar-I", "C", "0.31", "−1.4", "0.98", ("validated PD", GOOD)],
        ["Adampur", "C", "0.30", "−4.9", "0.89", ("validated PD", GOOD)],
        ["Talwandi Sabo", "SW", "0.50", "+14.5", "0.97", ("validated PD", GOOD)],
        ["Gurdaspur", "C", "0.29", "+2.3", "0.97", "PD with caveat"],
        ["Banga", "C", "0.34", "+5.6", "0.72", "PD with caveat"],
        ["Samana (temporal)", "C", "0.63", "−9.1", "0.40", ("dropped", BAD)],
        ["Dirba (temporal)", "C", "0.71", "−8.2", "0.39", ("dropped", BAD)],
        ["Lehra, Zira, Moonak / Guruharsahai", "C / SW", "0.79–0.90", "", "", "contrast NDs"]]
table(s, M, TOP, W - 2 * M, rows, [3.6, 1.1, 1.6, 1.8, 1.4, 2.63], size=13, row_h=0.43)

s = backup("B5 · Drivers vs burning within groups")
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
        "* p < 0.05, ** p < 0.01 (report Table 8)")

s = backup("B6 · Survey modules and logframe")
rows = [["#", "Survey module", "#", "Survey module"],
        ["1", "Household and farm", "6", "Labour and livestock"],
        ["2", "Paddy season (variety, harvest, combine)", "7", "Next crop and timing"],
        ["3", "Residue handling per plot", "8", "Norms and enforcement"],
        ["4", "Machines (own / hire, cost, waiting)", "9", "Barriers and preferences"],
        ["5", "Straw market (buyer, price, distance)", "10", "List experiment (burning)"]]
table(s, M, TOP, W - 2 * M, rows, [0.6, 5.47, 0.6, 5.46], size=14, row_h=0.5)
bullets(s, M, TOP + 3.3, W - 2 * M, 2.2, [
    ("Impact: ", "less burning in South-west villages (satellite burnt share, peer-group adjusted)."),
    ("Outcome: ", "farmers manage straw without burning (list experiment; straw sold / fed)."),
    ("Outputs: ", "lever delivered on time (villages served, tonnes collected, labour days)."),
], size=15, gap=6)

prs.save(OUT)
print(f"Saved {OUT} ({len(prs.slides)} slides)")
