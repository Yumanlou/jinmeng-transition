#!/usr/bin/env python3
"""Build province-level natural wind/solar endowments and clean-power proxies.

The natural endowment variables reproduce the provincial capacity-factor and
technical-potential measures reported by He and Kammen (2014, 2016). They are
based on 2001--2010 hourly resource data and therefore precede the 2012 Green
Credit Guidelines.

The clean-power variables use observed generation, capacity, additions, and
GDP already present in the project panel. They measure physical output,
revealed electricity specialization, and expansion intensity. They must not be
described as directly observed renewable-sector value added, employment, or
tax revenue.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT
    / "data"
    / "final_data.1.3.4_did_full_resource_v2_credit_greencredit_0716.csv"
)
DEFAULT_OUTPUT = (
    ROOT
    / "data"
    / "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_0718.csv"
)
MODULE_DIR = ROOT / "data" / "natural_endowment_clean_energy_0718"


# Average onshore wind capacity factor and lower-case technical potential.
# Source: He and Kammen (2014), Table 2. Inner Mongolia is reported as east
# and west subregions and is aggregated below using potential capacity weights.
WIND_RESOURCE = {
    "Anhui": (0.1050, 3.31, 3.04),
    "Beijing": (0.1044, 0.37, 0.34),
    "Chongqing": (0.1690, 1.46, 2.16),
    "East Neimenggu": (0.2178, 102.55, 195.67),
    "Fujian": (0.2562, 2.84, 6.37),
    "Gansu": (0.1168, 54.99, 56.27),
    "Guangdong": (0.1742, 6.88, 10.50),
    "Guangxi": (0.1629, 13.85, 19.76),
    "Guizhou": (0.1342, 8.87, 10.42),
    "Hainan": (0.1520, 2.28, 3.04),
    "Hebei": (0.2329, 5.78, 11.79),
    "Heilongjiang": (0.1797, 37.54, 59.10),
    "Henan": (0.0720, 2.22, 1.40),
    "Hubei": (0.1018, 4.98, 4.44),
    "Hunan": (0.1024, 10.12, 9.08),
    "Jiangsu": (0.1622, 0.44, 0.63),
    "Jiangxi": (0.0993, 8.67, 7.54),
    "Jilin": (0.1435, 13.29, 16.70),
    "Liaoning": (0.1362, 5.58, 6.66),
    "Ningxia": (0.0855, 6.42, 4.81),
    "Qinghai": (0.0852, 28.47, 21.24),
    "Shaanxi": (0.1177, 13.55, 13.97),
    "Shandong": (0.1551, 4.23, 5.75),
    "Shanghai": (0.2150, 0.01, 0.02),
    "Shanxi": (0.2149, 7.21, 13.57),
    "Sichuan": (0.0985, 2.06, 1.78),
    "Tianjin": (0.0964, 0.09, 0.08),
    "Xizang": (0.2912, 0.10, 0.26),
    "West Neimenggu": (0.2243, 189.00, 371.32),
    "Xinjiang": (0.1486, 285.14, 371.30),
    "Yunnan": (0.1574, 8.13, 11.21),
    "Zhejiang": (0.1607, 2.22, 3.12),
}


# Average stationary-solar capacity factor and lower-case technical potential.
# Source: He and Kammen (2016), Table 4. Inner Mongolia is aggregated below
# using potential capacity weights.
SOLAR_RESOURCE = {
    "Anhui": (0.1734, 8.0, 12.0),
    "Beijing": (0.1865, 4.0, 7.0),
    "Chongqing": (0.1514, 5.0, 6.0),
    "East Neimenggu": (0.1918, 540.0, 907.0),
    "Fujian": (0.1931, 32.0, 55.0),
    "Gansu": (0.2143, 287.0, 540.0),
    "Guangdong": (0.1920, 163.0, 274.0),
    "Guangxi": (0.1841, 199.0, 320.0),
    "Guizhou": (0.1862, 45.0, 73.0),
    "Hainan": (0.2160, 91.0, 172.0),
    "Hebei": (0.1877, 63.0, 104.0),
    "Heilongjiang": (0.1727, 183.0, 276.0),
    "Henan": (0.1732, 11.0, 16.0),
    "Hubei": (0.1682, 10.0, 15.0),
    "Hunan": (0.1642, 1.0, 2.0),
    "Jiangsu": (0.1730, 7.0, 11.0),
    "Jiangxi": (0.1754, 56.0, 86.0),
    "Jilin": (0.1784, 252.0, 393.0),
    "Liaoning": (0.1814, 59.0, 94.0),
    "Ningxia": (0.2140, 58.0, 108.0),
    "Qinghai": (0.2603, 30.0, 67.0),
    "Shaanxi": (0.1908, 91.0, 153.0),
    "Shandong": (0.1784, 113.0, 176.5),
    "Shanghai": (0.1682, 0.6, 0.9),
    "Shanxi": (0.1970, 51.0, 88.0),
    "Sichuan": (0.1924, 3.0, 6.0),
    "Tianjin": (0.1797, 3.0, 5.0),
    "Xizang": (0.3087, 1.0, 3.0),
    "West Neimenggu": (0.2144, 858.0, 1611.0),
    "Xinjiang": (0.1928, 1363.0, 2302.0),
    "Yunnan": (0.2394, 67.0, 140.0),
    "Zhejiang": (0.1764, 13.0, 21.0),
}


SOURCE_METADATA = {
    "wind": {
        "citation": (
            "He, G. and Kammen, D. M. (2014). Where, when and how much wind "
            "is available? A provincial-scale wind resource assessment for "
            "China. Energy Policy 74, 116-122."
        ),
        "doi": "10.1016/j.enpol.2014.07.003",
        "data_url": (
            "https://www.researchgate.net/publication/273258314_Where_when_and_"
            "how_much_wind_is_available_A_provincial-scale_wind_resource_"
            "assessment_for_China_Dataset"
        ),
        "table": "Table 2",
        "resource_period": "2001-2010",
    },
    "solar": {
        "citation": (
            "He, G. and Kammen, D. M. (2016). Where, when and how much solar "
            "is available? A provincial-scale solar resource assessment for "
            "China. Renewable Energy 85, 74-82."
        ),
        "doi": "10.1016/j.renene.2015.06.027",
        "data_url": (
            "https://www.researchgate.net/publication/278679097_Where_when_and_"
            "how_much_solar_is_available_A_provincial-scale_solar_resource_"
            "assessment_for_China_Dataset"
        ),
        "table": "Table 4",
        "resource_period": "2001-2010",
    },
}


CODEBOOK_ROWS = [
    ("wind_resource_cf_0110", "风能资源容量因子", "ratio", "2001-2010年省级陆上风电平均容量因子；先天资源质量"),
    ("wind_technical_capacity_gw_lower", "风电技术潜在装机", "GW", "文献下限情景；受省域面积影响，不作为主禀赋质量指标"),
    ("wind_technical_output_twh_lower", "风电技术潜在发电量", "TWh", "文献下限情景；受省域面积影响"),
    ("solar_resource_cf_0110", "太阳能资源容量因子", "ratio", "2001-2010年固定式光伏省级平均容量因子；先天资源质量"),
    ("solar_technical_capacity_gw_lower", "光伏技术潜在装机", "GW", "文献下限情景；受省域面积影响"),
    ("solar_technical_output_twh_lower", "光伏技术潜在发电量", "TWh", "文献下限情景；受省域面积影响"),
    ("wind_resource_cf_z", "标准化风能资源禀赋", "z-score", "风能容量因子跨省标准化"),
    ("solar_resource_cf_z", "标准化太阳能资源禀赋", "z-score", "太阳能容量因子跨省标准化"),
    ("natural_wind_solar_endowment", "风光自然禀赋指数", "z-score mean", "风能与太阳能容量因子z值均值；稳健性综合指标"),
    ("clean_generation_billion_kwh", "风光发电量", "billion kWh", "风电与光伏发电量合计；物理产出"),
    ("clean_generation_component_n", "风光发电分项覆盖数", "count", "风电、光伏两个分项中当年可用的数量"),
    ("clean_generation_share_recalc", "风光发电占比", "ratio", "风光发电量/总发电量"),
    ("clean_generation_lq", "清洁电力发电区位商", "ratio", "本省风光发电占比/全国风光发电占比；显性专业化"),
    ("clean_generation_kwh_per_cny_gdp", "清洁电力产出强度", "kWh/CNY GDP", "风光发电量/GDP；不是清洁能源增加值"),
    ("clean_capacity_10k_kw", "风光装机容量", "10,000 kW", "风电与光伏装机合计"),
    ("clean_capacity_component_n", "风光装机分项覆盖数", "count", "风电、光伏两个分项中当年可用的数量"),
    ("clean_capacity_share_recalc", "风光装机占比", "ratio", "风光装机/总装机"),
    ("clean_capacity_lq", "清洁电力装机区位商", "ratio", "本省风光装机占比/全国风光装机占比"),
    ("clean_capacity_addition_10k_kw", "风光新增装机", "10,000 kW", "风电与光伏装机存量差分合计；负差分按口径断点置缺失"),
    ("clean_capacity_addition_component_n", "新增装机分项覆盖数", "count", "风电、光伏两个存量差分中当年可用的数量"),
    ("clean_capacity_addition_per_gdp", "风光新增装机强度", "10,000 kW per 100m CNY GDP", "新增装机/GDP；不是货币投资额"),
    ("clean_capacity_addition_data_break_flag", "新增装机口径断点标记", "binary", "任一风电或光伏装机存量差分为负时取1"),
    ("pre_clean_generation_lq_0811", "政策前清洁电力专业化", "ratio", "2008-2011年清洁电力发电区位商均值；覆盖不足，仅用于缺口审计"),
    ("pre_clean_generation_lq_0811_n", "政策前专业化有效年份", "count", "2008-2011年清洁电力发电区位商有效年份数"),
    ("early_clean_generation_lq_1316", "早期清洁电力专业化", "ratio", "2013-2016年清洁电力发电区位商均值；属于政策后早期实现基础"),
    ("early_clean_generation_lq_1316_n", "早期专业化有效年份", "count", "2013-2016年清洁电力发电区位商有效年份数"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--module-dir", type=Path, default=MODULE_DIR)
    return parser.parse_args()


def standardize(series: pd.Series) -> pd.Series:
    sd = series.std(ddof=1)
    if not np.isfinite(sd) or sd == 0:
        return pd.Series(np.nan, index=series.index)
    return (series - series.mean()) / sd


def combine_neimenggu(resource: dict[str, tuple[float, float, float]]) -> dict[str, tuple[float, float, float]]:
    result = {
        province: values
        for province, values in resource.items()
        if province not in {"East Neimenggu", "West Neimenggu"}
    }
    east_cf, east_capacity, east_output = resource["East Neimenggu"]
    west_cf, west_capacity, west_output = resource["West Neimenggu"]
    total_capacity = east_capacity + west_capacity
    combined_cf = (
        east_cf * east_capacity + west_cf * west_capacity
    ) / total_capacity
    result["Neimenggu"] = (
        combined_cf,
        total_capacity,
        east_output + west_output,
    )
    return result


def build_endowment() -> pd.DataFrame:
    wind = combine_neimenggu(WIND_RESOURCE)
    solar = combine_neimenggu(SOLAR_RESOURCE)
    provinces = sorted(set(wind) | set(solar))
    rows = []
    for province in provinces:
        wind_cf, wind_capacity, wind_output = wind[province]
        solar_cf, solar_capacity, solar_output = solar[province]
        rows.append(
            {
                "province": province,
                "wind_resource_cf_0110": wind_cf,
                "wind_technical_capacity_gw_lower": wind_capacity,
                "wind_technical_output_twh_lower": wind_output,
                "solar_resource_cf_0110": solar_cf,
                "solar_technical_capacity_gw_lower": solar_capacity,
                "solar_technical_output_twh_lower": solar_output,
            }
        )
    frame = pd.DataFrame(rows)
    frame["wind_resource_cf_z"] = standardize(frame["wind_resource_cf_0110"])
    frame["solar_resource_cf_z"] = standardize(frame["solar_resource_cf_0110"])
    frame["natural_wind_solar_endowment"] = frame[
        ["wind_resource_cf_z", "solar_resource_cf_z"]
    ].mean(axis=1)
    frame["natural_endowment_source_period"] = "2001-2010"
    frame["natural_endowment_source"] = "He and Kammen (2014, 2016)"
    return frame


def numeric(panel: pd.DataFrame, variable: str) -> pd.Series:
    if variable not in panel:
        return pd.Series(np.nan, index=panel.index, dtype="float64")
    return pd.to_numeric(panel[variable], errors="coerce")


def first_available(panel: pd.DataFrame, variables: list[str]) -> pd.Series:
    result = pd.Series(np.nan, index=panel.index, dtype="float64")
    for variable in variables:
        values = numeric(panel, variable)
        result = result.fillna(values)
    return result


def sum_with_component_count(components: list[pd.Series]) -> tuple[pd.Series, pd.Series]:
    matrix = pd.concat(components, axis=1)
    count = matrix.notna().sum(axis=1)
    total = matrix.sum(axis=1, min_count=1)
    return total, count


def add_clean_power_proxies(panel: pd.DataFrame) -> pd.DataFrame:
    wind_gen = first_available(panel, ["gen_wind", "wind_generation_billion_kwh"])
    solar_gen = first_available(panel, ["gen_solar", "solar_generation_billion_kwh"])
    total_gen = first_available(panel, ["gen_total", "total_generation_billion_kwh"])
    wind_cap = first_available(panel, ["cap_wind", "wind_capacity_10k_kw"])
    solar_cap = first_available(panel, ["cap_solar", "solar_capacity_10k_kw"])
    total_cap = first_available(panel, ["cap_total", "total_capacity_10k_kw"])
    # Use changes in the capacity stock consistently. The separately reported
    # wind-addition series changes statistical scope in several years and is
    # not comparable with the solar stock-difference series.
    wind_add_raw = numeric(panel, "wind_capacity_addition_from_stock_10k_kw")
    solar_add_raw = numeric(panel, "solar_capacity_addition_from_stock_10k_kw")
    panel["clean_capacity_addition_data_break_flag"] = (
        (wind_add_raw < 0) | (solar_add_raw < 0)
    ).astype("int8")
    wind_add = wind_add_raw.where(wind_add_raw >= 0)
    solar_add = solar_add_raw.where(solar_add_raw >= 0)
    gdp = numeric(panel, "gdp")

    panel["clean_generation_billion_kwh"], panel["clean_generation_component_n"] = (
        sum_with_component_count([wind_gen, solar_gen])
    )
    panel["clean_generation_share_recalc"] = (
        panel["clean_generation_billion_kwh"] / total_gen.where(total_gen > 0)
    )
    panel["clean_generation_kwh_per_cny_gdp"] = (
        10.0 * panel["clean_generation_billion_kwh"] / gdp.where(gdp > 0)
    )

    panel["clean_capacity_10k_kw"], panel["clean_capacity_component_n"] = (
        sum_with_component_count([wind_cap, solar_cap])
    )
    panel["clean_capacity_share_recalc"] = (
        panel["clean_capacity_10k_kw"] / total_cap.where(total_cap > 0)
    )
    panel["clean_capacity_addition_10k_kw"], panel["clean_capacity_addition_component_n"] = (
        sum_with_component_count([wind_add, solar_add])
    )
    panel.loc[
        panel["clean_capacity_addition_data_break_flag"].eq(1),
        "clean_capacity_addition_10k_kw",
    ] = np.nan
    panel["clean_capacity_addition_per_gdp"] = (
        panel["clean_capacity_addition_10k_kw"] / gdp.where(gdp > 0)
    )

    national_generation = panel.groupby("year", dropna=False).apply(
        lambda group: group["clean_generation_billion_kwh"].sum(min_count=1)
        / total_gen.loc[group.index].sum(min_count=1),
        include_groups=False,
    )
    national_capacity = panel.groupby("year", dropna=False).apply(
        lambda group: group["clean_capacity_10k_kw"].sum(min_count=1)
        / total_cap.loc[group.index].sum(min_count=1),
        include_groups=False,
    )
    panel["national_clean_generation_share"] = panel["year"].map(national_generation)
    panel["national_clean_capacity_share"] = panel["year"].map(national_capacity)
    panel["clean_generation_lq"] = (
        panel["clean_generation_share_recalc"]
        / panel["national_clean_generation_share"].where(
            panel["national_clean_generation_share"] > 0
        )
    )
    panel["clean_capacity_lq"] = (
        panel["clean_capacity_share_recalc"]
        / panel["national_clean_capacity_share"].where(
            panel["national_clean_capacity_share"] > 0
        )
    )

    pre = (
        panel.loc[
            panel["year"].between(2008, 2011),
            ["province", "clean_generation_lq"],
        ]
        .groupby("province", as_index=False)
        .agg(
            pre_clean_generation_lq_0811=("clean_generation_lq", "mean"),
            pre_clean_generation_lq_0811_n=("clean_generation_lq", "count"),
        )
    )
    panel = panel.merge(pre, on="province", how="left", validate="many_to_one")
    early = (
        panel.loc[
            panel["year"].between(2013, 2016),
            ["province", "clean_generation_lq"],
        ]
        .groupby("province", as_index=False)
        .agg(
            early_clean_generation_lq_1316=("clean_generation_lq", "mean"),
            early_clean_generation_lq_1316_n=("clean_generation_lq", "count"),
        )
    )
    panel = panel.merge(early, on="province", how="left", validate="many_to_one")
    return panel


def add_endowment_interactions(panel: pd.DataFrame) -> pd.DataFrame:
    post2012 = (numeric(panel, "year") >= 2012).astype("int8")
    coal_exposure = first_available(panel, ["coalexp_pre", "pre_coal_share_energy5_terminal_0811_approx"])
    panel["post2012_main"] = post2012
    for variable, short in [
        ("wind_resource_cf_z", "windendow"),
        ("solar_resource_cf_z", "solarendow"),
        ("natural_wind_solar_endowment", "naturalendow"),
    ]:
        panel[f"post2012_x_{short}"] = post2012 * panel[variable]
        panel[f"coalexp_x_{short}"] = coal_exposure * panel[variable]
        panel[f"post2012_x_coalexp_x_{short}"] = (
            post2012 * coal_exposure * panel[variable]
        )
    return panel


def build_coverage(panel: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    rows = []
    for variable in variables:
        valid = panel.loc[panel[variable].notna(), ["province", "year"]]
        rows.append(
            {
                "variable": variable,
                "nonmissing_observations": len(valid),
                "province_count": valid["province"].nunique(),
                "year_min": valid["year"].min() if len(valid) else np.nan,
                "year_max": valid["year"].max() if len(valid) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    args.module_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    panel = pd.read_csv(args.input, low_memory=False)
    panel["year"] = pd.to_numeric(panel["year"], errors="raise").astype(int)
    if panel.duplicated(["province", "year"]).any():
        raise ValueError("Input panel has duplicate province-year rows")

    endowment = build_endowment()
    panel_provinces = set(panel["province"].dropna().unique())
    endowment_provinces = set(endowment["province"])
    missing_endowment = sorted(panel_provinces - endowment_provinces)
    extra_endowment = sorted(endowment_provinces - panel_provinces)
    if missing_endowment or extra_endowment:
        raise ValueError(
            f"Province mismatch: missing={missing_endowment}, extra={extra_endowment}"
        )

    output = panel.merge(endowment, on="province", how="left", validate="many_to_one")
    output = add_clean_power_proxies(output)
    output = add_endowment_interactions(output)
    if len(output) != len(panel):
        raise ValueError("Merge changed the number of panel rows")

    module_variables = [row[0] for row in CODEBOOK_ROWS]
    coverage = build_coverage(output, module_variables)
    codebook = pd.DataFrame(
        CODEBOOK_ROWS,
        columns=["variable", "chinese_name", "unit", "definition_and_boundary"],
    )

    endowment.to_csv(
        args.module_dir / "natural_wind_solar_endowment_province.csv",
        index=False,
        encoding="utf-8-sig",
    )
    output[["province", "year", *module_variables]].to_csv(
        args.module_dir / "clean_energy_proxy_panel_2000_2023.csv",
        index=False,
        encoding="utf-8-sig",
    )
    coverage.to_csv(
        args.module_dir / "natural_clean_proxy_coverage.csv",
        index=False,
        encoding="utf-8-sig",
    )
    codebook.to_csv(
        args.module_dir / "natural_clean_proxy_codebook.csv",
        index=False,
        encoding="utf-8-sig",
    )
    correlation_variables = [
        "coalexp_pre",
        "wind_resource_cf_0110",
        "solar_resource_cf_0110",
        "natural_wind_solar_endowment",
        "pre_nontherm_cap",
        "early_wind_cap",
        "early_wind_gen",
        "resdep_pre",
    ]
    correlation_variables = [
        variable for variable in correlation_variables if variable in output.columns
    ]
    province_cross_section = (
        output.sort_values(["province", "year"])
        .drop_duplicates("province")
        .set_index("province")
    )
    province_cross_section[correlation_variables].corr(min_periods=10).to_csv(
        args.module_dir / "natural_endowment_correlations.csv",
        encoding="utf-8-sig",
    )
    (args.module_dir / "source_metadata.json").write_text(
        json.dumps(SOURCE_METADATA, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output.to_csv(args.output, index=False, encoding="utf-8-sig")

    print(f"input={args.input}")
    print(f"output={args.output}")
    print(
        f"rows={len(output)} provinces={output['province'].nunique()} "
        f"years={output['year'].min()}-{output['year'].max()} columns={len(output.columns)}"
    )
    print(f"module_dir={args.module_dir}")


if __name__ == "__main__":
    main()
