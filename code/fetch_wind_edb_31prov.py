#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐省搜代码 + 取数，拼成 31 省面板（贷款余额、工业增加值增速）。"""
import subprocess, json, csv, os, time

SKILL_DIR = os.path.expanduser("~/.agents/skills/wind-mcp-skill")
ROOT = "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
OUT_DIR = os.path.join(ROOT, "data", "wind_edb", "province_panel")
os.makedirs(OUT_DIR, exist_ok=True)

PROVINCES = [
    "北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
    "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
    "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州",
    "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆",
]


def call_cli(params_obj):
    params = json.dumps(params_obj, ensure_ascii=False)
    cmd = ["node", "scripts/cli.mjs", "call", "economic_data",
           "natural_language_get_edb_data", params]
    r = subprocess.run(cmd, cwd=SKILL_DIR, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return None, f"exit={r.returncode} stderr={r.stderr[:150]}"
    try:
        outer = json.loads(r.stdout)
    except Exception as e:
        return None, f"parse fail: {e}"
    if outer.get("ok") is False or outer.get("isError"):
        return None, f"err: {outer.get('error', {}).get('code', '?')} {outer.get('error', {}).get('message', '')[:120]}"
    try:
        text = outer["content"][0]["text"]
        inner = json.loads(text)
        d = inner.get("data") or {}
        if d.get("code") not in (0, None, "0"):
            return None, f"backend code={d.get('code')} msg={d.get('message', '')[:120]}"
        return d.get("data"), None
    except Exception as e:
        return None, f"inner parse fail: {e}"


def search(question):
    return call_cli({"executionMode": "search", "question": question})


def fetch(code, begin, end):
    return call_cli({"executionMode": "fetch", "question": code,
                     "beginDate": begin, "endDate": end})


def pick_loan(blocks):
    if not blocks:
        return None
    # 优先：含"金融机构各项贷款余额"且不含"银行业"；其次任意"各项贷款余额"
    for b in blocks:
        name = b.get("meta", {}).get("name", "")
        if "各项贷款余额" in name and "银行业" not in name:
            return b["meta"]["code"]
    for b in blocks:
        name = b.get("meta", {}).get("name", "")
        if "各项贷款余额" in name:
            return b["meta"]["code"]
    return None


def pick_industry(blocks):
    if not blocks:
        return None
    # 优先月频"累计同比"；其次"同比"规模以上工业
    for b in blocks:
        name = b.get("meta", {}).get("name", "")
        freq = b.get("meta", {}).get("freq", "")
        if "工业增加值" in name and "累计同比" in name:
            return b["meta"]["code"]
    for b in blocks:
        name = b.get("meta", {}).get("name", "")
        if "工业增加值" in name and "同比" in name and "规模以上" in name:
            return b["meta"]["code"]
    return None


def main():
    loan_rows, ind_rows = [], []
    loan_codes, ind_codes = [], []
    for prov in PROVINCES:
        # 贷款余额
        blocks, err = search(f"{prov}金融机构各项贷款余额")
        code_loan = pick_loan(blocks) if blocks else None
        if code_loan:
            blk, ferr = fetch(code_loan, "2009-01-01", "2024-12-31")
            if ferr is None and blk:
                b = blk[0]
                for dt, v in zip(b.get("date") or [], b.get("value") or []):
                    loan_rows.append((prov, dt, v))
                loan_codes.append((prov, code_loan, b["meta"].get("name", "")))
                print(f"[贷款 OK] {prov} {code_loan} {len(b.get('date') or [])}行", flush=True)
            else:
                print(f"[贷款 FAIL] {prov} {code_loan}: {ferr}", flush=True)
        else:
            print(f"[贷款 MISS] {prov}: 未找到代码", flush=True)
        time.sleep(0.2)

        # 工业增加值
        blocks, err = search(f"{prov}规模以上工业增加值增速")
        code_ind = pick_industry(blocks) if blocks else None
        if code_ind:
            blk, ferr = fetch(code_ind, "2005-01-01", "2024-12-31")
            if ferr is None and blk:
                b = blk[0]
                for dt, v in zip(b.get("date") or [], b.get("value") or []):
                    ind_rows.append((prov, dt, v))
                ind_codes.append((prov, code_ind, b["meta"].get("name", "")))
                print(f"[工业 OK] {prov} {code_ind} {len(b.get('date') or [])}行", flush=True)
            else:
                print(f"[工业 FAIL] {prov} {code_ind}: {ferr}", flush=True)
        else:
            print(f"[工业 MISS] {prov}: 未找到代码", flush=True)
        time.sleep(0.2)

    def write_panel(rows, fname):
        with open(os.path.join(OUT_DIR, fname), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["province", "date", "value"])
            for prov, dt, v in rows:
                w.writerow([prov, dt, v])

    write_panel(loan_rows, "loan_balance_31prov_panel.csv")
    write_panel(ind_rows, "industry_va_31prov_panel.csv")

    with open(os.path.join(OUT_DIR, "code_mapping.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["province", "edb_code", "indicator"])
        for prov, code, name in loan_codes:
            w.writerow([prov, code, name])
        for prov, code, name in ind_codes:
            w.writerow([prov, code, name])

    print(f"\n贷款：{len(loan_codes)}/31 省成功，{len(loan_rows)} 行")
    print(f"工业：{len(ind_codes)}/31 省成功，{len(ind_rows)} 行")
    print(f"输出目录：{OUT_DIR}")


if __name__ == "__main__":
    main()
