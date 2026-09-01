#!/Users/yumanlou/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
"""Fetch major-bank green-loan and total-loan series from Wind.

These bank-year series provide the national shock component for a future
bank-network shift-share IV. Provincial pre-policy bank-network weights are
still required before the instrument can be constructed.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = Path("/Users/yumanlou/.agents/skills/wind-mcp-skill")
CLI = SKILL_DIR / "scripts" / "cli.mjs"
OUTPUT_DIR = ROOT / "data" / "wind_bank_green_loan_shocks"

GREEN_QUERY = "工商银行、农业银行、中国银行、建设银行、交通银行、邮储银行2012年至2022年各年绿色贷款余额"
TOTAL_QUERY = "工商银行、农业银行、中国银行、建设银行、交通银行、邮储银行2012年至2022年各年客户贷款总额"


def call_wind(question: str) -> dict:
    params = json.dumps({"question": question, "lang": "CNS"}, ensure_ascii=False)
    command = ["node", str(CLI), "call", "analytics_data", "get_financial_data", params]
    result = subprocess.run(
        command, cwd=SKILL_DIR, check=True, capture_output=True, text=True, encoding="utf-8"
    )
    outer = json.loads(result.stdout)
    if outer.get("isError"):
        raise RuntimeError(f"Wind returned an error: {outer}")
    content = outer.get("content") or []
    if not content or "text" not in content[0]:
        raise ValueError(f"Unexpected Wind response: {outer}")
    inner = json.loads(content[0]["text"])
    if inner.get("error"):
        raise RuntimeError(f"Wind inner error: {inner['error']}")
    blocks = inner.get("data") or []
    if len(blocks) != 1:
        raise ValueError(f"Expected one Wind data block, got {len(blocks)}")
    return blocks[0]


def green_frame(block: dict) -> pd.DataFrame:
    rows = block["rows"]
    if len(rows) != 62:
        raise ValueError(f"Expected 62 green-loan bank-years, got {len(rows)}")
    source_columns = [column["name"] for column in block["columns"]]
    frame = pd.DataFrame(rows, columns=source_columns).rename(columns={
        source_columns[0]: "windcode", source_columns[1]: "bank",
        source_columns[2]: "green_loan_100m_cny", source_columns[3]: "report_period",
        source_columns[4]: "currency",
    })
    frame["year"] = frame["report_period"].str.extract(r"FY(\d{4})")[0].astype(int)
    return frame


def total_frame(block: dict) -> pd.DataFrame:
    rows = block["rows"]
    if len(rows) != 66:
        raise ValueError(f"Expected 66 total-loan bank-years, got {len(rows)}")
    source_columns = [column["name"] for column in block["columns"]]
    frame = pd.DataFrame(rows, columns=source_columns).rename(columns={
        source_columns[0]: "windcode", source_columns[1]: "bank",
        source_columns[2]: "total_loan_trillion_cny", source_columns[3]: "report_period_total",
        source_columns[4]: "currency_total",
    })
    frame["year"] = frame["report_period_total"].str.extract(r"FY(\d{4})")[0].astype(int)
    return frame


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    green_block = call_wind(GREEN_QUERY)
    total_block = call_wind(TOTAL_QUERY)
    green = green_frame(green_block)
    total = total_frame(total_block)

    panel = total.merge(
        green,
        on=["windcode", "bank", "year"],
        how="left",
        validate="one_to_one",
    )
    panel["total_loan_100m_cny"] = panel["total_loan_trillion_cny"] * 10000.0
    panel["green_loan_share"] = panel["green_loan_100m_cny"] / panel["total_loan_100m_cny"]
    panel["green_loan_share_change"] = panel.groupby("windcode")["green_loan_share"].diff()

    five_banks = panel[panel["bank"] != "邮储银行"]
    if len(five_banks) != 55 or five_banks["green_loan_share"].isna().any():
        raise ValueError("The five consistently disclosed banks are not complete for 2012-2022")
    missing = panel[panel["green_loan_share"].isna()][["bank", "year"]]
    expected_missing = {("邮储银行", year) for year in range(2012, 2016)}
    if set(map(tuple, missing.to_records(index=False))) != expected_missing:
        raise ValueError(f"Unexpected green-loan gaps: {missing.to_dict(orient='records')}")

    keep = [
        "windcode", "bank", "year", "green_loan_100m_cny", "total_loan_100m_cny",
        "green_loan_share", "green_loan_share_change", "report_period", "report_period_total",
    ]
    panel[keep].sort_values(["bank", "year"]).to_csv(
        OUTPUT_DIR / "wind_major_bank_green_loan_shocks_2012_2022.csv",
        index=False, encoding="utf-8-sig",
    )
    (OUTPUT_DIR / "wind_major_bank_green_loan_shocks_metadata.json").write_text(
        json.dumps({
            "provider": "Wind Financial Data Service",
            "green_loan_query": GREEN_QUERY,
            "total_loan_query": TOTAL_QUERY,
            "green_loan_rows": len(green),
            "total_loan_rows": len(total),
            "complete_core_banks": ["工商银行", "农业银行", "中国银行", "建设银行", "交通银行"],
            "complete_years": [2012, 2022],
            "post_bank_missing_green_loan_years": [2012, 2013, 2014, 2015],
            "intended_use": "Bank-year shock component for a bank-network shift-share IV",
            "missing_component": "Province-by-bank pre-policy branch or loan shares around 2011",
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(panel[keep].sort_values(["year", "bank"]).to_string(index=False))
    print(f"saved={OUTPUT_DIR}")


if __name__ == "__main__":
    main()
