#!/usr/bin/env python3
"""Build a 31-province renewable-electricity consumption panel from NEA reports.

The consumption measure adjusts local renewable generation for interprovincial
inflows and outflows. It therefore captures realized local absorption more
closely than a province's generation mix alone.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "nea_renewable_monitoring" / "source_docs"
OUT_DIR = ROOT / "data" / "nea_renewable_consumption"

PROVINCE_CN_TO_MAIN = {
    "北京": "Beijing", "天津": "Tianjin", "河北": "Hebei", "山西": "Shanxi",
    "内蒙古": "Neimenggu", "辽宁": "Liaoning", "吉林": "Jilin",
    "黑龙江": "Heilongjiang", "上海": "Shanghai", "江苏": "Jiangsu",
    "浙江": "Zhejiang", "安徽": "Anhui", "福建": "Fujian", "江西": "Jiangxi",
    "山东": "Shandong", "河南": "Henan", "湖北": "Hubei", "湖南": "Hunan",
    "广东": "Guangdong", "广西": "Guangxi", "海南": "Hainan", "重庆": "Chongqing",
    "四川": "Sichuan", "贵州": "Guizhou", "云南": "Yunnan", "西藏": "Xizang",
    "陕西": "Shaanxi", "甘肃": "Gansu", "青海": "Qinghai", "宁夏": "Ningxia",
    "新疆": "Xinjiang",
}

SOURCE_URLS = {
    2015: "https://zfxxgk.nea.gov.cn/auto87/201608/t20160823_2289.htm",
    2016: "https://zfxxgk.nea.gov.cn/auto87/201704/t20170418_2773.htm",
    2017: "https://zfxxgk.nea.gov.cn/auto87/201805/t20180522_3179.htm",
    2018: "https://zfxxgk.nea.gov.cn/auto87/201906/t20190610_3673.htm",
    2019: "https://zfxxgk.nea.gov.cn/2020-05/06/c_139059627.htm",
    2020: "https://zfxxgk.nea.gov.cn/2021-06/20/c_1310039970.htm",
    2021: "https://www.nea.gov.cn/2022-09/16/c_1310663387.htm",
    2022: "https://zfxxgk.nea.gov.cn/2023-09/07/c_1310741874.htm",
    2023: "https://zfxxgk.nea.gov.cn/2024-10/10/c_1310787115.htm",
}


def normalize(value: str) -> str:
    return re.sub(r"[\s\u3000]+", "", value).strip().replace("*", "")


def source_path(year: int) -> Path:
    doc = SOURCE_DIR / f"nea_renewable_monitoring_{year}.doc"
    if doc.exists():
        return doc
    docx = doc.with_suffix(".docx")
    if docx.exists():
        return docx
    raise FileNotFoundError(f"Missing NEA source report for {year}")


def report_lines(year: int) -> list[str]:
    result = subprocess.run(
        ["textutil", "-convert", "txt", "-stdout", str(source_path(year))],
        check=True,
        capture_output=True,
        text=True,
    )
    text = result.stdout.replace("\x07", "\n")
    return [line.strip() for line in text.splitlines() if line.strip()]


def table_section(lines: list[str], table_number: int) -> list[str]:
    start = next(
        index for index, line in enumerate(lines)
        if normalize(line).startswith(f"表{table_number}")
    )
    seen_province = False
    end = len(lines)
    for index in range(start + 1, len(lines)):
        token = normalize(lines[index])
        if token in PROVINCE_CN_TO_MAIN:
            seen_province = True
        if not seen_province:
            continue
        if token.startswith(f"表{table_number + 1}") or re.match(
            r"^[三四五六七八九十]+、", token
        ):
            end = index
            break
    return lines[start + 1:end]


def parse_table(year: int, table_number: int, kind: str) -> list[dict]:
    section = table_section(report_lines(year), table_number)
    province_indexes = [
        index for index, line in enumerate(section)
        if normalize(line) in PROVINCE_CN_TO_MAIN or normalize(line) == "全国"
    ]
    rows: list[dict] = []
    for position, index in enumerate(province_indexes):
        province_cn = normalize(section[index])
        next_index = province_indexes[position + 1] if position + 1 < len(province_indexes) else len(section)
        block = [normalize(value) for value in section[index + 1:next_index]]
        if province_cn == "全国":
            continue

        percentages: list[tuple[int, float]] = []
        numbers: list[tuple[int, float]] = []
        for block_index, value in enumerate(block):
            percent_match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)%\*?", value)
            if percent_match:
                percentages.append((block_index, float(percent_match.group(1)) / 100.0))
                continue
            number_match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)", value)
            if number_match:
                numbers.append((block_index, float(number_match.group(1))))

        if not percentages:
            raise ValueError(f"No percentage found for {year} table {table_number}: {province_cn}")
        first_percent_index = percentages[0][0]
        amount = next((value for idx, value in numbers if idx < first_percent_index), None)
        yoy_change = next((value for idx, value in numbers if idx > first_percent_index), None)
        second_percentage = percentages[1][1] if len(percentages) > 1 else None

        row = {
            "province": PROVINCE_CN_TO_MAIN[province_cn],
            "province_cn": province_cn,
            "year": year,
            f"{kind}_consumption_100m_kwh": amount,
            f"{kind}_consumption_share": percentages[0][1],
            f"{kind}_consumption_share_yoy_pp": yoy_change,
        }
        if year >= 2020:
            row[f"{kind}_minimum_target_share"] = second_percentage
        elif kind == "nonhydro_renewable" and year in {2015, 2016, 2017, 2018}:
            row[f"{kind}_benchmark_2020_share"] = second_percentage
        rows.append(row)
    return rows


def build_panel() -> pd.DataFrame:
    frames = []
    for year in range(2015, 2024):
        total = pd.DataFrame(parse_table(year, 1, "renewable"))
        nonhydro = pd.DataFrame(parse_table(year, 2, "nonhydro_renewable"))
        merged = total.merge(
            nonhydro,
            on=["province", "province_cn", "year"],
            how="outer",
            validate="one_to_one",
        )
        if len(merged) != 31 or merged["province"].nunique() != 31:
            raise ValueError(f"Unexpected province coverage for {year}: {len(merged)} rows")
        merged["source_report"] = f"{year}年度全国可再生能源电力发展监测评价报告"
        merged["source_url"] = SOURCE_URLS[year]
        frames.append(merged)

    panel = pd.concat(frames, ignore_index=True).sort_values(
        ["province", "year"]
    ).reset_index(drop=True)
    panel["re_cons_sh"] = panel["renewable_consumption_share"]
    panel["nonhydro_re_cons_sh"] = panel["nonhydro_renewable_consumption_share"]
    return panel


def merge_main(panel: pd.DataFrame, main_path: Path) -> pd.DataFrame:
    main = pd.read_csv(main_path, low_memory=False)
    if main.duplicated(["province", "year"]).any():
        raise ValueError("Main panel has duplicate province-year keys")
    return main.merge(panel, on=["province", "year"], how="left", validate="one_to_one")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--main-panel",
        type=Path,
        default=ROOT / "data" / "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_0718.csv",
    )
    parser.add_argument(
        "--panel-output",
        type=Path,
        default=OUT_DIR / "nea_renewable_consumption_province_2015_2023.csv",
    )
    parser.add_argument(
        "--coverage-output",
        type=Path,
        default=OUT_DIR / "nea_renewable_consumption_coverage.csv",
    )
    parser.add_argument(
        "--merged-output",
        type=Path,
        default=ROOT / "data" / "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_0718.csv",
    )
    args = parser.parse_args()

    panel = build_panel()
    merged = merge_main(panel, args.main_panel)
    coverage = panel.groupby("year").agg(
        provinces=("province", "nunique"),
        renewable_share_nonmissing=("renewable_consumption_share", "count"),
        nonhydro_share_nonmissing=("nonhydro_renewable_consumption_share", "count"),
        renewable_amount_nonmissing=("renewable_consumption_100m_kwh", "count"),
        nonhydro_amount_nonmissing=("nonhydro_renewable_consumption_100m_kwh", "count"),
    ).reset_index()

    for path in [args.panel_output, args.coverage_output, args.merged_output]:
        path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(args.panel_output, index=False, encoding="utf-8-sig")
    coverage.to_csv(args.coverage_output, index=False, encoding="utf-8-sig")
    merged.to_csv(args.merged_output, index=False, encoding="utf-8-sig")
    print(f"panel={args.panel_output} rows={len(panel)} provinces={panel.province.nunique()}")
    print(f"coverage={args.coverage_output}")
    print(f"merged={args.merged_output} rows={len(merged)} columns={len(merged.columns)}")
    print(coverage.to_string(index=False))


if __name__ == "__main__":
    main()
