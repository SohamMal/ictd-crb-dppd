"""
Final presentation deck (2026-11-25, 15 min): 22 main slides + 7 backup.

Content follows report/final_deck_outline.md. Numbers come from report/report_draft.md and the outputs it
cites; figures from make_final_figures.py (+ make_grouping_figures.py / make_pd_figures.py).
Helpers and style are copied from make_a3_deck.py so both decks look the same.

Run:  python Code/figures/make_final_deck.py
Out:  report/final_deck.pptx
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
OUT = ROOT / "report" / "final_deck.pptx"

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
TOTAL = 27


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
notes(s, "Fifteen minutes: who burns less than their peers, why we trust that, why they burn less, "
         "and what to do about it.")

# ---------- 2. Problem ----------
s = S("The problem", "Punjab burns over half its paddy straw every autumn")
image(s, FIG / "fig_G_burn_map.png", M, TOP + 0.1, 5.6, 5.4, align="left")
caption(s, M, 6.95, 5.6, "Our measure: share of sample rice points burnt, mean 2020–24, by tehsil")
stat(s, 6.8, TOP + 0.3, 5.8, "52–64%", "of paddy area burnt each season, 2019–23\n(our Sentinel-2 measure)",
     big_size=48)
bullets(s, 6.8, TOP + 2.2, 5.9, 3.2, [
    ("Why burn: ", "harvest to wheat sowing leaves only a few weeks; fire is the cheapest way to clear straw."),
    ("Despite: ", "CRM machine subsidies since 2018, custom hiring centres, short-duration varieties."),
    ("But uneven: ", "places that look alike burn very differently. Some may already have an answer."),
], size=17, gap=10)
notes(s, "Burning is a major seasonal source of pollution in the Indo-Gangetic Plain and Delhi NCR (§1).")

# ---------- 3. The clock ----------
s = S("The problem", "From paddy to wheat in a few weeks")
image(s, FF / "f01_season_field.png", M, TOP + 0.35, W - 2 * M, 3.1)
caption(s, M, TOP + 3.55, W - 2 * M, "Sentinel-2 true colour, one sample point in Central Punjab, 2022 "
        "(magenta box = the 10 m point).")
panel(s, M, 5.45, W - 2 * M, 1.3)
text(s, M + 0.3, 5.5, W - 2 * M - 0.6, 1.2, [
    [("Median turnaround: 14–22 days ", {"bold": True, "color": EMBER}),
     ("from paddy harvest to wheat sowing (2020–24, checked against the CIMMYT farmer survey). "
      "The straw has to go in that window.", {})]], size=17, anchor=MSO_ANCHOR.MIDDLE, margin=0)
notes(s, "Harvest ≈ 22–26 Oct; South-west harvests about a week later than Central.")

# ---------- 4. Fire counts ----------
s = S("The problem", "Fire counts are no longer a reliable way to measure burning")
image(s, FF / "f02_viirs_collapse.png", M, TOP + 0.2, 8.4, 3.4, align="left")
caption(s, M, TOP + 3.7, 8.4, "Left: VIIRS active fires (FIRMS) summed over our 97 tehsils. "
        "Right: our field-level Sentinel-2 measure.")
stat(s, 9.4, TOP + 0.2, 3.4, "−91%", "VIIRS fires 2021 → 2024", color=BAD, big_size=48)
bullets(s, 9.4, TOP + 1.9, 3.4, 3.2, [
    "Farmers now burn after the satellite's afternoon pass.",
    "Fire counts also miss ~3 of 4 burns seen by Sentinel-2.",
    ("We need a field-level measure ", "that cannot be dodged."),
], size=15, gap=8)
notes(s, "2024 is a doubtful season for our measure too (72% of burns seen after 15 Nov), "
         "so we never rely on it alone.")

# ---------- 5. Answer ----------
s = S("The answer", "Abohar and a Doaba belt burn far less than places like them")
image(s, FF / "f03_pd_map.png", M, TOP - 0.05, 7.6, 5.7, align="left")
card(s, 8.45, TOP + 0.1, 4.28, 1.7, "Abohar (South-west)", "burns 34% vs group median 73%; also among the "
     "fastest to reduce", head_color=GOOD, size=15)
card(s, 8.45, TOP + 2.0, 4.28, 1.7, "Doaba belt (Central)", "Dinanagar, Phagwara, Jalandhar-I, Adampur: "
     "about half the Central median", head_color=GOOD, size=15)
text(s, 8.45, TOP + 3.95, 4.28, 1.4, "Question: which of Punjab's 97 tehsils burn much less paddy straw "
     "than structurally similar peers, and why?", size=14, color=MUTED, italic=True, margin=0)
notes(s, "Answer first; the rest of the talk is why we believe it, why they differ, and what to do.")

# ---------- M0. Pipeline ----------
s = S("Method", "How we did it: the DPPD pipeline, step by step")
steps = [("1", "Peer groups", "Gower distance on 5 structural dimensions → hierarchical clustering → 3 groups",
          "Frozen before any burning data"),
         ("2", "Burn measure", "Sentinel-2 flag → candidate look → before/after → random forest; 100 points per tehsil",
          "Burnt vs ploughed separated"),
         ("3", "Find PDs", "Log-scale IQR fence within each group: static (level) and temporal (trend)",
          "Two season runs; strict rule"),
         ("4", "Validate", "Bootstrap, other settings, cloud gaps, rice map, real paddy, harvest timing",
          "On the data; no fieldwork"),
         ("5", "Drivers", "9 public drivers: rank correlation, partial (rice held constant), PD/ND sides",
          "Leads, not causes")]
bw = (W - 2 * M - 4 * 0.22) / 5
for i, (k, h_, b_, r_) in enumerate(steps):
    x = M + i * (bw + 0.22)
    panel(s, x, TOP + 0.2, bw, 4.6)
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.18), Inches(TOP + 0.4), Inches(0.55), Inches(0.55))
    fill(c, EMBER)
    text(s, x + 0.18, TOP + 0.4, 0.55, 0.55, k, size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, margin=0)
    text(s, x + 0.18, TOP + 1.1, bw - 0.36, 0.45, h_, size=18, bold=True, margin=0)
    text(s, x + 0.18, TOP + 1.65, bw - 0.36, 2.2, b_, size=14, margin=0)
    text(s, x + 0.18, TOP + 3.95, bw - 0.36, 0.7, r_, size=13, color=GOOD, bold=True, margin=0)
text(s, M, 6.55, W - 2 * M, 0.5, "Hard rules: groups use only conditions a tehsil cannot change; burning data never "
     "enters grouping; every number comes from code in the repository.", size=14, color=MUTED, italic=True, margin=0)
notes(s, "Follows the DPPD handbook (Albanna et al. 2021). Grouping was done before measurement on purpose.")

# ---------- 6. Peers ----------
s = S("A · Fair peers", "Peers are built only from conditions a tehsil cannot change",
      "No machines, mandis or policies, and no burning data. Frozen before burning was measured.")
image(s, FF / "f04_grouping_variables.png", M, TOP + 0.6, W - 2 * M, 3.6)
bullets(s, M, 5.55, W - 2 * M, 1.4, [
    ("Distance: ", "dimension-balanced Gower (each of the 5 dimensions gets one equal vote)."),
    ("Clustering: ", "average-linkage hierarchical; stable under resampling (ARI 0.89) and ±15% weights."),
], size=16, gap=6)
notes(s, "Rice share calibrated to official district rice area (Chen map was biased by region). "
         "DPPD rule: grouping on drivers would hide the deviance we want to find.")

# ---------- M1. Gower worked example ----------
s = S("A · Fair peers", "Step 1: how alike are two tehsils? (dimension-balanced Gower)")
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
card(s, 9.2, TOP + 2.0, 3.53, 1.75, "Categories", "same = 0, different = 1 (soil: average of its 8)", size=14)
card(s, 9.2, TOP + 3.9, 3.53, 1.75, "Balanced", "average inside each dimension first, so soil's 8 columns get 1 vote, "
     "not 8", size=14)
text(s, M, TOP + 4.2, 8.3, 1.2, "Phagwara and Adampur differ mainly in soil, so they are close (0.24) and land in the "
     "same group. Abohar differs on every dimension (0.51).", size=15, margin=0)
notes(s, "Why Gower: the variables mix numbers and categories. Why balanced: plain Gower would let soil "
         "(8 columns) outvote rainfall (1). Dhar Kalan is left out when computing ranges.")

# ---------- M2. Clustering ----------
s = S("A · Fair peers", "Step 2: merge the closest tehsils, then choose where to cut")
image(s, FIG / "fig_B_dendrogram.png", M, TOP + 0.05, 7.4, 3.3, align="left")
caption(s, M, TOP + 3.4, 7.4, "Average-linkage tree of all 97 tehsils; dashed line = cut into 3 groups + outlier")
image(s, FIG / "fig_D_choosing_k.png", M, TOP + 3.75, 7.4, 1.9, align="left")
stat(s, 8.4, TOP + 0.05, 4.3, "0.377", "silhouette at k = 3 (how well each tehsil sits in its group)", big_size=34)
stat(s, 8.4, TOP + 1.55, 4.3, "0.890", "bootstrap ARI: regroup 300 random 80% samples; 1 = identical", big_size=34)
bullets(s, 8.4, TOP + 3.15, 4.33, 2.5, [
    ("Average linkage: ", "works on any distance matrix; no forced round or equal groups."),
    ("Sensitivity: ", "each weight ±15%, each dimension dropped; 8 of 10 weight changes keep ARI ≥ 0.83."),
    ("Weak point: ", "the South-west / Central border, so PDs are also checked under a 2-group split."),
], size=13, gap=5)
notes(s, "Borderline tehsils (switch group in > 20% of resamples) get their consensus group.")

# ---------- 7. Groups ----------
s = S("A · Fair peers", "Three peer regions emerge, though no location was given")
image(s, FIG / "fig_A_group_map.png", M, TOP, 6.2, 5.6, align="left")
rows = [["Group", "Tehsils", "Rice share", "Monsoon rain"],
        [("Central", GROUP["Central"]), "63", "75%", "721 mm"],
        [("South-west", GROUP["South-west"]), "18", "59%", "467 mm"],
        [("Foothills", GROUP["Foothills"]), "15", "28%", "981 mm"]]
table(s, 7.2, TOP + 0.4, 5.53, rows, [1.8, 1.1, 1.3, 1.33], size=15, row_h=0.55)
caption(s, 7.2, TOP + 2.7, 5.53, "Group medians; Dhar Kalan (hill outlier) set aside")
text(s, 7.2, TOP + 3.3, 5.53, 1.8, "Central plains, dry Malwa south-west and Kandi foothills: real "
     "agro-ecological belts. Each tehsil is compared only with its own group.", size=17, margin=0)
notes(s, "Foothills are measured but not ranked: only 15 tehsils and the weakest validation.")

# ---------- 8. Burnt vs ploughed ----------
s = S("A · Measuring burning", "Burnt and ploughed fields soon look alike")
image(s, FF / "f05_planet_burnt_vs_ploughed.png", M, TOP + 0.2, W - 2 * M, 4.3)
caption(s, M, TOP + 4.6, W - 2 * M, "PlanetScope 3 m daily images, Jalandhar 2021, CEEW fields (cyan outline). "
        "Top: goes black, then fades to soil colour. Bottom: ploughed, never black.")
text(s, M, 6.55, W - 2 * M, 0.5, [[("A season-long burn index flagged 81% of ploughed, unburnt fields as burnt.",
                                     {"bold": True, "color": BAD})]], size=17, margin=0)
notes(s, "Walker et al. ground truth: 98% of burns caught but 81% of ploughed-not-burnt fields flagged. "
         "A tehsil that ploughs instead of burning would look like a burner.")

# ---------- 9. Ash fades ----------
s = S("A · Measuring burning", "Planet sees every day; Sentinel-2 saw this field on 2 of 10")
image(s, FF / "f06_planet_vs_s2.png", M, TOP + 0.05, W - 2 * M, 3.2)
caption(s, M, TOP + 3.3, W - 2 * M, "Same burnt field, every PlanetScope day 30 Oct – 9 Nov 2021. "
        "Orange frame = a clear Sentinel-2 pass that day.")
card(s, M, 5.05, 5.9, 1.75, "Sentinel-2 (free, 10 m, every 5 days)",
     "Often sees the field only after the ash has faded: char and fresh soil look the same (AUC 0.51).", size=15)
card(s, M + 6.25, 5.05, 5.9, 1.75, "PlanetScope (daily, 3 m, limited quota)",
     "Sees the dark days and separates ash from soil (AUC 0.96). Used as an independent judge.", size=15)
notes(s, "Also tried and rejected: land surface temperature (ash not hotter than soil) and Sentinel-1 radar "
         "roughness (Basma's suggestion; 12-day revisit, moved the wrong way on ploughed fields).")

# ---------- M3. Detector method ----------
s = S("A · Measuring burning", "Our detector: flag, pick the sudden change, let a forest decide")
image(s, FF / "f19_detector_series.png", M, TOP + 0.05, W - 2 * M, 3.75)
caption(s, M, TOP + 3.85, W - 2 * M, "Two real sample points in Lehra, 2022. Both cross the flag line; only the "
        "sudden jump is judged a burn.")
card(s, M, 5.75, 4.0, 1.3, "1 · Flag", "BAIS2 (red-edge burn index) + TCB (brightness), fitted on 438 CEEW fields: "
     "score > 0", size=12)
card(s, M + 4.1, 5.75, 4.0, 1.3, "2–3 · Candidate + before/after", "largest rise in score; compare 14 bands and "
     "indices with the last clear look ≤ 20 days earlier", size=12)
card(s, M + 8.2, 5.75, 3.93, 1.3, "4 · Random forest", "500 trees, trained on Walker et al. 2,204 burnt vs 223 "
     "ploughed fields; burnt if p ≥ 0.79", size=12)
notes(s, "Why the jump: burning darkens a field overnight; drying and harvest change it gradually. "
         "Cut-off 0.79 keeps 90% of Walker's burns; 0.5 is the sensitivity check.")

# ---------- 10. Detector ----------
s = S("A · Measuring burning", "How good is it? Ploughing false alarms fall from 81% to 18%")
steps = [("1", "Flag", "burn index > 0 on a clear look"), ("2", "Candidate", "the sharpest jump: burning is sudden"),
         ("3", "Before / after", "compare bands and indices with the look before"),
         ("4", "Decide", "random forest trained on 2,204 burnt + 223 ploughed fields")]
bw = 1.72
for i, (k, h_, b_) in enumerate(steps):
    y = TOP + 0.15 + i * 1.32
    panel(s, M, y, 5.6, 1.15)
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(M + 0.18), Inches(y + 0.3), Inches(0.55), Inches(0.55))
    fill(c, EMBER)
    text(s, M + 0.18, y + 0.3, 0.55, 0.55, k, size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, margin=0)
    text(s, M + 0.95, y + 0.12, 4.5, 0.4, h_, size=17, bold=True, margin=0)
    text(s, M + 0.95, y + 0.55, 4.5, 0.5, b_, size=14, color=MUTED, margin=0)
image(s, FF / "f07_detector_bars.png", 6.5, TOP + 0.1, 6.2, 4.2)
caption(s, 6.5, TOP + 4.35, 6.2, "Walker et al. ground truth, 5-fold cross-validation")
text(s, 6.5, TOP + 4.75, 6.2, 0.8, [[("New district and year, not retrained: ", {"bold": True}),
     ("CEEW unburnt fields called burnt 28/95 → 1–2/95 (Jalandhar 2021).", {})]], size=14, margin=0)
notes(s, "Cost: it misses partial burns. Fine for DPPD if the miss rate is similar across tehsils (stated assumption).")

# ---------- 11. Points ----------
s = S("A · Measuring burning", "From fields to tehsils: 100 points per tehsil")
image(s, FF / "f08_points_two_tehsils.png", M, TOP + 0.05, 8.6, 5.55, align="left")
mp, ml = meta("tehsil_phagwara.json"), meta("tehsil_lehra.json")
caption(s, M, 7.0, 8.6, f"Sentinel-2 true colour, cloud-free {mp['date']}, with each point's 2022 verdict")
bullets(s, 9.5, TOP + 0.4, 3.25, 5, [
    ("100 rice pixels ", "per tehsil (rice in both 2020 and 2022 maps), same points every season."),
    ("Tehsil value ", "= share of its points burnt."),
    ("≥ 97% ", "of points get a verdict each season."),
], size=17, gap=14)
notes(s, "Points are pixels that are rice in both the Chen 2020 and 2022 maps; the same panel is read every season, so year-to-year change is not sampling noise.")

# ---------- 12. Holds up ----------
s = S("A · Measuring burning", "The tehsil measure matches fire counts and is stable")
image(s, FIG / "fig_H_burn_vs_viirs.png", M, TOP + 0.05, 5.2, 3.7, align="left")
caption(s, M, TOP + 3.8, 5.2, "Our burnt share vs VIIRS fires per 1,000 ha rice, 2021")
stat(s, 6.3, TOP + 0.05, 3.0, "ρ 0.78–0.87", "rank agreement with VIIRS,\n2019–23", big_size=28)
stat(s, 9.6, TOP + 0.05, 3.1, "ρ 0.82–0.91", "same ranks year after year", big_size=28)
image(s, FF / "f09_yearly_maps.png", 6.2, TOP + 1.7, 6.5, 2.3)
caption(s, 6.2, TOP + 4.0, 6.5, "Burnt share by tehsil, 2020–24: the same places stay low or high")
text(s, M, 6.3, W - 2 * M, 0.6, "Official CREAMS 2022: district ρ 0.87. Weak spot: 2024, so every result is "
     "also checked on 2020–23.", size=14, color=MUTED, margin=0)
notes(s, "Agreement with VIIRS is reassuring but not proof, since farmers time fires to dodge the overpass.")

# ---------- 13. PD rule ----------
s = S("B · Positive deviants", "A positive deviant lies beyond its own group's fence")
image(s, FIG / "fig_I_pd_fences.png", M, TOP + 0.05, 8.2, 4.2, align="left")
caption(s, M, TOP + 4.3, 8.2, "Each dot = a tehsil's mean burnt share 2020–24 (log scale). Hollow = Doaba tehsils.")
bullets(s, 9.1, TOP + 0.1, 3.65, 5.4, [
    ("Scale: ", "log(share + c), c = 10% of group median: halving counts the same at any level."),
    ("Static PD: ", "5-season mean below Q1 − 1.5 × IQR of its group, and in the bottom quarter in 4 of 5 seasons."),
    ("Temporal PD: ", "Theil–Sen trend minus the group's median trend, beyond the same fence."),
    ("Strict: ", "beyond the fence in both 2020–24 and 2020–23."),
], size=14, gap=7)
notes(s, "Static deviance = burns least; temporal (Basma) = falls fastest vs group trend. "
         "Doaba tehsils sit together, so the fence treats them as part of the normal spread.")

# ---------- 14. Abohar ----------
s = S("B · Positive deviants", "Abohar burns far less than its group in every season")
image(s, FF / "f10_abohar_vs_group.png", M, TOP + 0.05, 7.8, 4.6, align="left")
stat(s, 8.9, TOP + 0.2, 3.8, "0.34 vs 0.73", "Abohar vs South-west median,\nmean 2020–24", color=GOOD, big_size=34)
stat(s, 8.9, TOP + 1.9, 3.8, "−11% / yr", "burning trend relative to its group", color=GOOD, big_size=34)
text(s, 8.9, TOP + 3.6, 3.8, 1.2, "The only tehsil that is a deviant on both level and trend.",
     size=16, margin=0)
notes(s, "Abohar is the only strict PD.")

# ---------- M4. Validation design ----------
s = S("B · Positive deviants", "Before trusting a PD: six checks on the data, fixed in advance")
rows = [["Check", "Question", "How", "Pass rule"],
        ["V1 Resampling", "Luck of the 100 points?", "redraw verdicts 1,000×, rerun", "flag kept ≥ 80%"],
        ["V2 Settings", "Depends on our choices?", "cut 0.5; offset 5% / 20%; other grouping", "kept in all but one"],
        ["V3 Clear looks", "Do clouds hide fires?", "unknown points, looks per point", "≤ 2× group median"],
        ["V4 Rice map", "Less paddy to burn?", "rice share; harvest seen at points", "not below group Q1"],
        ["V4b Real paddy", "Non-paddy points pulling it down?", "score only harvest-confirmed points", "flag survives"],
        ["V5 Timing", "Harvest after the window?", "median harvest vs group", "< 10 days later"]]
table(s, M, TOP + 0.1, W - 2 * M, rows, [2.4, 3.6, 3.9, 2.23], size=14, row_h=0.56)
text(s, M, TOP + 4.25, W - 2 * M, 0.9, [[("Label: ", {"bold": True, "color": EMBER}),
     ("any fail → dropped; at most one flag → validated PD; more → PD with caveat. "
      "VIIRS and CREAMS used for triangulation only.", {})]], size=15, margin=0)
notes(s, "Handbook pp. 67-68: check a deviant is a real signal before fieldwork. A planned blind visual check (V7) "
         "was not done; stated as a limitation.")

# ---------- 15. Validation ----------
s = S("B · Positive deviants", "Low burners survive every check; fast reducers do not")
image(s, FF / "f11_validation_grid.png", M, TOP + 0.05, 8.4, 5.4, align="left")
bullets(s, 9.3, TOP + 0.3, 3.45, 5, [
    ("Resampling: ", "PDs keep their flag in ≥ 89% of resamples."),
    ("Trends ", "from 5 seasons × 100 points are too noisy: Samana, Dirba kept in only 4 of 10."),
    ("! = warning, ", "checked further (rice map, next slide)."),
], size=15, gap=10)
notes(s, "Checks V1–V5: bootstrap, alternative settings (cut 0.5, offset, Plains grouping), clear looks, "
         "rice map, harvest-confirmed rescoring, harvest timing (report Table 7).")

# ---------- 16. Rice ----------
s = S("B · Positive deviants", "Not just less rice: PDs stay low on real paddy fields")
image(s, FF / "f12_burn_vs_rice.png", M, TOP + 0.05, 7.6, 4.9, align="left")
caption(s, M, TOP + 5.0, 7.6, "Each dot = a tehsil. Green rings = PDs, red rings = negative deviants.")
bullets(s, 8.6, TOP + 0.3, 4.1, 5, [
    ("Warning: ", "more rice, more burning, even inside a group (ρ 0.70 Central)."),
    ("Check: ", "score only points where a paddy harvest is seen."),
    ("Result: ", "Abohar 0.45 vs 0.73; Dinanagar 0.25 vs 0.62. The PDs stay low."),
], size=16, gap=10)
notes(s, "So rice share is treated as structural and held constant in Stage 3.")

# ---------- M5. Driver method ----------
s = S("C · Why they burn less", "Stage 3: nine public drivers, tested three ways")
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
card(s, 8.3, TOP + 3.25, 4.43, 1.45, "3 · Rice held constant", "partial ρ: remove rice share's rank from both, "
     "then correlate", size=13)
text(s, 8.3, TOP + 4.85, 4.43, 0.8, "8 PDs, 4 NDs, 44 tests → only patterns that repeat across all three readings "
     "count.", size=13, color=MUTED, margin=0)
notes(s, "Drivers are things that could change or transfer; structural conditions are never re-used as drivers.")

# ---------- 17. Drivers ----------
s = S("C · Why they burn less", "Only urban surroundings line up; others restate rice")
image(s, FF / "f13_drivers.png", M, TOP + 0.05, 7.8, 5.2, align="left")
bullets(s, 8.8, TOP + 0.3, 3.95, 5.2, [
    ("Urban share: ", "7 of 8 PDs above their group median, all 4 NDs below."),
    ("Turnaround, small farms: ", "link vanishes once rice share is held constant."),
    ("Surprise: ", "in the South-west, tehsils near the state border burn less (cotton belt)."),
], size=15, gap=10)
notes(s, "Nine candidate drivers from public online data, no fieldwork. Border effect runs opposite to "
         "Dipoppa & Gulzar. District CRM machine data was not available online.")

# ---------- 18. Doaba ----------
s = S("C · Why they burn less", "Doaba burns little as a region, not near towns")
image(s, FF / "f14_doaba_far_fields.png", M, TOP + 0.05, 7.6, 4.3, align="left")
caption(s, M, TOP + 4.4, 7.6, "Share of points burnt, 2020–24: all fields vs fields more than 5 km from any town")
bullets(s, 8.6, TOP + 0.3, 4.1, 5, [
    "Fields within 2 km of a town burn 6–8 points less, but only 4% of fields are that close.",
    "Far from towns, the Doaba PDs burn just as little.",
    ("So read urban share as a marker ", "of the Doaba region: potato and vegetable rotations, off-farm and "
     "overseas income."),
], size=15, gap=10)
notes(s, "A transferable practice would have to be found inside the region, e.g. what farmers do with "
         "straw before an October potato crop. Only fieldwork can show that.")

# ---------- 20. Abohar profile ----------
s = S("C · Why they burn less", "Abohar: straw buyer, labour, livestock, early second crop")
image(s, FF / "f15_abohar_profile.png", M, TOP + 0.05, 7.6, 4.4, align="left")
bullets(s, 8.6, TOP + 0.3, 4.1, 5, [
    ("A biomass power plant ", "inside the tehsil: an assured straw buyer."),
    ("Most farm labourers per cultivator ", "in Punjab; most cattle per cultivator in its group."),
    ("One tehsil: ", "these cannot be separated. A lead for fieldwork, not a finding."),
], size=15, gap=10)
notes(s, "Percentiles within the South-west group (report §4.4). 13 km from the Rajasthan border.")

# ---------- 21. So what ----------
s = S("D · So what", "What to do, and how we would test it")
cards = [("Where to look", "Abohar and the Doaba tehsils first; heavy burners as comparison."),
         ("What to test", "Assured straw buyer, labour for straw handling, fodder demand."),
         ("How to target", "Rank within peer groups and allow for rice share."),
         ("How to monitor", "Rerun the free Sentinel-2 detector every December.")]
cw = 2.85
for i, (h_, b_) in enumerate(cards):
    card(s, M + i * (cw + 0.21), TOP + 0.05, cw, 1.75, h_, b_, head_color=GOOD, size=14)
flow = [("Phase 1", "Field validation, 1 season: PD, ND and typical villages; farmer survey; ground-truth photos"),
        ("Phase 2", "Pilot confirmed levers in matched villages of non-PD tehsils, randomised within pairs"),
        ("Measure", "Satellite burnt share (primary) + survey with a list experiment")]
fw = 2.35
for i, (h_, b_) in enumerate(flow):
    x = M + i * (fw + 0.35)
    panel(s, x, 3.55, fw, 2.95)
    text(s, x + 0.15, 3.65, fw - 0.3, 0.4, h_, size=17, bold=True, color=EMBER, margin=0)
    text(s, x + 0.15, 4.1, fw - 0.3, 2.3, b_, size=14, margin=0)
    if i < 2:
        arrow(s, x + fw + 0.02, 4.85, w=0.3, h=0.3)
image(s, FF / "f16_sample_size.png", 8.7, 3.45, 4.05, 2.85)
caption(s, 8.7, 6.35, 4.05, "~30 villages per arm to detect a 10-point drop (35 pairs per lever)")
notes(s, "Impact assessment proposal (report §8): theory of change, logframe, survey modules, sample size. "
         "Frame: 1,633 South-west villages outside Abohar.")

# ---------- 22. Limits + takeaways ----------
s = S("Limits and takeaways", "Limits, and three takeaways", dark=False)
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
notes(s, "With field access, more PlanetScope quota and CRM data, the same pipeline would give firmer answers.")

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

s = backup("B2 · Grouping: dendrogram, choice of k, sensitivity")
image(s, FIG / "fig_B_dendrogram.png", M, TOP, 6.2, 2.9, align="left")
image(s, FIG / "fig_D_choosing_k.png", M, TOP + 3.0, 6.2, 2.6, align="left")
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

s = backup("B6 · Pilot sample size")
image(s, FF / "f16_sample_size.png", M, TOP, 6.3, 4.3, align="left")
bullets(s, 7.3, TOP + 0.2, 5.43, 5, [
    "ANCOVA on village baseline, 80% power, 5% two-sided, 2023 as pilot season, 30 points per village.",
    "Between-village spread set at 1×, 2×, 3× the tehsil value; steadiness 0.9 / 0.7 / 0.5 (assumptions).",
    "Middle case 30 per arm → 35 pairs (70 villages) per lever; pessimistic 52.",
    "Recompute after Phase 1 measures village-level spread.",
], size=15, gap=8)

s = backup("B7 · Survey modules and logframe")
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

# ---------- 19. Landscapes ----------
s = backup("B8 · What the landscapes look like from space")
mm = {k: meta(f"s2_{k}.json") for k in ["phagwara", "lehra", "abohar", "guruharsahai"]}
iw = (W - 2 * M - 0.6) / 4
for i, (k, lab, col) in enumerate([("phagwara", "Phagwara · PD", GOOD), ("lehra", "Lehra · ND", BAD),
                                   ("abohar", "Abohar · PD", GOOD), ("guruharsahai", "Guruharsahai · ND", BAD)]):
    x = M + i * (iw + 0.2)
    text(s, x, TOP + 0.05, iw, 0.4, lab, size=17, bold=True, color=col, margin=0)
    image(s, RAWF / f"s2_{k}.png", x, TOP + 0.5, iw, iw)
    caption(s, x, TOP + 0.55 + iw, iw, f"{mm[k]['date']} · {mm[k]['box_km']:.0f} km box")
text(s, M, TOP + 1.1 + iw, (W - 2 * M) / 2, 0.8, "Central: Doaba PD vs heavy burner. Mixed fields, more green.",
     size=14, color=MUTED, margin=0)
text(s, M + (W - 2 * M) / 2 + 0.1, TOP + 1.1 + iw, (W - 2 * M) / 2, 0.8, "South-west: Abohar's orchards and cotton vs "
     "solid harvested paddy.", size=14, color=MUTED, margin=0)
notes(s, "Sentinel-2 true colour, same stretch for all four. Illustration only; drivers are tested on slide 17.")


prs.save(OUT)
print(f"Saved {OUT} ({len(prs.slides)} slides)")
