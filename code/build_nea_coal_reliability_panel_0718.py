#!/usr/bin/env python3
"""Extract provincial coal-unit operation and standby hours from NEA reports."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "nea_power_reliability" / "source_pdfs"
OUT_DIR = ROOT / "data" / "nea_power_reliability"

PAGE_HINTS = {2018: 34, 2019: 32, 2020: 33, 2021: 27, 2022: 29, 2023: 27}

PROVINCE_VARIANTS = {
    "北京市": "Beijing", "天津市": "Tianjin", "河北省": "Hebei", "山西省": "Shanxi",
    "内蒙古自治区": "Neimenggu", "辽宁省": "Liaoning", "吉林省": "Jilin",
    "黑龙江省": "Heilongjiang", "上海市": "Shanghai", "江苏省": "Jiangsu",
    "浙江省": "Zhejiang", "安徽省": "Anhui", "福建省": "Fujian", "江西省": "Jiangxi",
    "山东省": "Shandong", "河南省": "Henan", "湖北省": "Hubei", "湖南省": "Hunan",
    "广东省": "Guangdong", "广西壮族自治区": "Guangxi", "广西自治区": "Guangxi",
    "广西区": "Guangxi",
    "海南省": "Hainan", "重庆市": "Chongqing", "四川省": "Sichuan", "贵州省": "Guizhou",
    "云南省": "Yunnan", "陕西省": "Shaanxi", "甘肃省": "Gansu", "青海省": "Qinghai",
    "宁夏回族自治区": "Ningxia", "宁夏自治区": "Ningxia",
    "新疆维吾尔自治区": "Xinjiang", "新疆自治区": "Xinjiang", "新疆区": "Xinjiang",
}

SOURCE_URLS = {
    2018: "http://prpq.nea.gov.cn/9152.pdf",
    2019: "https://prpq.nea.gov.cn/uploads/file1/20260612/6a2b67c840cdf.pdf",
    2020: "https://prpq.nea.gov.cn/uploads/file1/20221220/63a11862d6604.pdf",
    2021: "https://prpq.nea.gov.cn/uploads/file1/20230308/640801ab6e248.pdf",
    2022: "https://prpq.nea.gov.cn/uploads/file1/20231213/657951e0b1c7a.pdf",
    2023: "https://prpq.nea.gov.cn/uploads/file1/20240911/66e102e09bfea.pdf",
}


def normalize(value: str) -> str:
    return re.sub(r"\s+", "", value)


def parse_page(year: int) -> list[dict]:
    pdf = SOURCE_DIR / f"nea_power_reliability_{year}.pdf"
    reader = PdfReader(pdf)
    page_index = PAGE_HINTS[year]
    # Some annual tables continue onto the following PDF page (notably 2022).
    text = "\n".join(
        reader.pages[index].extract_text() or ""
        for index in range(page_index, min(page_index + 2, len(reader.pages)))
    )
    rows = []
    for raw_line in text.splitlines():
        line = normalize(raw_line)
        province = None
        matched_variant = None
        for variant in sorted(PROVINCE_VARIANTS, key=len, reverse=True):
            if line.startswith(variant):
                province = PROVINCE_VARIANTS[variant]
                matched_variant = variant
                break
        if province is None:
            continue
        # Preserve whitespace between adjacent numeric columns. The normalized
        # line is only for robust province-name matching.
        values = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", raw_line)]
        if year <= 2020 and len(values) >= 5:
            unit_count, average_capacity, utilization_hours, operating_hours, standby_hours = values[:5]
        elif year >= 2021 and len(values) >= 4:
            unit_count, average_capacity, operating_hours, standby_hours = values[:4]
            utilization_hours = None
        else:
            continue
        # Narrative text preceding the table can also begin with a province
        # name. A valid row starts with a plausible integer unit count.
        if not unit_count.is_integer() or not 0 < unit_count <= 500:
            continue
        rows.append({
            "province": province,
            "year": year,
            "coal_unit_count": int(unit_count),
            "coal_unit_average_capacity_mw": average_capacity,
            "coal_unit_utilization_hours": utilization_hours,
            "coal_unit_operating_hours": operating_hours,
            "coal_unit_standby_hours": standby_hours,
            "coal_unit_operating_factor": operating_hours / 8784.0 if year % 4 == 0 else operating_hours / 8760.0,
            "coal_unit_standby_factor": standby_hours / 8784.0 if year % 4 == 0 else standby_hours / 8760.0,
            "source_report": f"{year}年全国电力可靠性年度报告",
            "source_url": SOURCE_URLS[year],
        })
    frame = pd.DataFrame(rows)
    if len(frame) != 30 or frame["province"].nunique() != 30:
        duplicates = frame.loc[frame["province"].duplicated(keep=False), "province"].tolist()
        raise ValueError(
            f"Expected 30 reported provinces for {year}, got {len(frame)} rows and "
            f"{frame['province'].nunique()} provinces; duplicates={duplicates}"
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--main-panel", type=Path,
        default=ROOT / "data" / "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_0718.csv",
    )
    parser.add_argument(
        "--merged-output", type=Path,
        default=ROOT / "data" / "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_0718.csv",
    )
    args = parser.parse_args()

    rows = []
    for year in range(2018, 2024):
        rows.extend(parse_page(year))
        rows.append({
            "province": "Xizang", "year": year, "coal_unit_count": 0,
            "source_report": f"{year}年全国电力可靠性年度报告",
            "source_url": SOURCE_URLS[year],
        })
    panel = pd.DataFrame(rows).sort_values(["province", "year"]).reset_index(drop=True)
    coverage = panel.groupby("year").agg(
        provinces=("province", "nunique"),
        reported_provinces=("coal_unit_operating_hours", "count"),
        utilization_hours_nonmissing=("coal_unit_utilization_hours", "count"),
        operating_hours_nonmissing=("coal_unit_operating_hours", "count"),
        standby_hours_nonmissing=("coal_unit_standby_hours", "count"),
    ).reset_index()
    main = pd.read_csv(args.main_panel, low_memory=False)
    merged = main.merge(panel, on=["province", "year"], how="left", validate="one_to_one")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT_DIR / "nea_coal_unit_reliability_province_2018_2023.csv", index=False, encoding="utf-8-sig")
    coverage.to_csv(OUT_DIR / "nea_coal_unit_reliability_coverage.csv", index=False, encoding="utf-8-sig")
    merged.to_csv(args.merged_output, index=False, encoding="utf-8-sig")
    print(f"panel rows={len(panel)} provinces={panel.province.nunique()}")
    print(f"merged={args.merged_output} rows={len(merged)} columns={len(merged.columns)}")
    print(coverage.to_string(index=False))


if __name__ == "__main__":
    main()
