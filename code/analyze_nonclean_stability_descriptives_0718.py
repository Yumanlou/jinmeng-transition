#!/usr/bin/env python3
"""Descriptive stability and persistent-capacity evidence for thermal power."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_0718.csv"
OUTPUT_DIR = ROOT / "result/tables/0718_nonclean_tide_inertia"


def consecutive_log_change(panel: pd.DataFrame, variable: str) -> pd.Series:
    logged = np.log(panel[variable].where(panel[variable] > 0))
    previous = logged.groupby(panel["province_id"]).shift(1)
    previous_year = panel.groupby("province_id")["year"].shift(1)
    return (logged - previous).where(panel["year"] - previous_year == 1)


def two_way_residual(panel: pd.DataFrame, variable: str) -> pd.Series:
    values = panel[variable]
    return (
        values
        - values.groupby(panel["province_id"]).transform("mean")
        - values.groupby(panel["year"]).transform("mean")
        + values.mean()
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(INPUT).sort_values(["province_id", "year"]).copy()
    panel["dln_thermal_generation"] = consecutive_log_change(
        panel, "thermal_generation_billion_kwh"
    )
    panel["dln_windsolar_generation"] = consecutive_log_change(
        panel, "clean_generation_billion_kwh"
    )
    panel["dln_thermal_capacity"] = consecutive_log_change(
        panel, "thermal_capacity_10k_kw"
    )

    stability = panel.loc[panel["year"].between(2018, 2023)].dropna(
        subset=["dln_thermal_generation", "dln_windsolar_generation"]
    ).copy()
    stability["thermal_abs_residual"] = two_way_residual(
        stability, "dln_thermal_generation"
    ).abs()
    stability["windsolar_abs_residual"] = two_way_residual(
        stability, "dln_windsolar_generation"
    ).abs()
    province_stability = stability.groupby(
        ["province_id", "province"], as_index=False
    ).agg(
        thermal_abs_residual=("thermal_abs_residual", "mean"),
        windsolar_abs_residual=("windsolar_abs_residual", "mean"),
    )
    province_stability["windsolar_minus_thermal"] = (
        province_stability["windsolar_abs_residual"]
        - province_stability["thermal_abs_residual"]
    )

    random = np.random.default_rng(20260718)
    differences = province_stability["windsolar_minus_thermal"].to_numpy()
    bootstrap_means = np.empty(10_000)
    for repetition in range(len(bootstrap_means)):
        bootstrap_means[repetition] = random.choice(
            differences, size=len(differences), replace=True
        ).mean()
    stability_summary = pd.DataFrame(
        {
            "period": ["2018-2023"],
            "provinces": [len(province_stability)],
            "mean_thermal_absolute_residual": [
                province_stability["thermal_abs_residual"].mean()
            ],
            "mean_windsolar_absolute_residual": [
                province_stability["windsolar_abs_residual"].mean()
            ],
            "windsolar_minus_thermal_mean": [differences.mean()],
            "province_bootstrap_ci_2_5": [np.quantile(bootstrap_means, 0.025)],
            "province_bootstrap_ci_97_5": [np.quantile(bootstrap_means, 0.975)],
            "provinces_windsolar_more_volatile": [(differences > 0).sum()],
        }
    )

    period_rows = []
    for start_year, end_year in [(2007, 2012), (2013, 2016), (2017, 2023)]:
        sample = panel.loc[panel["year"].between(start_year, end_year)].dropna(
            subset=["dln_thermal_capacity"]
        )
        period_rows.append(
            {
                "period": f"{start_year}-{end_year}",
                "province_year_observations": len(sample),
                "mean_thermal_capacity_growth": sample["dln_thermal_capacity"].mean(),
                "median_thermal_capacity_growth": sample["dln_thermal_capacity"].median(),
                "positive_growth_share": (sample["dln_thermal_capacity"] > 0).mean(),
            }
        )
    capacity_summary = pd.DataFrame(period_rows)

    province_stability.to_csv(
        OUTPUT_DIR / "Table_0718_Thermal_vs_WindSolar_Stability_Province.csv",
        index=False,
    )
    stability_summary.to_csv(
        OUTPUT_DIR / "Table_0718_Thermal_vs_WindSolar_Stability_Summary.csv",
        index=False,
    )
    capacity_summary.to_csv(
        OUTPUT_DIR / "Table_0718_Thermal_Capacity_Persistence.csv", index=False
    )
    print(stability_summary.to_string(index=False))
    print("\n", capacity_summary.to_string(index=False))


if __name__ == "__main__":
    main()
