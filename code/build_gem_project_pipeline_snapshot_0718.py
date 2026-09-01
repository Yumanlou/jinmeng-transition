#!/usr/bin/env python3
"""Build a province-level 2026 coal, wind, and solar project-pipeline snapshot.

These are post-sample status snapshots from GEM summary tables. They are kept
separate from the 2000-2023 causal panel to avoid post-treatment leakage.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "gem_project_pipeline_2026"

PROVINCE_MAP = {"Inner Mongolia": "Neimenggu", "Tibet": "Xizang"}

COAL = """province,announced,prepermit,permitted,construction,shelved,cancelled,operating,mothballed,retired
Anhui,12640,4000,3320,10620,12200,16280,58725,0,5075
Beijing,0,0,0,0,0,0,0,770,2025
Chongqing,3550,2000,0,4100,0,4770,14854,0,1430
Fujian,2700,1320,3710,2790,100,9270,33701,700,1590
Gansu,5438,2000,6120,6370,4700,30790,31980,0,1369
Guangdong,19640,0,2860,19872,11200,24920,76709,335,10322
Guangxi,1420,35,1470,2640,5240,7910,29328,0,1444
Guizhou,5980,2070,5500,5420,9000,40430,37420,0,4223
Hainan,0,0,0,0,0,2020,3060,0,652
Hebei,5690,1320,3060,10390,450,10320,49669,1325,6905
Heilongjiang,2000,0,2680,3300,480,10220,19591,0,2795
Henan,3000,880,5470,6000,2060,21190,66710,740,14085
Hubei,10000,1420,245,9670,2060,11890,37773,0,2130
Hunan,3700,2000,700,6320,5920,5422,27565,0,2440
Inner Mongolia,22190,1120,1890,20720,4320,121680,121402,0,2400
Jiangsu,8640,1320,2794,13474,0,16020,88624,0,12180
Jiangxi,6000,2000,0,9000,0,8680,32359,0,3105
Jilin,5300,0,2640,2020,1664,5740,16211,0,2850
Liaoning,2080,0,2250,2140,1300,14520,33565,0,6291
Ningxia,0,0,0,8660,0,12370,31000,0,1080
Qinghai,0,2640,3960,1980,1320,6465,4480,0,725
Shaanxi,4310,3320,8640,10660,13420,39010,56840,0,2930
Shandong,9670,6630,6820,9310,1320,30470,105690,300,22306
Shanghai,2000,0,2000,3580,1200,0,15500,0,1263
Shanxi,2000,4700,10640,5130,12100,37200,75122,100,7096
Sichuan,5320,2000,2000,4000,0,9200,13155,0,4184
Tianjin,0,0,0,1320,0,4250,12244,0,2160
Xinjiang,10880,2960,1810,19735,6058,57900,78980,0,4250
Yunnan,4060,0,3400,0,700,3300,11900,0,2235
Zhejiang,7320,30,1000,7140,0,9000,54865,0,3431
"""

WIND = """province,operating,construction,preconstruction,announced,cancelled,shelved,retired,mothballed
Anhui,8571,1356,7386,2780,719,496,0,0
Beijing,236,0,0,0,0,0,0,0
Hunan,12493,4386,11356,762,629,3257,0,160
Chongqing,2171,1807,3694,110,0,0,0,0
Shanxi,25736,3254,14975,3598,844,490,0,0
Fujian,7881,2970,9126,900,0,301,0,0
Gansu,36508,14760,24662,11685,0,350,0,0
Guangdong,17385,9223,25452,7825,998,8683,17,0
Guangxi,17827,9517,35896,6048,356,7312,0,0
Guizhou,8713,6997,24676,9759,2856,924,14,0
Hainan,3218,3404,2100,900,0,0,50,0
Hebei,31899,9165,24325,4575,0,1119,0,250
Henan,22205,3364,7933,3354,200,2462,0,0
Shaanxi,14366,2980,13251,1710,750,800,0,0
Heilongjiang,13890,6760,8130,750,0,100,0,0
Hubei,8924,1495,2592,5866,1757,271,0,0
Inner Mongolia,96817,37549,62585,59116,400,4250,0,0
Jiangsu,22230,2624,872,0,0,476,201,0
Jiangxi,6211,1060,2665,1936,143,112,0,0
Jilin,13720,3271,5905,350,0,348,0,0
Shandong,26825,5779,2541,0,0,468,0,0
Liaoning,16298,8244,4798,1231,0,299,50,0
Ningxia,15081,4904,8070,663,10,60,665,0
Qinghai,11470,9760,8000,2150,88,520,0,0
Shanghai,1257,368,828,0,0,0,0,0
Sichuan,7336,2281,1133,0,0,155,0,0
Tianjin,1796,2170,3959,2273,0,263,0,0
Tibet,662,600,800,840,0,0,0,0
Xinjiang,67723,48180,38348,32400,0,0,158,0
Yunnan,17229,975,4298,2691,0,380,0,0
Zhejiang,6083,3586,6176,0,0,0,0,0
"""

SOLAR = """province,operating,construction,preconstruction,announced,shelved,mothballed,retired,cancelled
Anhui,13990,1561,10462,2574,933,0,52,841
Beijing,244,0,18,0,0,0,0,0
Chongqing,1344,2279,2995,1136,413,0,0,0
Fujian,2129,2260,5378,1546,652,0,0,0
Gansu,31734,11092,16821,11640,349,0,0,50
Guangdong,17451,8060,11777,3370,4770,89,0,1286
Guangxi,12380,8868,15167,11429,1275,0,0,764
Guizhou,23731,7259,5959,5503,4471,0,0,1540
Hainan,3431,646,482,0,84,0,0,0
Hebei,26281,10968,27622,2382,3157,0,0,2613
Heilongjiang,5107,376,1565,0,0,0,0,0
Henan,5748,446,647,775,1852,0,0,257
Hubei,21292,1893,2815,4273,340,0,0,1229
Hunan,6766,7903,7474,3969,2680,0,0,262
Inner Mongolia,48794,17247,30205,46738,2961,0,0,459
Jiangsu,14061,4690,11324,25089,239,0,0,0
Jiangxi,13970,2847,2490,627,1173,0,0,314
Jilin,3854,485,413,0,0,0,0,0
Liaoning,4082,392,2201,1157,257,0,0,0
Ningxia,35723,6583,20750,16028,202,0,0,0
Qinghai,36720,19067,16582,7922,1173,0,0,0
Shaanxi,23655,4075,4023,904,1201,0,0,496
Shandong,29596,18966,24677,1764,1395,0,28,18
Shanghai,624,368,1225,0,0,0,0,13
Shanxi,24691,6738,11177,540,688,0,0,1159
Sichuan,13403,7766,9025,2518,0,0,0,0
Tianjin,4550,980,5329,1477,363,0,0,0
Tibet,4512,5565,2326,349,0,0,0,0
Xinjiang,87921,63847,39003,56883,300,0,0,0
Yunnan,45636,11173,16516,9920,432,0,0,0
Zhejiang,10650,1283,2109,2756,178,0,0,0
"""

EXPECTED_TOTALS = {
    "coal": {"operating": 1239022, "construction": 206361, "cancelled": 571237},
    "wind": {"operating": 542758, "construction": 212786, "cancelled": 9750},
    "solar": {"operating": 574071, "construction": 235683, "cancelled": 11302},
}


def read_source(text: str, prefix: str) -> pd.DataFrame:
    frame = pd.read_csv(StringIO(text))
    frame["province"] = frame["province"].replace(PROVINCE_MAP)
    frame = frame.rename(columns={column: f"{prefix}_{column}_mw" for column in frame.columns if column != "province"})
    return frame


def validate(frame: pd.DataFrame, prefix: str) -> None:
    if frame["province"].duplicated().any():
        raise ValueError(f"Duplicate provinces in {prefix}")
    for variable, expected in EXPECTED_TOTALS[prefix].items():
        actual = int(frame[f"{prefix}_{variable}_mw"].sum())
        # Province cells are displayed as whole MW, while source totals can be
        # calculated from underlying unrounded phase capacities.
        if abs(actual - expected) > 5:
            raise ValueError(f"{prefix} {variable}: expected {expected}, got {actual}")


def main() -> None:
    coal = read_source(COAL, "coal")
    # Tibet is absent from the coal summary table because no tracked coal unit is present.
    coal = pd.concat([
        coal,
        pd.DataFrame([{column: 0 if column != "province" else "Xizang" for column in coal.columns}]),
    ], ignore_index=True)
    wind = read_source(WIND, "wind")
    solar = read_source(SOLAR, "solar")
    validate(coal, "coal")
    validate(wind, "wind")
    validate(solar, "solar")

    panel = coal.merge(wind, on="province", how="outer", validate="one_to_one")
    panel = panel.merge(solar, on="province", how="outer", validate="one_to_one")
    if len(panel) != 31 or panel["province"].nunique() != 31 or panel.isna().any().any():
        raise ValueError("GEM snapshot must contain a complete 31-province cross-section")

    panel["coal_development_mw"] = (
        panel["coal_announced_mw"] + panel["coal_prepermit_mw"]
        + panel["coal_permitted_mw"] + panel["coal_construction_mw"]
    )
    panel["wind_development_mw"] = (
        panel["wind_announced_mw"] + panel["wind_preconstruction_mw"]
        + panel["wind_construction_mw"]
    )
    panel["solar_development_mw"] = (
        panel["solar_announced_mw"] + panel["solar_preconstruction_mw"]
        + panel["solar_construction_mw"]
    )
    panel["windsolar_operating_mw"] = panel["wind_operating_mw"] + panel["solar_operating_mw"]
    panel["windsolar_development_mw"] = panel["wind_development_mw"] + panel["solar_development_mw"]
    denominator = panel["windsolar_development_mw"] + panel["coal_development_mw"]
    panel["clean_share_of_power_pipeline"] = panel["windsolar_development_mw"] / denominator.replace(0, pd.NA)
    panel["coal_development_to_operating"] = panel["coal_development_mw"] / panel["coal_operating_mw"].replace(0, pd.NA)
    panel["windsolar_development_to_operating"] = (
        panel["windsolar_development_mw"] / panel["windsolar_operating_mw"].replace(0, pd.NA)
    )
    panel["snapshot_date"] = "2026-02"
    panel["coal_release"] = "Global Coal Plant Tracker, January 2026"
    panel["wind_release"] = "Global Wind Power Tracker, February 2026"
    panel["solar_release"] = "Global Solar Power Tracker, February 2026"
    panel["usage_note"] = "Post-sample descriptive pipeline snapshot; do not use as a pre-treatment regressor"
    panel = panel.sort_values("province").reset_index(drop=True)

    coverage = pd.DataFrame([
        {"technology": "coal", "release": panel["coal_release"].iloc[0], "provinces": 31, "scope": "Coal units >=30 MW; Xizang absent and coded zero; province cells rounded to whole MW"},
        {"technology": "wind", "release": panel["wind_release"].iloc[0], "provinces": 31, "scope": "Utility-scale wind phases >=10 MW; province cells rounded to whole MW"},
        {"technology": "solar", "release": panel["solar_release"].iloc[0], "provinces": 31, "scope": "Utility-scale solar phases >=1 MWac; province cells rounded to whole MWac"},
    ])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel_path = OUT_DIR / "gem_power_project_pipeline_province_2026.csv"
    coverage_path = OUT_DIR / "gem_power_project_pipeline_coverage.csv"
    panel.to_csv(panel_path, index=False, encoding="utf-8-sig")
    coverage.to_csv(coverage_path, index=False, encoding="utf-8-sig")
    print(f"panel={panel_path} rows={len(panel)} columns={len(panel.columns)}")
    print(f"coverage={coverage_path}")
    print(panel.loc[panel.province.isin(["Shanxi", "Neimenggu"]), [
        "province", "coal_operating_mw", "coal_development_mw",
        "windsolar_operating_mw", "windsolar_development_mw",
        "clean_share_of_power_pipeline",
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
