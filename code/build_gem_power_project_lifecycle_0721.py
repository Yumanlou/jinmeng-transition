#!/usr/bin/env python3
"""Build retrospective province-year power-project lifecycle measures from GEM."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "gem_power_project_lifecycle"
SOURCE_DIR = DATA_DIR / "source"

COAL_FILE = SOURCE_DIR / "GEM_GCPT_January_2026.xlsx"
WIND_FILE = SOURCE_DIR / "GEM_GWPT_February_2026.xlsx"
SOLAR_FILE = SOURCE_DIR / "GEM_GSPT_February_2026.xlsx"

BASE_PANEL = ROOT / "data" / (
    "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_"
    "tide_absorption_monthly_reliability_policyworkreports_0721.csv"
)
OUTPUT_PANEL = ROOT / "data" / (
    "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_"
    "tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_0721.csv"
)

PROVINCE_MAP = {
    "Anhui": "Anhui",
    "Beijing": "Beijing",
    "Chongqing": "Chongqing",
    "Fujian": "Fujian",
    "Gansu": "Gansu",
    "Guangdong": "Guangdong",
    "Guangxi": "Guangxi",
    "Guizhou": "Guizhou",
    "Hainan": "Hainan",
    "Hebei": "Hebei",
    "Heilongjiang": "Heilongjiang",
    "Henan": "Henan",
    "Hubei": "Hubei",
    "Hunan": "Hunan",
    "Inner Mongolia": "Neimenggu",
    "Jiangsu": "Jiangsu",
    "Jiangxi": "Jiangxi",
    "Jilin": "Jilin",
    "Liaoning": "Liaoning",
    "Ningxia": "Ningxia",
    "Qinghai": "Qinghai",
    "Shaanxi": "Shaanxi",
    "Shandong": "Shandong",
    "Shanghai": "Shanghai",
    "Shanxi": "Shanxi",
    "Sichuan": "Sichuan",
    "Tianjin": "Tianjin",
    "Tibet": "Xizang",
    "Xinjiang": "Xinjiang",
    "Yunnan": "Yunnan",
    "Zhejiang": "Zhejiang",
}

ASSET_SPECS = {
    "coal": {
        "path": COAL_FILE,
        "sheet": "Units",
        "province_col": "Subnational unit (province, state)",
        "id_col": "GEM unit/phase ID",
    },
    "wind": {
        "path": WIND_FILE,
        "sheet": "Data",
        "province_col": "State/Province",
        "id_col": "GEM phase ID",
    },
    "solar": {
        "path": SOLAR_FILE,
        "sheet": "Utility-Scale (1 MW+)",
        "province_col": "State/Province",
        "id_col": "GEM phase ID",
    },
}

ACTIVE_OR_HISTORICAL_STATUSES = {"operating", "retired", "mothballed"}


def load_asset(asset: str, spec: dict[str, object]) -> pd.DataFrame:
    usecols = [
        "Country/Area",
        str(spec["province_col"]),
        str(spec["id_col"]),
        "Capacity (MW)",
        "Status",
        "Start year",
        "Retired year",
    ]
    data = pd.read_excel(spec["path"], sheet_name=spec["sheet"], usecols=usecols)
    data = data.loc[data["Country/Area"].eq("China")].copy()
    data["province"] = data[str(spec["province_col"])].map(PROVINCE_MAP)
    data["asset"] = asset
    data["capacity_mw"] = pd.to_numeric(data["Capacity (MW)"], errors="coerce")
    data["start_year"] = pd.to_numeric(data["Start year"], errors="coerce")
    data["retired_year"] = pd.to_numeric(data["Retired year"], errors="coerce")
    data["status"] = data["Status"].astype(str).str.strip().str.lower()
    data["gem_id"] = data[str(spec["id_col"])].astype(str)

    if data["province"].isna().any():
        missing = sorted(data.loc[data["province"].isna(), str(spec["province_col"])].dropna().unique())
        raise ValueError(f"Unmapped {asset} provinces: {missing}")
    return data[
        ["province", "asset", "gem_id", "capacity_mw", "status", "start_year", "retired_year"]
    ]


def build_lifecycle(assets: pd.DataFrame) -> pd.DataFrame:
    provinces = sorted(PROVINCE_MAP.values())
    years = range(2000, 2024)
    rows: list[dict[str, object]] = []

    for asset in ASSET_SPECS:
        subset = assets.loc[
            assets["asset"].eq(asset) & assets["status"].isin(ACTIVE_OR_HISTORICAL_STATUSES)
        ].copy()
        for province in provinces:
            province_assets = subset.loc[subset["province"].eq(province)]
            for year in years:
                commissioned = province_assets.loc[province_assets["start_year"].eq(year)]
                retired = province_assets.loc[province_assets["retired_year"].eq(year)]
                observed_start = province_assets["start_year"].notna()
                active = province_assets.loc[
                    observed_start
                    & province_assets["start_year"].le(year)
                    & (province_assets["retired_year"].isna() | province_assets["retired_year"].gt(year))
                ]
                rows.append(
                    {
                        "province": province,
                        "year": year,
                        "asset": asset,
                        "gem_new_capacity_mw": commissioned["capacity_mw"].sum(min_count=1),
                        "gem_new_project_count": commissioned["gem_id"].nunique(),
                        "gem_retired_capacity_mw": retired["capacity_mw"].sum(min_count=1),
                        "gem_retired_project_count": retired["gem_id"].nunique(),
                        "gem_reconstructed_stock_mw": active["capacity_mw"].sum(min_count=1),
                        "gem_reconstructed_stock_count": active["gem_id"].nunique(),
                    }
                )

    long = pd.DataFrame(rows)
    value_cols = [c for c in long.columns if c.startswith("gem_")]
    wide = long.pivot(index=["province", "year"], columns="asset", values=value_cols)
    wide.columns = [f"{metric.replace('gem_', 'gem_')}_{asset}" for metric, asset in wide.columns]
    wide = wide.reset_index()
    lifecycle_cols = [c for c in wide.columns if c.startswith("gem_")]
    wide[lifecycle_cols] = wide[lifecycle_cols].fillna(0)

    # Combined wind and solar measures are useful for the clean-energy investment margin.
    for metric in value_cols:
        wind_col = f"{metric}_wind"
        solar_col = f"{metric}_solar"
        wide[f"{metric}_windsolar"] = wide[[wind_col, solar_col]].sum(axis=1, min_count=1)

    aliases = {
        "gem_coal_new_mw": "gem_new_capacity_mw_coal",
        "gem_wind_new_mw": "gem_new_capacity_mw_wind",
        "gem_solar_new_mw": "gem_new_capacity_mw_solar",
        "gem_ws_new_mw": "gem_new_capacity_mw_windsolar",
        "gem_coal_retired_mw": "gem_retired_capacity_mw_coal",
        "gem_coal_stock_mw": "gem_reconstructed_stock_mw_coal",
        "gem_wind_stock_mw": "gem_reconstructed_stock_mw_wind",
        "gem_solar_stock_mw": "gem_reconstructed_stock_mw_solar",
        "gem_ws_stock_mw": "gem_reconstructed_stock_mw_windsolar",
    }
    for alias, source in aliases.items():
        wide[alias] = wide[source]
    return wide


def build_current_pipeline(assets: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        assets.groupby(["province", "asset", "status"], as_index=False)
        .agg(project_count=("gem_id", "nunique"), capacity_mw=("capacity_mw", "sum"))
    )
    count = grouped.pivot(index="province", columns=["asset", "status"], values="project_count")
    count.columns = [f"gem2026_{asset}_{status}_project_count" for asset, status in count.columns]
    cap = grouped.pivot(index="province", columns=["asset", "status"], values="capacity_mw")
    cap.columns = [f"gem2026_{asset}_{status}_capacity_mw" for asset, status in cap.columns]
    return count.join(cap, how="outer").fillna(0).reset_index()


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    assets = pd.concat(
        [load_asset(asset, spec) for asset, spec in ASSET_SPECS.items()], ignore_index=True
    )
    lifecycle = build_lifecycle(assets)
    pipeline = build_current_pipeline(assets)

    lifecycle_path = DATA_DIR / "gem_province_year_lifecycle_2000_2023.csv"
    pipeline_path = DATA_DIR / "gem_province_current_pipeline_2026.csv"
    assets_path = DATA_DIR / "gem_china_project_units_2026_snapshot.csv"
    lifecycle.to_csv(lifecycle_path, index=False, encoding="utf-8-sig")
    pipeline.to_csv(pipeline_path, index=False, encoding="utf-8-sig")
    assets.to_csv(assets_path, index=False, encoding="utf-8-sig")

    panel = pd.read_csv(BASE_PANEL, low_memory=False)
    merged = panel.merge(lifecycle, on=["province", "year"], how="left", validate="one_to_one")
    merged = merged.merge(pipeline, on="province", how="left", validate="many_to_one")
    if len(merged) != len(panel) or merged.duplicated(["province", "year"]).any():
        raise ValueError("Panel key integrity check failed after GEM lifecycle merge")
    merged.to_csv(OUTPUT_PANEL, index=False, encoding="utf-8-sig")

    coverage = []
    for asset, group in assets.groupby("asset"):
        relevant = group.loc[group["status"].isin(ACTIVE_OR_HISTORICAL_STATUSES)]
        coverage.append(
            {
                "asset": asset,
                "china_rows": int(len(group)),
                "active_or_historical_rows": int(len(relevant)),
                "start_year_nonmissing_share": float(relevant["start_year"].notna().mean()),
                "retired_year_nonmissing_share": float(relevant["retired_year"].notna().mean()),
                "province_count": int(group["province"].nunique()),
            }
        )
    pd.DataFrame(coverage).to_csv(
        DATA_DIR / "gem_lifecycle_coverage.csv", index=False, encoding="utf-8-sig"
    )

    metadata = {
        "source_record": "https://zenodo.org/records/20843067",
        "source_doi": "10.5281/zenodo.20843067",
        "original_source": "Global Energy Monitor power trackers",
        "license": "CC BY 4.0",
        "retrieved": "2026-07-21",
        "historical_measure_note": (
            "Province-year additions, retirements, and stocks are reconstructed from the start and "
            "retired years recorded in the 2026 tracker snapshot. They are retrospective project-level "
            "measures, not contemporaneous historical vintages. Missing start years make early stocks "
            "lower bounds; official yearbook capacity remains the primary level measure."
        ),
        "output_panel": str(OUTPUT_PANEL.relative_to(ROOT)),
    }
    (DATA_DIR / "source_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"lifecycle={lifecycle_path.relative_to(ROOT)} rows={len(lifecycle)}")
    print(f"pipeline={pipeline_path.relative_to(ROOT)} rows={len(pipeline)}")
    print(f"panel={OUTPUT_PANEL.relative_to(ROOT)} shape={merged.shape}")


if __name__ == "__main__":
    main()
