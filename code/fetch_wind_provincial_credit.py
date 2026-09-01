#!/usr/bin/env python3
"""Fetch provincial RMB loan/deposit balances from Wind EDB and merge them.

The resulting variables measure general local credit supply. They are controls
or conditioning variables and must not be interpreted as green credit.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIND_SKILL_DIR = Path.home() / ".agents" / "skills" / "wind-mcp-skill"
WIND_CLI = WIND_SKILL_DIR / "scripts" / "cli.mjs"
OUT_DIR = ROOT / "data" / "wind_provincial_credit"

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

SPECS = {
    "loan": {
        "query": "中国各省金融机构人民币各项贷款余额月度",
        "suffix": "金融机构各项贷款余额:人民币",
        "variable": "wind_loan_balance_100m_cny",
    },
    "deposit": {
        "query": "中国各省金融机构人民币各项存款余额月度",
        "suffix": "金融机构各项存款余额:人民币",
        "variable": "wind_deposit_balance_100m_cny",
    },
}

# The broad Wind discovery response substitutes a short Jiangsu statistical
# bureau series for the longer PBoC series. These PBoC codes were verified by
# direct Wind EDB fetch on 2026-07-16.
STATIC_MONTHLY_CODES = {
    "loan": ["M0059518"],
    "deposit": ["M0059509"],
}


def wind_search_fetch(question: str) -> list[dict]:
    params = {
        "executionMode": "searchFetch",
        "question": question,
        "beginDate": "20000101",
        "endDate": "20231231",
    }
    command = [
        "node", str(WIND_CLI), "call", "economic_data",
        "natural_language_get_edb_data", json.dumps(params, ensure_ascii=False),
    ]
    result = subprocess.run(
        command, cwd=WIND_SKILL_DIR, check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        detail = result.stdout.strip() or result.stderr.strip()
        raise RuntimeError(f"Wind CLI failed: {detail}")
    outer = json.loads(result.stdout)
    blocks = [item["text"] for item in outer.get("content", []) if item.get("type") == "text"]
    if not blocks:
        return []
    inner = json.loads(blocks[0])
    response = inner.get("data") or {}
    if response.get("code") != 0:
        raise RuntimeError(f"Wind EDB error: {response}")
    return response.get("data") or []


def wind_fetch_codes(codes: list[str]) -> list[dict]:
    if not codes:
        return []
    params = {
        "executionMode": "fetch",
        "question": ",".join(codes),
        "beginDate": "20000101",
        "endDate": "20231231",
    }
    command = [
        "node", str(WIND_CLI), "call", "economic_data",
        "natural_language_get_edb_data", json.dumps(params, ensure_ascii=False),
    ]
    result = subprocess.run(
        command, cwd=WIND_SKILL_DIR, check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        detail = result.stdout.strip() or result.stderr.strip()
        raise RuntimeError(f"Wind CLI code fetch failed: {detail}")
    outer = json.loads(result.stdout)
    blocks = [item["text"] for item in outer.get("content", []) if item.get("type") == "text"]
    if not blocks:
        return []
    inner = json.loads(blocks[0])
    response = inner.get("data") or {}
    if response.get("code") != 0:
        raise RuntimeError(f"Wind EDB code fetch error: {response}")
    return response.get("data") or []


def identify_province(name: str) -> tuple[str, str] | None:
    for province_cn, province in PROVINCE_CN_TO_MAIN.items():
        if name.startswith(f"{province_cn}:"):
            return province_cn, province
    return None


def select_series(series: list[dict], suffix: str) -> dict[str, dict]:
    candidates: dict[str, list[dict]] = defaultdict(list)
    for item in series:
        meta = item.get("meta") or {}
        name = str(meta.get("name") or "")
        province = identify_province(name)
        if province is None:
            continue
        province_cn, province_main = province
        if not name.endswith(suffix):
            continue
        if meta.get("freq") not in {"月", "年"} or meta.get("unit") != "亿元":
            continue
        candidates[province_main].append(item)

    selected = {}
    for province, items in candidates.items():
        def rank(item: dict) -> tuple[int, int, int]:
            meta = item.get("meta") or {}
            dates = item.get("date") or []
            year_end_n = sum(str(date).endswith("1231") for date in dates)
            return (
                int(meta.get("freq") == "月"),
                int(meta.get("source") == "中国人民银行"),
                year_end_n,
            )

        items.sort(key=rank, reverse=True)
        selected[province] = items[0]
    return selected


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fetch_panel() -> tuple[list[dict], list[dict]]:
    values: dict[tuple[str, int], dict] = defaultdict(dict)
    metadata_rows: list[dict] = []
    for kind, spec in SPECS.items():
        discovered = wind_search_fetch(spec["query"])
        discovered.extend(wind_fetch_codes(STATIC_MONTHLY_CODES.get(kind, [])))
        selected = select_series(discovered, spec["suffix"])
        for province, item in selected.items():
            meta = item["meta"]
            dates = item.get("date") or []
            observations = item.get("value") or []
            year_end_dates = [date for date in dates if str(date).endswith("1231")]
            metadata_rows.append({
                "kind": kind,
                "province": province,
                "wind_code": meta.get("code"),
                "wind_name": meta.get("name"),
                "source": meta.get("source"),
                "unit": meta.get("unit"),
                "frequency": meta.get("freq"),
                "update_date": meta.get("updateDate"),
                "first_year": min((int(date[:4]) for date in year_end_dates), default=""),
                "last_year": max((int(date[:4]) for date in year_end_dates), default=""),
                "observation_n": len(year_end_dates),
            })
            for date, value in zip(dates, observations):
                if not str(date).endswith("1231"):
                    continue
                year = int(date[:4])
                if not 2000 <= year <= 2023 or value is None:
                    continue
                key = (province, year)
                if spec["variable"] in values[key]:
                    raise ValueError(f"Duplicate selected value for {key} {kind}")
                values[key][spec["variable"]] = float(value)

    rows = []
    for (province, year), item in sorted(values.items()):
        loan = item.get("wind_loan_balance_100m_cny")
        deposit = item.get("wind_deposit_balance_100m_cny")
        ratio = loan / deposit if loan is not None and deposit not in (None, 0) else ""
        rows.append({
            "province": province,
            "year": year,
            "wind_loan_balance_100m_cny": loan if loan is not None else "",
            "wind_deposit_balance_100m_cny": deposit if deposit is not None else "",
            "wind_loan_deposit_ratio": ratio,
        })
    return rows, metadata_rows


def add_pre_policy_means(rows: list[dict]) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if 2008 <= int(row["year"]) <= 2011:
            grouped[row["province"]].append(row)
    result = {}
    for province in PROVINCE_CN_TO_MAIN.values():
        province_rows = grouped.get(province, [])
        ratios = [float(row["wind_loan_deposit_ratio"]) for row in province_rows
                  if row["wind_loan_deposit_ratio"] != ""]
        loans = [float(row["wind_loan_balance_100m_cny"]) for row in province_rows
                 if row["wind_loan_balance_100m_cny"] != ""]
        result[province] = {
            "pre_wind_loan_deposit_ratio_0811": statistics.mean(ratios) if len(ratios) == 4 else "",
            "pre_wind_loan_balance_0811_100m_cny": statistics.mean(loans) if len(loans) == 4 else "",
            "pre_wind_credit_0811_n": len(ratios),
        }
    complete = [value["pre_wind_loan_deposit_ratio_0811"] for value in result.values()
                if value["pre_wind_loan_deposit_ratio_0811"] != ""]
    mean_value = statistics.mean(complete)
    sd_value = statistics.stdev(complete)
    for value in result.values():
        ratio = value["pre_wind_loan_deposit_ratio_0811"]
        value["pre_wind_loan_deposit_ratio_0811_z"] = (
            (ratio - mean_value) / sd_value if ratio != "" else ""
        )
    return result


def merge_panel(input_path: Path, output_path: Path, rows: list[dict], pre: dict[str, dict]) -> None:
    annual = {(row["province"], int(row["year"])): row for row in rows}
    with input_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        fieldnames = list(reader.fieldnames or [])
        panel_rows = list(reader)
        additions = [
            "wind_loan_balance_100m_cny", "wind_deposit_balance_100m_cny",
            "wind_loan_deposit_ratio", "wind_loan_gdp_ratio",
            "pre_wind_loan_deposit_ratio_0811",
            "pre_wind_loan_balance_0811_100m_cny", "pre_wind_credit_0811_n",
            "pre_wind_loan_deposit_ratio_0811_z", "pre_wind_loan_gdp_ratio_0811",
            "pre_wind_loan_gdp_ratio_0811_z",
        ]
        if any(name in fieldnames for name in additions):
            raise ValueError("Credit variables already exist in input panel")

    seen = set()
    for row in panel_rows:
        key = (row["province"], int(float(row["year"])))
        if key in seen:
            raise ValueError(f"Duplicate panel key: {key}")
        seen.add(key)
        annual_row = annual.get(key, {})
        for name in additions[:3]:
            row[name] = annual_row.get(name, "")
        loan = row["wind_loan_balance_100m_cny"]
        gdp = row.get("gdp", "")
        row["wind_loan_gdp_ratio"] = (
            float(loan) / float(gdp) if loan != "" and gdp != "" and float(gdp) > 0 else ""
        )
        row.update(pre.get(row["province"], {}))

    gdp_pre_by_province: dict[str, list[float]] = defaultdict(list)
    for row in panel_rows:
        year = int(float(row["year"]))
        if 2008 <= year <= 2011 and row["wind_loan_gdp_ratio"] != "":
            gdp_pre_by_province[row["province"]].append(float(row["wind_loan_gdp_ratio"]))
    gdp_pre = {
        province: statistics.mean(values)
        for province, values in gdp_pre_by_province.items() if len(values) == 4
    }
    gdp_pre_mean = statistics.mean(gdp_pre.values())
    gdp_pre_sd = statistics.stdev(gdp_pre.values())
    for row in panel_rows:
        value = gdp_pre.get(row["province"], "")
        row["pre_wind_loan_gdp_ratio_0811"] = value
        row["pre_wind_loan_gdp_ratio_0811_z"] = (
            (value - gdp_pre_mean) / gdp_pre_sd if value != "" else ""
        )

    if len(panel_rows) != 744:
        raise ValueError(f"Expected 744 rows after merge, got {len(panel_rows)}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames + additions)
        writer.writeheader()
        writer.writerows(panel_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path,
        default=ROOT / "data" / "final_data.1.3.4_did_full_resource_v2_0716.csv",
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "data" / "final_data.1.3.4_did_full_resource_v2_credit_0716.csv",
    )
    args = parser.parse_args()

    rows, metadata = fetch_panel()
    pre = add_pre_policy_means(rows)
    write_csv(
        OUT_DIR / "wind_provincial_credit_2000_2023.csv", rows,
        ["province", "year", "wind_loan_balance_100m_cny",
         "wind_deposit_balance_100m_cny", "wind_loan_deposit_ratio"],
    )
    write_csv(
        OUT_DIR / "wind_provincial_credit_metadata.csv", metadata,
        ["kind", "province", "wind_code", "wind_name", "source", "unit",
         "frequency", "update_date", "first_year", "last_year", "observation_n"],
    )
    pre_rows = [{"province": province, **values} for province, values in sorted(pre.items())]
    write_csv(
        OUT_DIR / "wind_provincial_credit_pre_0811.csv", pre_rows,
        ["province", "pre_wind_loan_deposit_ratio_0811",
         "pre_wind_loan_balance_0811_100m_cny", "pre_wind_credit_0811_n",
         "pre_wind_loan_deposit_ratio_0811_z"],
    )
    merge_panel(args.input, args.output, rows, pre)

    loan_n = sum(row["wind_loan_balance_100m_cny"] != "" for row in rows)
    deposit_n = sum(row["wind_deposit_balance_100m_cny"] != "" for row in rows)
    ratio_n = sum(row["wind_loan_deposit_ratio"] != "" for row in rows)
    pre_n = sum(item["pre_wind_loan_deposit_ratio_0811"] != "" for item in pre.values())
    print(f"annual rows={len(rows)} loan_n={loan_n} deposit_n={deposit_n} ratio_n={ratio_n}")
    print(f"complete pre-2008-2011 provinces={pre_n}")
    print(f"merged panel={args.output}")


if __name__ == "__main__":
    main()
