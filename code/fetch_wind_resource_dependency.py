#!/usr/bin/env python3
"""Fetch province-year resource-dependence indicators from Wind EDB.

The script uses the installed Wind MCP skill CLI, discovers matching EDB
series, fetches their histories, and writes source-level and panel outputs.
It does not merge into the paper's main panel automatically because coverage
and denominator consistency must be reviewed first.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "wind_resource_dependency"
WIND_SKILL_DIR = Path.home() / ".agents" / "skills" / "wind-mcp-skill"
WIND_CLI = WIND_SKILL_DIR / "scripts" / "cli.mjs"

PROVINCE_CN_TO_MAIN = {
    "北京": "Beijing", "天津": "Tianjin", "河北": "Hebei", "山西": "Shanxi",
    "内蒙古": "Neimenggu", "辽宁": "Liaoning", "吉林": "Jilin", "黑龙江": "Heilongjiang",
    "上海": "Shanghai", "江苏": "Jiangsu", "浙江": "Zhejiang", "安徽": "Anhui",
    "福建": "Fujian", "江西": "Jiangxi", "山东": "Shandong", "河南": "Henan",
    "湖北": "Hubei", "湖南": "Hunan", "广东": "Guangdong", "广西": "Guangxi",
    "海南": "Hainan", "重庆": "Chongqing", "四川": "Sichuan", "贵州": "Guizhou",
    "云南": "Yunnan", "西藏": "Xizang", "陕西": "Shaanxi", "甘肃": "Gansu",
    "青海": "Qinghai", "宁夏": "Ningxia", "新疆": "Xinjiang",
}

SPECS = [
    {
        "type": "mining_employment",
        "query": "中国各省采矿业城镇单位就业人员年度",
        "accept": lambda name: name.endswith("就业人员数:城镇非私营单位:采矿业"),
        "panel_name": "mining_employment_10k_person",
        "base_unit": "万人",
    },
    {
        "type": "urban_nonprivate_employment",
        "query": "就业人员数城镇非私营单位年度各省",
        "accept": lambda name: name.endswith("就业人员数:城镇非私营单位"),
        "panel_name": "urban_nonprivate_employment_10k_person",
        "base_unit": "万人",
    },
    {
        "type": "coal_mining_assets",
        "query": "资产总计规模以上工业企业煤炭开采和洗选业年度各省",
        "accept": lambda name: name.endswith("煤炭开采和洗选业") and "资产总计" in name,
        "panel_name": "coal_mining_assets_10k_cny",
        "base_unit": "万元",
    },
    {
        "type": "industrial_assets",
        "query": "中国各省规模以上工业企业资产总计年度",
        "accept": lambda name: name.endswith("规模以上工业企业") and (
            "资产总计" in name or "资产合计" in name
        ),
        "panel_name": "industrial_assets_10k_cny",
        "base_unit": "万元",
    },
    {
        "type": "state_owned_industrial_assets",
        "query": "各省国有控股工业企业资产总计年度",
        "province_query": "{province}:资产总计:国有控股工业企业",
        "accept": lambda name: name.endswith("国有控股工业企业") and (
            "资产总计" in name or "资产合计" in name
        ),
        "panel_name": "state_owned_industrial_assets_10k_cny",
        "base_unit": "万元",
    },
    {
        "type": "resource_tax_revenue",
        "query": "一般公共预算收入资源税年度各省",
        "accept": lambda name: name.endswith("一般公共预算收入:税收收入:资源税"),
        "panel_name": "resource_tax_revenue_10k_cny",
        "base_unit": "万元",
    },
    {
        "type": "mining_tax_revenue",
        "query": "中国各省采矿业税收收入",
        "province_query": "{province}:税收收入:采矿业",
        "accept": lambda name: name.endswith(":税收收入:采矿业"),
        "panel_name": "mining_tax_revenue_10k_cny",
        "base_unit": "万元",
    },
    {
        "type": "raw_coal_output",
        "query": "中国各省原煤产量年度",
        "province_query": "{province}:产量:原煤",
        "accept": lambda name: "原煤" in name and (
            "产量" in name or "生产量" in name
        ),
        "accepted_units": {"万吨"},
        "accepted_freqs": {"年"},
        "panel_name": "raw_coal_output_10k_ton",
        "base_unit": "万吨",
    },
    {
        "type": "public_budget_revenue",
        "query": "一般公共预算收入年度各省",
        "accept": lambda name: name.endswith("一般公共预算收入:合计"),
        "panel_name": "public_budget_revenue_10k_cny",
        "base_unit": "万元",
    },
]

# These codes were returned by successful Wind EDB discovery calls in this
# project. Keeping them makes the fetch reproducible when the NL discovery
# endpoint is temporarily unable to rediscover an unchanged indicator.
STATIC_CODES = {
    "mining_employment": {
        "北京": "M5127760", "天津": "M5127785", "河北": "M5127810", "山西": "M5127835",
        "内蒙古": "M5127860", "辽宁": "M5127885", "吉林": "M5127910", "黑龙江": "M5127935",
        "上海": "M5127960", "江苏": "M5127985", "浙江": "M5128010", "安徽": "M5128035",
        "福建": "M5128060", "江西": "M5128085", "山东": "M5128110", "河南": "M5128135",
        "湖北": "M5128160", "湖南": "M5128185", "广东": "M5128210", "广西": "M5128235",
        "海南": "M5128260", "重庆": "M5128285", "四川": "M5128310", "贵州": "M5128335",
        "云南": "M5128360", "西藏": "M5128385", "陕西": "M5128410", "甘肃": "M5128435",
        "青海": "M5128460", "宁夏": "M5128485", "新疆": "M5128510",
    },
    "urban_nonprivate_employment": {
        "北京": "D8862726", "天津": "O0265321", "河北": "O6219065", "山西": "O3039525",
        "内蒙古": "A0728670", "辽宁": "J7322594", "吉林": "O9187281", "黑龙江": "T4097627",
        "上海": "B0988631", "江苏": "U1401681", "浙江": "N9636170", "安徽": "X4601217",
        "福建": "N0715528", "江西": "A0728672", "山东": "Q2255303", "河南": "P8444075",
        "湖北": "B4409033", "湖南": "L4165481", "广东": "F6788565", "广西": "F6788546",
        "海南": "F7092490", "重庆": "Z0494377", "四川": "V5517275", "贵州": "O0397172",
        "云南": "A8433678", "西藏": "Q0289004", "陕西": "P3310683", "甘肃": "V8761565",
        "青海": "N4766248", "宁夏": "A9517631", "新疆": "Z8004296",
    },
    "coal_mining_assets": {
        "天津": "M5114325", "河北": "M5114363", "山西": "M5114402", "内蒙古": "M5114440",
        "辽宁": "M5114478", "吉林": "M5114516", "黑龙江": "M5452474", "江苏": "M5114589",
        "浙江": "M5114627", "安徽": "M5114665", "福建": "M5114703", "江西": "M5114741",
        "山东": "M5114779", "河南": "M5114817", "湖北": "M5114855", "湖南": "M5114893",
        "广西": "M5114969", "重庆": "M5115045", "四川": "M5115083", "贵州": "M5115121",
        "云南": "M5115159", "陕西": "M5115235", "甘肃": "M5115273", "青海": "M5115311",
        "宁夏": "M5115349", "新疆": "M5115387",
    },
    "industrial_assets": {
        "北京": "M6262884", "天津": "M5114324", "河北": "M5114362", "山西": "M6014033",
        "内蒙古": "M5132285", "辽宁": "M5132289", "吉林": "M6065851", "上海": "M5132299",
        "江苏": "M5132302", "浙江": "M5132306", "安徽": "M5132312", "福建": "M5132317",
        "江西": "M5132322", "山东": "M5132328", "河南": "M5132332", "湖北": "M5132421",
        "湖南": "M5132339", "广东": "M5132345", "广西": "M5132350", "海南": "M5132356",
        "重庆": "M6244243", "四川": "M5993296", "贵州": "M5132374", "云南": "M5132376",
        "西藏": "M5132382", "陕西": "M5132388", "甘肃": "M5132411", "青海": "M5132399",
        "宁夏": "M5132405", "新疆": "M6145090",
    },
    "resource_tax_revenue": {
        "北京": "M0025050", "天津": "M0025076", "河北": "M0025102", "山西": "M0025128",
        "内蒙古": "M0025154", "辽宁": "M0025180", "吉林": "M0025206", "黑龙江": "M0025232",
        "上海": "M0025258", "江苏": "M0025284", "浙江": "M0025310", "安徽": "M0025336",
        "福建": "M0025362", "江西": "M0025388", "山东": "M0025414", "河南": "M0025440",
        "湖北": "M0025466", "湖南": "M0025492", "广东": "M0025518", "广西": "M0025544",
        "海南": "M0025570", "重庆": "M0025596", "四川": "M0025622", "贵州": "M0025648",
        "云南": "M0025674", "西藏": "M0025700", "陕西": "M0025726", "甘肃": "M0025752",
        "青海": "M0025778", "宁夏": "M0025804", "新疆": "M0025830",
    },
    "public_budget_revenue": {
        "北京": "M6249284", "天津": "B3478799", "河北": "M0025096", "山西": "M6012438",
        "内蒙古": "M0025148", "辽宁": "M0025174", "吉林": "M0025200", "黑龙江": "M0025226",
        "上海": "Y2067850", "江苏": "M0025278", "浙江": "M0025304", "安徽": "M0025330",
        "福建": "M5731342", "江西": "M0025382", "山东": "M0025408", "河南": "M0025434",
        "湖北": "M0025460", "湖南": "M0025486", "广东": "M0025512", "广西": "M0025538",
        "海南": "M0025564", "重庆": "M6246003", "四川": "M0025616", "贵州": "M0025642",
        "云南": "M6136627", "西藏": "M0025694", "陕西": "M6308739", "甘肃": "M0025746",
        "青海": "M0025772", "宁夏": "M0025798", "新疆": "M0025824",
    },
    "raw_coal_output": {
        "山西": "M6013691", "宁夏": "T9609626", "云南": "M6155182",
        "江西": "Y6504166", "四川": "A6950655", "青海": "P7796669",
    },
}


def wind_call(mode: str, question: str, observation: str | None = None) -> list[dict]:
    params = {"executionMode": mode, "question": question}
    if observation is not None:
        params["observation"] = observation
    command = [
        "node", str(WIND_CLI), "call", "economic_data",
        "natural_language_get_edb_data", json.dumps(params, ensure_ascii=False),
    ]
    result = subprocess.run(
        command, cwd=WIND_SKILL_DIR, check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        detail = result.stdout.strip() or result.stderr.strip()
        raise RuntimeError(f"Wind CLI failed for {mode} {question}: {detail}")
    outer = json.loads(result.stdout)
    text_blocks = [item["text"] for item in outer.get("content", []) if item.get("type") == "text"]
    if not text_blocks:
        return []
    inner = json.loads(text_blocks[0])
    response = inner.get("data") or {}
    if response.get("code") != 0:
        raise RuntimeError(f"Wind EDB error: {response}")
    return response.get("data") or []


def normalize_value(value: float, unit: str, base_unit: str) -> float:
    if base_unit == "万元":
        if unit == "亿元":
            return value * 10000.0
        if unit == "万元":
            return value
    if base_unit == "万人" and unit == "万人":
        return value
    if base_unit == "万吨" and unit == "万吨":
        return value
    raise ValueError(f"Unsupported unit conversion: {unit} -> {base_unit}")


def province_from_name(name: str) -> str:
    prefix = name.split(":", 1)[0]
    for province_cn in PROVINCE_CN_TO_MAIN:
        if province_cn in prefix:
            return province_cn
    return prefix


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_cached_codes(path: Path) -> dict[str, dict[str, str]]:
    cached: dict[str, dict[str, str]] = defaultdict(dict)
    if not path.exists():
        return cached
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            series_type = row.get("series_type", "")
            province_cn = row.get("province_cn", "")
            code = row.get("code", "")
            if series_type and province_cn and code:
                cached[series_type][province_cn] = code
    return cached


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--employment-only", action="store_true",
        help="Fetch only mining and total urban non-private employment series.",
    )
    args = parser.parse_args()

    codebook: list[dict] = []
    codebook_seen: set[tuple[str, str]] = set()
    long_rows: list[dict] = []
    cached_codes = load_cached_codes(OUT_DIR / "wind_resource_dependency_codebook.csv")

    specs = SPECS[:2] if args.employment_only else SPECS
    for spec in specs:
        known_codes = dict(STATIC_CODES.get(spec["type"], {}))
        if spec["type"] != "raw_coal_output":
            known_codes.update(cached_codes.get(spec["type"], {}))
        found = [] if known_codes else wind_call("search", spec["query"])
        selected = []
        seen = set()
        if known_codes:
            selected = [{"code": code} for code in known_codes.values()]
            seen = {item["code"] for item in selected}
        for item in found:
            meta = item.get("meta") or {}
            name = meta.get("name", "")
            province_cn = province_from_name(name)
            code = meta.get("code", "")
            accepted_units = spec.get("accepted_units")
            accepted_freqs = spec.get("accepted_freqs")
            if (
                province_cn not in PROVINCE_CN_TO_MAIN
                or not spec["accept"](name)
                or (accepted_units and meta.get("unit", "") not in accepted_units)
                or (accepted_freqs and meta.get("freq", "") not in accepted_freqs)
                or code in seen
            ):
                continue
            seen.add(code)
            selected.append(meta)

        if spec.get("province_query"):
            selected_provinces = {
                province_from_name(meta.get("name", ""))
                for meta in selected if meta.get("name")
            }
            selected_provinces.update(known_codes)
            for province_cn in PROVINCE_CN_TO_MAIN:
                if province_cn in selected_provinces:
                    continue
                query = spec["province_query"].format(province=province_cn)
                try:
                    province_results = wind_call("search", query)
                except RuntimeError as exc:
                    print(f"Wind discovery skipped: {query}: {exc}", file=sys.stderr)
                    continue
                for item in province_results:
                    meta = item.get("meta") or {}
                    name = meta.get("name", "")
                    code = meta.get("code", "")
                    if (
                        province_from_name(name) == province_cn
                        and spec["accept"](name)
                        and (
                            not spec.get("accepted_units")
                            or meta.get("unit", "") in spec["accepted_units"]
                        )
                        and (
                            not spec.get("accepted_freqs")
                            or meta.get("freq", "") in spec["accepted_freqs"]
                        )
                        and code not in seen
                    ):
                        seen.add(code)
                        selected.append(meta)
                        selected_provinces.add(province_cn)
                        break

        for start in range(0, len(selected), 20):
            codes = ",".join(meta["code"] for meta in selected[start:start + 20])
            for series in wind_call("fetch", codes, observation="all"):
                meta = series.get("meta") or {}
                name = meta.get("name", "")
                province_cn = province_from_name(name)
                unit = meta.get("unit", "")
                codebook_key = (spec["type"], meta.get("code", ""))
                if province_cn in PROVINCE_CN_TO_MAIN and codebook_key not in codebook_seen:
                    codebook_seen.add(codebook_key)
                    codebook.append({
                        "series_type": spec["type"],
                        "province": PROVINCE_CN_TO_MAIN[province_cn],
                        "province_cn": province_cn,
                        "code": meta.get("code", ""),
                        "name": name,
                        "unit": unit,
                        "source": meta.get("source", ""),
                        "frequency": meta.get("freq", ""),
                        "update_date": meta.get("updateDate", ""),
                    })
                for date, value in zip(series.get("date", []), series.get("value", [])):
                    year = int(str(date)[:4])
                    if value is None or year < 2000 or year > 2023:
                        continue
                    long_rows.append({
                        "province": PROVINCE_CN_TO_MAIN[province_cn],
                        "province_cn": province_cn,
                        "year": year,
                        "series_type": spec["type"],
                        "variable": spec["panel_name"],
                        "value": value,
                        "unit": unit,
                        "value_normalized": normalize_value(float(value), unit, spec["base_unit"]),
                        "normalized_unit": spec["base_unit"],
                        "code": meta.get("code", ""),
                        "name": name,
                        "source": meta.get("source", ""),
                    })

    codebook.sort(key=lambda row: (row["series_type"], row["province"]))
    long_rows.sort(key=lambda row: (row["province"], row["year"], row["series_type"]))

    write_csv(
        OUT_DIR / "wind_resource_dependency_codebook.csv", codebook,
        ["series_type", "province", "province_cn", "code", "name", "unit", "source", "frequency", "update_date"],
    )
    write_csv(
        OUT_DIR / "wind_resource_dependency_long_2000_2023.csv", long_rows,
        ["province", "province_cn", "year", "series_type", "variable", "value", "unit", "value_normalized", "normalized_unit", "code", "name", "source"],
    )

    panel: dict[tuple[str, int], dict] = {}
    seen_panel_variables: set[tuple[str, int, str]] = set()
    for row in long_rows:
        key = (row["province"], int(row["year"]))
        variable_key = (*key, row["variable"])
        if variable_key in seen_panel_variables:
            raise ValueError(f"Duplicate province-year-variable observation: {variable_key}")
        seen_panel_variables.add(variable_key)
        if key not in panel:
            panel[key] = {
                "province": row["province"], "province_cn": row["province_cn"], "year": row["year"]
            }
        panel[key][row["variable"]] = row["value_normalized"]

    for row in panel.values():
        pairs = [
            ("mining_employment_10k_person", "urban_nonprivate_employment_10k_person", "mining_employment_share"),
            ("coal_mining_assets_10k_cny", "industrial_assets_10k_cny", "coal_mining_asset_share"),
            ("resource_tax_revenue_10k_cny", "public_budget_revenue_10k_cny", "resource_tax_share"),
            ("state_owned_industrial_assets_10k_cny", "industrial_assets_10k_cny", "state_owned_industrial_asset_share"),
        ]
        for numerator, denominator, output in pairs:
            if row.get(numerator) is not None and row.get(denominator):
                row[output] = row[numerator] / row[denominator]

    panel_rows = [panel[key] for key in sorted(panel)]
    panel_fields = ["province", "province_cn", "year"]
    for spec in specs:
        panel_fields.append(spec["panel_name"])
    panel_fields.extend([
        "mining_employment_share", "coal_mining_asset_share", "resource_tax_share",
        "state_owned_industrial_asset_share",
    ])
    write_csv(OUT_DIR / "wind_resource_dependency_panel_2000_2023.csv", panel_rows, panel_fields)

    pre_rows = []
    by_province: dict[str, list[dict]] = defaultdict(list)
    for row in panel_rows:
        if 2008 <= int(row["year"]) <= 2011:
            by_province[row["province"]].append(row)
    for province, rows in sorted(by_province.items()):
        out = {"province": province, "province_cn": rows[0]["province_cn"]}
        for variable in [
            "mining_employment_share", "coal_mining_asset_share", "resource_tax_share",
            "state_owned_industrial_asset_share", "raw_coal_output_10k_ton",
        ]:
            values = [float(row[variable]) for row in rows if row.get(variable) not in (None, "")]
            if values:
                out[f"pre_{variable}_0811"] = sum(values) / len(values)
                out[f"pre_{variable}_0811_n"] = len(values)
        pre_rows.append(out)
    pre_fields = ["province", "province_cn"]
    for variable in [
        "mining_employment_share", "coal_mining_asset_share", "resource_tax_share",
        "state_owned_industrial_asset_share", "raw_coal_output_10k_ton",
    ]:
        pre_fields.extend([f"pre_{variable}_0811", f"pre_{variable}_0811_n"])
    write_csv(OUT_DIR / "wind_resource_dependency_pre_0811.csv", pre_rows, pre_fields)

    coverage = []
    for spec in specs:
        rows = [row for row in long_rows if row["series_type"] == spec["type"]]
        years = [int(row["year"]) for row in rows]
        coverage.append({
            "series_type": spec["type"],
            "series_count": sum(1 for row in codebook if row["series_type"] == spec["type"]),
            "province_count": len({row["province"] for row in rows}),
            "observation_count": len(rows),
            "min_year": min(years) if years else "",
            "max_year": max(years) if years else "",
        })
    write_csv(
        OUT_DIR / "wind_resource_dependency_coverage.csv", coverage,
        ["series_type", "series_count", "province_count", "observation_count", "min_year", "max_year"],
    )

    for row in coverage:
        print(row)


if __name__ == "__main__":
    main()
