#!/usr/bin/env python3
"""Build provincial clean versus non-clean generation amounts and shares."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_0718.csv"
OUTPUT_DIR = ROOT / "data/clean_nonclean_generation_0718"
TABLE_DIR = ROOT / "result/tables/0718_thermal_threshold"

PROVINCE_CN = {
    "Beijing": "北京", "Tianjin": "天津", "Hebei": "河北",
    "Shanxi": "山西", "Neimenggu": "内蒙古", "Liaoning": "辽宁",
    "Jilin": "吉林", "Heilongjiang": "黑龙江", "Shanghai": "上海",
    "Jiangsu": "江苏", "Zhejiang": "浙江", "Anhui": "安徽",
    "Fujian": "福建", "Jiangxi": "江西", "Shandong": "山东",
    "Henan": "河南", "Hubei": "湖北", "Hunan": "湖南",
    "Guangdong": "广东", "Guangxi": "广西", "Hainan": "海南",
    "Chongqing": "重庆", "Sichuan": "四川", "Guizhou": "贵州",
    "Yunnan": "云南", "Xizang": "西藏", "Shaanxi": "陕西",
    "Gansu": "甘肃", "Qinghai": "青海", "Ningxia": "宁夏",
    "Xinjiang": "新疆",
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    source = pd.read_csv(INPUT)
    panel = source[
        [
            "province_id",
            "province",
            "year",
            "total_generation_billion_kwh",
            "thermal_generation_billion_kwh",
            "therm_gen_sh",
            "nontherm_gen_sh",
            "windsolar_gen_sh",
        ]
    ].copy()
    panel["province_cn"] = panel["province"].map(PROVINCE_CN)

    # One billion kWh equals ten 100-million kWh.
    panel["total_generation_100m_kwh"] = (
        10.0 * panel["total_generation_billion_kwh"]
    )
    panel["nonclean_generation_100m_kwh"] = (
        10.0 * panel["thermal_generation_billion_kwh"]
    )
    panel["clean_generation_100m_kwh"] = (
        panel["total_generation_100m_kwh"]
        - panel["nonclean_generation_100m_kwh"]
    )
    panel["nonclean_generation_share_percent"] = 100.0 * panel["therm_gen_sh"]
    panel["clean_generation_share_percent"] = 100.0 * panel["nontherm_gen_sh"]
    panel["windsolar_generation_share_percent"] = 100.0 * panel["windsolar_gen_sh"]

    columns = [
        "province_id",
        "province",
        "province_cn",
        "year",
        "total_generation_100m_kwh",
        "clean_generation_100m_kwh",
        "clean_generation_share_percent",
        "nonclean_generation_100m_kwh",
        "nonclean_generation_share_percent",
        "windsolar_generation_share_percent",
    ]
    panel = panel[columns]
    latest = (
        panel.loc[panel["year"] == 2023]
        .sort_values("nonclean_generation_share_percent", ascending=False)
        .reset_index(drop=True)
    )

    national = pd.DataFrame(
        {
            "year": [2023],
            "total_generation_100m_kwh": [latest["total_generation_100m_kwh"].sum()],
            "clean_generation_100m_kwh": [latest["clean_generation_100m_kwh"].sum()],
            "nonclean_generation_100m_kwh": [latest["nonclean_generation_100m_kwh"].sum()],
        }
    )
    national["clean_generation_share_percent"] = (
        100.0
        * national["clean_generation_100m_kwh"]
        / national["total_generation_100m_kwh"]
    )
    national["nonclean_generation_share_percent"] = (
        100.0
        * national["nonclean_generation_100m_kwh"]
        / national["total_generation_100m_kwh"]
    )

    panel.to_csv(OUTPUT_DIR / "province_clean_nonclean_generation_2000_2023.csv", index=False)
    latest.to_csv(OUTPUT_DIR / "province_clean_nonclean_generation_2023.csv", index=False)
    national.to_csv(OUTPUT_DIR / "national_clean_nonclean_generation_2023.csv", index=False)

    workbook = TABLE_DIR / "Province_Clean_Nonclean_Generation_0718.xlsx"
    with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
        latest.to_excel(writer, sheet_name="2023分省", index=False)
        national.to_excel(writer, sheet_name="2023全国汇总", index=False)
        panel.to_excel(writer, sheet_name="2000-2023年度面板", index=False)

    assert len(latest) == 31
    assert not latest[
        [
            "total_generation_100m_kwh",
            "clean_generation_100m_kwh",
            "nonclean_generation_100m_kwh",
            "clean_generation_share_percent",
            "nonclean_generation_share_percent",
        ]
    ].isna().any().any()
    assert (latest["clean_generation_100m_kwh"] >= 0).all()
    print(latest.to_string(index=False))
    print("\nNational summary")
    print(national.to_string(index=False))
    print(f"\nWorkbook: {workbook}")


if __name__ == "__main__":
    main()
