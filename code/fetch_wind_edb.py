#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量从 Wind EDB 取数并落盘 CSV。走 wind-mcp-skill 的 cli.mjs。"""
import subprocess, json, csv, os, sys

SKILL_DIR = os.path.expanduser("~/.agents/skills/wind-mcp-skill")
ROOT = "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
OUT_DIR = os.path.join(ROOT, "data", "wind_edb")
os.makedirs(OUT_DIR, exist_ok=True)

# (edb_code, 中文名, beginDate, endDate)
INDICATORS = [
    ("M6194125", "全国绿色贷款余额_亿元", "2018-01-01", "2024-12-31"),
    ("M0059249", "山西各项贷款余额_亿元", "2009-01-01", "2024-12-31"),
    ("M0059313", "内蒙古各项贷款余额_亿元", "2009-01-01", "2024-12-31"),
    ("M0004418", "山西工业增加值增速_pct", "2005-01-01", "2024-12-31"),
    ("M0004421", "内蒙古工业增加值增速_pct", "2005-01-01", "2024-12-31"),
    ("M6013703", "山西发电量_亿千瓦时", "2000-01-01", "2024-12-31"),
    ("V7060010", "山西风电新增装机_万千瓦", "2000-01-01", "2024-12-31"),
]


def fetch(code, begin, end):
    params = json.dumps({
        "executionMode": "fetch",
        "question": code,
        "beginDate": begin,
        "endDate": end,
    }, ensure_ascii=False)
    cmd = ["node", "scripts/cli.mjs", "call", "economic_data",
           "natural_language_get_edb_data", params]
    r = subprocess.run(cmd, cwd=SKILL_DIR, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return None, f"exit={r.returncode} stderr={r.stderr[:200]}"
    try:
        outer = json.loads(r.stdout)
    except Exception as e:
        return None, f"parse outer fail: {e}; stdout={r.stdout[:200]}"
    if outer.get("isError"):
        return None, f"isError: {json.dumps(outer.get('error', {}), ensure_ascii=False)[:300]}"
    try:
        text = outer["content"][0]["text"]
        inner = json.loads(text)
        d = inner["data"]
        if d.get("code") != 0 and d.get("code") is not None and d.get("code") != "0":
            return None, f"backend code={d.get('code')} msg={d.get('message')}"
        if not d.get("data"):
            return None, f"no data: msg={d.get('message')}"
        blk = d["data"][0]
        dates = blk.get("date") or []
        vals = blk.get("value") or []
        return (blk.get("meta", {}), dates, vals), None
    except Exception as e:
        return None, f"parse inner fail: {e}; text={text[:200]}"


def main():
    manifest = []
    for code, cname, b, e in INDICATORS:
        (meta, dates, vals), err = fetch(code, b, e)
        if err:
            print(f"[SKIP] {code} {cname}: {err}")
            manifest.append({"code": code, "name": cname, "status": "FAIL", "rows": 0, "err": err})
            continue
        # 写该指标的 CSV（宽表：date, value）
        safe = cname.replace("/", "_").replace(":", "_")
        fpath = os.path.join(OUT_DIR, f"{code}_{safe}.csv")
        with open(fpath, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["edb_code", "indicator", "unit", "freq", "date", "value"])
            unit = meta.get("unit", "")
            freq = meta.get("freq", "")
            for dt, v in zip(dates, vals):
                w.writerow([code, meta.get("name", cname), unit, freq, dt, v])
        n = len(dates)
        print(f"[OK] {code} {meta.get('name', cname)}: {n} 行 -> {os.path.basename(fpath)}")
        manifest.append({"code": code, "name": cname, "status": "OK", "rows": n, "err": ""})

    # 写 manifest
    mpath = os.path.join(OUT_DIR, "manifest.csv")
    with open(mpath, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["code", "name", "status", "rows", "err"])
        for m in manifest:
            w.writerow([m["code"], m["name"], m["status"], m["rows"], m["err"]])
    print(f"\nDone. {sum(1 for m in manifest if m['status']=='OK')}/{len(manifest)} 成功，输出目录 {OUT_DIR}")


if __name__ == "__main__":
    main()
