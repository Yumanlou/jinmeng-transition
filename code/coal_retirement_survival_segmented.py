#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精细时间分段 Cox：看高煤省退役 hazard 比在各政策阶段的演变。"""
import csv, os
import pandas as pd
from lifelines import CoxPHFitter

ROOT = "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
GEM = os.path.join(ROOT, "data/gem_power_project_lifecycle/gem_china_project_units_2026_snapshot.csv")
MAIN = os.path.join(ROOT, "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_leadership_0721.csv")
OUT = os.path.join(ROOT, "result", "tables", "0820_coal_retirement_survival")

CENSOR = 2026.0
EXCLUDE = {"cancelled", "construction", "announced", "shelved", "permitted", "pre-permit", "mothballed"}

# 时间分段：(窗口起点, 窗口终点)
WINDOWS = [
    ("2000-2011 上大压小", 2000, 2011),
    ("2012-2015 绿贷早期", 2012, 2015),
    ("2016-2020 供给侧", 2016, 2020),
    ("2021-2025 双碳", 2021, 2025),
]


def load_coalexp():
    m = {}
    for r in csv.DictReader(open(MAIN, encoding="utf-8-sig")):
        p, c = r.get("province"), r.get("coalexp_pre")
        if p and c not in (None, ""):
            try:
                m[p] = float(c)
            except ValueError:
                pass
    return m


def load_units(coalexp):
    recs = []
    for r in csv.DictReader(open(GEM, encoding="utf-8-sig")):
        if r["asset"] != "coal" or r["status"] in EXCLUDE:
            continue
        if r["start_year"] in (None, ""):
            continue
        sy = float(r["start_year"])
        prov = r["province"]
        if prov not in coalexp:
            continue
        ry = r["retired_year"]
        cap = float(r["capacity_mw"]) if r["capacity_mw"] not in (None, "") else float("nan")
        ret = float(ry) if ry not in (None, "") else None
        if ret is not None and ret < sy:
            continue
        recs.append({"ce": coalexp[prov], "start": sy, "ret": ret, "cap": cap})
    return recs


def main():
    coalexp = load_coalexp()
    recs = load_units(coalexp)

    rows_out = []
    for name, w0, w1 in WINDOWS:
        df_rows = []
        for x in recs:
            sy = x["start"]
            if sy > w1:  # 窗口结束前还没投产
                continue
            entry = max(0.0, w0 - sy)
            if x["ret"] is not None and x["ret"] <= w1:
                dur = x["ret"] - sy
                ev = 1
            else:
                dur = (w1 + 1) - sy  # 到窗口结束（含当年）仍存活 → 删失
                ev = 0
            if dur <= entry:
                continue
            df_rows.append({"entry": entry, "dur": dur, "ev": ev,
                            "ce": x["ce"], "cap": x["cap"], "start": sy})
        df = pd.DataFrame(df_rows)
        if len(df) < 50 or df["ev"].sum() < 5:
            print(f"[{name}] 样本{len(df)} 事件{df['ev'].sum()} → 跳过（太少）")
            continue
        cph = CoxPHFitter()
        cph.fit(df, duration_col="dur", event_col="ev", entry_col="entry",
                formula="ce + cap + start")
        import math
        coef = cph.params_["ce"]
        hr = math.exp(coef)
        p = cph.summary.loc["ce", "p"]
        print(f"[{name}] 样本{len(df)} 事件{int(df['ev'].sum())} | "
              f"coalexp_pre 系数={coef:.3f}  hazard比={hr:.2f}  p={p:.4f}")
        rows_out.append({"window": name, "n": len(df), "events": int(df["ev"].sum()),
                         "coef": round(coef, 4), "hazard_ratio": round(float(hr), 3),
                         "p": round(float(p), 4)})

    with open(os.path.join(OUT, "segmented_cox.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["window", "n", "events", "coef", "hazard_ratio", "p"])
        w.writeheader()
        w.writerows(rows_out)
    print(f"\n分段结果已写 {OUT}/segmented_cox.csv")


if __name__ == "__main__":
    main()
