#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""煤电退出的最终版分段风险模型。

将每台机组拆为日历政策阶段内的风险区间，使用左截断 Cox 模型；
以省份聚类稳健标准误估计煤炭暴露与各阶段的关联，并直接检验
2012--2015 年系数是否低于 2000--2011 年。连续暴露度（每 1 SD）为
主规格；按样本中位数划分的高煤组为便于解释的辅助规格。
"""
import csv
import math
import os

import pandas as pd
from lifelines import CoxPHFitter


ROOT = "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
GEM = os.path.join(ROOT, "data/gem_power_project_lifecycle/gem_china_project_units_2026_snapshot.csv")
MAIN = os.path.join(ROOT, "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_leadership_0721.csv")
OUT = os.path.join(ROOT, "result/tables/0820_coal_retirement_survival_final")
EXCLUDE = {"cancelled", "construction", "announced", "shelved", "permitted", "pre-permit", "mothballed"}
PERIODS = [
    ("pre_2000_2011", 2000, 2011),
    ("early_2012_2015", 2012, 2015),
    ("supply_2016_2020", 2016, 2020),
    ("carbon_2021_2025", 2021, 2025),
]


def normal_pvalue(z):
    return math.erfc(abs(z) / math.sqrt(2.0))


def load_exposure():
    exposure = {}
    with open(MAIN, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                exposure[row["province"]] = float(row["coalexp_pre"])
            except (KeyError, TypeError, ValueError):
                continue
    return exposure


def build_episodes(exposure):
    rows = []
    with open(GEM, encoding="utf-8-sig") as f:
        for unit_id, row in enumerate(csv.DictReader(f)):
            if row.get("asset") != "coal" or row.get("status") in EXCLUDE:
                continue
            try:
                start_year = float(row["start_year"])
                capacity = float(row["capacity_mw"])
            except (KeyError, TypeError, ValueError):
                continue
            province = row.get("province")
            if province not in exposure:
                continue
            try:
                retired_year = float(row["retired_year"]) if row.get("retired_year") else None
            except ValueError:
                continue
            if retired_year is not None and retired_year < start_year:
                continue
            for period, first_year, last_year in PERIODS:
                if start_year > last_year or (retired_year is not None and retired_year < first_year):
                    continue
                interval_start = max(start_year, float(first_year))
                interval_end = min(retired_year if retired_year is not None else float(last_year + 1), float(last_year + 1))
                if interval_end <= interval_start:
                    continue
                event = int(retired_year is not None and first_year <= retired_year <= last_year)
                rows.append({
                    "unit_id": unit_id,
                    "province": province,
                    "period": period,
                    "entry_age": interval_start - start_year,
                    "exit_age": interval_end - start_year,
                    "event": event,
                    "coalexp": exposure[province],
                    "capacity_100mw": capacity / 100.0,
                    "vintage_decade": (start_year - 2000.0) / 10.0,
                })
    return pd.DataFrame(rows)


def make_design(episodes, exposure_type):
    df = episodes.copy()
    if exposure_type == "standardized_continuous":
        province_exposure = pd.Series(list(load_exposure().values()))
        df["exposure"] = (df["coalexp"] - province_exposure.mean()) / province_exposure.std(ddof=1)
        label = "coalexp_pre（每 1 个省级标准差）"
    elif exposure_type == "median_high_coal":
        median = pd.Series(list(load_exposure().values())).median()
        df["exposure"] = (df["coalexp"] >= median).astype(float)
        label = f"高煤组（coalexp_pre >= 样本中位数 {median:.4f}）"
    else:
        raise ValueError(exposure_type)

    for period, _, _ in PERIODS:
        df[f"exposure_{period}"] = df["exposure"] * (df["period"] == period).astype(float)
    # 共同的日历阶段冲击；政策前作为参照期。
    for period, _, _ in PERIODS[1:]:
        df[f"period_{period}"] = (df["period"] == period).astype(float)
    return df, label


def fit_and_collect(episodes, exposure_type):
    df, label = make_design(episodes, exposure_type)
    exposure_terms = [f"exposure_{period}" for period, _, _ in PERIODS]
    period_terms = [f"period_{period}" for period, _, _ in PERIODS[1:]]
    formula = " + ".join(exposure_terms + period_terms + ["capacity_100mw", "vintage_decade"])
    model = CoxPHFitter()
    model.fit(
        df,
        duration_col="exit_age",
        event_col="event",
        entry_col="entry_age",
        cluster_col="province",
        robust=True,
        formula=formula,
    )

    rows = []
    for period, _, _ in PERIODS:
        term = f"exposure_{period}"
        s = model.summary.loc[term]
        rows.append({
            "specification": exposure_type,
            "exposure_definition": label,
            "period": period,
            "n_intervals": len(df),
            # Report events occurring in this calendar period, rather than
            # repeating the full-sample event count on every result row.
            "events": int(df.loc[df["period"].eq(period), "event"].sum()),
            "coef": float(s["coef"]),
            "hazard_ratio": float(s["exp(coef)"]),
            "se_cluster_province": float(s["se(coef)"]),
            "p": float(s["p"]),
        })

    comparisons = []
    base = "exposure_pre_2000_2011"
    covariance = model.variance_matrix_
    for period, _, _ in PERIODS[1:]:
        term = f"exposure_{period}"
        diff = float(model.params_[term] - model.params_[base])
        variance = float(covariance.loc[term, term] + covariance.loc[base, base] - 2 * covariance.loc[term, base])
        se = math.sqrt(max(variance, 0.0))
        comparisons.append({
            "specification": exposure_type,
            "comparison": f"{period} minus pre_2000_2011",
            "coef_difference": diff,
            "se_model": se,
            # variance_matrix_ is the model-based covariance matrix.  The
            # period-specific p-values above use province-clustered robust SE;
            # this contrast is retained only as a diagnostic and must not be
            # reported as a cluster-robust hypothesis test.
            "p_unclustered_model": normal_pvalue(diff / se) if se > 0 else float("nan"),
        })
    return rows, comparisons, model, df


def main():
    os.makedirs(OUT, exist_ok=True)
    episodes = build_episodes(load_exposure())
    if episodes.empty:
        raise RuntimeError("未构造出可估计的风险区间")
    result_rows, comparison_rows = [], []
    with open(os.path.join(OUT, "run.log"), "w", encoding="utf-8") as log:
        log.write(f"风险区间={len(episodes)}；机组={episodes['unit_id'].nunique()}；事件={int(episodes['event'].sum())}\n")
        for spec in ["standardized_continuous", "median_high_coal"]:
            rows, comparisons, model, _ = fit_and_collect(episodes, spec)
            result_rows.extend(rows)
            comparison_rows.extend(comparisons)
            log.write(f"\n[{spec}]\n")
            log.write(model.summary[["coef", "exp(coef)", "se(coef)", "p"]].to_string())
            log.write("\n")
    pd.DataFrame(result_rows).to_csv(os.path.join(OUT, "period_specific_cox.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(comparison_rows).to_csv(os.path.join(OUT, "period_difference_tests.csv"), index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
