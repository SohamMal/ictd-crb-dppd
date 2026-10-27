"""Check the Sentinel-2 BAIS2+TCB burn detector against Soham's Planet labels (Jalandhar 2021).

Labels: outputs/planet/labels_v2_jalandhar_2021.csv (pilot, final = chat labels) +
        labels_v2_jalandhar_2021_p03-19.csv. Blank labels are skipped.
Event day per field: Soham's change_day where given; otherwise (burnt fields) the Planet day
with the largest one-step fall in relative brightness (relbright_v2_*), marked derived.
S2 series: outputs/burn_checks/charsoil_timeseries.csv (field medians, relaxed SCL 2/4/5/7),
scored with the same model as everywhere else (labelling_package.model()).

Questions
  burnt fields       flagged on the first clear S2 look after the burn? on any look in +0..+15 d?
  stubble / green    (no event to 13 Nov) flagged on any S2 look up to 13 Nov? -> false alarms
  ploughed / unclear described only (1 ploughed field)

Out: outputs/planet/s2check_looks.csv (field x S2 date), s2check_fields.csv, s2check_summary.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "burn"))
import labelling_package as lp  # noqa: E402

OUT = ROOT / "outputs" / "planet"
LABEL_DAY = pd.Timestamp("2021-10-29")
PLANET_END = pd.Timestamp("2021-11-13")


def labels():
    l = pd.concat([pd.read_csv(OUT / "labels_v2_jalandhar_2021.csv"),
                   pd.read_csv(OUT / "labels_v2_jalandhar_2021_p03-19.csv")], ignore_index=True)
    l["label"] = l.label.astype(str).str.strip().str.lower().replace("nan", np.nan)
    l = l.dropna(subset=["label"])
    rb = pd.concat([pd.read_csv(OUT / "relbright_v2_jalandhar_2021.csv"),
                    pd.read_csv(OUT / "relbright_v2_jalandhar_2021_p03-19.csv")], ignore_index=True)
    rb = rb[rb.clear_share >= 0.9].sort_values(["field_id", "day"])
    rb["fall"] = rb.groupby("field_id").rel_brightness.diff().mul(-1)
    biggest = rb.loc[rb.groupby("field_id").fall.idxmax().dropna()].set_index("field_id")
    ev, src, fall = [], [], []
    for _, r in l.iterrows():
        cd = str(r.change_day).strip()
        if cd and cd != "nan":
            ev.append(pd.to_datetime(cd.replace("th", "") + " 2021", format="mixed", dayfirst=True))
            src.append("soham"); fall.append(np.nan)
        elif r.label == "burnt" and r.field_id in biggest.index:
            ev.append(pd.Timestamp(biggest.loc[r.field_id, "day"]))
            src.append("derived_max_fall"); fall.append(biggest.loc[r.field_id, "fall"])
        else:
            ev.append(pd.NaT); src.append(""); fall.append(np.nan)
    l["event_day"], l["event_source"], l["event_fall"] = ev, src, fall
    return l[["field_id", "label", "event_day", "event_source", "event_fall", "note"]]


def s2_scores():
    d = pd.read_csv(ROOT / "outputs" / "burn_checks" / "charsoil_timeseries.csv")
    d = d[d.year == 2021].replace([np.inf, -np.inf], np.nan).dropna(subset=["BAIS2", "TCB"]).copy()
    sc, m = lp.model()
    d["z"] = m.decision_function(sc.transform(d[["BAIS2", "TCB"]].to_numpy()))
    d["flag"] = (d.z > 0).astype(int)
    d["date"] = pd.to_datetime(d.date)
    return d[["field_id", "field_category", "date", "BAIS2", "TCB", "z", "flag"]]


def main():
    l = labels()
    s = s2_scores()
    looks = s.merge(l, on="field_id")
    looks["days_from_event"] = (looks.date - looks.event_day).dt.days
    looks.to_csv(OUT / "s2check_looks.csv", index=False)

    rows = []
    for fid, g in looks.groupby("field_id"):
        r = g.iloc[0]
        rec = {"field_id": fid, "label": r.label, "event_day": r.event_day, "event_source": r.event_source}
        win = g[(g.date >= LABEL_DAY) & (g.date <= PLANET_END)]
        rec["s2_looks_29oct_13nov"] = len(win)
        rec["flag_any_29oct_13nov"] = int(win.flag.max()) if len(win) else np.nan
        on = g[g.date == LABEL_DAY]
        rec["flag_29oct"] = int(on.flag.iloc[0]) if len(on) else np.nan
        if pd.notna(r.event_day):
            after = g[g.days_from_event > 0].sort_values("date")
            rec["first_look_after"] = after.date.iloc[0] if len(after) else pd.NaT
            rec["flag_first_after"] = int(after.flag.iloc[0]) if len(after) else np.nan
            w = g[(g.days_from_event > 0) & (g.days_from_event <= 15)]
            rec["flag_any_1_15d"] = int(w.flag.max()) if len(w) else np.nan
            pre = g[(g.days_from_event <= 0) & (g.date >= LABEL_DAY)]
            rec["flag_any_before_event"] = int(pre.flag.max()) if len(pre) else np.nan
        rows.append(rec)
    f = pd.DataFrame(rows)
    f.to_csv(OUT / "s2check_fields.csv", index=False)

    summ = []
    for lab, g in f.groupby("label"):
        summ.append({"label": lab, "fields": len(g),
                     "flagged_29oct": g.flag_29oct.mean(),
                     "flagged_any_29oct_13nov": g.flag_any_29oct_13nov.mean(),
                     "flagged_first_look_after_event": g.get("flag_first_after", pd.Series(dtype=float)).mean(),
                     "flagged_any_1_15d_after_event": g.get("flag_any_1_15d", pd.Series(dtype=float)).mean(),
                     "flagged_before_event": g.get("flag_any_before_event", pd.Series(dtype=float)).mean()})
    summ = pd.DataFrame(summ).round(3)
    summ.to_csv(OUT / "s2check_summary.csv", index=False)
    pd.set_option("display.width", 220)
    print(l.groupby(["label", "event_source"], dropna=False).size())
    print(summ.to_string(index=False))
    print(f[f.label.isin(["burnt", "ploughed", "stubble", "green"])].sort_values("label").to_string(index=False))
    print("\nS2 looks per date (labelled fields):")
    print(looks.groupby("date").field_id.nunique().to_string())


if __name__ == "__main__":
    main()
