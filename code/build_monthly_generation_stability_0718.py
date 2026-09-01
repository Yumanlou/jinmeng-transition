#!/usr/bin/env python3
"""Recover monthly provincial generation increments from Wind YTD series."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DEFAULT = ROOT / "data" / "wind_energy_transition_0718" / "wind_energy_transition_raw_long.csv"
OUT_DIR = ROOT / "data" / "monthly_generation_stability"

SOURCE_VARIABLES = {
    "nbs_thermal_generation_billion_kwh": "thermal",
    "nbs_wind_generation_billion_kwh": "wind",
    "nbs_solar_generation_billion_kwh": "solar",
    "nbs_hydro_generation_billion_kwh": "hydro",
    "nbs_nuclear_generation_billion_kwh": "nuclear",
}


def build_monthly(raw_path: Path) -> pd.DataFrame:
    raw = pd.read_csv(raw_path, low_memory=False)
    raw = raw.loc[raw["variable"].isin(SOURCE_VARIABLES)].copy()
    raw["date"] = raw["date"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(8)
    raw["year"] = raw["date"].str[:4].astype(int)
    raw["month"] = raw["date"].str[4:6].astype(int)
    raw["technology"] = raw["variable"].map(SOURCE_VARIABLES)
    raw["generation_ytd_100m_kwh"] = pd.to_numeric(raw["value"], errors="coerce") / 10000.0
    raw = raw.sort_values(["province", "technology", "year", "month"])

    group = raw.groupby(["province", "technology", "year"], sort=False)
    raw["generation_monthly_100m_kwh"] = group["generation_ytd_100m_kwh"].diff()
    first_observation = group.cumcount().eq(0)
    january = first_observation & raw["month"].eq(1)
    raw.loc[january, "generation_monthly_100m_kwh"] = raw.loc[january, "generation_ytd_100m_kwh"]
    raw["combined_jan_feb_flag"] = first_observation & raw["month"].eq(2)
    raw["negative_increment_flag"] = raw["generation_monthly_100m_kwh"].lt(0)
    raw.loc[raw["negative_increment_flag"], "generation_monthly_100m_kwh"] = np.nan

    keep = [
        "province", "province_cn", "year", "month", "technology",
        "generation_ytd_100m_kwh", "generation_monthly_100m_kwh",
        "combined_jan_feb_flag", "negative_increment_flag", "wind_code",
        "wind_name", "wind_source",
    ]
    return raw[keep].reset_index(drop=True)


def build_wide(monthly: pd.DataFrame) -> pd.DataFrame:
    wide = monthly.pivot_table(
        index=["province", "province_cn", "year", "month"],
        columns="technology",
        values="generation_monthly_100m_kwh",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    for technology in SOURCE_VARIABLES.values():
        if technology not in wide:
            wide[technology] = np.nan
        wide = wide.rename(columns={technology: f"{technology}_generation_monthly_100m_kwh"})
    source_columns = [f"{technology}_generation_monthly_100m_kwh" for technology in SOURCE_VARIABLES.values()]
    wide["windsolar_generation_monthly_100m_kwh"] = wide[
        ["wind_generation_monthly_100m_kwh", "solar_generation_monthly_100m_kwh"]
    ].sum(axis=1, min_count=1)
    wide["observed_source_generation_monthly_100m_kwh"] = wide[source_columns].sum(axis=1, min_count=1)
    return wide.sort_values(["province", "year", "month"]).reset_index(drop=True)


def coefficient_of_variation(series: pd.Series) -> float:
    values = series.dropna()
    if len(values) < 6 or values.mean() <= 0:
        return np.nan
    return float(values.std(ddof=1) / values.mean())


def build_stability(wide: pd.DataFrame) -> pd.DataFrame:
    value_columns = [column for column in wide.columns if column.endswith("monthly_100m_kwh")]
    rows = []
    for (province, province_cn, year), group in wide.groupby(["province", "province_cn", "year"]):
        row = {"province": province, "province_cn": province_cn, "year": year}
        for column in value_columns:
            prefix = column.removesuffix("_generation_monthly_100m_kwh")
            values = group[column].dropna()
            row[f"{prefix}_monthly_observations"] = len(values)
            row[f"{prefix}_monthly_mean_100m_kwh"] = values.mean() if len(values) else np.nan
            row[f"{prefix}_monthly_sd_100m_kwh"] = values.std(ddof=1) if len(values) > 1 else np.nan
            row[f"{prefix}_monthly_cv"] = coefficient_of_variation(group[column])
        rows.append(row)
    stability = pd.DataFrame(rows).sort_values(["province", "year"]).reset_index(drop=True)
    aliases = {
        "thermal_monthly_observations": "therm_month_n",
        "thermal_monthly_cv": "therm_month_cv",
        "windsolar_monthly_observations": "windsolar_month_n",
        "windsolar_monthly_cv": "windsolar_month_cv",
        "observed_source_monthly_observations": "allsrc_month_n",
        "observed_source_monthly_cv": "allsrc_month_cv",
    }
    for source, target in aliases.items():
        stability[target] = stability[source]
    return stability


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=RAW_DEFAULT)
    parser.add_argument(
        "--main-panel", type=Path,
        default=ROOT / "data" / "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_0718.csv",
    )
    parser.add_argument(
        "--merged-output", type=Path,
        default=ROOT / "data" / "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_0718.csv",
    )
    args = parser.parse_args()

    monthly_long = build_monthly(args.raw)
    monthly_wide = build_wide(monthly_long)
    stability = build_stability(monthly_wide)
    coverage = monthly_long.groupby("technology").agg(
        provinces=("province", "nunique"),
        first_year=("year", "min"),
        last_year=("year", "max"),
        ytd_observations=("generation_ytd_100m_kwh", "count"),
        monthly_increments=("generation_monthly_100m_kwh", "count"),
        combined_jan_feb=("combined_jan_feb_flag", "sum"),
        negative_increments=("negative_increment_flag", "sum"),
    ).reset_index()

    main = pd.read_csv(args.main_panel, low_memory=False)
    merged = main.merge(stability, on=["province", "year"], how="left", validate="one_to_one")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    monthly_long.to_csv(OUT_DIR / "monthly_generation_long_2000_2023.csv", index=False, encoding="utf-8-sig")
    monthly_wide.to_csv(OUT_DIR / "monthly_generation_wide_2000_2023.csv", index=False, encoding="utf-8-sig")
    stability.to_csv(OUT_DIR / "province_year_generation_stability_2000_2023.csv", index=False, encoding="utf-8-sig")
    coverage.to_csv(OUT_DIR / "monthly_generation_coverage.csv", index=False, encoding="utf-8-sig")
    merged.to_csv(args.merged_output, index=False, encoding="utf-8-sig")
    print(f"monthly_long rows={len(monthly_long)}")
    print(f"monthly_wide rows={len(monthly_wide)}")
    print(f"stability rows={len(stability)}")
    print(f"merged={args.merged_output} rows={len(merged)} columns={len(merged.columns)}")
    print(coverage.to_string(index=False))


if __name__ == "__main__":
    main()
