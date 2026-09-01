#!/usr/bin/env python3
"""Build a comparable 31-province policy-attention panel from work reports.

Source: Li (2025), PLOS ONE, supplementary file for DOI
10.1371/journal.pone.0324713. The source corpus contains one provincial
government work report per province-year from 2003 through 2023.
"""

from __future__ import annotations

import argparse
import json
import lzma
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "data" / "provincial_government_work_reports" / "source"
OUT_DIR = ROOT / "data" / "provincial_government_work_reports"

PROVINCE_MAP = {
    1: ("Beijing", "北京"), 2: ("Tianjin", "天津"), 3: ("Hebei", "河北"),
    4: ("Shandong", "山东"), 5: ("Jiangsu", "江苏"), 6: ("Shanghai", "上海"),
    7: ("Zhejiang", "浙江"), 8: ("Fujian", "福建"), 9: ("Guangdong", "广东"),
    10: ("Hainan", "海南"), 11: ("Shanxi", "山西"), 12: ("Henan", "河南"),
    13: ("Anhui", "安徽"), 14: ("Hubei", "湖北"), 15: ("Hunan", "湖南"),
    16: ("Jiangxi", "江西"), 17: ("Heilongjiang", "黑龙江"), 18: ("Jilin", "吉林"),
    19: ("Liaoning", "辽宁"), 20: ("Neimenggu", "内蒙古"), 21: ("Ningxia", "宁夏"),
    22: ("Shaanxi", "陕西"), 23: ("Gansu", "甘肃"), 24: ("Sichuan", "四川"),
    25: ("Chongqing", "重庆"), 26: ("Guizhou", "贵州"), 27: ("Guangxi", "广西"),
    28: ("Yunnan", "云南"), 29: ("Qinghai", "青海"), 30: ("Xinjiang", "新疆"),
    31: ("Xizang", "西藏"),
}

LEXICONS = {
    "green_finance": [
        "绿色金融", "绿色信贷", "绿色贷款", "绿色债券", "转型金融",
        "碳金融", "绿色保险", "绿色基金", "绿色融资", "绿色担保",
    ],
    "fossil_security": [
        "煤炭", "煤矿", "煤电", "煤化工", "焦化", "能源安全", "能源保供",
        "稳产保供", "增产保供", "迎峰度夏", "迎峰度冬", "先进产能",
    ],
    "coal_retrofit": [
        "煤炭清洁高效利用", "煤炭清洁利用", "煤电超低排放改造",
        "煤电节能改造", "煤电灵活性改造", "智能化矿山", "智能化煤矿",
        "绿色矿山", "煤矸石", "煤层气", "煤炭洗选",
    ],
    "pollution_control": [
        "污染治理", "污染防治", "污染物", "二氧化硫", "氮氧化物", "烟粉尘",
        "颗粒物", "减污", "超低排放", "大气污染", "工业固废", "固体废物",
    ],
    "renewable": [
        "新能源", "风电", "光伏", "太阳能发电", "可再生能源", "清洁能源",
        "绿电", "绿色电力", "风光基地", "新能源基地", "沙戈荒",
    ],
    "grid_absorption": [
        "电网", "并网", "消纳", "外送", "特高压", "储能", "源网荷储", "绿电交易",
        "电力市场", "输电通道", "电网调峰", "抽水蓄能", "电力外送",
    ],
}


def find_corpus() -> Path:
    matches = list(SOURCE_ROOT.rglob("compessed gov report.xz"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one compressed corpus, found {len(matches)}")
    return matches[0]


def extract_documents(corpus: Path) -> pd.DataFrame:
    decompressed = lzma.open(corpus, "rt", encoding="utf-8").read()
    info, combined_text = decompressed.split("\n\n", 1)
    rows = []
    for line in info.splitlines():
        filename, start, end = line.split(",")
        match = re.fullmatch(r"(\d{4})P(\d+)\.txt", filename)
        if not match:
            raise ValueError(f"Unexpected source filename: {filename}")
        year, code = map(int, match.groups())
        province, province_cn = PROVINCE_MAP[code]
        raw_text = combined_text[int(start):int(end)]
        clean_text = re.sub(r"\s+", "", raw_text)
        rows.append({
            "province": province,
            "province_cn": province_cn,
            "year": year,
            "source_file": filename,
            "content_chars": len(clean_text),
            "report_text": raw_text,
        })
    frame = pd.DataFrame(rows).sort_values(["province", "year"]).reset_index(drop=True)
    if len(frame) != 651 or frame["province"].nunique() != 31:
        raise ValueError("Expected a balanced 31-province, 2003-2023 corpus")
    if frame.duplicated(["province", "year"]).any():
        raise ValueError("Duplicate province-year reports")
    return frame


def count_attention(documents: pd.DataFrame) -> pd.DataFrame:
    panel = documents.drop(columns="report_text").copy()
    for topic, terms in LEXICONS.items():
        counts = documents["report_text"].fillna("").map(
            lambda text: sum(text.count(term) for term in terms)
        )
        panel[f"gwr_{topic}_count"] = counts
        panel[f"gwr_{topic}_per10k"] = counts * 10000 / panel["content_chars"]
        panel[f"gwr_{topic}_mention"] = counts.gt(0).astype(int)

    panel = panel.sort_values(["province", "year"]).reset_index(drop=True)
    for topic in LEXICONS:
        variable = f"gwr_{topic}_per10k"
        grouped = panel.groupby("province", sort=False)[variable]
        panel[f"{variable}_lag1"] = grouped.shift(1)
        panel[f"{variable}_change"] = grouped.diff()
        panel[f"{variable}_roll3"] = grouped.transform(
            lambda values: values.rolling(3, min_periods=2).mean()
        )
    short_topics = {
        "green_finance": "gf",
        "fossil_security": "fs",
        "coal_retrofit": "cr",
        "pollution_control": "pc",
        "renewable": "re",
        "grid_absorption": "ga",
    }
    for topic, short in short_topics.items():
        panel[f"gwr_{short}_chg"] = panel[f"gwr_{topic}_per10k_change"]
    return panel


def merge_panel(policy: pd.DataFrame, main_path: Path) -> pd.DataFrame:
    main = pd.read_csv(main_path, low_memory=False)
    if main.duplicated(["province", "year"]).any():
        raise ValueError("Main panel has duplicate province-year keys")
    return main.merge(policy.drop(columns=["province_cn", "source_file"]),
                      on=["province", "year"], how="left", validate="one_to_one")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--main-panel", type=Path,
        default=ROOT / "data" / (
            "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_"
            "cleanproxy_tide_absorption_monthly_reliability_0718.csv"
        ),
    )
    parser.add_argument(
        "--merged-output", type=Path,
        default=ROOT / "data" / (
            "final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_"
            "cleanproxy_tide_absorption_monthly_reliability_policyworkreports_0721.csv"
        ),
    )
    args = parser.parse_args()

    documents = extract_documents(find_corpus())
    policy = count_attention(documents)
    merged = merge_panel(policy, args.main_panel)
    coverage = policy.groupby("year").agg(
        provinces=("province", "nunique"),
        reports=("source_file", "count"),
        mean_chars=("content_chars", "mean"),
    ).reset_index()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    documents.to_csv(OUT_DIR / "provincial_gov_work_reports_2003_2023.csv",
                     index=False, encoding="utf-8-sig")
    policy.to_csv(OUT_DIR / "provincial_policy_attention_panel_2003_2023.csv",
                  index=False, encoding="utf-8-sig")
    coverage.to_csv(OUT_DIR / "provincial_policy_attention_coverage.csv",
                    index=False, encoding="utf-8-sig")
    args.merged_output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.merged_output, index=False, encoding="utf-8-sig")
    metadata = {
        "source": "Li (2025), PLOS ONE supplementary file",
        "doi": "10.1371/journal.pone.0324713",
        "supplement_doi": "10.1371/journal.pone.0324713.s001",
        "coverage": "31 provincial-level regions, 2003-2023, one report per province-year",
        "license": "Article and supplementary materials distributed under CC BY 4.0",
        "interpretation": "Dictionary frequencies measure policy attention, not policy support or semantic direction",
        "lexicons": LEXICONS,
    }
    (OUT_DIR / "source_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"documents rows={len(documents)} provinces={documents.province.nunique()}")
    print(f"policy rows={len(policy)} columns={len(policy.columns)}")
    print(f"merged rows={len(merged)} columns={len(merged.columns)}")
    print(coverage.to_string(index=False))


if __name__ == "__main__":
    main()
