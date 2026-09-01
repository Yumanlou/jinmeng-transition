#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEM 煤电退役的分段 Cox 生存分析（lifelines）。

回答：2012 绿色信贷后，高煤省的煤电退役 hazard 是否相对下降（结构替代更慢）？

设计：
  - 分析1（政策前 2000-2011）：出生到退役/2011，比较高煤 vs 低煤 hazard（基准：上大压小淘汰落后产能）。
  - 分析2（政策后 2012-2025，左截断）：2012 存量机组从 2012 起观察，比较高煤 vs 低煤 hazard。
对比两次 coalexp_pre 系数：若政策前显著为正、政策后减弱/反转，则支持"政策让高煤省退役相对放缓"。
"""
import csv, os
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.statistics import logrank_test
from lifelines import KaplanMeierFitter

ROOT = "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
GEM = os.path.join(ROOT, "data/gem_power_project_lifecycle/gem_china_project_units_2026_snapshot.csv")
MAIN = os.path.join(ROOT, "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_leadership_0721.csv")
OUT = os.path.join(ROOT, "result", "tables", "0820_coal_retirement_survival")
os.makedirs(OUT, exist_ok=True)

CENSOR = 2026.0
EXCLUDE = {"cancelled", "construction", "announced", "shelved", "permitted", "pre-permit", "mothballed"}


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
        ry = r["retired_year"]
        prov = r["province"]
        if prov not in coalexp:
            continue
        cap = float(r["capacity_mw"]) if r["capacity_mw"] not in (None, "") else float("nan")
        if ry not in (None, ""):
            ry = float(ry)
            if ry < sy:
                continue
            recs.append({"prov": prov, "ce": coalexp[prov], "start": sy, "ret": ry,
                         "cap": cap, "retired": True})
        else:
            recs.append({"prov": prov, "ce": coalexp[prov], "start": sy, "ret": None,
                         "cap": cap, "retired": False})
    return recs


def main():
    coalexp = load_coalexp()
    recs = load_units(coalexp)
    print(f"机组总数(运营+退役): {len(recs)}")

    # ---- 分析1：政策前 (2000-2011) ----
    pre = []
    for x in recs:
        sy = x["start"]
        if sy >= 2012:
            continue  # 2012 后才投产的，不进入政策前窗口
        if x["retired"]:
            ry = x["ret"]
            if ry <= 2011:
                pre.append({"dur": ry - sy, "ev": 1, "ce": x["ce"], "cap": x["cap"], "start": sy})
            else:
                pre.append({"dur": 2011 - sy, "ev": 0, "ce": x["ce"], "cap": x["cap"], "start": sy})
        else:
            pre.append({"dur": 2011 - sy, "ev": 0, "ce": x["ce"], "cap": x["cap"], "start": sy})
    pre_df = pd.DataFrame(pre)
    pre_df = pre_df[pre_df["dur"] > 0]
    print(f"\n[政策前 2000-2011] 样本 {len(pre_df)}，事件 {pre_df['ev'].sum()}")

    cph1 = CoxPHFitter()
    cph1.fit(pre_df, duration_col="dur", event_col="ev", formula="ce + cap + start")
    print("Cox 政策前：")
    print(cph1.summary[["coef", "exp(coef)", "p"]].round(4).to_string())

    # ---- 分析2：政策后 (2012-2025) 左截断 ----
    post = []
    for x in recs:
        sy = x["start"]
        if sy >= 2012:
            # 2012 后投产的机组，也纳入（它们从投产起就在政策后窗口）
            entry = 0.0
            if x["retired"]:
                post.append({"entry": entry, "dur": x["ret"] - sy, "ev": 1,
                             "ce": x["ce"], "cap": x["cap"], "start": sy})
            else:
                post.append({"entry": entry, "dur": CENSOR - sy, "ev": 0,
                             "ce": x["ce"], "cap": x["cap"], "start": sy})
        else:
            # 2012 前投产的存量机组，从 2012 起左截断观察
            entry = 2012 - sy
            if x["retired"]:
                if x["ret"] >= 2012:
                    post.append({"entry": entry, "dur": x["ret"] - sy, "ev": 1,
                                 "ce": x["ce"], "cap": x["cap"], "start": sy})
                # 2012 前已退役的，不进入政策后窗口
            else:
                post.append({"entry": entry, "dur": CENSOR - sy, "ev": 0,
                             "ce": x["ce"], "cap": x["cap"], "start": sy})
    post_df = pd.DataFrame(post)
    post_df = post_df[post_df["dur"] > post_df["entry"]]
    print(f"\n[政策后 2012-2025] 样本 {len(post_df)}，事件 {post_df['ev'].sum()}")

    cph2 = CoxPHFitter()
    cph2.fit(post_df, duration_col="dur", event_col="ev", entry_col="entry",
             formula="ce + cap + start")
    print("Cox 政策后：")
    print(cph2.summary[["coef", "exp(coef)", "p"]].round(4).to_string())

    # ---- 政策后窗口的 KM + log-rank（高煤 vs 低煤，按中位数分组） ----
    med = post_df["ce"].median()
    hi = post_df[post_df["ce"] >= med]
    lo = post_df[post_df["ce"] < med]
    lr = logrank_test(hi["dur"], lo["dur"], hi["ev"], lo["ev"])
    print(f"\n[政策后 KM] 高煤组 n={len(hi)} 事件{hi['ev'].sum()}；低煤组 n={len(lo)} 事件{lo['ev'].sum()}")
    print(f"log-rank: test_statistic={lr.test_statistic:.3f}, p={lr.p_value:.4f}")

    # 保存 KM 曲线（政策后）
    km_hi = KaplanMeierFitter().fit(hi["dur"], hi["ev"])
    km_lo = KaplanMeierFitter().fit(lo["dur"], lo["ev"])
    with open(os.path.join(OUT, "km_post2012_curves.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["group", "duration", "survival"])
        for t, s in zip(km_hi.timeline, km_hi.survival_function_.values[:, 0]):
            w.writerow(["high_coal", t, s])
        for t, s in zip(km_lo.timeline, km_lo.survival_function_.values[:, 0]):
            w.writerow(["low_coal", t, s])
    print(f"\n政策后 KM 曲线已写 {OUT}/km_post2012_curves.csv")


if __name__ == "__main__":
    main()
