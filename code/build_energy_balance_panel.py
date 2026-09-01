#!/usr/bin/env python3
"""
Clean Wind-exported regional energy balance sheets and merge them with the
existing province-year panel.

Inputs
------
data/append_0518/数据模板命名1.csv
    Coal, oil products, and LPG balance sheets.
data/append_0518/数据模板 5.csv
    Natural gas and electricity balance sheets.
data/final_data.1.3.4_did.csv
    Existing province-year panel.

Outputs
-------
data/append_0518/energy_balance_long.csv
data/append_0518/energy_balance_panel.csv
data/final_data.1.3.4_did_energy_0518.csv
data/final_data.1.3.4_did_energy_0518_missing_report.csv
"""

from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPEND_DIR = ROOT / "data" / "append_0518"
MAIN_PANEL = ROOT / "data" / "final_data.1.3.4_did.csv"

BALANCE_FILES = [
    APPEND_DIR / "数据模板命名1.csv",
    APPEND_DIR / "数据模板 5.csv",
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

BALANCE_TYPE_TO_PREFIX = {
    "煤平衡表": "coal",
    "油品平衡表": "oil",
    "液化石油气平衡表": "lpg",
    "天然气平衡表": "gas",
    "电力平衡表": "electricity",
}

ITEM_TO_SUFFIX = {
    "可供消费的能源总量": "available_total",
    "可供消费的能源总量:一次能源生产量": "primary_production",
    "能源消费": "consumption",
    "终端消费量": "terminal",
    "终端消费量:工业": "terminal_industry",
    "加工转换投入和产出量:火力发电": "thermal_power_input",
}

# Common physical-unit to 10k tons standard coal conversion coefficients.
# These are used only for approximate cross-energy aggregation. Raw physical
# quantities remain the authoritative fields.
TCE_10K_COEFF = {
    # input unit: 千吨. value * coeff / 10 = 万吨标准煤
    "coal": 0.7143 / 10.0,
    "oil": 1.4286 / 10.0,
    "lpg": 1.7143 / 10.0,
    # input unit: 百万立方米. 1 m3 natural gas ~= 1.33 kgce.
    "gas": 0.133,
    # input unit: 百万千瓦时. 1 kWh ~= 0.1229 kgce.
    "electricity": 0.01229,
}


def read_csv(path: Path, encoding: str = "utf-8-sig") -> list[list[str]]:
    with path.open(encoding=encoding, newline="") as f:
        rows = list(csv.reader(f))
    width = max(len(r) for r in rows)
    for row in rows:
        row.extend([""] * (width - len(row)))
    return rows


def parse_float(value: str) -> float | None:
    value = (value or "").strip().replace(",", "")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_year(value: str) -> int | None:
    value = (value or "").strip()
    if re.fullmatch(r"\d{4}", value):
        return int(value)
    if re.fullmatch(r"\d{4}-12-31", value):
        return int(value[:4])
    return None


def parse_header(header: str) -> tuple[str, str, str] | None:
    parts = header.split(":")
    if len(parts) < 3:
        return None
    province, balance_type = parts[0], parts[1]
    item = ":".join(parts[2:])
    if province not in PROVINCE_CN_TO_MAIN:
        return None
    if balance_type not in BALANCE_TYPE_TO_PREFIX:
        return None
    if item not in ITEM_TO_SUFFIX:
        return None
    return province, balance_type, item


def clean_energy_balance() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    long_rows: list[dict[str, str]] = []
    panel: dict[tuple[str, int], dict[str, str]] = {}

    for path in BALANCE_FILES:
        rows = read_csv(path)
        headers = rows[0]
        units = rows[4]
        sources = rows[5]
        series_ids = rows[7]

        selected_columns: dict[int, tuple[str, str, str]] = {}
        for idx, header in enumerate(headers):
            parsed = parse_header(header)
            if parsed:
                selected_columns[idx] = parsed

        for row in rows[15:]:
            year = parse_year(row[0])
            if year is None:
                continue
            for idx, (province_cn, balance_type, item) in selected_columns.items():
                value = parse_float(row[idx])
                if value is None:
                    continue

                province = PROVINCE_CN_TO_MAIN[province_cn]
                prefix = BALANCE_TYPE_TO_PREFIX[balance_type]
                suffix = ITEM_TO_SUFFIX[item]
                variable = f"{prefix}_{suffix}"

                record = {
                    "province": province,
                    "province_cn": province_cn,
                    "year": str(year),
                    "energy_type": prefix,
                    "balance_type_cn": balance_type,
                    "item": suffix,
                    "item_cn": item,
                    "variable": variable,
                    "value": f"{value:.10g}",
                    "unit": units[idx],
                    "source": sources[idx],
                    "series_id": series_ids[idx],
                    "original_header": headers[idx],
                }
                long_rows.append(record)

                key = (province, year)
                if key not in panel:
                    panel[key] = {"province": province, "year": str(year)}
                panel[key][variable] = f"{value:.10g}"

                if suffix in {"consumption", "terminal"}:
                    tce_variable = f"{variable}_10k_tce_approx"
                    tce = value * TCE_10K_COEFF[prefix]
                    panel[key][tce_variable] = f"{tce:.10g}"

    panel_rows = [panel[k] for k in sorted(panel, key=lambda x: (x[0], x[1]))]
    add_derived_energy_fields(panel_rows)
    return long_rows, panel_rows


def add_derived_energy_fields(panel_rows: list[dict[str, str]]) -> None:
    for row in panel_rows:
        for suffix in ["consumption", "terminal"]:
            pieces = {}
            for prefix in BALANCE_TYPE_TO_PREFIX.values():
                key = f"{prefix}_{suffix}_10k_tce_approx"
                pieces[prefix] = parse_float(row.get(key, ""))
            if any(v is not None for v in pieces.values()):
                total = sum(v for v in pieces.values() if v is not None)
                row[f"energy5_{suffix}_10k_tce_approx"] = f"{total:.10g}"
                coal = pieces.get("coal")
                if coal is not None and total > 0:
                    row[f"coal_share_energy5_{suffix}_approx"] = f"{coal / total:.10g}"
                wind_like = None

        coal = parse_float(row.get("coal_consumption", ""))
        if coal is not None:
            row["coal_consumption_10k_ton"] = f"{coal / 10.0:.10g}"

        coal_output = parse_float(row.get("coal_primary_production", ""))
        if coal_output is not None:
            # The raw regional coal balance sheet reports physical coal in kt.
            row["coal_primary_production_10k_ton"] = f"{coal_output / 10.0:.10g}"


def write_csv(path: Path, rows: list[dict[str, str]], preferred_order: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    if preferred_order:
        fields.extend(preferred_order)
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def merge_with_main(panel_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    with MAIN_PANEL.open(encoding="utf-8-sig", newline="") as f:
        main_rows = list(csv.DictReader(f))
    main_fields = set(main_rows[0].keys()) if main_rows else set()

    energy_by_key = {(r["province"], r["year"]): r for r in panel_rows}
    merged_rows: list[dict[str, str]] = []
    missing_report: list[dict[str, str]] = []

    for row in main_rows:
        key = (row["province"], row["year"])
        energy = energy_by_key.get(key)
        merged = dict(row)
        if energy:
            for k, v in energy.items():
                if k not in {"province", "year"}:
                    merged[k] = v
        add_intensity_fields(merged)
        merged_rows.append(merged)

    add_policy_exposure_fields(merged_rows)

    energy_fields = sorted({k for row in merged_rows for k in row if k not in main_fields})
    for field in energy_fields:
        missing = sum(1 for row in merged_rows if not row.get(field, "").strip())
        nonmissing = len(merged_rows) - missing
        missing_report.append(
            {
                "variable": field,
                "nonmissing": str(nonmissing),
                "missing": str(missing),
                "total": str(len(merged_rows)),
            }
        )

    return merged_rows, missing_report


def add_intensity_fields(row: dict[str, str]) -> None:
    gdp = parse_float(row.get("gdp", ""))
    if not gdp or gdp <= 0:
        return

    intensity_specs = {
        "coal_consumption_10k_ton": "coal_consumption_10k_ton_per_gdp",
        "coal_terminal": "coal_terminal_kt_per_gdp",
        "coal_consumption_10k_tce_approx": "coal_consumption_10k_tce_per_gdp_approx",
        "coal_terminal_10k_tce_approx": "coal_terminal_10k_tce_per_gdp_approx",
        "energy5_consumption_10k_tce_approx": "energy5_consumption_10k_tce_per_gdp_approx",
        "energy5_terminal_10k_tce_approx": "energy5_terminal_10k_tce_per_gdp_approx",
    }
    for src, dest in intensity_specs.items():
        value = parse_float(row.get(src, ""))
        if value is not None:
            row[dest] = f"{value / gdp:.10g}"


def add_policy_exposure_fields(rows: list[dict[str, str]]) -> None:
    by_province: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_province[row["province"]].append(row)

    for province, province_rows in by_province.items():
        pre_rows = [r for r in province_rows if r.get("year") in {"2008", "2009", "2010", "2011"}]

        def mean_var(var: str) -> float | None:
            values = [parse_float(r.get(var, "")) for r in pre_rows]
            values = [v for v in values if v is not None]
            if not values:
                return None
            return sum(values) / len(values)

        pre_coal_cons = mean_var("coal_consumption")
        pre_coal_terminal = mean_var("coal_terminal")
        pre_coal_share5 = mean_var("coal_share_energy5_consumption_approx")
        pre_coal_share5_terminal = mean_var("coal_share_energy5_terminal_approx")
        pre_thermal_input = mean_var("coal_thermal_power_input")
        pre_energy5_terminal_intensity = mean_var("energy5_terminal_10k_tce_per_gdp_approx")
        pre_coal_terminal_intensity = mean_var("coal_terminal_10k_tce_per_gdp_approx")

        for row in province_rows:
            year = int(row["year"])
            post2012 = 1 if year >= 2012 else 0
            row["post2012"] = str(post2012)
            if pre_coal_cons is not None:
                row["pre_coal_consumption_0811"] = f"{pre_coal_cons:.10g}"
                row["post2012_x_pre_coal_consumption"] = f"{post2012 * pre_coal_cons:.10g}"
            if pre_coal_terminal is not None:
                row["pre_coal_terminal_0811"] = f"{pre_coal_terminal:.10g}"
                row["post2012_x_pre_coal_terminal"] = f"{post2012 * pre_coal_terminal:.10g}"
            if pre_coal_share5 is not None:
                row["pre_coal_share_energy5_0811_approx"] = f"{pre_coal_share5:.10g}"
                row["post2012_x_pre_coal_share_energy5"] = f"{post2012 * pre_coal_share5:.10g}"
            if pre_coal_share5_terminal is not None:
                row["pre_coal_share_energy5_terminal_0811_approx"] = f"{pre_coal_share5_terminal:.10g}"
                row["post2012_x_pre_coal_share_energy5_terminal"] = f"{post2012 * pre_coal_share5_terminal:.10g}"
            if pre_thermal_input is not None:
                row["pre_coal_thermal_power_input_0811"] = f"{pre_thermal_input:.10g}"
                row["post2012_x_pre_coal_thermal_power_input"] = f"{post2012 * pre_thermal_input:.10g}"
            if pre_energy5_terminal_intensity is not None:
                row["pre_energy5_terminal_intensity_0811_approx"] = f"{pre_energy5_terminal_intensity:.10g}"
                row["post2012_x_pre_energy5_terminal_intensity"] = f"{post2012 * pre_energy5_terminal_intensity:.10g}"
            if pre_coal_terminal_intensity is not None:
                row["pre_coal_terminal_intensity_0811_approx"] = f"{pre_coal_terminal_intensity:.10g}"
                row["post2012_x_pre_coal_terminal_intensity"] = f"{post2012 * pre_coal_terminal_intensity:.10g}"


def main() -> None:
    long_rows, panel_rows = clean_energy_balance()

    write_csv(
        APPEND_DIR / "energy_balance_long.csv",
        long_rows,
        [
            "province",
            "province_cn",
            "year",
            "energy_type",
            "balance_type_cn",
            "item",
            "item_cn",
            "variable",
            "value",
            "unit",
            "source",
            "series_id",
            "original_header",
        ],
    )
    write_csv(APPEND_DIR / "energy_balance_panel.csv", panel_rows, ["province", "year"])

    merged_rows, missing_report = merge_with_main(panel_rows)
    write_csv(ROOT / "data" / "final_data.1.3.4_did_energy_0518.csv", merged_rows)
    write_csv(
        ROOT / "data" / "final_data.1.3.4_did_energy_0518_missing_report.csv",
        missing_report,
        ["variable", "nonmissing", "missing", "total"],
    )

    print(f"long rows: {len(long_rows)}")
    print(f"energy panel rows: {len(panel_rows)}")
    print(f"merged panel rows: {len(merged_rows)}")
    print("outputs:")
    print(f"  {APPEND_DIR / 'energy_balance_long.csv'}")
    print(f"  {APPEND_DIR / 'energy_balance_panel.csv'}")
    print(f"  {ROOT / 'data' / 'final_data.1.3.4_did_energy_0518.csv'}")
    print(f"  {ROOT / 'data' / 'final_data.1.3.4_did_energy_0518_missing_report.csv'}")


if __name__ == "__main__":
    main()
