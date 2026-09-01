#!/usr/bin/env python3
"""
Clean all newly added 0518 data and merge them into the province-year panel.

This script intentionally keeps two layers:
1. append_0518_newdata_long.csv keeps source-level cleaned observations.
2. append_0518_newdata_panel.csv and the final merged panel keep annual,
   province-level variables with stable names.

The older energy-balance cleaner must be run first because this script uses
data/final_data.1.3.4_did_energy_0518.csv as its base.
"""

from __future__ import annotations

import csv
import datetime as dt
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPEND_DIR = ROOT / "data" / "append_0518"
BASE_PANEL = ROOT / "data" / "final_data.1.3.4_did_energy_0518.csv"

ENERGY_BALANCE_SCRIPT = ROOT / "code" / "build_energy_balance_panel.py"

POWER_CSV = APPEND_DIR / "数据模板命名.csv"
WIND_ENERGY_CSV = APPEND_DIR / "上海_能源消费总量.csv"

NOX_XLSX = APPEND_DIR / (
    "https___wx.wind.com.cn_weaver_files_019e39c0-8200-705a-8378-ca980c063b7d_"
    "dataquery_1779085378_gteFX1_Step1.csv.xlsx"
)
PM_XLSX = APPEND_DIR / (
    "https___wx.wind.com.cn_weaver_files_019e39c2-a928-79ca-a66a-40bf992d8772_"
    "dataquery_1779085519_3Fuz1T_Step1.csv.xlsx"
)
POWER_XLSX_FILES = [
    APPEND_DIR / (
        "https___wx.wind.com.cn_weaver_files_019e3a0d-1d12-7678-844b-db4a661d1831_"
        "dataquery_1779090398_5kqQY0_Step1.csv.xlsx"
    ),
    APPEND_DIR / (
        "https___wx.wind.com.cn_weaver_files_019e3a0d-1d23-7d44-b8db-1255a69c8070_"
        "dataquery_1779090398_oNMQJt_Step2.csv.xlsx"
    ),
    APPEND_DIR / (
        "https___wx.wind.com.cn_weaver_files_019e3a0d-1d2d-7af5-8896-1d8181ab20bf_"
        "dataquery_1779090398_wHeWtZ_Step3.csv.xlsx"
    ),
    APPEND_DIR / (
        "https___wx.wind.com.cn_weaver_files_019e3a0e-9175-7db7-8d0f-79b82f8cec50_"
        "dataquery_1779090493_i3ZSbn_Step1.csv.xlsx"
    ),
    APPEND_DIR / (
        "https___wx.wind.com.cn_weaver_files_019e3a0e-93c8-7940-b287-c4f73e17b07f_"
        "dataquery_1779090494_uQq8o4_Step1.csv.xlsx"
    ),
]

PROVINCE_CN_TO_MAIN = {
    "北京": "Beijing",
    "天津": "Tianjin",
    "河北": "Hebei",
    "山西": "Shanxi",
    "内蒙古": "Neimenggu",
    "辽宁": "Liaoning",
    "吉林": "Jilin",
    "黑龙江": "Heilongjiang",
    "上海": "Shanghai",
    "江苏": "Jiangsu",
    "浙江": "Zhejiang",
    "安徽": "Anhui",
    "福建": "Fujian",
    "江西": "Jiangxi",
    "山东": "Shandong",
    "河南": "Henan",
    "湖北": "Hubei",
    "湖南": "Hunan",
    "广东": "Guangdong",
    "广西": "Guangxi",
    "海南": "Hainan",
    "重庆": "Chongqing",
    "四川": "Sichuan",
    "贵州": "Guizhou",
    "云南": "Yunnan",
    "西藏": "Xizang",
    "陕西": "Shaanxi",
    "甘肃": "Gansu",
    "青海": "Qinghai",
    "宁夏": "Ningxia",
    "新疆": "Xinjiang",
}
PROVINCES_CN = list(PROVINCE_CN_TO_MAIN.keys())


def read_csv_rect(path: Path, encoding: str = "utf-8-sig") -> list[list[str]]:
    with path.open(encoding=encoding, newline="") as f:
        rows = list(csv.reader(f))
    width = max(len(row) for row in rows)
    for row in rows:
        row.extend([""] * (width - len(row)))
    return rows


def write_dicts(path: Path, rows: list[dict[str, str]], preferred: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    if preferred:
        fields.extend(preferred)
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_float(value: str) -> float | None:
    value = (value or "").strip().replace(",", "")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_date(value: str) -> dt.date | None:
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    if re.fullmatch(r"\d{4}", value):
        return dt.date(int(value), 12, 31)
    return None


def detect_province(header: str) -> str | None:
    for province in sorted(PROVINCES_CN, key=len, reverse=True):
        if re.search(rf"(^|[:：]){re.escape(province)}($|[:：])", header):
            return province
    return None


def read_xlsx_sheet1(path: Path) -> list[list[str]]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for item in root.findall("a:si", ns):
                shared.append("".join(t.text or "" for t in item.findall(".//a:t", ns)))

        sheet_names = [name for name in zf.namelist() if name.startswith("xl/worksheets/sheet")]
        sheet_name = "xl/worksheets/sheet1.xml" if "xl/worksheets/sheet1.xml" in sheet_names else sheet_names[0]
        root = ET.fromstring(zf.read(sheet_name))

    def colnum(cell_ref: str) -> int:
        col = "".join(ch for ch in cell_ref if ch.isalpha())
        number = 0
        for ch in col:
            number = number * 26 + ord(ch.upper()) - 64
        return number

    rows: list[list[str]] = []
    for row in root.findall(".//a:sheetData/a:row", ns):
        cells: list[tuple[int, str]] = []
        for cell in row.findall("a:c", ns):
            value_node = cell.find("a:v", ns)
            value = "" if value_node is None else value_node.text or ""
            if cell.attrib.get("t") == "s" and value:
                value = shared[int(value)]
            cells.append((colnum(cell.attrib.get("r", "")), value))

        width = max((idx for idx, _ in cells), default=0)
        out = [""] * width
        for idx, value in cells:
            out[idx - 1] = value
        rows.append(out)

    width = max(len(row) for row in rows) if rows else 0
    for row in rows:
        row.extend([""] * (width - len(row)))
    return rows


def unit_to_capacity_10k_kw(value: float, unit: str) -> float | None:
    if "千千瓦" in unit:
        return value / 10.0
    if "千万瓦" in unit:
        return value
    if "万千瓦" in unit:
        return value
    return None


def unit_to_generation_billion_kwh(value: float, unit: str) -> float | None:
    if "十亿千瓦时" in unit:
        return value
    if "亿千瓦时" in unit:
        return value / 10.0
    if "万千瓦时" in unit:
        return value / 100000.0
    if "万瓦时" in unit:
        return value / 100000000.0
    return None


def unit_to_10k_tce(value: float, unit: str) -> float | None:
    if "万吨标准煤" in unit:
        return value
    return None


def unit_from_header(header: str, fallback: str = "") -> str:
    match = re.search(r"[（(]([^()（）]+)[）)]", header)
    if match:
        return match.group(1)
    return fallback


def add_long(
    rows: list[dict[str, str]],
    *,
    source_file: Path,
    variable: str,
    province_cn: str,
    year: int,
    value: float,
    unit: str,
    original_header: str,
    source: str = "",
    date: str = "",
    notes: str = "",
) -> None:
    rows.append(
        {
            "source_file": source_file.name,
            "province": PROVINCE_CN_TO_MAIN[province_cn],
            "province_cn": province_cn,
            "year": str(year),
            "variable": variable,
            "value": f"{value:.10g}",
            "unit": unit,
            "source": source,
            "date": date,
            "original_header": original_header,
            "notes": notes,
        }
    )


def set_panel_value(
    panel: dict[tuple[str, int], dict[str, str]],
    province_cn: str,
    year: int,
    variable: str,
    value: float,
    priority: int,
    source_file: Path,
) -> None:
    province = PROVINCE_CN_TO_MAIN[province_cn]
    key = (province, year)
    row = panel.setdefault(key, {"province": province, "year": str(year)})
    priority_key = f"__priority__{variable}"
    old_priority = int(row.get(priority_key, "-1"))
    if priority >= old_priority:
        row[variable] = f"{value:.10g}"
        row[f"{variable}_source_file"] = source_file.name
        row[priority_key] = str(priority)


def clean_power_csv(long_rows: list[dict[str, str]], panel: dict[tuple[str, int], dict[str, str]]) -> None:
    rows = read_csv_rect(POWER_CSV)
    headers = rows[0]
    frequencies = rows[3]
    units = rows[4]
    sources = rows[5]
    data_rows: list[tuple[dt.date, list[str]]] = []
    for row in rows[8:]:
        date = parse_date(row[0])
        if date:
            data_rows.append((date, row))

    def classify(header: str) -> tuple[str, str] | None:
        if header.startswith("发电设备容量:水电:"):
            return "hydro_capacity_10k_kw", "capacity"
        if header.startswith("发电设备容量:火电:"):
            return "thermal_capacity_10k_kw", "capacity"
        if header.startswith("发电设备容量:风力:"):
            return "wind_capacity_10k_kw", "capacity"
        if header.startswith("发电设备容量:截至累计:太阳能光伏:"):
            return "solar_capacity_10k_kw", "capacity"
        if header.startswith("发电设备容量:") and header.count(":") == 1:
            return "total_capacity_10k_kw", "capacity"
        if header.startswith("发电量:风力:"):
            return "wind_generation_billion_kwh", "generation"
        if header.startswith("发电量:太阳能:"):
            return "solar_generation_billion_kwh", "generation"
        if header.startswith("发电量:") and header.count(":") == 1:
            return "total_generation_billion_kwh", "generation"
        return None

    for col, header in enumerate(headers):
        variable_kind = classify(header)
        if not variable_kind:
            continue
        variable, kind = variable_kind
        province_cn = detect_province(header)
        if not province_cn:
            continue
        unit = units[col]
        source = sources[col]
        by_year: dict[int, tuple[dt.date, float]] = {}
        for date, row in data_rows:
            value = parse_float(row[col])
            if value is None:
                continue
            if kind == "capacity":
                converted = unit_to_capacity_10k_kw(value, unit)
                out_unit = "万千瓦"
            else:
                converted = unit_to_generation_billion_kwh(value, unit)
                out_unit = "十亿千瓦时"
            if converted is None:
                continue
            # Use the last nonmissing observation in each year; for annual Wind
            # series this is usually December/年终12月, while monthly cumulative
            # fields also resolve to December.
            old = by_year.get(date.year)
            if old is None or date > old[0]:
                by_year[date.year] = (date, converted)

        for year, (date, value) in by_year.items():
            add_long(
                long_rows,
                source_file=POWER_CSV,
                variable=variable,
                province_cn=province_cn,
                year=year,
                value=value,
                unit=out_unit,
                source=source,
                date=date.isoformat(),
                original_header=header,
                notes=f"frequency={frequencies[col]}",
            )
            set_panel_value(panel, province_cn, year, variable, value, 100, POWER_CSV)


def clean_power_xlsx(long_rows: list[dict[str, str]], panel: dict[tuple[str, int], dict[str, str]]) -> None:
    def classify(header: str) -> tuple[str, str] | None:
        if "新增" in header:
            if "风电" in header:
                return "wind_capacity_addition_10k_kw", "capacity"
            return None
        if "装机容量" in header and "火电" in header:
            return "thermal_capacity_10k_kw", "capacity"
        if "装机容量" in header and "水电" in header:
            return "hydro_capacity_10k_kw", "capacity"
        if "装机容量" in header and "风电" in header:
            return "wind_capacity_10k_kw", "capacity"
        if "装机容量" in header and "太阳能" in header:
            return "solar_capacity_10k_kw", "capacity"
        if "发电量" in header and ("火力" in header or "火电" in header):
            return "thermal_generation_billion_kwh", "generation"
        if "发电量" in header and "风力" in header:
            return "wind_generation_billion_kwh", "generation"
        if "发电量" in header and "太阳能" in header:
            return "solar_generation_billion_kwh", "generation"
        if "发电量" in header and all(k not in header for k in ["火力", "火电", "风力", "太阳能", "水力", "水电"]):
            return "total_generation_billion_kwh", "generation"
        return None

    for path in POWER_XLSX_FILES:
        rows = read_xlsx_sheet1(path)
        if not rows:
            continue
        headers = rows[0]
        for col, header in enumerate(headers):
            variable_kind = classify(header)
            if not variable_kind:
                continue
            variable, kind = variable_kind
            province_cn = detect_province(header)
            if not province_cn:
                continue
            unit = unit_from_header(header)
            is_monthly_flow = "当月值" in header
            by_year: dict[int, tuple[dt.date, float]] = {}
            by_year_sum: dict[int, tuple[dt.date, float]] = {}
            for row in rows[1:]:
                date = parse_date(row[0])
                if not date:
                    continue
                value = parse_float(row[col])
                if value is None:
                    continue
                if kind == "capacity":
                    converted = unit_to_capacity_10k_kw(value, unit)
                    out_unit = "万千瓦"
                else:
                    converted = unit_to_generation_billion_kwh(value, unit)
                    out_unit = "十亿千瓦时"
                if converted is None:
                    continue
                if is_monthly_flow:
                    old_date, old_value = by_year_sum.get(date.year, (date, 0.0))
                    by_year_sum[date.year] = (max(old_date, date), old_value + converted)
                else:
                    old = by_year.get(date.year)
                    if old is None or date > old[0]:
                        by_year[date.year] = (date, converted)

            if is_monthly_flow:
                by_year = by_year_sum

            priority = 40
            if "累计值" in header:
                priority = 90
            if "当月值" in header:
                priority = 80
            if "万瓦时" in unit:
                priority = 10
            # New xlsx capacity files are useful backstops, but the broader CSV
            # from CEC/Wind is preferred when both exist.
            if kind == "capacity":
                priority = min(priority, 60)

            for year, (date, value) in by_year.items():
                add_long(
                    long_rows,
                    source_file=path,
                    variable=variable,
                    province_cn=province_cn,
                    year=year,
                    value=value,
                    unit=out_unit,
                    source="Wind",
                    date=date.isoformat(),
                    original_header=header,
                )
                set_panel_value(panel, province_cn, year, variable, value, priority, path)


def clean_pollution_xlsx(long_rows: list[dict[str, str]], panel: dict[tuple[str, int], dict[str, str]]) -> None:
    specs = [
        (
            NOX_XLSX,
            [
                ("industrial_nox_10k_ton", lambda h: "工业氮氧化物排放量" in h or "工业废气排放量:氮氧化物" in h),
                (
                    "total_nox_10k_ton",
                    lambda h: ("氮氧化物" in h and "工业" not in h and "生活" not in h and "宁波" not in h),
                ),
            ],
        ),
        (
            PM_XLSX,
            [
                (
                    "total_pm_10k_ton",
                    lambda h: ("颗粒物" in h and "生活" not in h and "工业" not in h and "宁波" not in h),
                ),
                (
                    "industrial_pm_10k_ton",
                    lambda h: ("工业" in h and ("颗粒物" in h or "烟粉尘" in h)),
                ),
            ],
        ),
    ]

    for path, rules in specs:
        rows = read_xlsx_sheet1(path)
        headers = rows[0]
        for variable, predicate in rules:
            for col, header in enumerate(headers):
                if not predicate(header):
                    continue
                province_cn = detect_province(header)
                if not province_cn:
                    continue
                unit = unit_from_header(header, "万吨")
                by_year: dict[int, tuple[dt.date, float]] = {}
                for row in rows[1:]:
                    date = parse_date(row[0])
                    if not date:
                        continue
                    value = parse_float(row[col])
                    if value is None:
                        continue
                    old = by_year.get(date.year)
                    if old is None or date > old[0]:
                        by_year[date.year] = (date, value)
                for year, (date, value) in by_year.items():
                    add_long(
                        long_rows,
                        source_file=path,
                        variable=variable,
                        province_cn=province_cn,
                        year=year,
                        value=value,
                        unit=unit,
                        source="Wind",
                        date=date.isoformat(),
                        original_header=header,
                    )
                    set_panel_value(panel, province_cn, year, variable, value, 90, path)


def clean_wind_energy_csv(long_rows: list[dict[str, str]], panel: dict[tuple[str, int], dict[str, str]]) -> None:
    rows = read_csv_rect(WIND_ENERGY_CSV, encoding="gb18030")
    headers = rows[1]
    frequencies = rows[3]
    units = rows[4]
    sources = rows[7]
    data_rows: list[tuple[dt.date, list[str]]] = []
    for row in rows[9:]:
        date = parse_date(row[0])
        if date:
            data_rows.append((date, row))

    def classify(header: str) -> tuple[str, str] | None:
        if re.fullmatch(r"[^:：]+:能源消费总量", header):
            return "wind_total_energy_consumption_10k_tce", "energy"
        if re.fullmatch(r"[^:：]+:能源消费总量:工业", header):
            return "wind_industrial_energy_consumption_10k_tce", "energy"
        if "占能源消费总量的比重:煤炭" in header or "能源消费总量占比:煤炭" in header:
            return "wind_coal_share_energy_consumption_pct", "pct"
        return None

    for col, header in enumerate(headers):
        variable_kind = classify(header)
        if not variable_kind:
            continue
        variable, kind = variable_kind
        province_cn = detect_province(header)
        if not province_cn:
            continue
        unit = units[col]
        by_year: dict[int, tuple[dt.date, float]] = {}
        for date, row in data_rows:
            value = parse_float(row[col])
            if value is None:
                continue
            if kind == "energy":
                converted = unit_to_10k_tce(value, unit)
                out_unit = "万吨标准煤"
            else:
                converted = value
                out_unit = unit or "%"
            if converted is None:
                continue
            old = by_year.get(date.year)
            if old is None or date > old[0]:
                by_year[date.year] = (date, converted)
        for year, (date, value) in by_year.items():
            add_long(
                long_rows,
                source_file=WIND_ENERGY_CSV,
                variable=variable,
                province_cn=province_cn,
                year=year,
                value=value,
                unit=out_unit,
                source=sources[col],
                date=date.isoformat(),
                original_header=header,
                notes=f"frequency={frequencies[col]}; supplemental Wind energy-consumption series",
            )
            set_panel_value(panel, province_cn, year, variable, value, 50, WIND_ENERGY_CSV)


def add_derived_fields(panel: dict[tuple[str, int], dict[str, str]]) -> None:
    for row in panel.values():
        total_capacity = parse_float(row.get("total_capacity_10k_kw", ""))
        thermal_capacity = parse_float(row.get("thermal_capacity_10k_kw", ""))
        hydro_capacity = parse_float(row.get("hydro_capacity_10k_kw", ""))
        wind_capacity = parse_float(row.get("wind_capacity_10k_kw", ""))
        solar_capacity = parse_float(row.get("solar_capacity_10k_kw", ""))

        if total_capacity and total_capacity > 0:
            for src, dest in [
                (thermal_capacity, "thermal_capacity_share"),
                (hydro_capacity, "hydro_capacity_share"),
                (wind_capacity, "wind_capacity_share"),
                (solar_capacity, "solar_capacity_share"),
            ]:
                if src is not None:
                    row[dest] = f"{src / total_capacity:.10g}"
            if wind_capacity is not None or solar_capacity is not None:
                wind_solar = (wind_capacity or 0.0) + (solar_capacity or 0.0)
                row["wind_solar_capacity_share"] = f"{wind_solar / total_capacity:.10g}"
            if thermal_capacity is not None:
                row["nonthermal_capacity_share"] = f"{1 - thermal_capacity / total_capacity:.10g}"

        total_generation = parse_float(row.get("total_generation_billion_kwh", ""))
        thermal_generation = parse_float(row.get("thermal_generation_billion_kwh", ""))
        wind_generation = parse_float(row.get("wind_generation_billion_kwh", ""))
        solar_generation = parse_float(row.get("solar_generation_billion_kwh", ""))

        if total_generation and total_generation > 0:
            if thermal_generation is not None:
                thermal_share = thermal_generation / total_generation
                if 0 <= thermal_share <= 1:
                    row["thermal_generation_share"] = f"{thermal_share:.10g}"
                    row["nonthermal_generation_share"] = f"{1 - thermal_share:.10g}"
                else:
                    row["thermal_generation_share_flag"] = "out_of_range"
            if wind_generation is not None:
                wind_share = wind_generation / total_generation
                if 0 <= wind_share <= 1:
                    row["wind_generation_share"] = f"{wind_share:.10g}"
                else:
                    row["wind_generation_share_flag"] = "out_of_range"
            if solar_generation is not None:
                solar_share = solar_generation / total_generation
                if 0 <= solar_share <= 1:
                    row["solar_generation_share"] = f"{solar_share:.10g}"
                else:
                    row["solar_generation_share_flag"] = "out_of_range"
            if wind_generation is not None or solar_generation is not None:
                wind_solar = (wind_generation or 0.0) + (solar_generation or 0.0)
                wind_solar_share = wind_solar / total_generation
                if 0 <= wind_solar_share <= 1:
                    row["wind_solar_generation_share"] = f"{wind_solar_share:.10g}"
                else:
                    row["wind_solar_generation_share_flag"] = "out_of_range"

    by_province: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in panel.values():
        by_province[row["province"]].append(row)

    for province_rows in by_province.values():
        province_rows.sort(key=lambda row: int(row["year"]))
        prev_wind_capacity = None
        prev_solar_capacity = None
        prev_wind_generation = None
        prev_solar_generation = None
        for row in province_rows:
            wind_capacity = parse_float(row.get("wind_capacity_10k_kw", ""))
            solar_capacity = parse_float(row.get("solar_capacity_10k_kw", ""))
            wind_generation = parse_float(row.get("wind_generation_billion_kwh", ""))
            solar_generation = parse_float(row.get("solar_generation_billion_kwh", ""))
            if wind_capacity is not None and prev_wind_capacity is not None:
                row["wind_capacity_addition_from_stock_10k_kw"] = f"{wind_capacity - prev_wind_capacity:.10g}"
            if solar_capacity is not None and prev_solar_capacity is not None:
                row["solar_capacity_addition_from_stock_10k_kw"] = f"{solar_capacity - prev_solar_capacity:.10g}"
            if wind_generation is not None and prev_wind_generation is not None:
                row["wind_generation_addition_billion_kwh"] = f"{wind_generation - prev_wind_generation:.10g}"
            if solar_generation is not None and prev_solar_generation is not None:
                row["solar_generation_addition_billion_kwh"] = f"{solar_generation - prev_solar_generation:.10g}"

            if wind_capacity is not None:
                prev_wind_capacity = wind_capacity
            if solar_capacity is not None:
                prev_solar_capacity = solar_capacity
            if wind_generation is not None:
                prev_wind_generation = wind_generation
            if solar_generation is not None:
                prev_solar_generation = solar_generation


def add_lowcarbon_exposure_fields(merged_rows: list[dict[str, str]]) -> None:
    by_province: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in merged_rows:
        by_province[row["province"]].append(row)

    def mean_var(rows: list[dict[str, str]], variable: str, years: set[str]) -> float | None:
        values = [parse_float(row.get(variable, "")) for row in rows if row.get("year") in years]
        values = [value for value in values if value is not None]
        if not values:
            return None
        return sum(values) / len(values)

    for province_rows in by_province.values():
        pre_years = {"2008", "2009", "2010", "2011"}
        early_years = {"2013", "2014", "2015", "2016"}
        pre_nonthermal = mean_var(province_rows, "nonthermal_capacity_share", pre_years)
        early_wind = mean_var(province_rows, "wind_capacity_share", early_years)
        early_wind_gen = mean_var(province_rows, "wind_generation_share", early_years)
        pre_coal = mean_var(province_rows, "pre_coal_share_energy5_terminal_0811_approx", {"2008"})

        for row in province_rows:
            post2012 = parse_float(row.get("post2012", ""))
            post2012 = 1.0 if post2012 == 1.0 else 0.0
            if pre_nonthermal is not None:
                row["pre_nonthermal_capacity_share_0811"] = f"{pre_nonthermal:.10g}"
            if early_wind is not None:
                row["early_wind_capacity_share_1316"] = f"{early_wind:.10g}"
            if early_wind_gen is not None:
                row["early_wind_generation_share_1316"] = f"{early_wind_gen:.10g}"
            if pre_coal is not None and pre_nonthermal is not None:
                triple = post2012 * pre_coal * pre_nonthermal
                row["post2012_x_pre_coal_share_terminal_x_pre_nonthermal_capacity"] = f"{triple:.10g}"
            if pre_coal is not None and early_wind is not None:
                triple = post2012 * pre_coal * early_wind
                row["post2012_x_pre_coal_share_terminal_x_early_wind_capacity"] = f"{triple:.10g}"
            if pre_coal is not None and early_wind_gen is not None:
                triple = post2012 * pre_coal * early_wind_gen
                row["post2012_x_pre_coal_share_terminal_x_early_wind_generation"] = f"{triple:.10g}"


def add_stata_alias_fields(rows: list[dict[str, str]]) -> None:
    """Add <=32-character aliases for Stata regressions.

    Stata truncates long CSV headers on import, so the empirical do files use
    these aliases instead of the descriptive source names.
    """
    aliases = {
        "pre_coal_share_energy5_terminal_0811_approx": "coalexp_pre",
        "post2012_x_pre_coal_share_energy5_terminal": "coalexp_post",
        "energy5_terminal_10k_tce_per_gdp_approx": "energy5_int",
        "coal_terminal_10k_tce_per_gdp_approx": "coalterm_int",
        "coal_share_energy5_terminal_approx": "coalshare5",
        "total_capacity_10k_kw": "cap_total",
        "thermal_capacity_10k_kw": "cap_thermal",
        "wind_capacity_10k_kw": "cap_wind",
        "solar_capacity_10k_kw": "cap_solar",
        "thermal_capacity_share": "therm_cap_sh",
        "wind_capacity_share": "wind_cap_sh",
        "solar_capacity_share": "solar_cap_sh",
        "wind_solar_capacity_share": "windsolar_cap_sh",
        "nonthermal_capacity_share": "nontherm_cap_sh",
        "total_generation_billion_kwh": "gen_total",
        "thermal_generation_billion_kwh": "gen_thermal",
        "wind_generation_billion_kwh": "gen_wind",
        "solar_generation_billion_kwh": "gen_solar",
        "thermal_generation_share": "therm_gen_sh",
        "wind_generation_share": "wind_gen_sh",
        "solar_generation_share": "solar_gen_sh",
        "wind_solar_generation_share": "windsolar_gen_sh",
        "nonthermal_generation_share": "nontherm_gen_sh",
        "total_nox_10k_ton": "nox_total",
        "industrial_nox_10k_ton": "nox_ind",
        "total_pm_10k_ton": "pm_total",
        "industrial_pm_10k_ton": "pm_ind",
        "pre_nonthermal_capacity_share_0811": "pre_nontherm_cap",
        "early_wind_capacity_share_1316": "early_wind_cap",
        "early_wind_generation_share_1316": "early_wind_gen",
        "post2012_x_pre_coal_share_terminal_x_pre_nonthermal_capacity": "ddd_nontherm",
        "post2012_x_pre_coal_share_terminal_x_early_wind_capacity": "ddd_windcap",
        "post2012_x_pre_coal_share_terminal_x_early_wind_generation": "ddd_windgen",
    }
    for row in rows:
        for source, alias in aliases.items():
            if row.get(source, "").strip():
                row[alias] = row[source]


def merge_panel(panel: dict[tuple[str, int], dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    with BASE_PANEL.open(encoding="utf-8-sig", newline="") as f:
        base_rows = list(csv.DictReader(f))
    base_fields = set(base_rows[0].keys()) if base_rows else set()

    add_derived_fields(panel)

    merged_rows: list[dict[str, str]] = []
    for row in base_rows:
        key = (row["province"], int(row["year"]))
        merged = dict(row)
        extra = panel.get(key)
        if extra:
            for field, value in extra.items():
                if field.startswith("__priority__") or field in {"province", "year"}:
                    continue
                merged[field] = value
        merged_rows.append(merged)

    add_lowcarbon_exposure_fields(merged_rows)
    add_stata_alias_fields(merged_rows)

    new_fields = sorted({field for row in merged_rows for field in row if field not in base_fields})
    missing_report: list[dict[str, str]] = []
    for field in new_fields:
        if field.endswith("_source_file"):
            continue
        nonmissing = sum(1 for row in merged_rows if row.get(field, "").strip())
        provinces = {row["province"] for row in merged_rows if row.get(field, "").strip()}
        years = [int(row["year"]) for row in merged_rows if row.get(field, "").strip()]
        missing_report.append(
            {
                "variable": field,
                "nonmissing": str(nonmissing),
                "missing": str(len(merged_rows) - nonmissing),
                "total": str(len(merged_rows)),
                "provinces": str(len(provinces)),
                "min_year": str(min(years)) if years else "",
                "max_year": str(max(years)) if years else "",
            }
        )
    return merged_rows, missing_report


def main() -> None:
    subprocess.run([sys.executable, str(ENERGY_BALANCE_SCRIPT)], check=True, cwd=ROOT)

    long_rows: list[dict[str, str]] = []
    panel: dict[tuple[str, int], dict[str, str]] = {}

    clean_power_csv(long_rows, panel)
    clean_power_xlsx(long_rows, panel)
    clean_pollution_xlsx(long_rows, panel)
    clean_wind_energy_csv(long_rows, panel)

    panel_rows = [row for _, row in sorted(panel.items(), key=lambda item: (item[0][0], item[0][1]))]
    for row in panel_rows:
        for key in list(row):
            if key.startswith("__priority__"):
                del row[key]
    write_dicts(
        APPEND_DIR / "append_0518_newdata_long.csv",
        long_rows,
        [
            "source_file",
            "province",
            "province_cn",
            "year",
            "variable",
            "value",
            "unit",
            "source",
            "date",
            "original_header",
            "notes",
        ],
    )
    write_dicts(APPEND_DIR / "append_0518_newdata_panel.csv", panel_rows, ["province", "year"])

    merged_rows, missing_report = merge_panel(panel)
    write_dicts(ROOT / "data" / "final_data.1.3.4_did_full_0518.csv", merged_rows)
    write_dicts(
        ROOT / "data" / "final_data.1.3.4_did_full_0518_missing_report.csv",
        missing_report,
        ["variable", "nonmissing", "missing", "total", "provinces", "min_year", "max_year"],
    )

    print(f"new long rows: {len(long_rows)}")
    print(f"new panel rows: {len(panel_rows)}")
    print(f"merged rows: {len(merged_rows)}")
    print("outputs:")
    print(f"  {APPEND_DIR / 'append_0518_newdata_long.csv'}")
    print(f"  {APPEND_DIR / 'append_0518_newdata_panel.csv'}")
    print(f"  {ROOT / 'data' / 'final_data.1.3.4_did_full_0518.csv'}")
    print(f"  {ROOT / 'data' / 'final_data.1.3.4_did_full_0518_missing_report.csv'}")


if __name__ == "__main__":
    main()
