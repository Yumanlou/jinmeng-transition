#!/usr/bin/env python3
"""Extract provincial energy-transition indicators from Wind EDB.

Outputs are kept separate from the existing master panel so that Wind series
can be audited before any overwrite or merge. The script discovers EDB codes,
caches every Wind response, fetches observations in batches, and builds:

1. Provincial generation by source (December YTD observations).
2. Provincial wind/solar installed and newly installed capacity.
3. Provincial coal/electricity transfers in and out.
4. A combined province-year panel, codebook, coverage report, and QA report.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
WIND_SKILL = Path("/Users/yumanlou/.agents/skills/wind-mcp-skill")
WIND_CLI = WIND_SKILL / "scripts" / "cli.mjs"
OFFLINE = False

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
PROVINCES_CN = list(PROVINCE_CN_TO_MAIN)


@dataclass(frozen=True)
class SeriesSpec:
    variable: str
    module: str
    output_unit: str
    annual_method: str


GENERATION_SPECS = {
    "nbs_wind_generation_billion_kwh": (
        "各省风力发电量累计值",
        "发电量:风力:累计值",
    ),
    "nbs_solar_generation_billion_kwh": (
        "各省太阳能发电量累计值",
        "发电量:太阳能:累计值",
    ),
    "nbs_hydro_generation_billion_kwh": (
        "各省水力发电量累计值",
        "发电量:水力:累计值",
    ),
    "nbs_nuclear_generation_billion_kwh": (
        "各省核能发电量累计值",
        "发电量:核能:累计值",
    ),
    "nbs_thermal_generation_billion_kwh": (
        "各省火力发电量累计值",
        "发电量:火力:累计值",
    ),
}

CAPACITY_PATTERNS = {
    "wind_capacity_10k_kw": "装机容量:新能源:风电",
    "solar_capacity_10k_kw": "装机容量:新能源:太阳能",
    "wind_capacity_addition_10k_kw": "当年新增装机容量:新能源:风电",
    "solar_capacity_addition_10k_kw": "当年新增装机容量:新能源:太阳能",
}

FLOW_PATTERNS = {
    "coal_transfer_in_10k_ton": "外省(区、市)调入量:实物量:煤",
    "coal_transfer_out_raw_10k_ton": "本省(区、市)调出量:实物量:煤",
    "electricity_transfer_in_100m_kwh": "外省(区、市)调入量:实物量:电力",
    "electricity_transfer_out_raw_100m_kwh": "本省(区、市)调出量:实物量:电力",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "wind_energy_transition_0718",
    )
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Rebuild outputs only from existing Wind response caches.",
    )
    return parser.parse_args()


def safe_slug(text: str) -> str:
    keep = []
    for char in text:
        if char.isalnum() or char in "_-":
            keep.append(char)
        else:
            keep.append("_")
    return "".join(keep).strip("_")[:120]


def parse_cli_payload(stdout: str) -> dict[str, Any]:
    if not stdout.strip():
        raise RuntimeError("Wind CLI returned empty stdout")
    outer = json.loads(stdout)
    if outer.get("ok") is False:
        raise RuntimeError(json.dumps(outer.get("error", outer), ensure_ascii=False))
    content = outer.get("content") or []
    if not content:
        raise RuntimeError("Wind CLI returned no content")
    text = content[0].get("text", "")
    inner = json.loads(text) if isinstance(text, str) else text
    data = inner.get("data", inner)
    if data.get("code") not in (None, 0):
        raise RuntimeError(json.dumps(data, ensure_ascii=False))
    return inner


def call_wind(
    params: dict[str, str],
    cache_path: Path,
    refresh: bool,
    retries: int = 2,
) -> dict[str, Any]:
    if cache_path.exists() and not refresh:
        return parse_cli_payload(cache_path.read_text(encoding="utf-8"))
    if OFFLINE:
        raise RuntimeError(f"offline cache missing: {cache_path.name}")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "node",
        str(WIND_CLI.relative_to(WIND_SKILL)),
        "call",
        "economic_data",
        "natural_language_get_edb_data",
        json.dumps(params, ensure_ascii=False, separators=(",", ":")),
    ]
    last_error = ""
    for attempt in range(retries + 1):
        result = subprocess.run(
            command,
            cwd=WIND_SKILL,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        if result.returncode == 0 and result.stdout.strip():
            cache_path.write_text(result.stdout, encoding="utf-8")
            return parse_cli_payload(result.stdout)
        last_error = result.stdout.strip() or result.stderr.strip()
        try:
            error_payload = json.loads(result.stdout) if result.stdout.strip() else {}
        except json.JSONDecodeError:
            error_payload = {}
        if error_payload.get("error", {}).get("code") == "QUOTA_ERROR":
            raise RuntimeError(last_error)
        if attempt < retries:
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(last_error or "Wind CLI call failed")


def payload_series(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data", payload)
    series = data.get("data") or []
    return series if isinstance(series, list) else []


def detect_province(name: str) -> str | None:
    for province in sorted(PROVINCES_CN, key=len, reverse=True):
        if province in name:
            return province
    return None


def source_priority(meta: dict[str, Any]) -> tuple[int, int]:
    source = str(meta.get("source", ""))
    freq = str(meta.get("freq", ""))
    source_score = 3 if "国家能源局" in source else 2 if "国家统计局" in source else 1
    freq_score = 2 if freq == "年" else 1
    return source_score, freq_score


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def search_generation(
    cache_dir: Path, refresh: bool
) -> tuple[dict[str, SeriesSpec], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    code_specs: dict[str, SeriesSpec] = {}
    metadata: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []

    for variable, (query, pattern) in GENERATION_SPECS.items():
        cache_variable = variable.removeprefix("nbs_")
        cache_path = cache_dir / f"search_generation_{safe_slug(cache_variable)}.json"
        try:
            payload = call_wind(
                {"executionMode": "search", "question": query}, cache_path, refresh
            )
        except Exception as exc:  # noqa: BLE001
            failures.append({"stage": "search", "query": query, "error": str(exc)})
            continue
        for item in payload_series(payload):
            meta = item.get("meta", item)
            name = str(meta.get("name", ""))
            province = detect_province(name)
            code = str(meta.get("code", ""))
            if not province or not code or pattern not in name:
                continue
            old = metadata.get(code)
            if old is not None and source_priority(old) > source_priority(meta):
                continue
            metadata[code] = {**meta, "province_cn": province, "variable": variable}
            code_specs[code] = SeriesSpec(
                variable=variable,
                module="generation",
                output_unit="billion_kwh",
                annual_method="december_ytd",
            )
    return code_specs, metadata, failures


def search_one_province_capacity(
    province: str, cache_dir: Path, refresh: bool
) -> tuple[list[tuple[str, SeriesSpec, dict[str, Any]]], list[dict[str, Any]]]:
    query = (
        f"国家能源局{province}风电装机容量太阳能装机容量"
        "当年新增风电装机容量当年新增太阳能装机容量"
    )
    cache_path = cache_dir / f"search_capacity_{safe_slug(province)}.json"
    found: list[tuple[str, SeriesSpec, dict[str, Any]]] = []
    failures: list[dict[str, Any]] = []
    try:
        payload = call_wind(
            {"executionMode": "search", "question": query}, cache_path, refresh
        )
    except Exception as exc:  # noqa: BLE001
        failures.append({"stage": "search", "query": query, "error": str(exc)})
        return found, failures

    candidates: dict[str, list[dict[str, Any]]] = {key: [] for key in CAPACITY_PATTERNS}
    for item in payload_series(payload):
        meta = item.get("meta", item)
        name = str(meta.get("name", ""))
        if province not in name:
            continue
        for variable, pattern in CAPACITY_PATTERNS.items():
            if pattern not in name:
                continue
            if "capacity_addition" not in variable and "新增" in name:
                continue
            candidates[variable].append(meta)

    for variable, metas in candidates.items():
        if not metas:
            failures.append(
                {"stage": "search_missing", "query": query, "variable": variable}
            )
            continue
        meta = sorted(metas, key=source_priority, reverse=True)[0]
        code = str(meta.get("code", ""))
        found.append(
            (
                code,
                SeriesSpec(variable, "capacity", "10k_kw", "annual_observation"),
                {**meta, "province_cn": province, "variable": variable},
            )
        )
    return found, failures


def search_one_province_flows(
    province: str, cache_dir: Path, refresh: bool
) -> tuple[list[tuple[str, SeriesSpec, dict[str, Any]]], list[dict[str, Any]]]:
    query = (
        f"中国能源统计年鉴{province}煤炭调入量煤炭调出量"
        "电力调入量电力调出量"
    )
    cache_path = cache_dir / f"search_flows_{safe_slug(province)}.json"
    found: list[tuple[str, SeriesSpec, dict[str, Any]]] = []
    failures: list[dict[str, Any]] = []
    try:
        payload = call_wind(
            {"executionMode": "search", "question": query}, cache_path, refresh
        )
    except Exception as exc:  # noqa: BLE001
        failures.append({"stage": "search", "query": query, "error": str(exc)})
        return found, failures

    candidates: dict[str, list[dict[str, Any]]] = {key: [] for key in FLOW_PATTERNS}
    for item in payload_series(payload):
        meta = item.get("meta", item)
        name = str(meta.get("name", ""))
        if province not in name:
            continue
        for variable, pattern in FLOW_PATTERNS.items():
            if pattern in name:
                candidates[variable].append(meta)

    for variable, metas in candidates.items():
        if not metas:
            failures.append(
                {"stage": "search_missing", "query": query, "variable": variable}
            )
            continue
        meta = sorted(metas, key=source_priority, reverse=True)[0]
        code = str(meta.get("code", ""))
        unit = "10k_ton" if variable.startswith("coal_") else "100m_kwh"
        found.append(
            (
                code,
                SeriesSpec(variable, "flows", unit, "annual_observation"),
                {**meta, "province_cn": province, "variable": variable},
            )
        )
    return found, failures


def search_province_modules(
    workers: int, cache_dir: Path, refresh: bool
) -> tuple[dict[str, SeriesSpec], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    code_specs: dict[str, SeriesSpec] = {}
    metadata: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    jobs = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for province in PROVINCES_CN:
            jobs.append(
                pool.submit(search_one_province_capacity, province, cache_dir, refresh)
            )
            jobs.append(pool.submit(search_one_province_flows, province, cache_dir, refresh))
        for future in as_completed(jobs):
            found, local_failures = future.result()
            failures.extend(local_failures)
            for code, spec, meta in found:
                if code:
                    code_specs[code] = spec
                    metadata[code] = meta
    return code_specs, metadata, failures


def exact_query(module: str, province: str, variable: str) -> str:
    if module == "capacity":
        labels = {
            "wind_capacity_10k_kw": "装机容量新能源风电",
            "solar_capacity_10k_kw": "装机容量新能源太阳能",
            "wind_capacity_addition_10k_kw": "当年新增装机容量新能源风电",
            "solar_capacity_addition_10k_kw": "当年新增装机容量新能源太阳能",
        }
        return f"国家能源局{province}{labels[variable]}"
    labels = {
        "coal_transfer_in_10k_ton": "煤炭外省调入量",
        "coal_transfer_out_raw_10k_ton": "煤炭本省调出量",
        "electricity_transfer_in_100m_kwh": "电力外省调入量",
        "electricity_transfer_out_raw_100m_kwh": "电力本省调出量",
    }
    return f"中国能源统计年鉴{province}{labels[variable]}"


def search_exact_missing_one(
    module: str,
    province: str,
    variable: str,
    cache_dir: Path,
    refresh: bool,
) -> tuple[str, SeriesSpec, dict[str, Any]] | dict[str, Any]:
    query = exact_query(module, province, variable)
    cache_path = cache_dir / (
        f"search_exact_{module}_{safe_slug(province)}_{safe_slug(variable)}.json"
    )
    try:
        payload = call_wind(
            {"executionMode": "search", "question": query}, cache_path, refresh
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "stage": "search_exact",
            "query": query,
            "variable": variable,
            "error": str(exc),
        }

    pattern = CAPACITY_PATTERNS[variable] if module == "capacity" else FLOW_PATTERNS[variable]
    candidates: list[dict[str, Any]] = []
    for item in payload_series(payload):
        meta = item.get("meta", item)
        name = str(meta.get("name", ""))
        if province in name and pattern in name:
            if module == "capacity" and "capacity_addition" not in variable and "新增" in name:
                continue
            candidates.append(meta)
    if not candidates:
        return {
            "stage": "search_exact_missing",
            "query": query,
            "variable": variable,
        }
    meta = sorted(candidates, key=source_priority, reverse=True)[0]
    code = str(meta.get("code", ""))
    output_unit = (
        "10k_kw"
        if module == "capacity"
        else "10k_ton"
        if variable.startswith("coal_")
        else "100m_kwh"
    )
    return (
        code,
        SeriesSpec(variable, module, output_unit, "annual_observation"),
        {**meta, "province_cn": province, "variable": variable},
    )


def supplement_missing_series(
    code_specs: dict[str, SeriesSpec],
    metadata: dict[str, dict[str, Any]],
    workers: int,
    cache_dir: Path,
    refresh: bool,
) -> list[dict[str, Any]]:
    present = {
        (meta["province_cn"], spec.module, spec.variable)
        for code, spec in code_specs.items()
        for meta in [metadata[code]]
    }
    jobs: list[tuple[str, str, str]] = []
    for province in PROVINCES_CN:
        for variable in CAPACITY_PATTERNS:
            key = (province, "capacity", variable)
            if key not in present:
                jobs.append(key)
        for variable in FLOW_PATTERNS:
            key = (province, "flows", variable)
            if key not in present:
                jobs.append(key)

    failures: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                search_exact_missing_one,
                module,
                province,
                variable,
                cache_dir,
                refresh,
            ): (province, module, variable)
            for province, module, variable in jobs
        }
        for future in as_completed(futures):
            result = future.result()
            if isinstance(result, dict):
                failures.append(result)
                continue
            code, spec, meta = result
            if code:
                code_specs[code] = spec
                metadata[code] = meta
    return failures


def batched(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def fetch_codes(
    code_specs: dict[str, SeriesSpec],
    metadata: dict[str, dict[str, Any]],
    cache_dir: Path,
    start_year: int,
    end_year: int,
    batch_size: int,
    refresh: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    codes = sorted(code_specs)
    for batch_number, batch in enumerate(batched(codes, batch_size), start=1):
        params = {
            "executionMode": "fetch",
            "question": ",".join(batch),
            "beginDate": f"{start_year}0101",
            "endDate": f"{end_year}1231",
        }
        cache_path = cache_dir / f"fetch_batch_{batch_number:03d}.json"
        try:
            payload = call_wind(params, cache_path, refresh)
        except Exception as exc:  # noqa: BLE001
            failures.append(
                {
                    "stage": "fetch",
                    "codes": ",".join(batch),
                    "error": str(exc),
                }
            )
            continue
        returned_codes: set[str] = set()
        for item in payload_series(payload):
            meta = item.get("meta", {})
            code = str(meta.get("code", ""))
            if code not in code_specs:
                continue
            returned_codes.add(code)
            dates = item.get("date") or []
            values = item.get("value") or []
            stored_meta = metadata.get(code, {})
            for date, value in zip(dates, values):
                rows.append(
                    {
                        "province": PROVINCE_CN_TO_MAIN[stored_meta["province_cn"]],
                        "province_cn": stored_meta["province_cn"],
                        "variable": code_specs[code].variable,
                        "date": str(date),
                        "value": value,
                        "wind_code": code,
                        "wind_name": meta.get("name", stored_meta.get("name", "")),
                        "wind_unit": meta.get("unit", stored_meta.get("unit", "")),
                        "wind_frequency": meta.get("freq", stored_meta.get("freq", "")),
                        "wind_source": meta.get("source", stored_meta.get("source", "")),
                        "module": code_specs[code].module,
                        "annual_method": code_specs[code].annual_method,
                    }
                )
        for code in batch:
            if code not in returned_codes:
                failures.append({"stage": "fetch_missing", "codes": code})
    return rows, failures


def numeric(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def build_annual_values(
    raw_rows: list[dict[str, Any]], code_specs: dict[str, SeriesSpec]
) -> dict[tuple[str, int, str], dict[str, Any]]:
    annual: dict[tuple[str, int, str], dict[str, Any]] = {}
    for row in raw_rows:
        date = str(row["date"])
        if len(date) < 8 or not date[:4].isdigit():
            continue
        year = int(date[:4])
        month = int(date[4:6])
        variable = str(row["variable"])
        spec = code_specs[str(row["wind_code"])]
        if spec.annual_method == "december_ytd" and month != 12:
            continue
        value = numeric(row["value"])
        if value is None:
            continue
        if spec.output_unit == "billion_kwh":
            wind_unit = str(row.get("wind_unit", ""))
            if wind_unit == "万千瓦时":
                value /= 100000.0
            elif wind_unit == "亿千瓦时":
                value /= 10.0
            else:
                continue
        key = (str(row["province"]), year, variable)
        annual[key] = {
            "value": value,
            "wind_code": row["wind_code"],
            "wind_source": row["wind_source"],
            "wind_unit": row["wind_unit"],
        }
    return annual


def empty_panel(start_year: int, end_year: int) -> dict[tuple[str, int], dict[str, Any]]:
    return {
        (province, year): {"province": province, "year": year}
        for province in PROVINCE_CN_TO_MAIN.values()
        for year in range(start_year, end_year + 1)
    }


def panel_for_variables(
    annual: dict[tuple[str, int, str], dict[str, Any]],
    variables: list[str],
    start_year: int,
    end_year: int,
) -> list[dict[str, Any]]:
    panel = empty_panel(start_year, end_year)
    for (province, year, variable), item in annual.items():
        if variable not in variables or (province, year) not in panel:
            continue
        panel[(province, year)][variable] = item["value"]
        panel[(province, year)][f"{variable}_wind_code"] = item["wind_code"]
    return [panel[key] for key in sorted(panel)]


def add_capacity_differences(rows: list[dict[str, Any]]) -> None:
    by_province = {province: [] for province in PROVINCE_CN_TO_MAIN.values()}
    for row in rows:
        by_province[row["province"]].append(row)
    for province_rows in by_province.values():
        province_rows.sort(key=lambda row: int(row["year"]))
        for stock, addition in (
            ("wind_capacity_10k_kw", "wind_capacity_addition_from_stock_10k_kw"),
            ("solar_capacity_10k_kw", "solar_capacity_addition_from_stock_10k_kw"),
        ):
            previous: float | None = None
            for row in province_rows:
                current = numeric(row.get(stock))
                if current is not None and previous is not None:
                    row[addition] = current - previous
                previous = current if current is not None else previous


def add_flow_cleaning(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qa: list[dict[str, Any]] = []
    for row in rows:
        for raw_variable, clean_variable in (
            ("coal_transfer_out_raw_10k_ton", "coal_transfer_out_abs_10k_ton"),
            (
                "electricity_transfer_out_raw_100m_kwh",
                "electricity_transfer_out_abs_100m_kwh",
            ),
        ):
            value = numeric(row.get(raw_variable))
            if value is not None:
                row[clean_variable] = abs(value)

    for variable in (
        "coal_transfer_in_10k_ton",
        "coal_transfer_out_abs_10k_ton",
        "electricity_transfer_in_100m_kwh",
        "electricity_transfer_out_abs_100m_kwh",
    ):
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(str(row["province"]), []).append(row)
        for province, province_rows in grouped.items():
            province_rows.sort(key=lambda item: int(item["year"]))
            previous: float | None = None
            for row in province_rows:
                value = numeric(row.get(variable))
                if value is not None and previous not in (None, 0.0):
                    ratio = max(abs(value / previous), abs(previous / value)) if value else math.inf
                    if ratio >= 20:
                        qa.append(
                            {
                                "province": province,
                                "year": row["year"],
                                "variable": variable,
                                "value": value,
                                "previous_value": previous,
                                "flag": "year_to_year_ratio_ge_20",
                            }
                        )
                if value is not None:
                    previous = value
    return qa


def merge_panels(*panels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, int], dict[str, Any]] = {}
    for panel in panels:
        for row in panel:
            key = (str(row["province"]), int(row["year"]))
            target = merged.setdefault(key, {"province": key[0], "year": key[1]})
            target.update(row)
    return [merged[key] for key in sorted(merged)]


def build_coverage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    excluded = {"province", "year"}
    variables = sorted(
        {
            key
            for row in rows
            for key in row
            if key not in excluded and not key.endswith("_wind_code")
        }
    )
    output: list[dict[str, Any]] = []
    for variable in variables:
        available = [row for row in rows if numeric(row.get(variable)) is not None]
        years = [int(row["year"]) for row in available]
        provinces = {str(row["province"]) for row in available}
        output.append(
            {
                "variable": variable,
                "nonmissing_observations": len(available),
                "province_count": len(provinces),
                "first_year": min(years) if years else "",
                "last_year": max(years) if years else "",
            }
        )
    return output


def main() -> None:
    global OFFLINE
    args = parse_args()
    OFFLINE = args.offline
    output_dir = args.output_dir.resolve()
    cache_dir = output_dir / "cache"
    output_dir.mkdir(parents=True, exist_ok=True)

    gen_specs, gen_meta, failures = search_generation(cache_dir, args.refresh)
    module_specs, module_meta, module_failures = search_province_modules(
        args.workers, cache_dir, args.refresh
    )
    failures.extend(module_failures)
    code_specs = {**gen_specs, **module_specs}
    metadata = {**gen_meta, **module_meta}
    failures.extend(
        supplement_missing_series(
            code_specs,
            metadata,
            args.workers,
            cache_dir,
            args.refresh,
        )
    )

    raw_rows, fetch_failures = fetch_codes(
        code_specs,
        metadata,
        cache_dir,
        args.start_year,
        args.end_year,
        args.batch_size,
        args.refresh,
    )
    failures.extend(fetch_failures)
    annual = build_annual_values(raw_rows, code_specs)

    generation_variables = list(GENERATION_SPECS)
    capacity_variables = list(CAPACITY_PATTERNS)
    flow_variables = list(FLOW_PATTERNS)

    generation_panel = panel_for_variables(
        annual, generation_variables, args.start_year, args.end_year
    )
    capacity_panel = panel_for_variables(
        annual, capacity_variables, args.start_year, args.end_year
    )
    add_capacity_differences(capacity_panel)
    flow_panel = panel_for_variables(
        annual, flow_variables, args.start_year, args.end_year
    )
    qa_rows = add_flow_cleaning(flow_panel)
    combined_panel = merge_panels(generation_panel, capacity_panel, flow_panel)

    raw_rows.sort(key=lambda row: (row["province"], row["variable"], row["date"]))
    write_csv(output_dir / "wind_energy_transition_raw_long.csv", raw_rows)
    write_csv(
        output_dir / f"wind_generation_panel_{args.start_year}_{args.end_year}.csv",
        generation_panel,
    )
    write_csv(
        output_dir / f"wind_capacity_additions_panel_{args.start_year}_{args.end_year}.csv",
        capacity_panel,
    )
    write_csv(
        output_dir / f"wind_energy_flows_panel_{args.start_year}_{args.end_year}.csv",
        flow_panel,
    )
    write_csv(
        output_dir / f"wind_energy_transition_panel_{args.start_year}_{args.end_year}.csv",
        combined_panel,
    )

    codebook_rows = []
    for code in sorted(metadata):
        meta = metadata[code]
        spec = code_specs[code]
        codebook_rows.append(
            {
                "variable": spec.variable,
                "module": spec.module,
                "province": PROVINCE_CN_TO_MAIN[meta["province_cn"]],
                "province_cn": meta["province_cn"],
                "wind_code": code,
                "wind_name": meta.get("name", ""),
                "wind_source": meta.get("source", ""),
                "wind_unit": meta.get("unit", ""),
                "wind_frequency": meta.get("freq", ""),
                "output_unit": spec.output_unit,
                "annual_method": spec.annual_method,
                "update_date": meta.get("updateDate", ""),
            }
        )
    write_csv(output_dir / "wind_energy_transition_codebook.csv", codebook_rows)
    write_csv(
        output_dir / "wind_energy_transition_coverage.csv",
        build_coverage(combined_panel),
    )
    write_csv(output_dir / "wind_energy_transition_qa_flags.csv", qa_rows)
    write_csv(output_dir / "wind_energy_transition_failures.csv", failures)

    summary = {
        "completion_status": (
            "BLOCKED_QUOTA"
            if any("QUOTA_ERROR" in str(row.get("error", "")) for row in failures)
            else "DONE_WITH_LIMITS"
            if failures
            else "DONE"
        ),
        "start_year": args.start_year,
        "end_year": args.end_year,
        "province_count": len(PROVINCES_CN),
        "discovered_series": len(code_specs),
        "raw_observations": len(raw_rows),
        "combined_panel_rows": len(combined_panel),
        "failure_rows": len(failures),
        "qa_flag_rows": len(qa_rows),
    }
    (output_dir / "wind_energy_transition_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
