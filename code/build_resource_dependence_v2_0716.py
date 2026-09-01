#!/usr/bin/env python3
"""Add coal-production exposure to the policy-pre resource-dependence index."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


BASE_COMPONENTS = [
    "z_pre_mining_employment_share_0811",
    "z_pre_coal_mining_asset_share_0811",
    "z_pre_resource_tax_share_0811",
]


def standardize(series: pd.Series) -> pd.Series:
    return (series - series.mean()) / series.std(ddof=1)


def add_index(panel: pd.DataFrame, production_variable: str, alias: str) -> pd.DataFrame:
    cross = panel.loc[panel["year"].eq(2011), [
        "province", *BASE_COMPONENTS, production_variable,
    ]].copy()
    components = [*BASE_COMPONENTS, production_variable]
    cross[f"resdep_{alias}_component_n"] = cross[components].notna().sum(axis=1)
    raw = cross[components].mean(axis=1).where(cross[f"resdep_{alias}_component_n"] >= 3)
    cross[f"resdep_{alias}"] = standardize(raw)
    panel = panel.merge(
        cross[["province", f"resdep_{alias}_component_n", f"resdep_{alias}"]],
        on="province", how="left", validate="many_to_one",
    )
    panel[f"post_resdep_{alias}"] = panel["post2012"] * panel[f"resdep_{alias}"]
    panel[f"coalexp_resdep_{alias}"] = panel["coalexp_pre"] * panel[f"resdep_{alias}"]
    panel[f"ddd_resdep_{alias}"] = panel["coalexp_post"] * panel[f"resdep_{alias}"]
    return panel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path,
        default=Path("data/final_data.1.3.4_did_full_resource_coalpower_coalprod_0716.csv"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/final_data.1.3.4_did_full_resource_v2_0716.csv"),
    )
    args = parser.parse_args()

    panel = pd.read_csv(args.input, low_memory=False)
    panel = add_index(panel, "coal_production_share_z", "v2share")
    panel = add_index(panel, "coal_production_dep_log_z", "v2log")
    if panel.duplicated(["province", "year"]).any() or len(panel) != 744:
        raise ValueError("Unexpected panel key structure after resource-dependence v2 merge")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(args.output, index=False, encoding="utf-8-sig")
    cross = panel.loc[panel["year"].eq(2011), [
        "province", "resdep_pre", "resdep_v2share", "resdep_v2log",
        "resdep_v2share_component_n", "resdep_v2log_component_n",
    ]]
    print(f"output={args.output} rows={len(panel)} columns={len(panel.columns)}")
    print(cross[["resdep_pre", "resdep_v2share", "resdep_v2log"]].corr().round(4).to_string())
    print(cross.loc[cross["province"].isin(["Shanxi", "Neimenggu"])].to_string(index=False))


if __name__ == "__main__":
    main()
