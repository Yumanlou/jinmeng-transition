#!/usr/bin/env python3
"""Fetch provincial power-export and renewable-utilization indicators from Wind.

Wind publishes these indicators as monthly year-to-date series. Wind-power
utilization has December observations, while power output and solar-power
utilization are consistently available through November. The output labels
these reporting windows explicitly instead of treating them all as full-year.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from fetch_wind_resource_dependency import (
    PROVINCE_CN_TO_MAIN,
    wind_call,
    write_csv,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "wind_grid_absorption"

SPECS = [
    {
        "series_type": "power_output",
        "query": "各省输出电量累计值",
        "variable": "power_output_jan_nov_10k_kwh",
        "reference_month": 11,
        "accept": lambda name: name.endswith(":输出电量:累计值"),
    },
    {
        "series_type": "wind_utilization_hours",
        "query": "各省发电设备平均利用小时风电累计值",
        "variable": "wind_utilization_hours",
        "reference_month": 12,
        "accept": lambda name: name.endswith(":发电设备平均利用小时:风电:累计值"),
    },
    {
        "series_type": "solar_utilization_hours",
        "query": "中国各省太阳能发电平均利用小时累计值",
        "variable": "solar_utilization_hours_jan_nov",
        "reference_month": 11,
        "accept": lambda name: name.endswith(":平均利用小时:太阳能发电:累计值"),
    },
]


def date_parts(value: object) -> tuple[int, int]:
    text = str(value)
    year = int(text[:4])
    month = int(text[5:7]) if len(text) >= 7 and text[4] in "-/" else int(text[4:6])
    return year, month


def province_from_grid_name(name: str) -> str:
    """Extract province from Wind names such as 中国:山西:输出电量:累计值."""
    parts = name.split(":")
    for part in parts:
        if part in PROVINCE_CN_TO_MAIN:
            return part
    return ""


def main() -> None:
    codebook = []
    monthly_rows = []
    annual_by_key: dict[tuple[str, int], dict] = {}

    for spec in SPECS:
        discovered = wind_call("search", spec["query"])
        selected = []
        seen_codes = set()
        for item in discovered:
            meta = item.get("meta") or {}
            name = meta.get("name", "")
            code = meta.get("code", "")
            province_cn = province_from_grid_name(name)
            if (
                province_cn in PROVINCE_CN_TO_MAIN
                and spec["accept"](name)
                and code not in seen_codes
            ):
                seen_codes.add(code)
                selected.append(meta)

        for start in range(0, len(selected), 20):
            codes = ",".join(meta["code"] for meta in selected[start:start + 20])
            for series in wind_call("fetch", codes, observation="all"):
                meta = series.get("meta") or {}
                name = meta.get("name", "")
                province_cn = province_from_grid_name(name)
                if province_cn not in PROVINCE_CN_TO_MAIN:
                    continue
                province = PROVINCE_CN_TO_MAIN[province_cn]
                codebook.append({
                    "series_type": spec["series_type"],
                    "variable": spec["variable"],
                    "reference_month": spec["reference_month"],
                    "province": province,
                    "province_cn": province_cn,
                    "code": meta.get("code", ""),
                    "name": name,
                    "unit": meta.get("unit", ""),
                    "frequency": meta.get("freq", ""),
                    "source": meta.get("source", ""),
                    "update_date": meta.get("updateDate", ""),
                })
                for date, value in zip(series.get("date", []), series.get("value", [])):
                    if value is None:
                        continue
                    year, month = date_parts(date)
                    if not 2000 <= year <= 2023:
                        continue
                    monthly_rows.append({
                        "province": province,
                        "province_cn": province_cn,
                        "year": year,
                        "month": month,
                        "series_type": spec["series_type"],
                        "variable": spec["variable"],
                        "value": float(value),
                        "unit": meta.get("unit", ""),
                        "code": meta.get("code", ""),
                    })
                    if month == spec["reference_month"]:
                        key = (province, year)
                        if key not in annual_by_key:
                            annual_by_key[key] = {
                                "province": province,
                                "province_cn": province_cn,
                                "year": year,
                            }
                        annual_by_key[key][spec["variable"]] = float(value)

    codebook.sort(key=lambda row: (row["series_type"], row["province"]))
    monthly_rows.sort(key=lambda row: (row["province"], row["year"], row["month"], row["series_type"]))
    annual_rows = [annual_by_key[key] for key in sorted(annual_by_key)]

    write_csv(
        OUT_DIR / "wind_grid_absorption_codebook.csv",
        codebook,
        ["series_type", "variable", "reference_month", "province", "province_cn", "code", "name", "unit", "frequency", "source", "update_date"],
    )
    write_csv(
        OUT_DIR / "wind_grid_absorption_monthly_2000_2023.csv",
        monthly_rows,
        ["province", "province_cn", "year", "month", "series_type", "variable", "value", "unit", "code"],
    )
    write_csv(
        OUT_DIR / "wind_grid_absorption_annual_2000_2023.csv",
        annual_rows,
        ["province", "province_cn", "year", "power_output_jan_nov_10k_kwh", "wind_utilization_hours", "solar_utilization_hours_jan_nov"],
    )

    coverage = []
    for spec in SPECS:
        values = [row for row in annual_rows if row.get(spec["variable"]) not in (None, "")]
        coverage.append({
            "series_type": spec["series_type"],
            "variable": spec["variable"],
            "reference_month": spec["reference_month"],
            "series_count": sum(row["series_type"] == spec["series_type"] for row in codebook),
            "covered_provinces": len({row["province"] for row in values}),
            "annual_observations": len(values),
            "first_year": min((row["year"] for row in values), default=""),
            "last_year": max((row["year"] for row in values), default=""),
        })
    write_csv(
        OUT_DIR / "wind_grid_absorption_coverage.csv",
        coverage,
        ["series_type", "variable", "reference_month", "series_count", "covered_provinces", "annual_observations", "first_year", "last_year"],
    )
    for row in coverage:
        print(row)


if __name__ == "__main__":
    main()
