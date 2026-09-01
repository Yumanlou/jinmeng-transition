#!/usr/bin/env python3
"""Prepare the coarse 2012 bank-network exposure IV panel.

This is a feasibility test, not the final bank-level high-carbon exposure IV.
The available banking table identifies large commercial banks only as a group.
"""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(
    "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
)
MAIN = ROOT / "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_0716.csv"
NETWORK = ROOT / "data/green_credit_network_iv/green_credit_network_iv_panel_2005_2022.csv"
OUT = ROOT / "data/green_credit_bank_policy_proxy"

CN_TO_EN = {
    "北京市": "Beijing", "天津市": "Tianjin", "河北省": "Hebei",
    "山西省": "Shanxi", "内蒙古自治区": "Neimenggu", "辽宁省": "Liaoning",
    "吉林省": "Jilin", "黑龙江省": "Heilongjiang", "上海市": "Shanghai",
    "江苏省": "Jiangsu", "浙江省": "Zhejiang", "安徽省": "Anhui",
    "福建省": "Fujian", "江西省": "Jiangxi", "山东省": "Shandong",
    "河南省": "Henan", "湖北省": "Hubei", "湖南省": "Hunan",
    "广东省": "Guangdong", "广西壮族自治区": "Guangxi", "海南省": "Hainan",
    "重庆市": "Chongqing", "四川省": "Sichuan", "贵州省": "Guizhou",
    "云南省": "Yunnan", "西藏自治区": "Xizang", "陕西省": "Shaanxi",
    "甘肃省": "Gansu", "青海省": "Qinghai", "宁夏回族自治区": "Ningxia",
    "新疆维吾尔自治区": "Xinjiang",
}


def zscore(series: pd.Series) -> pd.Series:
    return (series - series.mean()) / series.std(ddof=1)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    main = pd.read_csv(MAIN, encoding="utf-8-sig")
    network = pd.read_csv(NETWORK, encoding="utf-8-sig")
    network["province"] = network["province"].map(CN_TO_EN)
    if network["province"].isna().any():
        raise ValueError("Unmapped Chinese province in bank-network panel")

    keep = network[
        ["province", "year", "large_bank_share_2011", "iv_network_post2012"]
    ].copy()
    panel = main.merge(keep, on=["province", "year"], how="left", validate="one_to_one")
    sample = panel["year"].between(2005, 2022) & panel["green_credit_proxy"].notna()

    panel["gc_proxy_z_full"] = np.nan
    panel.loc[sample, "gc_proxy_z_full"] = zscore(
        panel.loc[sample, "green_credit_proxy"]
    )
    panel["bank_policy_iv_z"] = np.nan
    panel.loc[sample, "bank_policy_iv_z"] = zscore(
        panel.loc[sample, "iv_network_post2012"]
    )
    panel["gc_proxy_z_x_resdep"] = (
        pd.to_numeric(panel["gc_proxy_z_full"]) * panel["resdep_pre"]
    )
    panel["bank_policy_iv_z_x_resdep"] = (
        pd.to_numeric(panel["bank_policy_iv_z"]) * panel["resdep_pre"]
    )

    if panel.loc[sample, "large_bank_share_2011"].isna().any():
        raise ValueError("Missing 2011 large-bank exposure in analysis sample")
    output = OUT / "green_credit_bank_policy_proxy_panel_2005_2022.csv"
    panel.to_csv(output, index=False, encoding="utf-8-sig")
    analysis_columns = [
        "province_id", "province", "year", "green_credit_proxy",
        "gc_proxy_z_full", "gc_proxy_z_x_resdep", "resdep_pre",
        "large_bank_share_2011", "iv_network_post2012",
        "bank_policy_iv_z", "bank_policy_iv_z_x_resdep",
        "ln_gdp", "population", "sec_pctg", "urbanization_rate",
        "env_exp_share", "market_index", "energy5_int", "coalterm_int",
        "industrial_so2", "coalshare5", "ln_co2", "therm_cap_sh",
        "therm_gen_sh", "windsolar_gen_sh",
    ]
    panel[analysis_columns].to_stata(
        OUT / "green_credit_bank_policy_proxy_panel_2005_2022.dta",
        write_index=False,
        version=118,
    )
    print(f"saved={output}")
    print(f"sample_n={sample.sum()}, provinces={panel.loc[sample, 'province'].nunique()}")


if __name__ == "__main__":
    main()
