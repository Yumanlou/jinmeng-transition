#!/usr/bin/env python3
"""Build province-year top-leadership turnover indicators from the CGOD archive."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "provincial_leadership"
SOURCE_FILE = DATA_DIR / "source" / "cgod_v6" / "province_basic_info.csv"
BASE_PANEL = ROOT / "data" / (
    "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_"
    "tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_0721.csv"
)
OUTPUT_PANEL = ROOT / "data" / (
    "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_"
    "tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_leadership_0721.csv"
)

PROVINCE_MAP = {
    "北京市": "Beijing",
    "天津市": "Tianjin",
    "河北省": "Hebei",
    "山西省": "Shanxi",
    "内蒙古自治区": "Neimenggu",
    "辽宁省": "Liaoning",
    "吉林省": "Jilin",
    "黑龙江省": "Heilongjiang",
    "上海市": "Shanghai",
    "江苏省": "Jiangsu",
    "浙江省": "Zhejiang",
    "安徽省": "Anhui",
    "福建省": "Fujian",
    "江西省": "Jiangxi",
    "山东省": "Shandong",
    "河南省": "Henan",
    "湖北省": "Hubei",
    "湖南省": "Hunan",
    "广东省": "Guangdong",
    "广西壮族自治区": "Guangxi",
    "海南省": "Hainan",
    "重庆市": "Chongqing",
    "四川省": "Sichuan",
    "贵州省": "Guizhou",
    "云南省": "Yunnan",
    "西藏自治区": "Xizang",
    "陕西省": "Shaanxi",
    "甘肃省": "Gansu",
    "青海省": "Qinghai",
    "宁夏回族自治区": "Ningxia",
    "新疆维吾尔自治区": "Xinjiang",
}

PARTY_TITLES = {"省委书记", "市委书记", "自治区党委书记"}
GOVERNMENT_TITLES = {"省长", "市长", "自治区主席"}


def start_year(term: object) -> float:
    match = re.match(r"\s*(\d{4})", str(term))
    return float(match.group(1)) if match else np.nan


def build_spells() -> pd.DataFrame:
    raw = pd.read_csv(SOURCE_FILE, encoding="gb18030", dtype=str).iloc[1:].copy()
    raw = raw.loc[raw["Pst"].isin(PARTY_TITLES | GOVERNMENT_TITLES)].copy()
    raw["province"] = raw["Prvn"].map(PROVINCE_MAP)
    raw["role"] = np.where(raw["Pst"].isin(PARTY_TITLES), "party", "government")
    raw["start_year"] = raw["Term"].map(start_year)
    raw = raw.dropna(subset=["province", "Name", "start_year"])
    raw["start_year"] = raw["start_year"].astype(int)

    # Acting and formal appointments of the same person are one leadership spell.
    spells = (
        raw.groupby(["province", "role", "Name"], as_index=False)
        .agg(start_year=("start_year", "min"), source_terms=("Term", lambda x: " | ".join(x)))
        .sort_values(["province", "role", "start_year", "Name"])
    )
    return spells


def years_since_turnover(flags: pd.Series, years: pd.Series) -> pd.Series:
    last_year = np.nan
    values: list[float] = []
    for flag, year in zip(flags, years):
        if flag == 1:
            last_year = year
        values.append(year - last_year if pd.notna(last_year) else np.nan)
    return pd.Series(values, index=flags.index)


def build_panel(spells: pd.DataFrame) -> pd.DataFrame:
    provinces = sorted(PROVINCE_MAP.values())
    panel = pd.MultiIndex.from_product(
        [provinces, range(2000, 2024)], names=["province", "year"]
    ).to_frame(index=False)

    starts = (
        spells.loc[spells["start_year"].between(2000, 2018)]
        .groupby(["province", "start_year", "role"], as_index=False)
        .agg(new_leader_count=("Name", "nunique"), new_leader_names=("Name", " / ".join))
        .rename(columns={"start_year": "year"})
    )
    count = starts.pivot(index=["province", "year"], columns="role", values="new_leader_count")
    count = count.rename(columns={"party": "party_turnover", "government": "government_turnover"})
    names = starts.pivot(index=["province", "year"], columns="role", values="new_leader_names")
    names = names.rename(
        columns={"party": "new_party_leader_names", "government": "new_government_leader_names"}
    )
    out = panel.merge(count.reset_index(), on=["province", "year"], how="left")
    out = out.merge(names.reset_index(), on=["province", "year"], how="left")

    # The archive was uploaded in 2020 but misses known 2019 changes in Shanxi
    # and Inner Mongolia. Cap usable coverage at 2018 instead of coding later
    # unknown years as no turnover.
    observed = out["year"].le(2018)
    for col in ["party_turnover", "government_turnover"]:
        out.loc[observed, col] = out.loc[observed, col].fillna(0).gt(0).astype(int)
        out.loc[~observed, col] = np.nan
    out["any_top_leader_turnover"] = out[["party_turnover", "government_turnover"]].max(axis=1)
    out["joint_top_leader_turnover"] = np.where(
        observed,
        ((out["party_turnover"] == 1) & (out["government_turnover"] == 1)).astype(float),
        np.nan,
    )
    out["leadership_data_observed"] = observed.astype(int)

    out = out.sort_values(["province", "year"])
    out["years_since_party_turnover"] = out.groupby("province", group_keys=False).apply(
        lambda g: years_since_turnover(g["party_turnover"], g["year"]),
        include_groups=False,
    ).reset_index(level=0, drop=True)
    out["years_since_government_turnover"] = out.groupby("province", group_keys=False).apply(
        lambda g: years_since_turnover(g["government_turnover"], g["year"]),
        include_groups=False,
    ).reset_index(level=0, drop=True)
    out.loc[~observed, ["years_since_party_turnover", "years_since_government_turnover"]] = np.nan
    return out


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    spells = build_spells()
    leadership = build_panel(spells)

    spells.to_csv(DATA_DIR / "provincial_top_leader_spells_cgod.csv", index=False, encoding="utf-8-sig")
    leadership.to_csv(
        DATA_DIR / "provincial_leadership_turnover_2000_2018.csv",
        index=False,
        encoding="utf-8-sig",
    )

    panel = pd.read_csv(BASE_PANEL, low_memory=False)
    merged = panel.merge(leadership, on=["province", "year"], how="left", validate="one_to_one")
    if len(merged) != len(panel) or merged.duplicated(["province", "year"]).any():
        raise ValueError("Panel key integrity check failed after leadership merge")
    merged.to_csv(OUTPUT_PANEL, index=False, encoding="utf-8-sig")

    metadata = {
        "source": "China Local Government Official Database (CGOD), Kaggle mirror",
        "source_url": "https://www.kaggle.com/datasets/bulter22/china-local-government-official-database",
        "license": "CC0: Public Domain",
        "source_last_updated": "2020-11-26",
        "retrieved": "2026-07-21",
        "coverage_used": "31 provinces, 2000-2018; 2019-2023 intentionally left missing",
        "construction": (
            "Turnover equals one in the first calendar year of a new provincial party secretary or "
            "governor/chair/mayor spell. Acting and formal appointments of the same person are combined."
        ),
        "interpretation": (
            "Use as descriptive or robustness evidence. Leadership replacement is not assumed exogenous, "
            "and the public archive misses known 2019 changes despite its 2020 upload date."
        ),
        "output_panel": str(OUTPUT_PANEL.relative_to(ROOT)),
    }
    (DATA_DIR / "source_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"spells={len(spells)} leadership_rows={len(leadership)}")
    print(f"panel={OUTPUT_PANEL.relative_to(ROOT)} shape={merged.shape}")


if __name__ == "__main__":
    main()
