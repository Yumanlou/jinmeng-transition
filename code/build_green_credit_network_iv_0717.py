#!/usr/bin/env python3
"""Build a coarse province-level bank-network IV panel.

The exposure is the 2011 share of large commercial-bank outlets in all
banking-financial-institution outlets. The current trial uses the national
green-credit proxy series as the time shock; it can be replaced by an external
large-bank green-loan shock without changing the exposure construction.
"""

from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BFI_XLSX = Path(
    "/Users/yumanlou/Downloads/"
    "%E9%93%B6%E8%A1%8C%E4%B8%9A%E9%87%91%E8%9E%8D%E6%9C%BA%E6%9E%84"
    "%E5%88%86%E5%B8%83%E8%A1%A8(%E5%88%86%E7%9C%81%E4%BB%BD)"
    "(%E5%B9%B4)204628379(%E4%BB%85%E4%BE%9B%E5%93%88%E4%BD%9B"
    "%E5%A4%A7%E5%AD%A6%E4%BD%BF%E7%94%A8)/BFI_BFINSTPRVY.xlsx"
)
GREEN_CREDIT_XLSX = Path("/Users/yumanlou/Downloads/2005-2022年绿色信贷水平.XLSX")
OUT_DIR = ROOT / "data" / "green_credit_network_iv"


PROVINCE_MAP = {
    "北京": "北京市",
    "天津": "天津市",
    "河北": "河北省",
    "山西": "山西省",
    "内蒙古": "内蒙古自治区",
    "辽宁": "辽宁省",
    "吉林": "吉林省",
    "黑龙江": "黑龙江省",
    "上海": "上海市",
    "江苏": "江苏省",
    "浙江": "浙江省",
    "安徽": "安徽省",
    "福建": "福建省",
    "江西": "江西省",
    "山东": "山东省",
    "河南": "河南省",
    "湖北": "湖北省",
    "湖南": "湖南省",
    "广东": "广东省",
    "广西": "广西壮族自治区",
    "海南": "海南省",
    "重庆": "重庆市",
    "四川": "四川省",
    "贵州": "贵州省",
    "云南": "云南省",
    "西藏": "西藏自治区",
    "陕西": "陕西省",
    "甘肃": "甘肃省",
    "青海": "青海省",
    "宁夏": "宁夏回族自治区",
    "新疆": "新疆维吾尔自治区",
}


def clean_name(value: object) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def build_network_exposure() -> pd.DataFrame:
    raw = pd.read_excel(BFI_XLSX, sheet_name="sheet1", header=None)
    raw.columns = raw.iloc[0].tolist()
    data = raw.iloc[3:].copy()
    data["SgnYear"] = pd.to_numeric(data["SgnYear"], errors="coerce")
    data["AgentTypeID"] = pd.to_numeric(data["AgentTypeID"], errors="coerce")
    data["SalesNetworkNumber"] = pd.to_numeric(
        data["SalesNetworkNumber"], errors="coerce"
    )
    data = data.loc[data["SgnYear"].eq(2011)].copy()

    # Shenzhen is reported separately from Guangdong. Aggregate it back to the
    # province so the exposure matches the 31-province outcome panel.
    data.loc[data["AreaName"].eq("深圳市"), "AreaName"] = "广东省"
    grouped = (
        data.groupby(["AreaName", "AgentTypeID"], as_index=False)["SalesNetworkNumber"]
        .sum(min_count=1)
    )
    wide = grouped.pivot(
        index="AreaName", columns="AgentTypeID", values="SalesNetworkNumber"
    )
    exposure = pd.DataFrame(
        {
            "province": wide.index,
            "large_bank_networks_2011": wide.get(2),
            "total_networks_2011": wide.get(13),
        }
    ).reset_index(drop=True)
    exposure["large_bank_share_2011"] = (
        exposure["large_bank_networks_2011"] / exposure["total_networks_2011"]
    )
    return exposure.sort_values("province").reset_index(drop=True)


def build_green_credit_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_excel(
        GREEN_CREDIT_XLSX, sheet_name="绿色信贷-计算结果", header=None
    )
    years = [int(x) for x in raw.iloc[0, 1:] if pd.notna(x) and 2005 <= int(x) <= 2022]
    year_to_col = {
        int(raw.iloc[0, c]): c
        for c in range(1, raw.shape[1])
        if pd.notna(raw.iloc[0, c]) and 2005 <= int(raw.iloc[0, c]) <= 2022
    }

    national_row = raw.loc[raw.iloc[:, 0].map(clean_name).eq("全国")].iloc[0]
    national = pd.DataFrame(
        {
            "year": years,
            "national_green_credit_level": [
                pd.to_numeric(national_row.iloc[year_to_col[y]], errors="coerce")
                for y in years
            ],
        }
    ).sort_values("year")
    national["national_green_credit_change"] = national[
        "national_green_credit_level"
    ].diff()
    base_2011 = national.loc[
        national["year"].eq(2011), "national_green_credit_level"
    ].iloc[0]
    national["national_green_credit_dev2011"] = (
        national["national_green_credit_level"] - base_2011
    )

    records: list[dict[str, object]] = []
    for _, row in raw.iloc[1:].iterrows():
        short = clean_name(row.iloc[0])
        if short not in PROVINCE_MAP:
            continue
        for year in years:
            records.append(
                {
                    "province": PROVINCE_MAP[short],
                    "year": year,
                    "green_credit_level": pd.to_numeric(
                        row.iloc[year_to_col[year]], errors="coerce"
                    ),
                }
            )
    return pd.DataFrame(records), national


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    exposure = build_network_exposure()
    green_credit, national = build_green_credit_panel()
    panel = green_credit.merge(exposure, on="province", how="left", validate="many_to_one")
    panel = panel.merge(national, on="year", how="left", validate="many_to_one")
    panel["post2012"] = (panel["year"] >= 2012).astype(int)
    panel["iv_network_post2012"] = panel["large_bank_share_2011"] * panel["post2012"]
    panel["iv_network_national_level"] = (
        panel["large_bank_share_2011"] * panel["national_green_credit_level"]
    )
    panel["iv_network_national_change"] = (
        panel["large_bank_share_2011"] * panel["national_green_credit_change"]
    )
    panel["iv_network_national_dev2011"] = (
        panel["large_bank_share_2011"] * panel["national_green_credit_dev2011"]
    )

    for col in [
        "iv_network_post2012",
        "iv_network_national_level",
        "iv_network_national_change",
        "iv_network_national_dev2011",
    ]:
        mean = panel[col].mean(skipna=True)
        std = panel[col].std(skipna=True, ddof=0)
        panel[f"z_{col}"] = (panel[col] - mean) / std if std else np.nan

    missing_exposure = sorted(panel.loc[panel["large_bank_share_2011"].isna(), "province"].unique())
    if missing_exposure:
        raise ValueError(f"Missing 2011 network exposure for: {missing_exposure}")

    exposure.to_csv(OUT_DIR / "large_bank_network_exposure_2011.csv", index=False)
    panel.to_csv(OUT_DIR / "green_credit_network_iv_panel_2005_2022.csv", index=False)
    panel.to_stata(
        OUT_DIR / "green_credit_network_iv_panel_2005_2022.dta",
        write_index=False,
        version=118,
    )
    print(
        f"built rows={len(panel)}, provinces={panel['province'].nunique()}, "
        f"years={panel['year'].min()}-{panel['year'].max()}"
    )
    print(
        exposure.loc[
            exposure["province"].isin(["山西省", "内蒙古自治区", "广东省"])
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
