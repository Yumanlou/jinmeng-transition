#!/usr/bin/env python3
"""Build a same-province city panel for the 2017 green-finance pilot DDD.

Wind EDB is queried through the installed wind-mcp-skill CLI. Ganjiang New Area
and Gui'an New Area are excluded because neither maps cleanly to one complete
prefecture-level city. The treatment group therefore contains the six complete
prefecture-level pilot units in Zhejiang, Guangdong, and Xinjiang.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(
    "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
)
WIND_SKILL = Path("/Users/yumanlou/.agents/skills/wind-mcp-skill")
OUT = ROOT / "data/green_finance_pilot_city_wind"
CACHE = OUT / "cache"

PROVINCE_CITIES = {
    "浙江": ["杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水"],
    "广东": ["广州", "韶关", "深圳", "珠海", "汕头", "佛山", "江门", "湛江", "茂名", "肇庆", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮"],
    "新疆": ["乌鲁木齐", "克拉玛依", "吐鲁番", "哈密", "昌吉州", "博尔塔拉州", "巴音郭楞州", "阿克苏地区", "克孜勒苏州", "喀什地区", "和田地区", "伊犁州", "塔城地区", "阿勒泰地区"],
}

PILOT_CITIES = {"湖州", "衢州", "广州", "哈密", "昌吉州", "克拉玛依"}

SEARCHES = {
    "so2": "{province}地级市二氧化硫排放量",
    "gdp": "{province}地级市地区生产总值",
    "mining_emp": "{province}地级市采矿业就业人员数",
    "urban_unit_emp": "{province}地级市城镇单位就业人员数",
}


def parse_cli(stdout: str) -> list[dict]:
    outer = json.loads(stdout)
    text = next(item["text"] for item in outer["content"] if item["type"] == "text")
    inner = json.loads(text)
    payload = inner["data"]
    if payload["code"] != 0:
        raise RuntimeError(payload)
    return payload.get("data") or []


def wind_call(params: dict, cache_name: str) -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE / f"{cache_name}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    command = [
        "node",
        "scripts/cli.mjs",
        "call",
        "economic_data",
        "natural_language_get_edb_data",
        json.dumps(params, ensure_ascii=False),
    ]
    completed = subprocess.run(
        command,
        cwd=WIND_SKILL,
        check=True,
        capture_output=True,
        text=True,
        timeout=90,
    )
    data = parse_cli(completed.stdout)
    cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    time.sleep(0.2)
    return data


def city_from_name(name: str, candidates: list[str]) -> str | None:
    normalized = name.replace("市:", ":").replace("自治州", "州")
    for city in sorted(candidates, key=len, reverse=True):
        if f":{city}:" in f":{normalized}:" or f":{city}市:" in f":{name}:":
            return city
    return None


def acceptable(metric: str, name: str) -> bool:
    if metric == "so2":
        return "二氧化硫排放量" in name and "工业" not in name
    if metric == "gdp":
        return ("地区生产总值" in name or name.endswith(":GDP")) and all(
            token not in name for token in ["人均", "指数", "增速", "占比"]
        )
    if metric == "mining_emp":
        return "采矿业" in name and "就业人员" in name
    if metric == "urban_unit_emp":
        return "城镇单位" in name and "就业人员" in name and "采矿业" not in name
    return False


def collect_metadata() -> pd.DataFrame:
    records: list[dict] = []
    for province, cities in PROVINCE_CITIES.items():
        for metric, template in SEARCHES.items():
            items = wind_call(
                {
                    "executionMode": "search",
                    "question": template.format(province=province),
                    "observation": "200",
                },
                f"search_{province}_{metric}",
            )
            for item in items:
                meta = item.get("meta", {})
                name = meta.get("name", "")
                city = city_from_name(name, cities)
                if city and acceptable(metric, name):
                    records.append(
                        {
                            "province": province,
                            "city": city,
                            "metric": metric,
                            "code": meta.get("code"),
                            "name": name,
                            "source": meta.get("source"),
                            "unit": meta.get("unit"),
                            "update_date": meta.get("updateDate"),
                        }
                    )
    metadata = pd.DataFrame(records).drop_duplicates(["province", "city", "metric", "code"])
    if metadata.empty:
        raise RuntimeError("Wind searches returned no usable city metadata")
    return metadata


def fetch_series(metadata: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    fetched: list[dict] = []
    coverage: list[dict] = []
    for metric, group in metadata.groupby("metric"):
        codes = group["code"].dropna().drop_duplicates().tolist()
        for batch_index in range(0, len(codes), 20):
            batch = codes[batch_index : batch_index + 20]
            items = wind_call(
                {
                    "executionMode": "fetch",
                    "question": ",".join(batch),
                    "beginDate": "20050101",
                    "endDate": "20221231",
                },
                f"fetch_{metric}_{batch_index // 20:02d}",
            )
            for item in items:
                meta = item.get("meta", {})
                code = meta.get("code")
                row = metadata.loc[metadata["code"].eq(code)].iloc[0]
                dates = item.get("date") or []
                values = item.get("value") or []
                valid_years: list[int] = []
                for date, value in zip(dates, values):
                    if value is None:
                        continue
                    year = int(str(date)[:4])
                    valid_years.append(year)
                    fetched.append(
                        {
                            **row.to_dict(),
                            "year": year,
                            "value": float(value),
                        }
                    )
                coverage.append(
                    {
                        **row.to_dict(),
                        "n_years": len(valid_years),
                        "first_year": min(valid_years) if valid_years else np.nan,
                        "last_year": max(valid_years) if valid_years else np.nan,
                    }
                )
    return pd.DataFrame(fetched), pd.DataFrame(coverage)


def choose_series(long: pd.DataFrame, coverage: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected = (
        coverage.sort_values(
            ["province", "city", "metric", "n_years", "last_year"],
            ascending=[True, True, True, False, False],
        )
        .drop_duplicates(["province", "city", "metric"])
        .copy()
    )
    chosen_codes = set(selected["code"])
    chosen = long.loc[long["code"].isin(chosen_codes)].copy()
    return chosen, selected


def unit_multiplier(metric: str, unit: str) -> float:
    unit = str(unit)
    if metric == "so2":
        return 10000.0 if "万吨" in unit else 1.0
    if metric == "gdp":
        return 0.0001 if unit == "万元" else 1.0
    if metric in {"mining_emp", "urban_unit_emp"}:
        if unit == "人":
            return 0.0001
        if unit == "千人":
            return 0.1
    return 1.0


def build_panel(chosen: pd.DataFrame) -> pd.DataFrame:
    chosen["normalized_value"] = chosen.apply(
        lambda row: row["value"] * unit_multiplier(row["metric"], row["unit"]), axis=1
    )
    wide = chosen.pivot_table(
        index=["province", "city", "year"],
        columns="metric",
        values="normalized_value",
        aggfunc="first",
    ).reset_index()
    skeleton = pd.MultiIndex.from_product(
        [
            [(province, city) for province, cities in PROVINCE_CITIES.items() for city in cities],
            range(2005, 2023),
        ],
        names=["province_city", "year"],
    ).to_frame(index=False)
    skeleton[["province", "city"]] = pd.DataFrame(
        skeleton.pop("province_city").tolist(), index=skeleton.index
    )
    panel = skeleton.merge(wide, on=["province", "city", "year"], how="left")
    panel["pilot_city"] = panel["city"].isin(PILOT_CITIES).astype(int)
    panel["post2017"] = (panel["year"] >= 2017).astype(int)
    panel["pilot_post2017"] = panel["pilot_city"] * panel["post2017"]

    base = panel.loc[panel["year"].eq(2016), ["province", "city", "mining_emp", "urban_unit_emp"]].copy()
    base["resource_share_2016"] = base["mining_emp"] / base["urban_unit_emp"]
    base["resource_share_2016"] = base["resource_share_2016"].replace([np.inf, -np.inf], np.nan)
    mean = base["resource_share_2016"].mean()
    std = base["resource_share_2016"].std(ddof=1)
    base["resource_share_2016_z"] = (base["resource_share_2016"] - mean) / std
    panel = panel.merge(
        base[["province", "city", "resource_share_2016", "resource_share_2016_z"]],
        on=["province", "city"],
        how="left",
    )
    panel["post_resource"] = panel["post2017"] * panel["resource_share_2016_z"]
    panel["pilot_resource"] = panel["pilot_city"] * panel["resource_share_2016_z"]
    panel["pilot_post_resource"] = panel["pilot_post2017"] * panel["resource_share_2016_z"]
    panel["ln_so2"] = np.log1p(panel["so2"])
    panel["ln_gdp"] = np.log(panel["gdp"].where(panel["gdp"] > 0))
    panel["so2_per_gdp"] = panel["so2"] / panel["gdp"]
    panel["ln_so2_per_gdp"] = np.log1p(panel["so2_per_gdp"])
    panel["city_id"] = pd.factorize(panel["province"] + "_" + panel["city"])[0] + 1
    panel["province_id"] = pd.factorize(panel["province"])[0] + 1
    panel["province_year_id"] = pd.factorize(panel["province"] + "_" + panel["year"].astype(str))[0] + 1
    return panel.sort_values(["province", "city", "year"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    metadata = collect_metadata()
    long, coverage = fetch_series(metadata)
    chosen, selected = choose_series(long, coverage)
    panel = build_panel(chosen)

    metadata.to_csv(OUT / "wind_city_indicator_candidates.csv", index=False, encoding="utf-8-sig")
    selected.to_csv(OUT / "wind_city_indicator_selected.csv", index=False, encoding="utf-8-sig")
    chosen.to_csv(OUT / "wind_city_indicator_long.csv", index=False, encoding="utf-8-sig")
    panel.to_csv(OUT / "green_finance_pilot_city_panel_2005_2022.csv", index=False, encoding="utf-8-sig")
    panel.to_stata(
        OUT / "green_finance_pilot_city_panel_2005_2022.dta",
        write_index=False,
        version=118,
    )
    available = panel.groupby("city")[["so2", "gdp", "resource_share_2016"]].count()
    print(f"panel_rows={len(panel)}, cities={panel['city'].nunique()}")
    print("treated coverage:")
    print(available.loc[available.index.intersection(sorted(PILOT_CITIES))].to_string())


if __name__ == "__main__":
    main()
