#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补2：分省贷款余额 + 工业增加值 的 2012 断点检验。

检验1（第一层"金融约束发生"）：2012 后，高煤省贷款余额增速是否相对放缓？
检验2（火电为何被保留）：高煤省工业增加值增速是否更平滑（波动更小）？
"""
import csv, os
from collections import defaultdict
import math

ROOT = "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
PANEL = os.path.join(ROOT, "data", "wind_edb", "province_panel")
MAIN = os.path.join(ROOT, "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_leadership_0721.csv")
OUT = os.path.join(ROOT, "result", "tables", "0820_finance_industry_break")


P2C = {
    "Beijing": "北京", "Tianjin": "天津", "Hebei": "河北", "Shanxi": "山西",
    "Neimenggu": "内蒙古", "Liaoning": "辽宁", "Jilin": "吉林", "Heilongjiang": "黑龙江",
    "Shanghai": "上海", "Jiangsu": "江苏", "Zhejiang": "浙江", "Anhui": "安徽",
    "Fujian": "福建", "Jiangxi": "江西", "Shandong": "山东", "Henan": "河南",
    "Hubei": "湖北", "Hunan": "湖南", "Guangdong": "广东", "Guangxi": "广西",
    "Hainan": "海南", "Chongqing": "重庆", "Sichuan": "四川", "Guizhou": "贵州",
    "Yunnan": "云南", "Xizang": "西藏", "Shaanxi": "陕西", "Gansu": "甘肃",
    "Qinghai": "青海", "Ningxia": "宁夏", "Xinjiang": "新疆",
}


def load_coalexp():
    m = {}
    for r in csv.DictReader(open(MAIN, encoding="utf-8-sig")):
        p, c = r.get("province"), r.get("coalexp_pre")
        if p and c not in (None, ""):
            try:
                m[P2C.get(p, p)] = float(c)
            except ValueError:
                pass
    return m


def load_panel(fname):
    """返回 {province: [(date_str, value)]}，date 格式 YYYYMMDD。"""
    d = defaultdict(list)
    for r in csv.DictReader(open(os.path.join(PANEL, fname), encoding="utf-8-sig")):
        try:
            v = float(r["value"])
        except (ValueError, TypeError):
            continue
        d[r["province"]].append((r["date"], v))
    return d


def yoy_by_year(series):
    """输入 [(YYYYMMDD, value)]，返回 {year: yoy_growth}（用每年12月值算YoY）。"""
    dec = {}
    for dt, v in series:
        if dt.endswith("1231"):
            y = int(dt[:4])
            dec[y] = v
    out = {}
    for y in sorted(dec):
        if (y - 1) in dec and dec[y - 1] > 0:
            out[y] = (dec[y] - dec[y - 1]) / dec[y - 1] * 100.0
    return out


def did_compare(coalexp, panel, value_fn):
    """简化 DID：高煤 vs 低煤，post2012 前后差异。"""
    med = sorted(coalexp.values())[len(coalexp) // 2]
    hi_pre, hi_post, lo_pre, lo_post = [], [], [], []
    for prov, ce in coalexp.items():
        if prov not in panel:
            continue
        series = value_fn(panel[prov])
        grp_hi = ce >= med
        for y, v in series.items():
            if y < 2012:
                (hi_pre if grp_hi else lo_pre).append(v)
            else:
                (hi_post if grp_hi else lo_post).append(v)
    def mean(x):
        return sum(x) / len(x) if x else float("nan")
    d_hi = mean(hi_post) - mean(hi_pre)
    d_lo = mean(lo_post) - mean(lo_pre)
    did = d_hi - d_lo
    return {
        "median_ce": med,
        "hi_pre_mean": mean(hi_pre), "hi_post_mean": mean(hi_post),
        "lo_pre_mean": mean(lo_pre), "lo_post_mean": mean(lo_post),
        "d_hi": d_hi, "d_lo": d_lo, "did": did,
        "hi_n": len(hi_pre), "lo_n": len(lo_pre),
    }


def main():
    coalexp = load_coalexp()
    loan = load_panel("loan_balance_31prov_panel.csv")
    ind = load_panel("industry_va_31prov_panel.csv")

    os.makedirs(OUT, exist_ok=True)

    # 检验1：贷款余额增速 DID
    r1 = did_compare(coalexp, loan, yoy_by_year)
    print("=== 检验1：贷款余额 YoY 增速 DID ===")
    print(f"高煤组：2012前均值 {r1['hi_pre_mean']:.2f}% → 2012后 {r1['hi_post_mean']:.2f}%（Δ={r1['d_hi']:.2f}pp）")
    print(f"低煤组：2012前均值 {r1['lo_pre_mean']:.2f}% → 2012后 {r1['lo_post_mean']:.2f}%（Δ={r1['d_lo']:.2f}pp）")
    print(f"DID（高煤-低煤）：{r1['did']:.2f} pp")

    # 检验2：工业增加值增速波动（政策前 vs 政策后，各高煤/低煤组的组内标准差）
    def vol_by_period(panel, prov, ce, med, pre_ok):
        vals_pre, vals_post = [], []
        for dt, v in panel[prov]:
            y = int(dt[:4])
            if pre_ok(y):
                vals_pre.append(v)
            else:
                vals_post.append(v)
        return vals_pre, vals_post

    med = sorted(coalexp.values())[len(coalexp) // 2]
    groups = {"hi": [], "lo": []}
    for prov, ce in coalexp.items():
        if prov not in ind:
            continue
        g = "hi" if ce >= med else "lo"
        pre, post = vol_by_period(ind, prov, ce, med, lambda y: y < 2012)
        for v in pre:
            groups[g].append(("pre", v))
        for v in post:
            groups[g].append(("post", v))

    print("\n=== 检验2：工业增加值增速 波动（标准差）===")
    for g in ["hi", "lo"]:
        pre = [v for p, v in groups[g] if p == "pre"]
        post = [v for p, v in groups[g] if p == "post"]
        def sd(x):
            m = sum(x) / len(x)
            return (sum((v - m) ** 2 for v in x) / len(x)) ** 0.5
        print(f"{'高煤' if g=='hi' else '低煤'}组：政策前 std={sd(pre):.2f}（n={len(pre)}）→ 政策后 std={sd(post):.2f}（n={len(post)}）")

    # 写结果
    with open(os.path.join(OUT, "break_test_summary.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["item", "value"])
        w.writerow(["loan_did_pp", round(r1["did"], 3)])
        w.writerow(["hi_d_loan_pp", round(r1["d_hi"], 3)])
        w.writerow(["lo_d_loan_pp", round(r1["d_lo"], 3)])
    print(f"\n结果已写 {OUT}/break_test_summary.csv")


if __name__ == "__main__":
    main()
