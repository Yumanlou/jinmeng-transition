#!/usr/bin/env python3
"""Build category-level leave-one-out banking supply instruments.

The instrument combines each province's fixed 2011 banking structure with
annual growth in the same bank category among a balanced set of other
provinces. Shenzhen is merged into Guangdong before any aggregation.
"""

from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd


ROOT = Path(
    "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
)
SOURCE = Path(
    "/Users/yumanlou/Downloads/"
    "%E9%93%B6%E8%A1%8C%E4%B8%9A%E9%87%91%E8%9E%8D%E6%9C%BA%E6%9E%84%E5%88%86%E5%B8%83%E8%A1%A8"
    "(%E5%88%86%E7%9C%81%E4%BB%BD)(%E5%B9%B4)204628379"
    "(%E4%BB%85%E4%BE%9B%E5%93%88%E4%BD%9B%E5%A4%A7%E5%AD%A6%E4%BD%BF%E7%94%A8)/"
    "BFI_BFINSTPRVY.xlsx"
)
GREEN_CREDIT = ROOT / "data/green_credit/green_credit_province_2005_2022.csv"
OUT = ROOT / "data/green_credit_category_loo_iv"

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


def read_malformed_xlsx(path: Path) -> pd.DataFrame:
    """Read a workbook whose declared sheet dimension incorrectly says A:A."""
    sheet = openpyxl.load_workbook(path, read_only=True, data_only=True).active
    sheet.reset_dimensions()
    rows = list(sheet.iter_rows(values_only=True))
    return pd.DataFrame(rows[3:], columns=rows[0])


def classify_bank(agent_type: pd.Series) -> pd.Series:
    code = agent_type.astype(str)
    mapping = {
        "1": "policy",
        "2": "large",
        "3": "joint_stock",
        "4": "postal",
        "5": "city",
        "6": "city",
        "7": "rural",
        "701": "rural",
        "702": "rural",
        "703": "rural",
        "11": "rural",
        "1101": "rural",
        "1102": "rural",
        "10": "foreign",
    }
    return code.map(mapping)


def interpolate_explicit_missing(
    panel: pd.DataFrame, value: str, eligible: pd.Series
) -> pd.Series:
    """Interpolate reported-but-missing values; other missing cells remain missing."""
    observed = panel[value].copy()
    interpolated = (
        panel.assign(_value=observed)
        .groupby(["province_cn", "bank_category"], sort=False)["_value"]
        .transform(lambda x: x.interpolate(limit_direction="both"))
    )
    result = observed.copy()
    result.loc[eligible & result.isna()] = interpolated.loc[eligible & result.isna()]
    return result


def build_complete_category_panel(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    raw = raw.copy()
    raw["year"] = pd.to_numeric(raw["SgnYear"], errors="coerce")
    raw = raw.loc[raw["year"].between(2005, 2022)].copy()
    raw["province_cn"] = raw["AreaName"].replace({"深圳市": "广东省"})
    raw["bank_category"] = classify_bank(raw["AgentTypeID"])
    raw = raw.loc[raw["bank_category"].notna()].copy()
    raw["assets"] = pd.to_numeric(raw["SalesNetworkAssets"], errors="coerce")
    raw["outlets"] = pd.to_numeric(raw["SalesNetworkNumber"], errors="coerce")

    raw_presence = (
        raw[["province_cn", "year"]]
        .drop_duplicates()
        .groupby("province_cn")["year"]
        .nunique()
    )
    balanced_donors = sorted(raw_presence.loc[raw_presence.eq(18)].index)

    grouped = (
        raw.groupby(["province_cn", "year", "bank_category"], as_index=False)
        .agg(
            assets=("assets", lambda x: x.sum(min_count=1)),
            outlets=("outlets", lambda x: x.sum(min_count=1)),
            category_reported=("AgentTypeID", "size"),
        )
    )

    provinces = sorted(PROVINCE_MAP)
    years = range(2005, 2023)
    categories = ["policy", "large", "joint_stock", "postal", "city", "rural", "foreign"]
    complete = pd.MultiIndex.from_product(
        [provinces, years, categories],
        names=["province_cn", "year", "bank_category"],
    ).to_frame(index=False)
    existing_py = raw[["province_cn", "year"]].drop_duplicates().assign(province_year_present=1)
    complete = complete.merge(grouped, how="left")
    complete = complete.merge(existing_py, on=["province_cn", "year"], how="left")

    # A missing category in an otherwise reported province-year means no such
    # category was listed. Explicit missing cells are interpolated separately.
    structural = complete["province_year_present"].eq(1) & complete["category_reported"].isna()
    complete.loc[structural, "assets"] = 0.0
    complete.loc[structural, "outlets"] = 0.0
    reported = complete["category_reported"].notna()
    complete["assets"] = interpolate_explicit_missing(complete, "assets", reported)
    outlet_eligible = reported & complete["year"].ge(2007)
    complete["outlets"] = interpolate_explicit_missing(
        complete, "outlets", outlet_eligible
    )
    complete["province"] = complete["province_cn"].map(PROVINCE_MAP)
    return complete, balanced_donors


def fixed_weights(panel: pd.DataFrame, value: str) -> pd.DataFrame:
    base = panel.loc[panel["year"].eq(2011), ["province", "bank_category", value]].copy()
    denom = base.groupby("province")[value].transform("sum")
    base[f"weight_{value}_2011"] = np.where(denom.gt(0), base[value] / denom, np.nan)
    return base[["province", "bank_category", f"weight_{value}_2011"]]


def leave_one_out_shocks(
    panel: pd.DataFrame, balanced_donors: list[str], value: str
) -> pd.DataFrame:
    donor = panel.loc[panel["province_cn"].isin(balanced_donors)].copy()
    totals = (
        donor.groupby(["year", "bank_category"], as_index=False)[value]
        .agg(lambda x: x.sum(min_count=1))
        .rename(columns={value: "donor_total"})
    )
    work = panel[["province", "province_cn", "year", "bank_category", value]].merge(
        totals, on=["year", "bank_category"], how="left"
    )
    in_donor = work["province_cn"].isin(balanced_donors)
    work["loo_total"] = work["donor_total"] - np.where(in_donor, work[value], 0.0)
    work["ln_loo_total"] = np.log(work["loo_total"].where(work["loo_total"].gt(0)))
    work = work.sort_values(["province", "bank_category", "year"])
    work[f"shock_{value}_growth_loo"] = work.groupby(
        ["province", "bank_category"]
    )["ln_loo_total"].diff()
    base = work.loc[work["year"].eq(2011), ["province", "bank_category", "ln_loo_total"]]
    base = base.rename(columns={"ln_loo_total": "ln_loo_total_2011"})
    work = work.merge(base, on=["province", "bank_category"], how="left")
    work[f"shock_{value}_cum2011_loo"] = work["ln_loo_total"] - work["ln_loo_total_2011"]
    return work[
        [
            "province",
            "year",
            "bank_category",
            f"shock_{value}_growth_loo",
            f"shock_{value}_cum2011_loo",
        ]
    ]


def weighted_iv(
    shocks: pd.DataFrame, weights: pd.DataFrame, shock_name: str, weight_name: str
) -> pd.DataFrame:
    merged = shocks.merge(weights, on=["province", "bank_category"], how="left")
    iv_name = f"iv_{weight_name.replace('weight_', '').replace('_2011', '')}_{shock_name.replace('shock_', '')}"
    merged[iv_name] = merged[weight_name] * merged[shock_name]
    return merged.groupby(["province", "year"], as_index=False)[iv_name].sum(min_count=1)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = read_malformed_xlsx(SOURCE)
    category_panel, donors = build_complete_category_panel(raw)
    asset_weights = fixed_weights(category_panel, "assets")
    outlet_weights = fixed_weights(category_panel, "outlets")
    asset_shocks = leave_one_out_shocks(category_panel, donors, "assets")
    outlet_shocks = leave_one_out_shocks(category_panel, donors, "outlets")

    pieces = []
    for shocks, shock_value in [(asset_shocks, "assets"), (outlet_shocks, "outlets")]:
        for suffix in ["growth_loo", "cum2011_loo"]:
            shock_name = f"shock_{shock_value}_{suffix}"
            pieces.append(weighted_iv(shocks, asset_weights, shock_name, "weight_assets_2011"))
            pieces.append(weighted_iv(shocks, outlet_weights, shock_name, "weight_outlets_2011"))

    instruments = pieces[0]
    for piece in pieces[1:]:
        instruments = instruments.merge(piece, on=["province", "year"], how="outer")

    green = pd.read_csv(GREEN_CREDIT, encoding="utf-8-sig")
    green = green.rename(
        columns={
            "green_credit_proxy": "green_credit_level",
            "green_credit_high_energy_interest_share": "high_energy_interest_share",
        }
    )
    final = green.merge(instruments, on=["province", "year"], how="left")
    final["post2012"] = final["year"].ge(2012).astype(int)
    final["iv_aw_acum_post"] = (
        final["iv_assets_assets_cum2011_loo"] * final["post2012"]
    )
    final["iv_ow_acum_post"] = (
        final["iv_outlets_assets_cum2011_loo"] * final["post2012"]
    )
    final["iv_aw_ocum_post"] = (
        final["iv_assets_outlets_cum2011_loo"] * final["post2012"]
    )
    final["iv_ow_ocum_post"] = (
        final["iv_outlets_outlets_cum2011_loo"] * final["post2012"]
    )

    category_panel.to_csv(OUT / "bank_category_panel_2005_2022.csv", index=False)
    asset_weights.merge(
        outlet_weights, on=["province", "bank_category"], how="outer"
    ).to_csv(OUT / "bank_category_weights_2011.csv", index=False)
    asset_shocks.merge(
        outlet_shocks, on=["province", "year", "bank_category"], how="outer"
    ).to_csv(OUT / "bank_category_loo_shocks_2005_2022.csv", index=False)
    final.to_csv(OUT / "green_credit_category_loo_iv_panel_2005_2022.csv", index=False)
    final.to_stata(
        OUT / "green_credit_category_loo_iv_panel_2005_2022.dta",
        write_index=False,
        version=118,
    )
    (OUT / "balanced_donor_provinces.txt").write_text(
        "\n".join(f"{PROVINCE_MAP[p]}\t{p}" for p in donors) + "\n",
        encoding="utf-8",
    )

    print(f"Balanced donor provinces: {len(donors)}")
    print(", ".join(PROVINCE_MAP[p] for p in donors))
    print(f"Final panel: {len(final)} rows, {final['province'].nunique()} provinces")
    print(final.filter(regex=r"^(iv_|province$|year$)").notna().sum().to_string())


if __name__ == "__main__":
    main()
