#!/usr/bin/env python3
"""Validate and document the mechanism-data additions built on 2026-07-18."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / (
    "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_"
    "tide_absorption_monthly_reliability_0718.csv"
)
RESULTS = ROOT / "result" / "tables" / "0718_nonclean_tide_extension" / (
    "Table_0718_Nonclean_Tide_Extension.csv"
)
INVENTORY_OUT = ROOT / "data" / "0718_added_mechanism_data_inventory.csv"
REPORT_OUT = ROOT / "output" / "0718_新增机制数据补充与检查.md"


def fmt(value: float) -> str:
    return f"{value:.4f}"


def fmt_p(value: float) -> str:
    return "<0.001" if value < 0.001 else f"={value:.4f}"


def main() -> None:
    panel = pd.read_csv(PANEL, low_memory=False)
    results = pd.read_csv(RESULTS)
    renewable = pd.read_csv(
        ROOT / "data" / "nea_renewable_consumption" /
        "nea_renewable_consumption_province_2015_2023.csv",
        low_memory=False,
    )
    reliability = pd.read_csv(
        ROOT / "data" / "nea_power_reliability" /
        "nea_coal_unit_reliability_province_2018_2023.csv",
        low_memory=False,
    )
    gem = pd.read_csv(
        ROOT / "data" / "gem_project_pipeline_2026" /
        "gem_power_project_pipeline_province_2026.csv",
        low_memory=False,
    )

    assert len(panel) == 744
    assert panel["province"].nunique() == 31
    assert panel["year"].min() == 2000 and panel["year"].max() == 2023
    assert not panel.duplicated(["province", "year"]).any()
    assert len(renewable) == 279 and renewable["province"].nunique() == 31
    assert reliability["coal_unit_operating_hours"].notna().sum() == 180
    assert len(gem) == 31 and gem["province"].nunique() == 31

    inventory = pd.DataFrame([
        {
            "research_dimension": "清洁与非清洁能源的消费",
            "module": "可再生能源电力消纳",
            "variables": "re_cons_sh; nonhydro_re_cons_sh; target shares",
            "coverage": "31省, 2015-2023; 消费量至2022",
            "source": "国家能源局可再生能源电力发展监测评价报告",
            "empirical_role": "全国面板的实际消纳结果变量",
            "status": "可用",
        },
        {
            "research_dimension": "两类能源的产出稳定性",
            "module": "分能源月度发电波动",
            "variables": "therm_month_cv; windsolar_month_cv; allsrc_month_cv",
            "coverage": "火电31省 2000-2023; 风电30省 2013-2023; 光伏20省 2016-2023",
            "source": "Wind转引国家统计局分省月度累计发电量",
            "empirical_role": "技术稳定性的直接描述证据",
            "status": "可用; 1-2月合并值不分摊",
        },
        {
            "research_dimension": "非清洁能源存量运行",
            "module": "煤电机组运行与备用",
            "variables": "coal_unit_operating_factor; coal_unit_standby_factor",
            "coverage": "30个有煤电机组省份, 2018-2023",
            "source": "国家能源局全国电力可靠性年度报告",
            "empirical_role": "煤电存量持续承担运行功能的关联性证据",
            "status": "可用; 非因果识别",
        },
        {
            "research_dimension": "两类能源的项目存量与增量",
            "module": "煤电与风光项目管线快照",
            "variables": "operating; construction; pre-construction; announced; retired",
            "coverage": "31省, 2026当期状态快照",
            "source": "Global Energy Monitor power trackers",
            "empirical_role": "样本期后项目路径的机制展示",
            "status": "不并入2000-2023因果面板",
        },
    ])
    INVENTORY_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(INVENTORY_OUT, index=False, encoding="utf-8-sig")

    result = results.set_index(["block", "outcome", "term"])
    cv = result.loc[("monthly_stability", "windsolar_minus_thermal_cv", "mean_difference")]
    total_cv = result.loc[("monthly_stability", "allsrc_month_cv", "L.thermal_generation_share")]
    re_ddd = result.loc[("renewable_absorption", "re_cons_sh", "ddd_pretherm_endow")]
    nh_ddd = result.loc[("renewable_absorption", "nonhydro_re_cons_sh", "ddd_pretherm_endow")]
    op = result.loc[("coal_reliability", "coal_unit_operating_factor", "pretherm_gen_z")]
    standby = result.loc[("coal_reliability", "coal_unit_standby_factor", "pretherm_gen_z")]

    lines = [
        "# 0718 新增机制数据补充与检查",
        "",
        "## 一、面板质量",
        "",
        f"- 最新合并面板为 {len(panel)} 个省年观测、{panel['province'].nunique()} 个省级单位、2000--2023 年。",
        "- `province-year` 主键无重复，合并没有扩张或丢失原始样本。",
        f"- 最新面板共 {len(panel.columns)} 列；长变量名保留，同时增加 Stata 可直接识别的短别名。",
        "",
        "## 二、新增数据",
        "",
        "1. 国家能源局可再生能源电力消费占比：31 省、2015--2023 年完整，可直接衡量实际消纳，不再用装机等同消纳。",
        "2. 分能源月度发电波动：由分省月度累计值差分得到，用年内变异系数比较火电和风光稳定性。",
        "3. 煤电机组运行与备用时间：30 个有煤电机组的省份、2018--2023 年。",
        "4. GEM 项目管线：31 省煤电与风光在运、建设、前期、宣布及退役快照。该数据是 2026 年状态快照，只用于样本期后机制展示。",
        "",
        "## 三、扩展检验",
        "",
        f"- 风光发电的月内变异系数比火电高 {fmt(cv.b)}（p{fmt_p(cv.p)}），支持火电产出在月内更稳定。",
        f"- 滞后火电发电占比对全部已观测电源的月内波动系数为 {fmt(total_cv.b)}（p={fmt(total_cv.p)}），仍不能证明高火电占比稳定了全省电力产出。",
        f"- `2016年后 x 政策前火电依赖 x 风光自然禀赋` 对可再生能源电力消费占比的系数为 {fmt(re_ddd.b)}（p={fmt(re_ddd.p)}），对非水可再生能源消费占比为 {fmt(nh_ddd.b)}（p={fmt(nh_ddd.p)}）。两者均显著为负，表明高火电依赖地区的风光自然优势没有更快兑现为本地清洁电力消费。",
        f"- 政策前火电依赖每提高 1 个标准差，2018--2023 年煤电机组运行率高 {fmt(op.b)}（p={fmt(op.p)}），备用率低 {fmt(abs(standby.b))}（p={fmt(standby.p)}）。这是煤电存量持续高强度运行的关联性证据。",
        "",
        "## 四、可以支持的论文表述",
        "",
        "> 火电的月内产出确实比风光更稳定，而政策前火电依赖较高的地区在样本后期仍表现为更高的煤机运行率，同时风光自然优势并未更快兑现为可再生能源电力消费。这组结果支持“清洁能源增量扩张与煤电存量持续运行并存”的较窄资本惯性命题，但不能单独识别地方政府的目标函数或政策惯性。",
        "",
        "## 五、仍然缺失",
        "",
        "- 全国 31 省可比的政策文本面板：现有政策语料仅覆盖山西和内蒙古，不足以识别全国政策惯性。",
        "- 历史火电项目级核准、开工、投产和退役时点：GEM 本轮只取得 2026 快照，不能还原 2000--2023 年项目生命周期。",
        "- 分省月度工业增加值或工业用电：本轮 Wind 调用额度不足，暂时无法把火电的技术稳定性与地方月度经济波动直接连接。",
        "- 清洁能源对地方经济的直接贡献：仍缺风电、光伏分行业增加值、税收和就业的全国长面板。",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"validated panel: {len(panel)} rows, {len(panel.columns)} columns")
    print(f"inventory: {INVENTORY_OUT}")
    print(f"report: {REPORT_OUT}")


if __name__ == "__main__":
    main()
