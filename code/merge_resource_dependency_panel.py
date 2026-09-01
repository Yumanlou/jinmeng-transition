#!/usr/bin/env python3
"""Merge Wind resource-dependence data into the empirical province-year panel."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


PRE_COMPONENTS = {
    "pre_mining_employment_share_0811": "mining_employment",
    "pre_coal_mining_asset_share_0811": "coal_mining_assets",
    "pre_resource_tax_share_0811": "resource_tax",
}

# Institutional lock-in is conceptually distinct from resource dependence and
# is therefore standardized and tested separately from the composite index.
LOCKIN_COMPONENTS = {
    "pre_state_owned_industrial_asset_share_0811": "state_owned_industrial_assets",
}


def standardize(series: pd.Series) -> pd.Series:
    return (series - series.mean()) / series.std(ddof=1)


def write_codebook(path: Path, panel: pd.DataFrame) -> None:
    definitions = [
        ("mining_employment_10k_person", "Mining employment", "10,000 persons", "Wind EDB; provincial statistical bureaus"),
        ("urban_nonprivate_employment_10k_person", "Urban non-private employment", "10,000 persons", "Wind EDB; provincial statistical bureaus"),
        ("coal_mining_assets_10k_cny", "Coal mining and washing industry assets", "CNY 10,000", "Wind EDB; provincial statistical bureaus"),
        ("industrial_assets_10k_cny", "Industrial enterprise assets", "CNY 10,000", "Wind EDB; provincial statistical bureaus"),
        ("state_owned_industrial_assets_10k_cny", "State-controlled industrial enterprise assets", "CNY 10,000", "Wind EDB; provincial statistical bureaus"),
        ("resource_tax_revenue_10k_cny", "Resource tax revenue", "CNY 10,000", "Wind EDB; provincial statistical bureaus"),
        ("mining_tax_revenue_10k_cny", "Mining-sector tax revenue", "CNY 10,000", "Wind EDB; State Taxation Administration"),
        ("public_budget_revenue_10k_cny", "General public budget revenue", "CNY 10,000", "Wind EDB; provincial statistical bureaus"),
        ("mining_employment_share", "Mining employment / urban non-private employment", "ratio", "Constructed"),
        ("coal_mining_asset_share", "Coal mining assets / industrial assets", "ratio", "Constructed"),
        ("resource_tax_share", "Resource tax revenue / general public budget revenue", "ratio", "Constructed"),
        ("mining_tax_gdp_ratio", "Mining-sector tax revenue / provincial GDP", "ratio", "Constructed"),
        ("state_owned_industrial_asset_share", "State-controlled industrial assets / industrial assets", "ratio", "Constructed"),
        ("pre_mining_employment_share_0811", "2008-2011 mean mining employment share", "ratio", "Constructed"),
        ("pre_coal_mining_asset_share_0811", "2008-2011 mean coal mining asset share", "ratio", "Constructed"),
        ("pre_resource_tax_share_0811", "2008-2011 mean resource tax share", "ratio", "Constructed"),
        ("pre_state_owned_industrial_asset_share_0811", "2008-2011 mean state-controlled industrial asset share", "ratio", "Constructed"),
        ("resdep_soe_z", "Standardized pre-policy state-controlled industrial asset share", "z-score", "Constructed; institutional lock-in dimension"),
        ("post_resdep_soe_z", "Post-2012 x standardized state-controlled industrial asset share", "interaction", "Constructed"),
        ("coalexp_resdep_soe_z", "Coal exposure x standardized state-controlled industrial asset share", "interaction", "Constructed; absorbed by province fixed effects"),
        ("ddd_resdep_soe_z", "Post-2012 x coal exposure x standardized state-controlled industrial asset share", "interaction", "Constructed"),
        ("pre_mining_tax_gdp_ratio_1011", "2010-2011 mean mining-sector tax revenue / GDP", "ratio", "Constructed; fiscal dependence dimension"),
        ("resdep_fisc_z", "Standardized pre-policy mining-sector tax revenue / GDP", "z-score", "Constructed; fiscal dependence dimension"),
        ("post_resdep_fisc_z", "Post-2012 x standardized fiscal dependence", "interaction", "Constructed"),
        ("coalexp_resdep_fisc_z", "Coal exposure x standardized fiscal dependence", "interaction", "Constructed; absorbed by province fixed effects"),
        ("ddd_resdep_fisc_z", "Post-2012 x coal exposure x standardized fiscal dependence", "interaction", "Constructed"),
        ("power_output_jan_nov_10k_kwh", "Interprovincial power output, January-November cumulative", "10,000 kWh", "Wind EDB"),
        ("wind_utilization_hours", "Annual average utilization hours of wind-power equipment", "hours", "Wind EDB"),
        ("solar_utilization_hours_jan_nov", "Solar-power average utilization hours, January-November cumulative", "hours", "Wind EDB"),
        ("wind_utilization_rate", "Actual wind-power utilization rate", "ratio", "National Energy Administration annual monitoring report"),
        ("wind_curtailment_rate", "One minus actual wind-power utilization rate", "ratio", "Constructed from National Energy Administration data"),
        ("solar_utilization_rate", "Actual solar-power utilization rate", "ratio", "National Energy Administration annual monitoring report"),
        ("solar_curtailment_rate", "One minus actual solar-power utilization rate", "ratio", "Constructed from National Energy Administration data"),
        ("early_power_export_ratio_2015_approx", "2015 Jan-Nov power output / 2015 annual power generation", "approximate ratio", "Constructed; reporting windows differ"),
        ("grid_export_pre16_z", "Standardized early power-export proxy", "z-score", "Constructed; supplementary infrastructure condition"),
        ("post16_grid_export_z", "Post-2016 x standardized early power-export proxy", "interaction", "Constructed"),
        ("coalexp_grid_export_z", "Coal exposure x standardized early power-export proxy", "interaction", "Constructed; absorbed by province fixed effects"),
        ("ddd_grid_export16_z", "Post-2016 x coal exposure x standardized early power-export proxy", "interaction", "Constructed"),
        ("resource_dependence_index_pre0811", "Mean standardized pre-policy resource-dependence components; at least two required", "z-score mean", "Constructed"),
        ("resdep_pre", "Stata-safe alias of resource_dependence_index_pre0811", "z-score mean", "Constructed"),
        ("post2012_x_resource_dependence", "Post-2012 indicator x pre-policy resource-dependence index", "interaction", "Constructed"),
        ("post_resdep", "Stata-safe alias of post2012_x_resource_dependence", "interaction", "Constructed"),
        ("coalexp_x_resource_dependence", "Pre-policy coal exposure x pre-policy resource-dependence index", "interaction", "Constructed; absorbed by province fixed effects"),
        ("coalexp_resdep", "Stata-safe alias of coalexp_x_resource_dependence", "interaction", "Constructed; absorbed by province fixed effects"),
        ("post2012_x_coalexp_x_resource_dependence", "Post-2012 x pre-policy coal exposure x pre-policy resource-dependence index", "interaction", "Constructed"),
        ("ddd_resdep", "Stata-safe alias of post2012_x_coalexp_x_resource_dependence", "interaction", "Constructed"),
        ("gfr_pilot2017_prov", "Province containing a first-batch 2017 green-finance reform and innovation pilot zone", "0/1", "2017 State Council first-batch list"),
        ("gfr_did2017", "First-batch pilot province x post-2017", "0/1", "Constructed"),
        ("gfr_ddd_resdep", "First-batch pilot province x post-2017 x pre-policy resource dependence", "interaction", "Constructed"),
    ]
    rows = []
    province_count = panel["province"].nunique()
    for variable, definition, unit, source in definitions:
        valid = panel[variable].notna()
        rows.append(
            {
                "variable": variable,
                "definition": definition,
                "unit": unit,
                "source": source,
                "nonmissing_observations": int(valid.sum()),
                "covered_provinces": int(panel.loc[valid, "province"].nunique()),
                "total_provinces": province_count,
                "first_year": int(panel.loc[valid, "year"].min()) if valid.any() else "",
                "last_year": int(panel.loc[valid, "year"].max()) if valid.any() else "",
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-panel", type=Path, default=Path("data/final_data.1.3.4_did_full_0518.csv"))
    parser.add_argument("--resource-panel", type=Path, default=Path("data/wind_resource_dependency/wind_resource_dependency_panel_2000_2023.csv"))
    parser.add_argument("--resource-pre", type=Path, default=Path("data/wind_resource_dependency/wind_resource_dependency_pre_0811.csv"))
    parser.add_argument("--grid-panel", type=Path, default=Path("data/wind_grid_absorption/wind_grid_absorption_annual_2000_2023.csv"))
    parser.add_argument("--nea-utilization-panel", type=Path, default=Path("data/nea_renewable_monitoring/nea_renewable_utilization_province_2020_2023.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/final_data.1.3.4_did_full_resource_0715.csv"))
    parser.add_argument("--codebook", type=Path, default=Path("data/wind_resource_dependency/resource_dependency_merged_codebook.csv"))
    args = parser.parse_args()

    main_panel = pd.read_csv(args.main_panel)
    resource_panel = pd.read_csv(args.resource_panel).drop(columns=["province_cn"])
    resource_pre = pd.read_csv(args.resource_pre).drop(columns=["province_cn"])
    grid_panel = pd.read_csv(args.grid_panel).drop(columns=["province_cn"])
    nea_utilization = pd.read_csv(args.nea_utilization_panel)[[
        "province", "year", "wind_utilization_rate", "wind_curtailment_rate",
        "solar_utilization_rate", "solar_curtailment_rate", "source_report_year",
    ]]

    if main_panel.duplicated(["province", "year"]).any():
        raise ValueError("Main panel has duplicate province-year keys")
    if resource_panel.duplicated(["province", "year"]).any():
        raise ValueError("Resource panel has duplicate province-year keys")
    if resource_pre.duplicated(["province"]).any():
        raise ValueError("Pre-policy resource file has duplicate province keys")
    if grid_panel.duplicated(["province", "year"]).any():
        raise ValueError("Grid panel has duplicate province-year keys")
    if nea_utilization.duplicated(["province", "year"]).any():
        raise ValueError("NEA utilization panel has duplicate province-year keys")

    panel = main_panel.merge(
        resource_panel,
        on=["province", "year"],
        how="left",
        validate="one_to_one",
    ).merge(
        resource_pre,
        on="province",
        how="left",
        validate="many_to_one",
    ).merge(
        grid_panel,
        on=["province", "year"],
        how="left",
        validate="one_to_one",
    ).merge(
        nea_utilization,
        on=["province", "year"],
        how="left",
        validate="one_to_one",
    )

    province_pre = resource_pre[["province", *PRE_COMPONENTS, *LOCKIN_COMPONENTS]].copy()
    z_columns = []
    for variable, short_name in PRE_COMPONENTS.items():
        z_name = f"z_{variable}"
        province_pre[z_name] = standardize(province_pre[variable])
        z_columns.append(z_name)
    province_pre["resource_dependence_component_n"] = province_pre[z_columns].notna().sum(axis=1)
    province_pre["resource_dependence_index_pre0811"] = (
        province_pre[z_columns].mean(axis=1).where(province_pre["resource_dependence_component_n"] >= 2)
    )
    lockin_z_columns = []
    for variable in LOCKIN_COMPONENTS:
        z_name = f"z_{variable}"
        province_pre[z_name] = standardize(province_pre[variable])
        lockin_z_columns.append(z_name)
    panel = panel.merge(
        province_pre[[
            "province", *z_columns, *lockin_z_columns,
            "resource_dependence_component_n", "resource_dependence_index_pre0811",
        ]],
        on="province",
        how="left",
        validate="many_to_one",
    )

    panel["post2012_x_resource_dependence"] = panel["post2012"] * panel["resource_dependence_index_pre0811"]
    panel["coalexp_x_resource_dependence"] = panel["coalexp_pre"] * panel["resource_dependence_index_pre0811"]
    panel["post2012_x_coalexp_x_resource_dependence"] = panel["coalexp_post"] * panel["resource_dependence_index_pre0811"]
    panel["resdep_pre"] = panel["resource_dependence_index_pre0811"]
    panel["post_resdep"] = panel["post2012_x_resource_dependence"]
    panel["coalexp_resdep"] = panel["coalexp_x_resource_dependence"]
    panel["ddd_resdep"] = panel["post2012_x_coalexp_x_resource_dependence"]

    first_batch_pilot_provinces = {"Zhejiang", "Jiangxi", "Guangdong", "Guizhou", "Xinjiang"}
    panel["gfr_pilot2017_prov"] = panel["province"].isin(first_batch_pilot_provinces).astype("int8")
    panel["post2017"] = (panel["year"] >= 2017).astype("int8")
    panel["gfr_did2017"] = panel["gfr_pilot2017_prov"] * panel["post2017"]
    panel["post2017_resdep"] = panel["post2017"] * panel["resdep_pre"]
    panel["gfr_treat_resdep"] = panel["gfr_pilot2017_prov"] * panel["resdep_pre"]
    panel["gfr_ddd_resdep"] = panel["gfr_did2017"] * panel["resdep_pre"]

    panel["mining_tax_revenue_100m_cny"] = panel["mining_tax_revenue_10k_cny"] / 10000.0
    panel["mining_tax_gdp_ratio"] = panel["mining_tax_revenue_100m_cny"] / panel["gdp"]
    fiscal_pre = (
        panel.loc[panel["year"].between(2010, 2011), ["province", "mining_tax_gdp_ratio"]]
        .groupby("province", as_index=False)
        .agg(
            pre_mining_tax_gdp_ratio_1011=("mining_tax_gdp_ratio", "mean"),
            pre_mining_tax_gdp_ratio_1011_n=("mining_tax_gdp_ratio", "count"),
        )
    )
    fiscal_pre["resdep_fisc_z"] = standardize(fiscal_pre["pre_mining_tax_gdp_ratio_1011"])
    panel = panel.merge(fiscal_pre, on="province", how="left", validate="many_to_one")
    panel["post_resdep_fisc_z"] = panel["post2012"] * panel["resdep_fisc_z"]
    panel["coalexp_resdep_fisc_z"] = panel["coalexp_pre"] * panel["resdep_fisc_z"]
    panel["ddd_resdep_fisc_z"] = panel["coalexp_post"] * panel["resdep_fisc_z"]

    panel["power_output_jan_nov_billion_kwh"] = panel["power_output_jan_nov_10k_kwh"] / 100000.0
    panel["power_export_ratio_approx"] = (
        panel["power_output_jan_nov_billion_kwh"] / panel["total_generation_billion_kwh"]
    )
    early_export = (
        panel.loc[panel["year"].eq(2015), ["province", "power_export_ratio_approx"]]
        .rename(columns={"power_export_ratio_approx": "early_power_export_ratio_2015_approx"})
    )
    early_export["grid_export_pre16_z"] = standardize(early_export["early_power_export_ratio_2015_approx"])
    panel = panel.merge(early_export, on="province", how="left", validate="many_to_one")
    panel["post16_grid_export_z"] = (panel["year"] >= 2016) * panel["grid_export_pre16_z"]
    panel["coalexp_grid_export_z"] = panel["coalexp_pre"] * panel["grid_export_pre16_z"]
    panel["ddd_grid_export16_z"] = (
        (panel["year"] >= 2016) * panel["coalexp_pre"] * panel["grid_export_pre16_z"]
    )

    for variable, short_name in {**PRE_COMPONENTS, **LOCKIN_COMPONENTS}.items():
        panel[f"post2012_x_{short_name}"] = panel["post2012"] * panel[variable]
        panel[f"coalexp_x_{short_name}"] = panel["coalexp_pre"] * panel[variable]
        panel[f"post2012_x_coalexp_x_{short_name}"] = panel["coalexp_post"] * panel[variable]

    component_aliases = {
        "emp": ("pre_mining_employment_share_0811", "z_pre_mining_employment_share_0811"),
        "asset": ("pre_coal_mining_asset_share_0811", "z_pre_coal_mining_asset_share_0811"),
        "tax": ("pre_resource_tax_share_0811", "z_pre_resource_tax_share_0811"),
        "soe": ("pre_state_owned_industrial_asset_share_0811", "z_pre_state_owned_industrial_asset_share_0811"),
    }
    for alias, (variable, z_variable) in component_aliases.items():
        panel[f"resdep_{alias}_pre"] = panel[variable]
        panel[f"post_resdep_{alias}"] = panel["post2012"] * panel[variable]
        panel[f"coalexp_resdep_{alias}"] = panel["coalexp_pre"] * panel[variable]
        panel[f"ddd_resdep_{alias}"] = panel["coalexp_post"] * panel[variable]
        panel[f"resdep_{alias}_z"] = panel[z_variable]
        panel[f"post_resdep_{alias}_z"] = panel["post2012"] * panel[z_variable]
        panel[f"coalexp_resdep_{alias}_z"] = panel["coalexp_pre"] * panel[z_variable]
        panel[f"ddd_resdep_{alias}_z"] = panel["coalexp_post"] * panel[z_variable]

    if len(panel) != len(main_panel):
        raise ValueError("Merge changed the number of province-year observations")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(args.output, index=False, encoding="utf-8-sig")
    write_codebook(args.codebook, panel)

    print(f"output={args.output}")
    print(f"rows={len(panel)} provinces={panel['province'].nunique()} years={panel['year'].min()}-{panel['year'].max()}")
    print(f"columns={len(panel.columns)}")
    print(f"resource_dependence_index_provinces={panel.loc[panel['resource_dependence_index_pre0811'].notna(), 'province'].nunique()}")


if __name__ == "__main__":
    main()
