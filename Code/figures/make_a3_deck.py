"""
Assignment 3 interim deck (due 2026-11-06): 20 main slides + 4 backup.

Content follows report/a3_deck_outline.md. Every number is taken from finished outputs or the
report draft; figures come from make_grouping_figures.py and make_pd_figures.py.

Run:  python Code/figures/make_a3_deck.py
Out:  report/A3_interim_deck.pptx
"""

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
OUT = ROOT / "report" / "A3_interim_deck.pptx"

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


# ---------- 1. Title ----------
s = new(dark=True)
dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(M), Inches(1.55), Inches(0.22), Inches(0.22))
fill(dot, EMBER)
text(s, M + 0.35, 1.45, 8, 0.45, "COL7761 ICTD · ASSIGNMENT 3 · INTERIM PROGRESS", size=13,
     color=ON_DARK_MUTED, bold=True, margin=0)
text(s, M, 2.1, 11.5, 2.0, "Finding Positive Deviants in Crop Residue Burning",
     size=48, font=HEAD, bold=True, color=WHITE, margin=0)
text(s, M, 3.85, 11.5, 0.6, "A Data-Powered Positive Deviance study of Punjab's 97 tehsils",
     size=22, color=ON_DARK_MUTED, margin=0)
text(s, M, 5.4, 11.5, 1.2, [
    [("Soham Malvadkar", {"bold": True, "color": WHITE})],
    "Supervisor: Prof. Aaditeshwar Seth  ·  Advisors: Basma Albanna, Andreas Pawelke",
], size=16, color=ON_DARK_MUTED, margin=0)
notes(s, "Interim update: grouping, burn measurement and PD identification are implemented; "
         "validation and underlying factors are in progress.")

# ---------- 2. Recap ----------
s = new("Recap")
title(s, "Where we are")
panel(s, M, TOP + 0.1, W - 2 * M, 1.25, color=PANEL)
text(s, M + 0.3, TOP + 0.2, W - 2 * M - 0.6, 1.05, [
    [("Question  ", {"bold": True, "color": EMBER}),
     ("Which of Punjab's 97 tehsils burn much less paddy straw than structurally similar peers, "
      "and what are they doing differently?", {})]], size=20, anchor=MSO_ANCHOR.MIDDLE, margin=0)
steps = [("Homogeneous grouping", "done", GOOD), ("Burn measurement", "done", GOOD),
         ("PD identification", "done", GOOD), ("PD validation", "in progress", EMBER),
         ("Underlying factors", "started", EMBER)]
bw, gap = 2.2, 0.28
x0 = M
for i, (name, st, col) in enumerate(steps):
    x = x0 + i * (bw + gap)
    panel(s, x, 3.45, bw, 1.85, color=PANEL)
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.2), Inches(3.6), Inches(0.5), Inches(0.5))
    fill(c, col)
    text(s, x + 0.2, 3.6, 0.5, 0.5, str(i + 1), size=16, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, margin=0)
    text(s, x + 0.2, 4.2, bw - 0.3, 0.6, name, size=16, bold=True, margin=0)
    text(s, x + 0.2, 4.85, bw - 0.3, 0.35, st, size=14, color=col, bold=True, margin=0)
    if i < len(steps) - 1:
        arrow(s, x + bw - 0.02, 4.2, w=0.3, h=0.3)
text(s, M, 5.6, W - 2 * M, 1.0, [
    [("Unit: ", {"bold": True}), ("97 current tehsils (LGD codes), Punjab only; Haryana deferred "
                                  "because its groundwater and boundary data are incomplete.", {})],
    [("Season: ", {"bold": True}), ("15 Sep – 30 Nov, the ISRO protocol CAQM uses for paddy residue "
                                    "burning; seasons 2019–2024.", {})]], size=15, color=TEXT, margin=0)
notes(s, "Everything shown today is reproducible from code in the repository.")

# ---------- 3. Grouping variables ----------
s = new("1 · Homogeneous grouping")
title(s, "Grouping variables: structural conditions only",
      "No drivers (machines, mandis) and no burning data. Groups were frozen before burning was measured.")
rows = [["Dimension", "Variable", "Why it matters for burning"],
        ["Rice", "Rice share of tehsil area, 2022 (Chen map calibrated to official)",
         "More paddy = more straw to clear in the same short window"],
        ["Rainfall", "Mean monsoon rainfall, Jun–Sep 2020–25 (CHIRPS)",
         "Separates the arid south-west from the wetter centre"],
        ["Agro-ecological zone", "Share of area in AESR zones 14.2, 2.5, 4.1, 9.1 (NBSS&LUP 2018)",
         "Climate + landform class; separates foothills from plains"],
        ["Groundwater", "Stage of extraction 2022, % of recharge (CGWB)",
         "Transplanting delay law → later harvest → less time before wheat"],
        ["Soil", "8 NBSS&LUP descriptors (texture, drainage, depth, pH, …)",
         "Drainage and workability; how easily wheat is sown into residue"]]
table(s, M, TOP + 0.55, W - 2 * M, rows, [2.4, 5.0, 4.73], size=14, row_h=0.72)
notes(s, "Rule from the DPPD handbook: grouping on drivers would hide the very deviance we want to find.")

# ---------- 4. Data problems ----------
s = new("1 · Homogeneous grouping")
title(s, "Data problems we found and fixed on the way")
cw = 3.55
cards = [
    ("Rice map biased by region", "Chen 2022 over-maps the south-west and foothills (Fazilka ×1.71) and "
     "under-maps the centre (×0.76–0.93). Calibrated to official district rice area."),
    ("Cropping intensity unreliable", "Our satellite estimate agreed poorly with official figures "
     "(ρ 0.18). Dropped; removing it moves only 2 tehsils."),
    ("Defective slope data", "Different tehsils had identical slope values. Terrain replaced by "
     "agro-ecological zone shares."),
    ("Boundaries changed since 2011", "Data are on 2011 villages; Punjab now has 97 tehsils. Built "
     "village and tehsil crosswalks from LGD."),
]
for i, (h_, b_) in enumerate(cards):
    r, c = divmod(i, 2)
    card(s, M + c * (cw + 0.25), TOP + 0.15 + r * 2.7, cw, 2.5, h_, b_, size=14)
image(s, FIG / "fig_F_rice_calibration.png", 8.3, TOP + 0.1, 4.45, 4.85)
caption(s, 8.3, 6.6, 4.45, "Chen rice area vs official, by district")
notes(s, "Each fix is logged with its evidence in the sub-journey files.")

# ---------- 5. Distance ----------
s = new("1 · Homogeneous grouping")
title(s, "Measuring how alike two tehsils are",
      "Dimension-balanced Gower distance: every dimension gets one equal vote")
bw = 3.75
boxes = [
    ("1  Score each column 0–1", ["Numbers: |a − b| ÷ range", "Categories (soil): 0 if same, 1 if different",
                                  "Missing value: skip that column"]),
    ("2  Average inside each dimension", ["Soil's 8 columns → one soil score",
                                          "Zones' 4 shares → one zone score",
                                          "So soil cannot out-vote rainfall"]),
    ("3  Average the 5 dimensions", ["Equal weights (1/5 each)",
                                     "0 = identical, 1 = completely different",
                                     "Weights tested ±15% later"]),
]
for i, (h_, b_) in enumerate(boxes):
    x = M + i * (bw + 0.48)
    card(s, x, TOP + 0.7, bw, 2.6, h_, b_, size=15)
    if i < 2:
        arrow(s, x + bw + 0.07, TOP + 1.85)
panel(s, M, 5.15, W - 2 * M, 1.4, color=PANEL)
text(s, M + 0.3, 5.25, W - 2 * M - 0.6, 1.2, [
    [("Why not plain Gower? ", {"bold": True, "color": EMBER}),
     ("Plain Gower averages all 15 columns, so soil (8 columns) would get 8 votes and rainfall 1.", {})],
    [("Outlier handling: ", {"bold": True, "color": EMBER}),
     ("Dhar Kalan (hill tehsil, 7% rice, 1,604 mm rain) is left out when computing ranges, "
      "otherwise it squeezes everyone else's differences by ~12%.", {})]],
     size=15, anchor=MSO_ANCHOR.MIDDLE, margin=0)
notes(s, "Code: Code/grouping/gower.py. Distances were checked against hand calculations.")

# ---------- 6. Dendrogram ----------
s = new("1 · Homogeneous grouping")
title(s, "Average-linkage hierarchical clustering",
      "Start with 97 single tehsils; repeatedly merge the two groups with the smallest average distance")
image(s, FIG / "fig_B_dendrogram.png", M, TOP + 0.5, W - 2 * M, 4.9)
caption(s, M, 6.95, W - 2 * M, "Leaf labels coloured by final group; dashed line = cut giving 3 groups + "
        "the outlier Dhar Kalan.")
notes(s, "Why average linkage: works on a custom distance matrix (k-means cannot), "
         "does not force round or equal-sized groups, and the tree shows how groups relate.")

# ---------- 7. Choosing k and stability ----------
s = new("1 · Homogeneous grouping")
title(s, "Choosing the number of groups and testing stability")
image(s, FIG / "fig_D_choosing_k.png", M, TOP + 0.05, 8.3, 3.3, align="left")
caption(s, M, TOP + 3.4, 8.3, "Silhouette and bootstrap ARI by number of groups (groups < 5 tehsils set aside)")
sx = 9.3
stat(s, sx, TOP, 3.4, "0.377", "silhouette at k = 3")
stat(s, sx, TOP + 1.55, 3.4, "0.890", "mean bootstrap ARI\n(300 resamples of 80%)")
stat(s, sx, TOP + 3.1, 3.4, "3", "borderline tehsils\n(Firozpur, Faridkot, Dinanagar)")
bullets(s, M, 5.45, 8.4, 1.6, [
    ("k = 4–5 ", "give the same 3 usable groups; k = 6 splits Central (ARI 0.71)."),
    ("Sensitivity: ", "8 of 10 weight changes (±15%) keep ARI ≥ 0.83; dropping any dimension "
                      "merges the South-west into Central."),
    ("Weak point: ", "the South-west / Central border is a gradient, so every PD must also hold under "
                     "the 2-group split Plains 81 / Foothills 15 (ARI 0.981)."),
], size=14, gap=4)
notes(s, "ARI: 1 = identical grouping, 0 = no better than chance. Borderline = switches group in "
         "more than 20% of resamples; each tehsil gets its consensus group.")

# ---------- 8. Final groups ----------
s = new("1 · Homogeneous grouping")
title(s, "Final groups: three agro-ecological belts")
image(s, FIG / "fig_A_group_map.png", M, TOP, 4.9, 5.6)
rows = [["Group", "Tehsils", "Rice share", "Monsoon rain", "GW extraction"],
        [("Central", GROUP["Central"]), "63", "75%", "721 mm", "230%"],
        [("South-west", GROUP["South-west"]), "18", "59%", "467 mm", "118%"],
        [("Foothills", GROUP["Foothills"]), "15", "28%", "981 mm", "117%"],
        ["Outlier (Dhar Kalan)", "1", "7%", "1,604 mm", "27%"]]
table(s, 5.9, TOP + 0.2, 6.83, rows, [2.2, 1.0, 1.2, 1.3, 1.13], size=14, row_h=0.5)
caption(s, 5.9, TOP + 2.75, 6.83, "Group medians")
panel(s, 5.9, TOP + 3.3, 6.83, 2.15, color=PANEL)
text(s, 6.15, TOP + 3.4, 6.35, 1.95, [
    [("No location was given to the method, ", {"bold": True}),
     ("yet the groups form connected regions: the central plains, the dry Malwa south-west and "
      "the Kandi / Siwalik foothills.", {})],
    [("→ The grouping captures real structure, not noise.", {"color": EMBER, "bold": True})]],
     size=16, anchor=MSO_ANCHOR.MIDDLE, margin=0)
notes(s, "Frozen v4, 7 Oct 2026. outputs/grouping/FROZEN_groups.csv.")

# ---------- 9. What we measure + first detector ----------
s = new("2 · Measuring burning")
title(s, "What we measure, and the first detector")
bullets(s, M, TOP + 0.1, 6.6, 2.4, [
    ("Target: ", "per tehsil and season, the share of paddy fields burnt (15 Sep – 30 Nov, 2020–24)."),
    ("Why not fire counts? ", "VIIRS sees ~3.7× fewer burns than Sentinel-2, and farmers now burn "
                              "after the satellite passes. Kept only as a cross-check."),
    ("First detector: ", "BAIS2 (red-edge burn index) + Tasseled Cap Brightness on Sentinel-2 (10–20 m), "
                         "trained on 438 CEEW labelled fields."),
], size=16, gap=8)
stat(s, 7.7, TOP + 0.1, 2.4, "95.5%", "accuracy on CEEW\nfields (5-fold CV)")
stat(s, 10.3, TOP + 0.1, 2.4, "98%", "of burnt fields\ncaught (recall)")
text(s, 7.7, TOP + 1.75, 5.0, 0.5, "NBR, the usual burn index: 81% accuracy", size=14, color=MUTED, margin=0)
card(s, M, 4.7, 5.9, 1.65, "Fix 1: the formula",
     "A simplified BAIS2 formula performed badly; the full red-edge formula (Filipponi 2018) fixed it.")
card(s, M + 6.25, 4.7, 5.9, 1.65, "Fix 2: the cloud mask",
     "Sentinel-2's scene classes label fresh ash as 'dark area', so the standard mask threw away "
     "burnt fields (3 of 54 kept). Widened mask: 436 of 438 kept.")
notes(s, "This detector looked excellent on single dates. The problem appeared over a whole season.")

# ---------- 10. The problem ----------
s = new("2 · Measuring burning")
title(s, "The problem: burnt fields look like ploughed fields")
image(s, PLANET / "chips_jalandhar_2021_2021-10-29.png", M, TOP, 7.4, 4.3, align="left")
caption(s, M, TOP + 4.35, 7.4, "PlanetScope 3 m, Jalandhar, 29 Oct 2021: completely burnt, partially burnt and "
        "unburnt CEEW fields. Fresh ash is near-black; a few days later it looks like soil.")
stat(s, 8.5, TOP, 4.3, "81%", "of ploughed-not-burnt fields flagged as burnt\n(Walker et al. ground truth, 2019)",
     big_size=54)
bullets(s, 8.5, TOP + 1.9, 4.3, 3.6, [
    "Over a whole season it flags 94.6% of random cropland points.",
    "Char vs fresh soil: same Sentinel-2 colour (AUC 0.51).",
    ("Why: ", "ash stays black only 2–3 days, then fades to soil colour. Sentinel-2 passes every 5 days."),
    ("Why it matters: ", "a tehsil that ploughs instead of burning would look like a burner and its "
                         "PD status would be hidden."),
], size=15, gap=6)
notes(s, "This was the single hardest problem in the project (difficulty D11 in the report).")

# ---------- 11. Failed vs worked ----------
s = new("2 · Measuring burning")
title(s, "What failed, and the idea that worked")
cw = (W - 2 * M - 0.35) / 2
card(s, M, TOP + 0.3, cw, 4.0, "Tried and rejected", [
    ("Heat (Landsat / MODIS land surface temperature): ", "ash is not hotter than ploughed soil. "
     "A heat-peak timing rule cut over-flagging 95% → 56%, but its tehsil ranks barely matched fire "
     "counts (ρ 0.10–0.27)."),
    ("Radar roughness (Sentinel-1, Basma's suggestion): ", "12-day revisit, and backscatter moved the "
     "wrong way on ploughed fields. Kept as a documented negative result."),
    ("Sharper index rules ", "(jump, NBR2, peak size): no gain on the CIMMYT field survey."),
], head_color=BAD, size=15)
card(s, M + cw + 0.35, TOP + 0.3, cw, 4.0, "What worked", [
    ("Look at the right moment: ", "daily PlanetScope sees the 2–3 dark days and separates ash from "
     "soil (AUC 0.96)."),
    ("Learn from ground truth: ", "Walker et al. published Sentinel-2 series for 2,204 burnt and 223 "
     "ploughed-not-burnt fields (Punjab 2019)."),
    ("So: ", "train a model on what a real burn looks like at the moment of change, then check it "
     "with daily Planet imagery in a new year and district."),
], head_color=GOOD, size=15)
notes(s, "Branch B (radar) is frozen as a negative result; branch A (heat) was superseded by the "
         "current detector.")

# ---------- 12. Current detector ----------
s = new("2 · Measuring burning")
title(s, "Current detector, step by step", "Applied to every Sentinel-2 look of a field (or point) in the season")
steps = [
    ("1", "Flag", "BAIS2 + TCB score > 0 on a clear look → possible event (burnt or ploughed)."),
    ("2", "Candidate", "Pick the flagged look with the largest jump from the previous clear look. "
                      "Burning is sudden; drying and harvest are gradual."),
    ("3", "Before / after", "Compare the candidate with the one clear look before it: bands B2–B12, "
                           "NDVI, NBR, NBR2, BAIS2, TCB (after values + changes)."),
    ("4", "Decide", "Random forest (500 trees) trained on Walker burnt vs ploughed. "
                   "Burnt if probability ≥ 0.79."),
]
bw = 2.75
for i, (n, h_, b_) in enumerate(steps):
    x = M + i * (bw + 0.38)
    panel(s, x, TOP + 0.75, bw, 3.6)
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.2), Inches(TOP + 0.95), Inches(0.6), Inches(0.6))
    fill(c, EMBER)
    text(s, x + 0.2, TOP + 0.95, 0.6, 0.6, n, size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, margin=0)
    text(s, x + 0.2, TOP + 1.7, bw - 0.4, 0.45, h_, size=19, bold=True, margin=0)
    text(s, x + 0.2, TOP + 2.2, bw - 0.4, 2.1, b_, size=15, margin=0)
    if i < 3:
        arrow(s, x + bw + 0.03, TOP + 2.4, w=0.32, h=0.32)
text(s, M, 6.0, W - 2 * M, 0.9, [
    [("Why 0.79? ", {"bold": True, "color": EMBER}),
     ("It keeps 90% of Walker's burns. Ploughing false alarms are the bigger threat for DPPD, because "
      "they hide tehsils that plough instead of burning. 0.5 is run as a sensitivity check.", {})]],
     size=15, margin=0)
notes(s, "Code: Code/planet/jalandhar_walker_model_test.py (field level), Code/burn/tehsil_metric_rf.py (tehsils).")

# ---------- 13. How good ----------
s = new("2 · Measuring burning")
title(s, "How good is it?")
rows = [["Test", "What is counted", "First detector", "Current detector"],
        ["Walker 2019, 5-fold CV", "Burns caught", "98%", "90%"],
        ["", "Ploughed called burnt", ("81%", BAD), ("18%", GOOD)],
        ["Jalandhar 2021, daily-Planet judge", "Not-burnt called burnt", ("23 / 32", BAD), ("0 / 32", GOOD)],
        ["(not retrained)", "Burns kept", "63 / 63", "37 / 63"],
        ["Jalandhar 2021, CEEW field visit", "Unburnt called burnt", ("28 / 95", BAD), ("1 / 95", GOOD)],
        ["", "Burns kept", "257 / 262", "89 / 262"]]
table(s, M, TOP + 0.1, 8.0, rows, [2.9, 2.2, 1.45, 1.45], size=14, row_h=0.55)
caption(s, M, TOP + 4.05, 8.0, "Current detector at cut-off 0.79. At 0.5, Jalandhar keeps 51/63 (Planet) and "
        "145/262 (CEEW) burns with 2–3 false alarms.")
stat(s, 9.1, TOP + 0.1, 3.6, "0.94", "AUC on Walker ground truth\n(first detector: 81% false alarms)")
card(s, 9.1, TOP + 1.85, 3.6, 2.3, "The cost", "It misses burns, mostly partially burnt fields "
     "(field averages dilute small burnt patches). For DPPD this is acceptable if the miss rate is "
     "similar across tehsils (stated assumption).", size=14)
notes(s, "False alarms fall sharply; the trade-off is under-counting of partial burns.")

# ---------- 14. Fields to tehsils ----------
s = new("2 · Measuring burning")
title(s, "From fields to tehsils")
flow = [("100", "random cropland points\nper tehsil"), ("6", "seasons per point\n(2019–2024)"),
        ("4-step", "detector verdict\nper point and season"), ("share", "of points burnt\n= tehsil value")]
bw = 2.75
for i, (big, lab) in enumerate(flow):
    x = M + i * (bw + 0.38)
    panel(s, x, TOP + 0.4, bw, 2.2)
    text(s, x + 0.2, TOP + 0.55, bw - 0.4, 0.9, big, size=40, font=HEAD, bold=True, color=EMBER, margin=0)
    text(s, x + 0.2, TOP + 1.45, bw - 0.4, 1.0, lab, size=15, color=TEXT, margin=0)
    if i < 3:
        arrow(s, x + bw + 0.03, TOP + 1.3, w=0.32, h=0.32)
bullets(s, M, 4.65, W - 2 * M, 2.4, [
    ("9,700 points per season; ", "97–99.9% get a verdict (lowest single tehsil: 70 of 100, 2022)."),
    ("All cropland, not Chen's rice map, ", "because that map is biased by region."),
    ("Season 15 Sep – 30 Nov ", "(ISRO protocol used by CAQM)."),
    ("PD identification uses 2020–24; ", "2019 kept for checks only."),
], size=16, gap=6)
notes(s, "Points rather than wall-to-wall mapping keep the Earth Engine cost manageable on a free tier.")

# ---------- 15. Does it hold up ----------
s = new("2 · Measuring burning")
title(s, "Does the tehsil measure hold up?")
image(s, FIG / "fig_H_burn_vs_viirs.png", M, TOP, 6.6, 4.8, align="left")
caption(s, M, TOP + 4.85, 6.6, "81 ranked tehsils, 2021. Each dot = one tehsil.")
sx = 7.6
stat(s, sx, TOP, 2.5, "0.78–0.87", "rank agreement with\nVIIRS fire counts, 2019–23", big_size=30)
stat(s, sx + 2.7, TOP, 2.5, "0.82–0.91", "year-to-year rank\nstability", big_size=30)
stat(s, sx, TOP + 1.65, 2.5, "0.87", "district agreement with\nofficial CREAMS 2022", big_size=30)
stat(s, sx + 2.7, TOP + 1.65, 2.5, "7.8 vs 9.9%", "state burnt share vs\nCREAMS (till 24 Oct 2022)", big_size=30)
card(s, sx, TOP + 3.45, 5.13, 2.05, "Weak spots", [
    "2024: 72% of burns first seen after 15 Nov; VIIRS ρ 0.51",
    "2019 level above CREAMS (CREAMS changed method)",
    "2020 district order weaker (ρ 0.50)"], head_color=BAD, size=14)
notes(s, "VIIRS agreement is reassuring but not proof: farmers time fires to dodge the overpass.")

# ---------- 16. Who burns how much ----------
s = new("3 · Positive deviants")
title(s, "Who burns how much")
image(s, FIG / "fig_G_burn_map.png", M, TOP, 4.6, 5.6)
rows = [["Group", "Burnt share, 2020–23", "Spread across tehsils (5-season mean)"],
        [("Central", GROUP["Central"]), "52–67%", "0.25 → 0.81"],
        [("South-west", GROUP["South-west"]), "60–70%", "0.34 → 0.90"],
        [("Foothills", GROUP["Foothills"]), "20–27%", "measured, not ranked"]]
table(s, 5.8, TOP + 0.2, 6.93, rows, [1.9, 2.2, 2.83], size=15, row_h=0.55)
caption(s, 5.8, TOP + 2.45, 6.93, "Area-weighted share of cropland points burnt, by season")
bullets(s, 5.8, TOP + 3.05, 6.93, 2.5, [
    ("Burning is not uniform inside a group: ", "in Central, the lowest tehsil burns a third as much "
     "as the highest. That spread is the room for positive deviance."),
    ("Foothills excluded from ranking: ", "only 15 tehsils and the weakest validation (4 districts)."),
], size=16, gap=8)
notes(s, "Black lines on the map are the group borders from slide 8.")

# ---------- 17. PD rule ----------
s = new("3 · Positive deviants")
title(s, "Two kinds of deviance and the PD rule")
image(s, FIG / "fig_I_pd_fences.png", M, TOP, 7.5, 3.75, align="left")
caption(s, M, TOP + 3.8, 7.5, "Static fences on the 2020–24 run. Hollow dots = Doaba cluster.")
card(s, 8.4, TOP, 4.33, 1.75, "Static", "Lowest 5-season mean burnt share (2020–24) within its own group.",
     size=14)
card(s, 8.4, TOP + 1.95, 4.33, 1.75, "Temporal (Basma)", "Fastest fall in burning per year compared "
     "with the group's own trend.", size=14)
panel(s, M, 5.75, W - 2 * M, 1.25, color=PANEL)
text(s, M + 0.3, 5.8, W - 2 * M - 0.6, 1.15, [
    [("Strict PD: ", {"bold": True, "color": GOOD}),
     ("beyond the group's IQR fence (Q1 − 1.5 × IQR, log scale) in both runs: 2020–24 and 2020–23 "
      "(because 2024 is suspect).", {})],
    [("Borderline: ", {"bold": True, "color": EMBER}),
     ("beyond the fence in one run, bottom 10% in the other. The old 'bottom 10%' list is kept as a "
      "broader low-burning set.", {})]], size=15, anchor=MSO_ANCHOR.MIDDLE, margin=0)
notes(s, "Fences: Central 0.225 (median 0.61), South-west 0.454 (median 0.73). "
         "Bottom 10% only says a tehsil is among the lowest, not that it is far from normal.")

# ---------- 18. PDs found ----------
s = new("3 · Positive deviants")
title(s, "Positive deviants found")
image(s, FIG / "fig_J_pd_map.png", M, TOP - 0.05, 6.9, 5.3, align="left")
x2 = 7.75
card(s, x2, TOP - 0.05, 4.98, 1.55, "Abohar (South-west): the only strict PD",
     "Burns 0.34 vs group median 0.73; also the fastest reducer (−11%/yr vs group).",
     head_color=GOOD, size=14)
card(s, x2, TOP + 1.65, 4.98, 1.2, "Borderline PDs",
     "Dinanagar (static) · Samana (temporal)", head_color=GOOD, size=14)
card(s, x2, TOP + 3.0, 4.98, 1.5, "Doaba low-burning cluster",
     "Gurdaspur, Phagwara, Adampur, Jalandhar-I, Banga: ~half the median, but low together → "
     "likely structural (e.g. potato rotation).", head_color=GROUP["Central"], size=14)
card(s, x2, TOP + 4.65, 4.98, 1.2, "Negative deviants",
     "Malout (borderline, rising fastest) · Lehra, Zira, Moonak, Guruharsahai", head_color=BAD, size=14)
caption(s, M, TOP + 5.3, 6.9, "Same tehsils stand out with VIIRS fire counts → not an artefact of one sensor.")
notes(s, "outputs/pd/robust/robust_deviants.csv. Doaba is studied as a structural question, not as PDs.")

# ---------- 19. Underlying factors ----------
s = new("4 · Status and next")
title(s, "Underlying factors: started")
text(s, M, TOP + 0.05, 7, 0.45, "First driver built: harvest-to-sowing turnaround (Sentinel-2 greenness)",
     size=17, bold=True, margin=0)
stat(s, M, TOP + 0.65, 2.6, "22–26 Oct", "median paddy\nharvest date", big_size=30)
stat(s, M + 2.75, TOP + 0.65, 2.6, "14–22 days", "harvest → wheat\nsowing (2020–24)", big_size=30)
stat(s, M + 5.5, TOP + 0.65, 2.6, "~1 week", "later harvest in the\nSouth-west than Central", big_size=30)
text(s, M, TOP + 2.35, 8.1, 0.8, "Checked against the CIMMYT farmer survey: district ranks agree "
     "(harvest ρ 0.80; sowing ρ 0.77–0.93).", size=15, color=MUTED, margin=0)
card(s, 9.0, TOP + 0.05, 3.73, 3.05, "Next drivers", [
    "CHCs / CRM machines", "Straw buyers (biomass plants)", "Mandis and towns", "Farm size, livestock",
    "Post-paddy crop", "Border proximity"], size=14)
panel(s, M, 4.85, W - 2 * M, 1.35, color=PANEL)
text(s, M + 0.3, 4.9, W - 2 * M - 0.6, 1.25, [
    [("Plan: ", {"bold": True, "color": EMBER}),
     ("compare Abohar (+ borderline Dinanagar, Samana) with the negative deviants and their group, "
      "driver by driver.", {})],
    [("Caution: ", {"bold": True, "color": EMBER}),
     ("enforcement data (red entries, FIRs) react to past burning, so they are used only as lagged "
      "context, never as a clean cause.", {})]], size=15, anchor=MSO_ANCHOR.MIDDLE, margin=0)
notes(s, "Code/predictors/harvest_gap.py. 2019 green-up dates are unreliable (December cloud/fog).")

# ---------- 20. Limitations and next ----------
s = new(dark=True)
dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(M), Inches(0.22), Inches(0.14), Inches(0.14))
fill(dot, EMBER)
text(s, M + 0.2, 0.12, 6, 0.32, "4 · STATUS AND NEXT", size=11, color=ON_DARK_MUTED, bold=True, margin=0)
text(s, M, TITLE_Y, W - 2 * M, TITLE_H, "Limitations and next steps to 25 Nov", size=34, font=HEAD,
     bold=True, color=WHITE, anchor=MSO_ANCHOR.BOTTOM, margin=0)
cw = (W - 2 * M - 0.4) / 2
text(s, M, TOP + 0.1, cw, 0.45, "Limitations", size=20, bold=True, color=EMBER, margin=0)
bullets(s, M, TOP + 0.65, cw, 4.5, [
    "Ploughing tested only on Walker 2019 (one season, two districts).",
    "Partial burns under-counted (about half missed).",
    "Rice map corrected only at district level; 5-year rainfall; equal weights; 97 units.",
    "Planet quota: daily imagery only as a judge, not at tehsil scale.",
    ("With more resources ", "(Planet quota, field labels), the same pipeline gives sharper results."),
], size=16, color=WHITE, gap=8)
x2 = M + cw + 0.4
text(s, x2, TOP + 0.1, cw, 0.45, "Next", size=20, bold=True, color=EMBER, margin=0)
bullets(s, x2, TOP + 0.65, cw, 4.5, [
    ("PD validation: ", "data quality at the PDs, cut-off 0.5 sensitivity, Doaba structural check, "
                        "Dinanagar border status."),
    ("Underlying factors: ", "what Abohar does differently."),
    ("Impact assessment design: ", "pilot in matched tehsils, our satellite measure as the outcome "
                                  "(before/after vs comparison), farmer survey."),
    ("Final report + talk: ", "25 Nov."),
], size=16, color=WHITE, gap=8)
notes(s, "Thank you. Backup slides follow.")

# ---------- Backup ----------
s = new("Backup")
title(s, "B1 · Data sources")
rows = [["Variable", "Source", "Level", "Year(s)", "Use"],
        ["Boundaries", "SHRUG v2.2 villages; Esri/LGD tehsils; own crosswalk", "Village / tehsil", "2011, 2024", "Base"],
        ["Rice area", "Chen et al. 10 m map, calibrated to Statistical Abstract", "Pixel → tehsil", "2022", "Grouping"],
        ["Rainfall", "CHIRPS daily (Earth Engine)", "~5 km", "2020–25", "Grouping"],
        ["Agro-ecological zones", "NBSS&LUP AESR 2018 (Bhoomi)", "Polygon", "2018", "Grouping"],
        ["Groundwater", "CGWB Ground Water Resources of Punjab", "Block", "2022", "Grouping"],
        ["Soil", "NBSS&LUP 1:250K soil map", "Map unit", "static", "Grouping"],
        ["Burn imagery", "Sentinel-2 SR Harmonized", "10–20 m", "2019–24", "Measure"],
        ["Ground truth", "Walker et al. (burnt vs ploughed); CEEW fields; CIMMYT survey", "Field", "2019–22", "Measure"],
        ["Daily imagery", "PlanetScope (Education & Research)", "3 m", "Oct–Nov 2021", "Judge"],
        ["Checks", "CREAMS (official), VIIRS / FIRMS fire counts", "District / 375 m", "2019–24", "Validation"]]
table(s, M, TOP, W - 2 * M, rows, [2.3, 5.2, 1.9, 1.5, 1.23], size=13, row_h=0.47)

s = new("Backup")
title(s, "B2 · Grouping sensitivity")
image(s, FIG / "fig_E_sensitivity.png", M, TOP, 7.6, 5.4, align="left")
bullets(s, 8.6, TOP + 0.3, 4.13, 5, [
    "Each dimension's weight ×0.85 and ×1.15; each dimension dropped; soil without near-constant descriptors.",
    "8 of 10 weight changes keep ARI ≥ 0.83 and move at most 5 tehsils.",
    "15% more weight on rice or soil merges the South-west into Central (ARI 0.48–0.60).",
    "The Foothills / Plains split survives every test.",
], size=15, gap=8)

s = new("Backup")
title(s, "B3 · Robust deviant table")
rows = [["Tehsil", "Group", "Strict rule", "Old rule", "Mean 2020–24", "%/yr vs group"],
        ["Abohar", "SW", ("PD static, borderline temporal", GOOD), "PD static + temporal", "0.338", "−11.1"],
        ["Dinanagar", "C", ("borderline PD static", GOOD), "PD static", "0.212", "+6.5"],
        ["Samana", "C", ("borderline PD temporal", GOOD), "PD temporal", "0.634", "−9.1"],
        ["Gurdaspur / Phagwara / Adampur", "C", "–", "PD static (Doaba)", "0.29–0.30", "−4.9 to +6.0"],
        ["Jalandhar-I / Banga", "C", "–", "PD static (Doaba)", "0.31–0.34", "−1.4 / +5.6"],
        ["Talwandi Sabo", "SW", "–", "PD static", "0.504", "+14.5"],
        ["Dirba", "C", "–", "PD temporal", "0.706", "−8.2"],
        ["Malout", "SW", ("borderline ND temporal", BAD), "ND temporal", "–", "+9.3"],
        ["Lehra / Zira / Moonak", "C", "–", "ND static", "0.79–0.81", "–"],
        ["Guruharsahai", "SW", "–", "ND static", "0.895", "–"],
        ["Batala / Majitha", "C", "–", "ND temporal", "–", "+9.9 / +7.7"]]
table(s, M, TOP, W - 2 * M, rows, [3.2, 0.9, 2.9, 2.2, 1.5, 1.43], size=13, row_h=0.45)

s = new("Backup")
title(s, "B4 · Cut-off 0.79 vs 0.5")
stat(s, M, TOP + 0.3, 4, "0.84–0.98", "rank agreement of tehsils between\nthe two cut-offs (81 tehsils, by year)",
     big_size=44)
bullets(s, 5.2, TOP + 0.3, 7.5, 4.5, [
    ("The cut-off changes the level, not the order: ", "at 0.5 every tehsil burns more, but tehsils "
     "keep almost the same ranks."),
    ("PD identification depends on order within a group, ", "so the PD list is not driven by the cut-off "
     "choice (full 0.5 re-run is part of PD validation)."),
    ("Walker trade-off: ", "0.79 → 90% burns caught, 18% ploughed called burnt; 0.5 → 97.5% and 51%."),
], size=16, gap=10)

prs.save(OUT)
print(f"Saved {OUT} ({len(prs.slides)} slides)")
