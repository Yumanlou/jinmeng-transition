from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List


TOPICS = ("green_finance", "coal_clean", "pollution_control", "renewable")


def safe_int(value: str) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def safe_ratio(numerator: int | float, denominator: int | float) -> str:
    if not denominator:
        return ""
    return f"{numerator / denominator:.8f}"


def read_document_rows(path: Path) -> Iterable[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        yield from csv.DictReader(f)


def build_panel(document_path: Path) -> List[Dict[str, str]]:
    panel: Dict[tuple, dict] = defaultdict(
        lambda: {
            "policy_count": 0,
            "docs_with_content": 0,
            "content_chars": 0,
            **{topic: 0 for topic in TOPICS},
            **{f"{topic}_doc_count": 0 for topic in TOPICS},
        }
    )

    for row in read_document_rows(document_path):
        province = row["province"]
        year = row.get("year", "")
        if not year:
            continue
        key = (province, int(year))
        out = panel[key]
        out["policy_count"] += 1
        content_len = safe_int(row.get("content_len", ""))
        out["docs_with_content"] += int(content_len > 0)
        out["content_chars"] += content_len
        for topic in TOPICS:
            count = safe_int(row.get(topic, ""))
            out[topic] += count
            out[f"{topic}_doc_count"] += int(count > 0)

    rows: List[Dict[str, str]] = []
    for (province, year), values in sorted(panel.items()):
        policy_count = values["policy_count"]
        docs_with_content = values["docs_with_content"]
        content_chars = values["content_chars"]
        row: Dict[str, str] = {
            "province": province,
            "year": str(year),
            "policy_count": str(policy_count),
            "docs_with_content": str(docs_with_content),
            "content_coverage": safe_ratio(docs_with_content, policy_count),
            "content_chars": str(content_chars),
        }
        for topic in TOPICS:
            raw = values[topic]
            doc_count = values[f"{topic}_doc_count"]
            row[topic] = str(raw)
            row[f"{topic}_doc_count"] = str(doc_count)
            row[f"{topic}_per_10k_chars"] = safe_ratio(raw * 10000, content_chars)
            row[f"{topic}_doc_share"] = safe_ratio(doc_count, policy_count)
            row[f"{topic}_per_policy"] = safe_ratio(raw, policy_count)
        rows.append(row)
    return rows


def fieldnames() -> List[str]:
    fields = [
        "province",
        "year",
        "policy_count",
        "docs_with_content",
        "content_coverage",
        "content_chars",
    ]
    for topic in TOPICS:
        fields.extend(
            [
                topic,
                f"{topic}_doc_count",
                f"{topic}_per_10k_chars",
                f"{topic}_doc_share",
                f"{topic}_per_policy",
            ]
        )
    return fields


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames())
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build normalized policy-text intensity indices.")
    parser.add_argument("--input-dir", default="data/policy_texts")
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-year", type=int, default=2023)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    sources = {
        "shanxi": input_dir / "shanxi_policy_documents_2000_2023.csv",
        "nmg": input_dir / "nmg_policy_documents_2000_2023.csv",
    }

    combined: List[Dict[str, str]] = []
    for prefix, path in sources.items():
        if not path.exists():
            continue
        rows = [
            row
            for row in build_panel(path)
            if args.start_year <= int(row["year"]) <= args.end_year
        ]
        write_csv(input_dir / f"{prefix}_policy_year_panel_indices_2000_2023.csv", rows)
        combined.extend(rows)

    combined.sort(key=lambda r: (r["province"], int(r["year"])))
    write_csv(input_dir / "jinmeng_policy_text_year_panel_2000_2023.csv", combined)
    print(f"wrote {len(combined)} province-year rows")


if __name__ == "__main__":
    main()
