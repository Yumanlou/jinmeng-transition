#!/usr/bin/env python3
"""Build province-year coal-power additions from GEM's January 2026 summary table."""

from __future__ import annotations

import argparse
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd


YEARS = list(range(2000, 2026))

# Source: Global Energy Monitor, Global Coal Plant Tracker, January 2026.
# Public summary sheet: "Newly Operating Coal Plants in China by Year (MW)".
# Values are embedded so the build remains reproducible when Google Sheets export
# is unavailable. Row and annual totals below are checked against the source.
SOURCE_ROWS = """province,values,total
Anhui,"640 700 0 0 0 1810 2590 5195 8750 1260 660 2320 2620 3980 2640 5320 2660 1000 4340 230 100 0 2670 1390 1380 4300",56555
Beijing,"0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",0
Chongqing,"0 0 0 0 0 350 2200 900 590 0 0 0 150 1380 1760 2000 1860 660 105 350 49 0 820 660 120 80",14034
Fujian,"600 1386 600 600 600 570 3720 1250 1860 1560 1920 2170 1270 0 300 2150 0 3320 660 690 30 1130 1160 420 1265 3110",32341
Gansu,"330 330 0 910 300 675 770 2365 1200 1980 1860 1980 700 1030 330 1050 650 1000 0 700 2000 0 0 2000 0 8350",30510
Guangdong,"1625 835 498 1670 1705 2530 3525 3395 3425 4758 5298 7025 1260 6692 950 3650 1230 700 1350 2350 5780 2000 600 4020 0 8560",75431
Guangxi,"1004 0 0 0 1115 455 300 4290 845 310 150 1750 2750 0 360 850 4270 700 490 33 0 1050 2350 690 2450 3370",29582
Guizhou,"250 535 405 1800 1400 2200 4400 2400 600 2100 650 1250 1200 3400 1000 2020 3960 660 810 1510 700 0 0 300 2330 2330",38210
Hainan,"138 0 0 0 300 0 330 330 0 700 0 0 700 0 0 700 0 0 0 0 0 0 0 0 0 0",3198
Hebei,"786 1790 0 625 1325 3355 2750 3610 2370 5370 2150 1320 1560 1900 735 1300 1400 1530 1360 3860 2430 0 0 1478 350 1670",45024
Heilongjiang,"0 350 350 250 100 330 700 2100 2400 100 900 900 75 1350 450 700 350 1100 50 155 1306 320 100 0 0 0",14436
Henan,"0 1530 405 1545 4055 3725 6215 6885 5320 3755 4105 4690 4680 2690 660 5320 700 1660 2210 3990 2350 1350 50 600 630 700",69820
Hubei,"555 0 0 0 1380 120 3840 0 1280 2620 1010 0 2940 1000 2130 350 1000 765 1070 2470 1440 60 1320 4020 350 3000",32720
Hunan,"330 330 0 630 1280 360 2860 4330 750 1370 100 1260 1260 0 0 1320 1260 0 0 0 0 2100 1000 3060 0 3000",26600
Inner Mongolia,"400 200 660 2920 2360 5340 8185 10815 4800 2160 8130 3780 2800 4730 1110 5140 4950 5280 1010 6616 5866 4390 6000 12160 2320 3700",115822
Jiangsu,"1055 710 330 1670 4146 8336 9585 2940 1367 4120 8330 5120 4000 4370 2660 1350 2940 4040 1700 2360 0 130 145 2190 1100 10035",84729
Jiangxi,"640 300 350 450 175 300 610 2700 700 2350 1360 1340 1300 0 0 2320 1000 0 2104 0 1445 2000 3320 0 2000 5060",31824
Jilin,"875 375 240 331 0 440 660 1190 300 2950 2400 1740 700 350 1450 0 0 90 990 0 0 0 0 0 0 0",15081
Liaoning,"1810 200 300 110 200 835 485 3350 2580 1900 5140 1260 2880 0 700 50 0 1250 1800 400 1560 660 700 0 850 30",29050
Ningxia,"0 150 330 660 330 465 2225 1200 400 1200 4460 3620 0 660 0 350 1400 4060 1450 4860 1320 0 700 30 0 80",29950
Qinghai,"125 0 0 0 125 0 600 540 0 0 0 0 0 0 0 1010 1010 0 0 0 0 0 0 0 0 1320",4730
Shaanxi,"520 300 50 690 470 1990 1170 3490 5250 2520 1450 2045 225 2850 800 3200 1350 350 4410 5410 3590 0 900 5300 5960 700",54990
Shandong,"1805 1095 3851 4635 2065 1358 8660 5600 2925 4960 3465 3140 6275 5700 3400 12456 7490 5087 1180 4679 2680 940 4160 2060 3030 3820",106516
Shanghai,"0 0 1300 0 1800 0 0 0 2000 1920 2000 100 0 0 0 0 0 0 0 0 0 0 650 650 0 0",10420
Shanxi,"900 1100 1270 790 2500 5085 3680 5045 4370 4320 2985 5216 4451 1620 2220 3300 3420 350 1670 3310 2680 7030 2350 2370 0 1050",73082
Sichuan,"442 142 0 0 270 1300 2070 2970 900 0 0 1800 765 600 0 0 330 0 0 0 0 2000 0 0 0 0",13589
Tianjin,"0 0 0 0 0 2127 300 300 600 2660 900 0 250 0 700 0 0 0 2000 350 0 340 0 170 0 0",10697
Xinjiang,"175 400 150 770 50 50 1025 320 2030 720 1665 4950 5260 6025 11065 6755 5605 6400 2370 5630 5010 1010 1360 2990 3030 7120",81935
Yunnan,"600 0 0 900 435 300 2100 2100 1200 600 600 600 2100 0 0 0 0 0 0 0 0 0 0 0 0 700",12235
Zhejiang,"1800 660 135 730 1609 2630 6672 3000 4650 3155 2120 2680 0 0 5010 4010 0 216 57 45 1320 297 57 2070 3420 6057",52400
"""

EXPECTED_ANNUAL_TOTALS = [
    17405, 13418, 11224, 22686, 30095, 47036, 82227, 82610, 63462,
    61418, 63808, 62056, 52171, 50327, 40430, 66671, 48835, 40218,
    33186, 49998, 41656, 26807, 30412, 48628, 30585, 78142,
]

PROVINCE_MAP = {"Inner Mongolia": "Neimenggu", "Tibet": "Xizang"}


def standardize(series: pd.Series) -> pd.Series:
    return (series - series.mean()) / series.std(ddof=1)


def build_long_panel() -> pd.DataFrame:
    source = pd.read_csv(StringIO(SOURCE_ROWS))
    records: list[dict[str, int | str]] = []
    for row in source.itertuples(index=False):
        values = [int(value) for value in row.values.split()]
        if len(values) != len(YEARS):
            raise ValueError(f"{row.province}: expected {len(YEARS)} annual values, got {len(values)}")
        if sum(values) != int(row.total):
            raise ValueError(f"{row.province}: row total does not match source total")
        province = PROVINCE_MAP.get(row.province, row.province)
        records.extend(
            {"province": province, "year": year, "gem_coal_new_capacity_mw": value}
            for year, value in zip(YEARS, values)
        )

    panel = pd.DataFrame.from_records(records)
    annual = panel.groupby("year")["gem_coal_new_capacity_mw"].sum().reindex(YEARS)
    if annual.tolist() != EXPECTED_ANNUAL_TOTALS:
        mismatch = pd.DataFrame({"actual": annual, "expected": EXPECTED_ANNUAL_TOTALS})
        raise ValueError(f"Annual totals do not match source:\n{mismatch[mismatch.actual != mismatch.expected]}")

    # Tibet is absent from GEM's China summary table and is retained as an
    # explicit structural zero for the 30 MW-and-above coal-unit universe.
    tibet = pd.DataFrame(
        {"province": "Xizang", "year": YEARS, "gem_coal_new_capacity_mw": 0}
    )
    panel = pd.concat([panel, tibet], ignore_index=True)
    panel["gem_source_release"] = "Global Coal Plant Tracker, January 2026"
    panel["gem_source_table"] = "Newly Operating Coal Plants in China by Year (MW)"
    panel["gem_scope_flag"] = "Coal-fired generating units >=30 MW; Xizang absent in source and coded zero"
    return panel.sort_values(["province", "year"]).reset_index(drop=True)


def build_pre_summary(panel: pd.DataFrame) -> pd.DataFrame:
    wide = panel.pivot(index="province", columns="year", values="gem_coal_new_capacity_mw")
    summary = pd.DataFrame(index=wide.index)
    summary["gem_pre_coal_additions_0011_mw"] = wide.loc[:, 2000:2011].sum(axis=1)
    summary["gem_pre_coal_additions_0811_mw"] = wide.loc[:, 2008:2011].sum(axis=1)
    summary["gem_post_coal_additions_1223_mw"] = wide.loc[:, 2012:2023].sum(axis=1)
    summary["gem_pre_coal_additions_mean_0811_mw"] = wide.loc[:, 2008:2011].mean(axis=1)
    summary["gem_post_to_pre_coal_additions_ratio"] = (
        summary["gem_post_coal_additions_1223_mw"]
        / summary["gem_pre_coal_additions_0011_mw"].replace(0, pd.NA)
    )
    return summary.reset_index()


def merge_with_main(main: pd.DataFrame, annual: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    if main.duplicated(["province", "year"]).any():
        raise ValueError("Main panel has duplicate province-year keys")
    annual_0023 = annual.loc[annual["year"].between(2000, 2023)].copy()
    merged = main.merge(annual_0023, on=["province", "year"], how="left", validate="one_to_one")
    merged = merged.merge(summary, on="province", how="left", validate="many_to_one")
    if merged["gem_coal_new_capacity_mw"].isna().any():
        missing = merged.loc[merged["gem_coal_new_capacity_mw"].isna(), "province"].unique()
        raise ValueError(f"Unmatched GEM provinces: {missing.tolist()}")

    base2011 = merged.loc[merged["year"].eq(2011), [
        "province", "population", "thermal_capacity_10k_kw",
    ]].rename(columns={
        "population": "population_2011_10k_person",
        "thermal_capacity_10k_kw": "thermal_capacity_2011_10k_kw",
    })
    merged = merged.merge(base2011, on="province", how="left", validate="many_to_one")
    population_million = merged["population_2011_10k_person"] / 100.0
    thermal_capacity_mw = merged["thermal_capacity_2011_10k_kw"] * 10.0
    merged["gem_pre_coal_additions_0011_mw_per_million_pop"] = (
        merged["gem_pre_coal_additions_0011_mw"] / population_million
    )
    merged["gem_pre_coal_additions_0811_mw_per_million_pop"] = (
        merged["gem_pre_coal_additions_0811_mw"] / population_million
    )
    merged["gem_pre_recent_additions_to_thermal_capacity_2011"] = (
        merged["gem_pre_coal_additions_0811_mw"] / thermal_capacity_mw
    )

    pre = merged.loc[merged["year"].eq(2011), [
        "province", "gem_pre_coal_additions_0811_mw_per_million_pop",
        "gem_pre_recent_additions_to_thermal_capacity_2011",
    ]].copy()
    pre["coal_power_build_lockin_z"] = standardize(
        pre["gem_pre_coal_additions_0811_mw_per_million_pop"]
    )
    pre["coal_power_build_pc_log_z"] = standardize(
        np.log1p(pre["gem_pre_coal_additions_0811_mw_per_million_pop"])
    )
    pre["coal_power_recent_vintage_z"] = standardize(
        pre["gem_pre_recent_additions_to_thermal_capacity_2011"]
    )
    merged = merged.merge(
        pre[[
            "province", "coal_power_build_lockin_z", "coal_power_build_pc_log_z",
            "coal_power_recent_vintage_z",
        ]],
        on="province", how="left", validate="many_to_one",
    )
    for variable in [
        "coal_power_build_lockin_z", "coal_power_build_pc_log_z",
        "coal_power_recent_vintage_z",
    ]:
        merged[f"post_{variable}"] = merged["post2012"] * merged[variable]
        merged[f"coalexp_{variable}"] = merged["coalexp_pre"] * merged[variable]
        merged[f"ddd_{variable}"] = merged["coalexp_post"] * merged[variable]

    stata_aliases = {
        "raw": "coal_power_build_lockin_z",
        "log": "coal_power_build_pc_log_z",
        "vintage": "coal_power_recent_vintage_z",
    }
    for alias, variable in stata_aliases.items():
        merged[f"cpbuild_{alias}_z"] = merged[variable]
        merged[f"post_cpbuild_{alias}_z"] = merged["post2012"] * merged[variable]
        merged[f"coalexp_cpbuild_{alias}_z"] = merged["coalexp_pre"] * merged[variable]
        merged[f"ddd_cpbuild_{alias}_z"] = merged["coalexp_post"] * merged[variable]
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--main-panel", type=Path,
        default=Path("data/final_data.1.3.4_did_full_resource_0715.csv"),
    )
    parser.add_argument(
        "--annual-output", type=Path,
        default=Path("data/gem_coal_power_lockin/gem_china_coal_additions_2000_2025.csv"),
    )
    parser.add_argument(
        "--pre-output", type=Path,
        default=Path("data/gem_coal_power_lockin/gem_china_coal_additions_pre_policy.csv"),
    )
    parser.add_argument(
        "--merged-output", type=Path,
        default=Path("data/final_data.1.3.4_did_full_resource_coalpower_0716.csv"),
    )
    args = parser.parse_args()

    annual = build_long_panel()
    summary = build_pre_summary(annual)
    main_panel = pd.read_csv(args.main_panel, low_memory=False)
    merged = merge_with_main(main_panel, annual, summary)

    for path in [args.annual_output, args.pre_output, args.merged_output]:
        path.parent.mkdir(parents=True, exist_ok=True)
    annual.to_csv(args.annual_output, index=False, encoding="utf-8-sig")
    summary.to_csv(args.pre_output, index=False, encoding="utf-8-sig")
    merged.to_csv(args.merged_output, index=False, encoding="utf-8-sig")

    print(f"annual_output={args.annual_output} rows={len(annual)}")
    print(f"pre_output={args.pre_output} provinces={len(summary)}")
    print(f"merged_output={args.merged_output} rows={len(merged)} columns={len(merged.columns)}")
    print(
        summary.loc[summary["province"].isin(["Shanxi", "Neimenggu"]), [
            "province", "gem_pre_coal_additions_0011_mw",
            "gem_pre_coal_additions_0811_mw", "gem_post_coal_additions_1223_mw",
        ]].to_string(index=False)
    )


if __name__ == "__main__":
    main()
