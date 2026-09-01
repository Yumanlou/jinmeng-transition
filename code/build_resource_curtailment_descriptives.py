#!/usr/bin/env python3
"""Build non-causal descriptive links between resource dependence and curtailment."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "final_data.1.3.4_did_full_resource_0715.csv"
OUT_DIR = ROOT / "result" / "tables" / "0715_resource_dependence"


def main() -> None:
    panel = pd.read_csv(PANEL)
    province = panel.groupby("province", as_index=False).agg(
        resource_dependence_index=("resdep_pre", "first"),
        mining_fiscal_dependence_z=("resdep_fisc_z", "first"),
        state_owned_asset_lockin_z=("resdep_soe_z", "first"),
        early_power_export_z=("grid_export_pre16_z", "first"),
        wind_curtailment_rate_2020_2023=("wind_curtailment_rate", "mean"),
        solar_curtailment_rate_2020_2023=("solar_curtailment_rate", "mean"),
        wind_utilization_hours_2018_2023=("wind_utilization_hours", "mean"),
    )

    variables = [column for column in province.columns if column != "province"]
    corr = province[variables].corr()
    corr_rows = []
    for left in variables:
        for right in variables:
            if variables.index(right) <= variables.index(left):
                continue
            valid = province[[left, right]].dropna()
            corr_rows.append({
                "variable_1": left,
                "variable_2": right,
                "correlation": valid[left].corr(valid[right]),
                "province_count": len(valid),
            })

    case = panel.loc[
        panel["province"].isin(["Shanxi", "Neimenggu"]) & panel["year"].between(2020, 2023),
        [
            "province", "year", "wind_utilization_rate", "wind_curtailment_rate",
            "solar_utilization_rate", "solar_curtailment_rate", "wind_utilization_hours",
            "solar_utilization_hours_jan_nov", "power_output_jan_nov_billion_kwh",
        ],
    ].sort_values(["province", "year"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    province.to_csv(OUT_DIR / "resource_curtailment_province_averages.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(corr_rows).to_csv(
        OUT_DIR / "resource_curtailment_correlations.csv", index=False, encoding="utf-8-sig"
    )
    case.to_csv(OUT_DIR / "shanxi_neimenggu_grid_absorption_2020_2023.csv", index=False, encoding="utf-8-sig")

    print(f"province_rows={len(province)}")
    print(f"correlation_rows={len(corr_rows)}")
    print(f"case_rows={len(case)}")
    print(
        corr.loc[
            ["resource_dependence_index", "mining_fiscal_dependence_z"],
            ["wind_curtailment_rate_2020_2023", "solar_curtailment_rate_2020_2023"],
        ].to_string()
    )


if __name__ == "__main__":
    main()
