#!/usr/bin/env python3
"""Clean provincial wind and solar utilization rates from NEA annual reports."""

from __future__ import annotations

import csv
import re
import subprocess
from collections import defaultdict
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "nea_renewable_monitoring" / "source_docs"
OUT_DIR = ROOT / "data" / "nea_renewable_monitoring"

PROVINCE_CN_TO_MAIN = {
    "北京": "Beijing", "天津": "Tianjin", "河北": "Hebei", "山西": "Shanxi", "内蒙古": "Neimenggu",
    "辽宁": "Liaoning", "吉林": "Jilin", "黑龙江": "Heilongjiang", "上海": "Shanghai",
    "江苏": "Jiangsu", "浙江": "Zhejiang", "安徽": "Anhui", "福建": "Fujian",
    "江西": "Jiangxi", "山东": "Shandong", "河南": "Henan", "湖北": "Hubei",
    "湖南": "Hunan", "广东": "Guangdong", "广西": "Guangxi", "海南": "Hainan",
    "重庆": "Chongqing", "四川": "Sichuan", "贵州": "Guizhou", "云南": "Yunnan",
    "西藏": "Xizang", "陕西": "Shaanxi", "甘肃": "Gansu", "青海": "Qinghai",
    "宁夏": "Ningxia", "新疆": "Xinjiang",
}

SOURCE_URLS = {
    2021: "https://www.nea.gov.cn/2022-09/16/c_1310663387.htm",
    2022: "https://zfxxgk.nea.gov.cn/2023-09/07/c_1310741874.htm",
    2023: "https://zfxxgk.nea.gov.cn/2024-10/10/c_1310787115.htm",
}


def clean_text(value: str) -> str:
    return re.sub(r"\s+", "", value.replace("\u3000", "").replace("\x0c", ""))


def percent(value: str) -> float:
    return float(clean_text(value).replace("%", "")) / 100.0


def add_value(store: dict, region: str, year: int, kind: str, value: float, source_year: int) -> None:
    key = (clean_text(region), year)
    variable = f"{kind}_utilization_rate"
    if key in store and variable in store[key]:
        if abs(store[key][variable] - value) > 1e-9:
            raise ValueError(f"Conflicting values for {key} {variable}")
        return
    store.setdefault(key, {"region_cn": key[0], "year": year})[variable] = value
    store[key][f"{kind}_source_report_year"] = source_year


def parse_docx_table(store: dict, report_year: int, table_index: int, kind: str) -> None:
    doc = Document(SOURCE_DIR / f"nea_renewable_monitoring_{report_year}.docx")
    table = doc.tables[table_index]
    headers = [clean_text(cell.text) for cell in table.rows[0].cells]
    years = []
    for header in headers[1:3]:
        match = re.search(r"(20\d{2})年", header)
        if not match:
            raise ValueError(f"Cannot identify year in {report_year} table {table_index}: {header}")
        years.append(int(match.group(1)))
    for row in table.rows[1:]:
        cells = [clean_text(cell.text) for cell in row.cells]
        region = cells[0]
        if not region or region == "全国":
            continue
        add_value(store, region, years[0], kind, percent(cells[1]), report_year)
        add_value(store, region, years[1], kind, percent(cells[2]), report_year)


def parse_2023_text_table(store: dict, start_marker: str, end_marker: str, kind: str) -> None:
    source = SOURCE_DIR / "nea_renewable_monitoring_2023.doc"
    result = subprocess.run(
        ["textutil", "-convert", "txt", "-stdout", str(source)],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [clean_text(line) for line in result.stdout.splitlines() if clean_text(line)]
    start = next(i for i, line in enumerate(lines) if line.startswith(start_marker))
    end = next(i for i, line in enumerate(lines[start + 1:], start + 1) if line.startswith(end_marker))
    body = lines[start + 1:end]
    body = [line for line in body if line not in {"2022年实际利用率", "2023年实际利用率", "全国"}]
    if body[:2] == ["96.8%", "97.3%"] or body[:2] == ["98.3%", "98.0%"]:
        body = body[2:]
    if len(body) % 3:
        raise ValueError(f"Unexpected 2023 {kind} table length: {len(body)}")
    for index in range(0, len(body), 3):
        region, value_2022, value_2023 = body[index:index + 3]
        add_value(store, region, 2022, kind, percent(value_2022), 2023)
        add_value(store, region, 2023, kind, percent(value_2023), 2023)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    regional: dict[tuple[str, int], dict] = {}
    parse_docx_table(regional, 2021, 4, "wind")
    parse_docx_table(regional, 2021, 5, "solar")
    parse_docx_table(regional, 2022, 4, "wind")
    parse_docx_table(regional, 2022, 5, "solar")
    parse_2023_text_table(regional, "表32023年全国风电并网消纳情况", "表42023年全国光伏并网消纳情况", "wind")
    parse_2023_text_table(regional, "表42023年全国光伏并网消纳情况", "表52023年全国主要流域水电利用情况", "solar")

    regional_rows = []
    for key in sorted(regional, key=lambda item: (item[1], item[0])):
        row = regional[key]
        for kind in ("wind", "solar"):
            rate = row.get(f"{kind}_utilization_rate")
            if rate is not None:
                row[f"{kind}_curtailment_rate"] = 1.0 - rate
        regional_rows.append(row)

    province_rows = []
    by_year: dict[int, list[dict]] = defaultdict(list)
    for row in regional_rows:
        by_year[row["year"]].append(row)
    for year in sorted(by_year):
        rows = by_year[year]
        for region_cn, province in PROVINCE_CN_TO_MAIN.items():
            source_rows = [row for row in rows if row["region_cn"] == region_cn]
            method = "direct province value"
            if province == "Neimenggu":
                source_rows = [row for row in rows if row["region_cn"] in {"蒙西", "蒙东"}]
                method = "unweighted mean of Mengxi and Mengdong"
            if not source_rows:
                continue
            out = {"province": province, "province_cn": region_cn, "year": year, "aggregation_method": method}
            for kind in ("wind", "solar"):
                rates = [row[f"{kind}_utilization_rate"] for row in source_rows if row.get(f"{kind}_utilization_rate") is not None]
                if rates:
                    out[f"{kind}_utilization_rate"] = sum(rates) / len(rates)
                    out[f"{kind}_curtailment_rate"] = 1.0 - out[f"{kind}_utilization_rate"]
            report_years = [
                row[f"{kind}_source_report_year"]
                for row in source_rows for kind in ("wind", "solar")
                if row.get(f"{kind}_source_report_year") is not None
            ]
            out["source_report_year"] = min(report_years)
            out["source_url"] = SOURCE_URLS[out["source_report_year"]]
            province_rows.append(out)

    regional_fields = [
        "region_cn", "year", "wind_utilization_rate", "wind_curtailment_rate",
        "solar_utilization_rate", "solar_curtailment_rate",
        "wind_source_report_year", "solar_source_report_year",
    ]
    province_fields = [
        "province", "province_cn", "year", "wind_utilization_rate", "wind_curtailment_rate",
        "solar_utilization_rate", "solar_curtailment_rate", "aggregation_method", "source_report_year", "source_url",
    ]
    write_csv(OUT_DIR / "nea_renewable_utilization_regional_2020_2023.csv", regional_rows, regional_fields)
    write_csv(OUT_DIR / "nea_renewable_utilization_province_2020_2023.csv", province_rows, province_fields)

    print(f"regional_rows={len(regional_rows)}")
    print(f"province_rows={len(province_rows)}")
    print(f"province_count={len({row['province'] for row in province_rows})}")
    print(f"years={min(row['year'] for row in province_rows)}-{max(row['year'] for row in province_rows)}")


if __name__ == "__main__":
    main()
