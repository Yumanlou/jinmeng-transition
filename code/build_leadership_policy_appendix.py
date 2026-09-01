from __future__ import annotations

import csv
import html
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "data/policy_texts/jinmeng_policy_text_year_panel_2000_2023.csv"
EVENT_PATH = ROOT / "data/leadership_turnover_jinmeng.csv"
OUT_TABLE = ROOT / "result/tables/0518_full_chain/Appendix_JinMeng_Leadership_Turnover.csv"
OUT_PLOT_DATA = ROOT / "result/tables/0518_full_chain/Appendix_JinMeng_Policy_Text_Leadership_Plot_Data.csv"
OUT_FIG_DIR = ROOT / "result/figures/0518_full_chain"


TOPICS = [
    ("green_finance_per_10k_chars", "Green finance words per 10k chars", "#2f6f4e"),
    ("coal_clean_per_10k_chars", "Coal clean-up words per 10k chars", "#8a5a20"),
    ("renewable_per_10k_chars", "Renewable words per 10k chars", "#2f6ea3"),
]


def read_csv(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def province_en(name: str) -> str:
    if name == "山西":
        return "Shanxi"
    if name == "内蒙古":
        return "Neimenggu"
    return name


def build_appendix_table(events: List[dict]) -> List[dict]:
    rows = []
    for row in events:
        if row.get("appendix_flag") != "1":
            continue
        rows.append(
            {
                "province": row["province_en"],
                "year": row["year"],
                "event_type": row["event_type"],
                "leader_position": row["leader_position"],
                "event_label": row["event_label"],
                "interpretive_use": row["note"],
            }
        )
    rows.sort(key=lambda r: (r["province"], int(r["year"]), r["event_type"]))
    return rows


def build_plot_rows(policy_rows: List[dict], events: List[dict]) -> List[dict]:
    event_years: Dict[tuple, List[str]] = {}
    for event in events:
        if event.get("appendix_flag") != "1":
            continue
        key = (event["province_en"], event["year"])
        event_years.setdefault(key, []).append(event["event_type"])

    rows = []
    for row in policy_rows:
        prov = province_en(row["province"])
        for topic, label, _color in TOPICS:
            rows.append(
                {
                    "province": prov,
                    "year": row["year"],
                    "topic": topic,
                    "topic_label": label,
                    "value": row[topic],
                    "leadership_event": ";".join(event_years.get((prov, row["year"]), [])),
                }
            )
    return rows


def scale(value: float, lo: float, hi: float, top: float, bottom: float) -> float:
    if hi <= lo:
        return (top + bottom) / 2
    return bottom - (value - lo) / (hi - lo) * (bottom - top)


def x_scale(year: int, left: float, right: float) -> float:
    return left + (year - 2000) / (2023 - 2000) * (right - left)


def polyline(points: List[tuple]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def svg_text(x: float, y: float, text: str, size: int = 12, anchor: str = "start", weight: str = "normal") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="#222">'
        f"{html.escape(text)}</text>"
    )


def build_svg(province: str, policy_rows: List[dict], events: List[dict], out_path: Path) -> None:
    rows = [r for r in policy_rows if province_en(r["province"]) == province]
    event_rows = [e for e in events if e["province_en"] == province and e.get("appendix_flag") == "1"]
    width, height = 1100, 780
    left, right = 80, 1040
    panel_h = 185
    gap = 45
    top0 = 90

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(40, 42, f"{province}: policy-text intensity and provincial leadership turnover", 22, weight="bold"),
        svg_text(40, 66, "Dashed vertical lines mark party/government leadership turnover years; the series are descriptive policy-attention indicators.", 12),
    ]

    for i, (topic, label, color) in enumerate(TOPICS):
        top = top0 + i * (panel_h + gap)
        bottom = top + panel_h
        values = [(int(r["year"]), float(r[topic] or 0)) for r in rows if r.get(topic) not in ("", None)]
        lo = 0.0
        hi = max(v for _y, v in values) if values else 1.0
        hi = hi * 1.12 if hi > 0 else 1.0

        parts.append(f'<rect x="{left}" y="{top}" width="{right-left}" height="{panel_h}" fill="#fbfbfb" stroke="#dddddd"/>')
        for yr in [2000, 2005, 2010, 2015, 2020, 2023]:
            x = x_scale(yr, left, right)
            parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" stroke="#eeeeee"/>')
            parts.append(svg_text(x, bottom + 18, str(yr), 11, anchor="middle"))
        for frac in [0, 0.5, 1]:
            y = bottom - frac * panel_h
            val = lo + frac * (hi - lo)
            parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#eeeeee"/>')
            parts.append(svg_text(left - 8, y + 4, f"{val:.1f}", 10, anchor="end"))

        for event in event_rows:
            yr = int(event["year"])
            if 2000 <= yr <= 2023:
                x = x_scale(yr, left, right)
                stroke = "#9a9a9a" if event["event_type"] != "joint_turnover" else "#555555"
                parts.append(
                    f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" '
                    f'stroke="{stroke}" stroke-dasharray="5,5" stroke-width="1.2"/>'
                )
                parts.append(svg_text(x + 3, top + 14, str(yr), 9, anchor="start"))

        points = [(x_scale(y, left, right), scale(v, lo, hi, top + 10, bottom - 12)) for y, v in values]
        parts.append(f'<polyline points="{polyline(points)}" fill="none" stroke="{color}" stroke-width="2.8"/>')
        for x, y in points:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{color}"/>')
        parts.append(svg_text(40, top + 20, label, 14, weight="bold"))

    parts.extend(
        [
            svg_text(80, 748, "Source: provincial policy-text corpus collected from Shanxi and Inner Mongolia government websites; leadership events compiled as appendix background.", 11),
            "</svg>",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    policy_rows = read_csv(POLICY_PATH)
    events = read_csv(EVENT_PATH)

    appendix_rows = build_appendix_table(events)
    write_csv(
        OUT_TABLE,
        appendix_rows,
        ["province", "year", "event_type", "leader_position", "event_label", "interpretive_use"],
    )

    plot_rows = build_plot_rows(policy_rows, events)
    write_csv(
        OUT_PLOT_DATA,
        plot_rows,
        ["province", "year", "topic", "topic_label", "value", "leadership_event"],
    )

    for province in ["Shanxi", "Neimenggu"]:
        build_svg(
            province,
            policy_rows,
            events,
            OUT_FIG_DIR / f"Appendix_{province}_Policy_Text_Leadership.svg",
        )

    print(f"wrote {OUT_TABLE}")
    print(f"wrote {OUT_PLOT_DATA}")
    print(f"wrote {OUT_FIG_DIR / 'Appendix_Shanxi_Policy_Text_Leadership.svg'}")
    print(f"wrote {OUT_FIG_DIR / 'Appendix_Neimenggu_Policy_Text_Leadership.svg'}")


if __name__ == "__main__":
    main()
