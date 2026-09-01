#!/usr/bin/env python3
"""Build variables for non-clean energy stability, tide, and inertia tests."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_0718.csv"
OUTPUT = ROOT / "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_0718.csv"
MODULE_DIR = ROOT / "data/nonclean_tide_policy_inertia_0718"


def consecutive_difference(frame: pd.DataFrame, variable: str) -> pd.Series:
    previous_value = frame.groupby("province_id")[variable].shift(1)
    previous_year = frame.groupby("province_id")["year"].shift(1)
    return (frame[variable] - previous_value).where(frame["year"] - previous_year == 1)


def consecutive_log_difference(frame: pd.DataFrame, variable: str) -> pd.Series:
    logged = np.log(pd.to_numeric(frame[variable], errors="coerce").where(frame[variable] > 0))
    previous_value = logged.groupby(frame["province_id"]).shift(1)
    previous_year = frame.groupby("province_id")["year"].shift(1)
    return (logged - previous_value).where(frame["year"] - previous_year == 1)


def cross_section_zscore(series: pd.Series) -> pd.Series:
    standard_deviation = series.std(ddof=0)
    if not standard_deviation or np.isnan(standard_deviation):
        return pd.Series(np.nan, index=series.index)
    return (series - series.mean()) / standard_deviation


def winsorize(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    valid = series.dropna()
    if valid.empty:
        return series
    return series.clip(valid.quantile(lower), valid.quantile(upper))


def main() -> None:
    MODULE_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(INPUT).sort_values(["province_id", "year"]).copy()

    for variable in [
        "total_generation_billion_kwh",
        "thermal_generation_billion_kwh",
        "thermal_capacity_10k_kw",
        "total_capacity_10k_kw",
        "gdp",
        "sec_val",
    ]:
        panel[f"dln_{variable}"] = consecutive_log_difference(panel, variable)

    panel["thermal_capacity_addition_10k_kw"] = consecutive_difference(
        panel, "thermal_capacity_10k_kw"
    )
    panel["total_capacity_addition_10k_kw"] = consecutive_difference(
        panel, "total_capacity_10k_kw"
    )
    panel["thermal_utilization_hours"] = (
        panel["thermal_generation_billion_kwh"]
        / panel["thermal_capacity_10k_kw"]
        * 100_000.0
    )
    panel["thermal_utilization_hours_w"] = winsorize(
        panel["thermal_utilization_hours"]
    )
    panel["dln_thermal_utilization"] = (
        panel["dln_thermal_generation_billion_kwh"]
        - panel["dln_thermal_capacity_10k_kw"]
    )
    panel["thermal_capacity_addition_per_gdp"] = (
        panel["thermal_capacity_addition_10k_kw"] / panel["gdp"]
    )
    panel["thermal_generation_per_gdp"] = (
        panel["thermal_generation_billion_kwh"] / panel["gdp"]
    )

    pre = panel.loc[panel["year"].between(2008, 2011)].groupby("province_id").agg(
        pre_thermal_generation_share_0811=("therm_gen_sh", "mean"),
        pre_thermal_capacity_share_0811=("therm_cap_sh", "mean"),
        pre_thermal_generation_per_gdp_0811=("thermal_generation_per_gdp", "mean"),
    )
    for variable in pre.columns:
        pre[f"{variable}_z"] = cross_section_zscore(pre[variable])
    panel = panel.merge(pre.reset_index(), on="province_id", how="left", validate="many_to_one")

    annual_wave = panel.groupby("year").agg(
        national_mean_dln_thermal_capacity=("dln_thermal_capacity_10k_kw", "mean"),
        national_mean_dln_total_generation=("dln_total_generation_billion_kwh", "mean"),
        thermal_capacity_growth_coverage=("dln_thermal_capacity_10k_kw", "count"),
    )
    annual_wave.loc[
        annual_wave["thermal_capacity_growth_coverage"] < 20,
        "national_mean_dln_thermal_capacity",
    ] = np.nan
    annual_wave["national_thermal_capacity_wave_z"] = cross_section_zscore(
        annual_wave["national_mean_dln_thermal_capacity"]
    )
    annual_wave["national_generation_demand_wave_z"] = cross_section_zscore(
        annual_wave["national_mean_dln_total_generation"]
    )
    panel = panel.merge(annual_wave.reset_index(), on="year", how="left", validate="many_to_one")

    panel["post2016"] = (panel["year"] >= 2016).astype(int)
    panel["post2012_prethermal_z"] = (
        panel["post2012"] * panel["pre_thermal_generation_share_0811_z"]
    )
    panel["post2016_prethermal_z"] = (
        panel["post2016"] * panel["pre_thermal_generation_share_0811_z"]
    )
    panel["post2016_natural_endowment"] = (
        panel["post2016"] * panel["natural_wind_solar_endowment"]
    )
    panel["prethermal_x_natural_endowment"] = (
        panel["pre_thermal_generation_share_0811_z"]
        * panel["natural_wind_solar_endowment"]
    )
    panel["ddd_prethermal_natural_2016"] = (
        panel["post2016"]
        * panel["prethermal_x_natural_endowment"]
    )
    panel["thermal_tide_loading"] = (
        panel["national_thermal_capacity_wave_z"]
        * panel["pre_thermal_generation_share_0811_z"]
    )
    panel["demand_tide_loading"] = (
        panel["national_generation_demand_wave_z"]
        * panel["pre_thermal_generation_share_0811_z"]
    )

    for name, variable in [
        ("fiscal", "resdep_fisc_z"),
        ("soe", "resdep_soe_z"),
    ]:
        panel[f"post2016_{name}_lockin"] = panel["post2016"] * panel[variable]
        panel[f"{name}_lockin_x_endowment"] = (
            panel[variable] * panel["natural_wind_solar_endowment"]
        )
        panel[f"ddd_{name}_endowment_2016"] = (
            panel["post2016"] * panel[f"{name}_lockin_x_endowment"]
        )

    stata_aliases = {
        "dln_totgen": "dln_total_generation_billion_kwh",
        "dln_thermgen": "dln_thermal_generation_billion_kwh",
        "dln_thermcap": "dln_thermal_capacity_10k_kw",
        "dln_totcap": "dln_total_capacity_10k_kw",
        "therm_cap_add": "thermal_capacity_addition_10k_kw",
        "therm_util_h": "thermal_utilization_hours",
        "therm_util_h_w": "thermal_utilization_hours_w",
        "dln_therm_util": "dln_thermal_utilization",
        "therm_cap_add_gdp": "thermal_capacity_addition_per_gdp",
        "therm_gen_gdp": "thermal_generation_per_gdp",
        "pretherm_gen": "pre_thermal_generation_share_0811",
        "pretherm_gen_z": "pre_thermal_generation_share_0811_z",
        "pretherm_cap": "pre_thermal_capacity_share_0811",
        "pretherm_cap_z": "pre_thermal_capacity_share_0811_z",
        "post12_pretherm_z": "post2012_prethermal_z",
        "post16_pretherm_z": "post2016_prethermal_z",
        "post16_endow": "post2016_natural_endowment",
        "ddd_pretherm_endow": "ddd_prethermal_natural_2016",
        "tide_loading": "thermal_tide_loading",
        "demand_loading": "demand_tide_loading",
        "post16_fiscal": "post2016_fiscal_lockin",
        "ddd_fiscal_endow": "ddd_fiscal_endowment_2016",
        "post16_soe": "post2016_soe_lockin",
        "ddd_soe_endow": "ddd_soe_endowment_2016",
    }
    for alias, source in stata_aliases.items():
        panel[alias] = panel[source]

    derived = [
        "province_id", "province", "year",
        "dln_total_generation_billion_kwh",
        "dln_thermal_generation_billion_kwh",
        "dln_thermal_capacity_10k_kw",
        "dln_total_capacity_10k_kw",
        "dln_gdp", "dln_sec_val",
        "thermal_capacity_addition_10k_kw",
        "total_capacity_addition_10k_kw",
        "thermal_utilization_hours",
        "thermal_utilization_hours_w",
        "dln_thermal_utilization",
        "thermal_capacity_addition_per_gdp",
        "thermal_generation_per_gdp",
        *pre.columns,
        "national_mean_dln_thermal_capacity",
        "national_mean_dln_total_generation",
        "thermal_capacity_growth_coverage",
        "national_thermal_capacity_wave_z",
        "national_generation_demand_wave_z",
        "post2016",
        "post2012_prethermal_z",
        "post2016_prethermal_z",
        "post2016_natural_endowment",
        "prethermal_x_natural_endowment",
        "ddd_prethermal_natural_2016",
        "thermal_tide_loading",
        "demand_tide_loading",
        "post2016_fiscal_lockin",
        "fiscal_lockin_x_endowment",
        "ddd_fiscal_endowment_2016",
        "post2016_soe_lockin",
        "soe_lockin_x_endowment",
        "ddd_soe_endowment_2016",
        *stata_aliases.keys(),
    ]
    panel[derived].to_csv(
        MODULE_DIR / "nonclean_tide_policy_inertia_panel_2000_2023.csv", index=False
    )
    annual_wave.reset_index().to_csv(
        MODULE_DIR / "national_thermal_capacity_wave_2000_2023.csv", index=False
    )
    pre.reset_index().to_csv(
        MODULE_DIR / "prepolicy_thermal_dependence_province.csv", index=False
    )
    panel.to_csv(OUTPUT, index=False)

    coverage = []
    for variable in derived[3:]:
        valid = panel[variable].notna()
        coverage.append(
            {
                "variable": variable,
                "observations": int(valid.sum()),
                "provinces": int(panel.loc[valid, "province_id"].nunique()),
                "first_year": int(panel.loc[valid, "year"].min()) if valid.any() else np.nan,
                "last_year": int(panel.loc[valid, "year"].max()) if valid.any() else np.nan,
            }
        )
    pd.DataFrame(coverage).to_csv(
        MODULE_DIR / "nonclean_tide_policy_inertia_coverage.csv", index=False
    )
    print(f"Rows: {len(panel)}; columns: {len(panel.columns)}")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()
