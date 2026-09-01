#!/usr/bin/env python3
"""Fetch annual provincial raw-coal output from Wind monthly YTD series.

The annual observation is the December cumulative value. Missing December
observations and provinces absent from Wind are left missing, never set to zero.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from fetch_wind_resource_dependency import PROVINCE_CN_TO_MAIN, wind_call


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "wind_raw_coal_output"

PROVINCE_CODES = {
    "北京": "S0075432", "河北": "S0075434", "山西": "S0075435",
    "内蒙古": "S0075436", "辽宁": "S0075437", "吉林": "S0075438",
    "黑龙江": "S0075439", "江苏": "S0075440", "安徽": "S0075442",
    "江西": "S0075444", "山东": "S0075445", "河南": "S0075446",
    "湖北": "S0075447", "湖南": "S0075448", "广西": "S0075449",
    "重庆": "S0075450", "四川": "S0075451", "云南": "S0075453",
    "陕西": "S0075454", "甘肃": "S0075455", "青海": "S0075456",
    "宁夏": "S0075457", "新疆": "S0075458", "贵州": "S5117168",
    "浙江": "S5117157", "福建": "S5117159",
}
NATIONAL_CODE = "S0026991"


def to_10k_ton(value: float, unit: str) -> float:
    if unit == "万吨":
        return float(value)
    if unit == "吨":
        return float(value) / 10000.0
    raise ValueError(f"Unsupported raw-coal output unit: {unit}")


def annual_december_rows(series: dict, province: str | None = None) -> list[dict]:
    meta = series.get("meta") or {}
    rows = []
    for date, value in zip(series.get("date", []), series.get("value", [])):
        date_text = str(date)
        if not date_text.endswith("1231") or value is None:
            continue
        year = int(date_text[:4])
        if year < 2000 or year > 2023:
            continue
        rows.append({
            "province": province,
            "year": year,
            "raw_coal_output_10k_ton": to_10k_ton(float(value), meta.get("unit", "")),
            "wind_code": meta.get("code", ""),
            "wind_name": meta.get("name", ""),
            "wind_original_unit": meta.get("unit", ""),
            "wind_source": meta.get("source", ""),
            "wind_update_date": meta.get("updateDate", ""),
            "annualization_rule": "December YTD value",
        })
    return rows


def standardize(series: pd.Series) -> pd.Series:
    return (series - series.mean()) / series.std(ddof=1)


def fetch_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict] = []
    items = list(PROVINCE_CODES.items())
    for start in range(0, len(items), 20):
        batch = items[start:start + 20]
        code_to_province = {code: PROVINCE_CN_TO_MAIN[province_cn] for province_cn, code in batch}
        codes = ",".join(code_to_province)
        for series in wind_call("fetch", codes, observation="all"):
            code = (series.get("meta") or {}).get("code", "")
            if code not in code_to_province:
                continue
            rows.extend(annual_december_rows(series, code_to_province[code]))

    national_series = wind_call("fetch", NATIONAL_CODE, observation="all")
    if len(national_series) != 1:
        raise ValueError("Expected one national raw-coal output series")
    national = pd.DataFrame(annual_december_rows(national_series[0], "China")).rename(columns={
        "raw_coal_output_10k_ton": "national_raw_coal_output_10k_ton",
        "wind_code": "national_wind_code",
        "wind_name": "national_wind_name",
        "wind_original_unit": "national_wind_original_unit",
        "wind_source": "national_wind_source",
        "wind_update_date": "national_wind_update_date",
    })
    national = national.drop(columns=["province", "annualization_rule"])

    panel = pd.DataFrame(rows)
    if panel.duplicated(["province", "year"]).any():
        raise ValueError("Duplicate province-year values in annualized raw-coal panel")
    panel = panel.merge(national, on="year", how="left", validate="many_to_one")
    panel["raw_coal_output_share_national"] = (
        panel["raw_coal_output_10k_ton"] / panel["national_raw_coal_output_10k_ton"]
    )
    panel["source_quality_flag"] = np.where(
        panel["wind_source"].eq("国家统计局"), "NBS", "secondary_compilation"
    )
    return panel.sort_values(["province", "year"]), national.sort_values("year")


def build_pre_summary(panel: pd.DataFrame) -> pd.DataFrame:
    pre_0811 = panel.loc[panel["year"].between(2008, 2011)].groupby("province", as_index=False).agg(
        pre_raw_coal_output_0811_10k_ton=("raw_coal_output_10k_ton", "mean"),
        pre_raw_coal_output_share_0811=("raw_coal_output_share_national", "mean"),
        pre_raw_coal_output_0811_n=("raw_coal_output_10k_ton", "count"),
        pre_raw_coal_source_quality=("source_quality_flag", "first"),
    )
    pre_0809 = panel.loc[panel["year"].between(2008, 2009)].groupby("province", as_index=False).agg(
        pre_raw_coal_output_0809_10k_ton=("raw_coal_output_10k_ton", "mean"),
        pre_raw_coal_output_share_0809=("raw_coal_output_share_national", "mean"),
        pre_raw_coal_output_0809_n=("raw_coal_output_10k_ton", "count"),
    )
    return pre_0809.merge(pre_0811, on="province", how="outer", validate="one_to_one")


def merge_main(main: pd.DataFrame, panel: pd.DataFrame, pre: pd.DataFrame) -> pd.DataFrame:
    merged = main.merge(
        panel[[
            "province", "year", "raw_coal_output_10k_ton",
            "national_raw_coal_output_10k_ton", "raw_coal_output_share_national",
            "wind_code", "wind_source", "source_quality_flag",
        ]],
        on=["province", "year"], how="left", validate="one_to_one",
    ).merge(pre, on="province", how="left", validate="many_to_one")

    pop2011 = merged.loc[merged["year"].eq(2011), ["province", "population"]].rename(
        columns={"population": "population_2011_10k_person_coal"}
    )
    merged = merged.merge(pop2011, on="province", how="left", validate="many_to_one")
    population_million = merged["population_2011_10k_person_coal"] / 100.0
    merged["pre_raw_coal_output_0811_per_million_pop"] = (
        merged["pre_raw_coal_output_0811_10k_ton"] / population_million
    )
    merged["pre_raw_coal_output_0809_per_million_pop"] = (
        merged["pre_raw_coal_output_0809_10k_ton"] / population_million
    )

    cross_section = merged.loc[merged["year"].eq(2011), [
        "province", "pre_raw_coal_output_0809_per_million_pop",
        "pre_raw_coal_output_share_0809",
    ]].copy()
    cross_section["coal_production_dep_log_z"] = standardize(
        np.log1p(cross_section["pre_raw_coal_output_0809_per_million_pop"])
    )
    cross_section["coal_production_share_z"] = standardize(
        cross_section["pre_raw_coal_output_share_0809"]
    )
    merged = merged.merge(
        cross_section[["province", "coal_production_dep_log_z", "coal_production_share_z"]],
        on="province", how="left", validate="many_to_one",
    )
    for variable in ["coal_production_dep_log_z", "coal_production_share_z"]:
        merged[f"post_{variable}"] = merged["post2012"] * merged[variable]
        merged[f"coalexp_{variable}"] = merged["coalexp_pre"] * merged[variable]
        merged[f"ddd_{variable}"] = merged["coalexp_post"] * merged[variable]
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--main-panel", type=Path,
        default=Path("data/final_data.1.3.4_did_full_resource_coalpower_0716.csv"),
    )
    parser.add_argument(
        "--merged-output", type=Path,
        default=Path("data/final_data.1.3.4_did_full_resource_coalpower_coalprod_0716.csv"),
    )
    args = parser.parse_args()

    panel, national = fetch_panel()
    pre = build_pre_summary(panel)
    main_panel = pd.read_csv(args.main_panel, low_memory=False)
    merged = merge_main(main_panel, panel, pre)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT_DIR / "wind_raw_coal_output_dec_ytd_2000_2023.csv", index=False, encoding="utf-8-sig")
    national.to_csv(OUT_DIR / "wind_national_raw_coal_output_dec_ytd_2000_2023.csv", index=False, encoding="utf-8-sig")
    pre.to_csv(OUT_DIR / "wind_raw_coal_output_pre_0811.csv", index=False, encoding="utf-8-sig")
    args.merged_output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.merged_output, index=False, encoding="utf-8-sig")

    coverage = panel.groupby("province").agg(
        observations=("year", "size"), first_year=("year", "min"), last_year=("year", "max"),
        pre_0811_n=("year", lambda x: int(x.between(2008, 2011).sum())),
        source=("wind_source", "first"),
    ).reset_index()
    coverage.to_csv(OUT_DIR / "wind_raw_coal_output_coverage.csv", index=False, encoding="utf-8-sig")
    print(f"province_count={panel['province'].nunique()} observations={len(panel)}")
    print(f"complete_pre_0809={(pre['pre_raw_coal_output_0809_n'] == 2).sum()}")
    print(f"complete_pre_0811={(coverage['pre_0811_n'] == 4).sum()}")
    print(f"merged_output={args.merged_output} rows={len(merged)} columns={len(merged.columns)}")
    print(pre.loc[pre["province"].isin(["Shanxi", "Neimenggu"])].to_string(index=False))


if __name__ == "__main__":
    main()
