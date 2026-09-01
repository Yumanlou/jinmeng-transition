#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补跑余额不足时缺失的省份，并 append 合并进现有 31 省面板。"""
import subprocess, json, csv, os, time

SKILL_DIR = os.path.expanduser("~/.agents/skills/wind-mcp-skill")
ROOT = "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
OUT_DIR = os.path.join(ROOT, "data", "wind_edb", "province_panel")

MISSING_LOAN = ["西藏", "陕西", "甘肃", "青海", "宁夏", "新疆"]
MISSING_IND = ["云南", "重庆", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆"]


def call_cli(params_obj):
    params = json.dumps(params_obj, ensure_ascii=False)
    cmd = ["node", "scripts/cli.mjs", "call", "economic_data",
           "natural_language_get_edb_data", params]
    r = subprocess.run(cmd, cwd=SKILL_DIR, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return None, f"exit={r.returncode} stderr={r.stderr[:120]}"
    try:
        outer = json.loads(r.stdout)
    except Exception as e:
        return None, f"parse fail: {e}"
    if outer.get("ok") is False or outer.get("isError"):
        e = outer.get("error", {})
        return None, f"{e.get('code', '?')} {e.get('message', '')[:100]}"
    try:
        text = outer["content"][0]["text"]
        inner = json.loads(text)
        d = inner.get("data") or {}
        if d.get("code") not in (0, None, "0"):
            return None, f"code={d.get('code')} {d.get('message', '')[:100]}"
        return d.get("data"), None
    except Exception as e:
        return None, f"inner fail: {e}"


def search(q):
    return call_cli({"executionMode": "search", "question": q})


def fetch(code, b, e):
    return call_cli({"executionMode": "fetch", "question": code,
                     "beginDate": b, "endDate": e})


def pick_loan(blocks):
    if not blocks:
        return None
    for b in blocks:
        n = b.get("meta", {}).get("name", "")
        if "各项贷款余额" in n and "银行业" not in n:
            return b["meta"]["code"]
    for b in blocks:
        if "各项贷款余额" in b.get("meta", {}).get("name", ""):
            return b["meta"]["code"]
    return None


def pick_ind(blocks):
    if not blocks:
        return None
    for b in blocks:
        n = b.get("meta", {}).get("name", "")
        if "工业增加值" in n and "累计同比" in n:
            return b["meta"]["code"]
    for b in blocks:
        n = b.get("meta", {}).get("name", "")
        if "工业增加值" in n and "同比" in n and "规模以上" in n:
            return b["meta"]["code"]
    return None


def append_panel(rows, fname):
    path = os.path.join(OUT_DIR, fname)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        for prov, dt, v in rows:
            w.writerow([prov, dt, v])


def main():
    loan_rows, ind_rows = [], []
    loan_codes, ind_codes = [], []
    for prov in MISSING_LOAN:
        blocks, _ = search(f"{prov}金融机构各项贷款余额")
        code = pick_loan(blocks)
        if code:
            blk, err = fetch(code, "2009-01-01", "2024-12-31")
            if err is None and blk:
                b = blk[0]
                for dt, v in zip(b.get("date") or [], b.get("value") or []):
                    loan_rows.append((prov, dt, v))
                loan_codes.append((prov, code, b["meta"].get("name", "")))
                print(f"[贷款 OK] {prov} {code} {len(b.get('date') or [])}行", flush=True)
            else:
                print(f"[贷款 FAIL] {prov} {code}: {err}", flush=True)
        else:
            print(f"[贷款 MISS] {prov}", flush=True)
        time.sleep(0.2)

    for prov in MISSING_IND:
        blocks, _ = search(f"{prov}规模以上工业增加值增速")
        code = pick_ind(blocks)
        if code:
            blk, err = fetch(code, "2005-01-01", "2024-12-31")
            if err is None and blk:
                b = blk[0]
                for dt, v in zip(b.get("date") or [], b.get("value") or []):
                    ind_rows.append((prov, dt, v))
                ind_codes.append((prov, code, b["meta"].get("name", "")))
                print(f"[工业 OK] {prov} {code} {len(b.get('date') or [])}行", flush=True)
            else:
                print(f"[工业 FAIL] {prov} {code}: {err}", flush=True)
        else:
            print(f"[工业 MISS] {prov}", flush=True)
        time.sleep(0.2)

    append_panel(loan_rows, "loan_balance_31prov_panel.csv")
    append_panel(ind_rows, "industry_va_31prov_panel.csv")

    with open(os.path.join(OUT_DIR, "code_mapping.csv"), "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        for prov, code, name in loan_codes + ind_codes:
            w.writerow([prov, code, name])

    print(f"\n补跑完成：贷款 {len(loan_codes)} 省 {len(loan_rows)} 行；工业 {len(ind_codes)} 省 {len(ind_rows)} 行")


if __name__ == "__main__":
    main()
