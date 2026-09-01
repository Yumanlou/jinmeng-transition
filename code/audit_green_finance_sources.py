#!/usr/bin/env python3
"""Locate candidate source files for the project's green-finance variables."""

from __future__ import annotations

import argparse
import csv
import zipfile
from pathlib import Path


SEARCH_TERMS = (
    "gf_index",
    "carbon_finance",
    "green_finance",
    "绿色金融指数",
    "碳金融",
)
TABULAR_SUFFIXES = {".csv", ".tsv", ".xlsx", ".xlsm", ".dta"}
MACOS_DATALESS_FLAG = 0x40000000


def scan_text_file(path: Path, max_bytes: int) -> set[str]:
    with path.open("rb") as handle:
        content = handle.read(max_bytes)
    return {term for term in SEARCH_TERMS if term.encode("utf-8") in content}


def scan_workbook(path: Path) -> set[str]:
    hits: set[str] = set()
    with zipfile.ZipFile(path) as workbook:
        for member in workbook.namelist():
            if not (
                member.endswith("sharedStrings.xml")
                or "worksheets/sheet" in member and member.endswith(".xml")
            ):
                continue
            content = workbook.read(member)
            hits.update(
                term for term in SEARCH_TERMS if term.encode("utf-8") in content
            )
    return hits


def scan_root(root: Path, max_bytes: int, max_file_size: int) -> list[tuple[Path, set[str]]]:
    matches: list[tuple[Path, set[str]]] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TABULAR_SUFFIXES:
            continue
        try:
            metadata = path.stat()
            if metadata.st_size > max_file_size:
                continue
            if getattr(metadata, "st_flags", 0) & MACOS_DATALESS_FLAG:
                continue
            if path.suffix.lower() in {".xlsx", ".xlsm"}:
                hits = scan_workbook(path)
            else:
                hits = scan_text_file(path, max_bytes)
        except (OSError, PermissionError, zipfile.BadZipFile):
            continue
        if hits:
            matches.append((path, hits))
    return matches


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--max-bytes", type=int, default=10_000_000)
    parser.add_argument("--max-file-size", type=int, default=300_000_000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    matches: list[tuple[Path, set[str]]] = []
    for root in args.roots:
        matches.extend(scan_root(root, args.max_bytes, args.max_file_size))

    rows = [
        {"path": str(path), "matched_terms": ";".join(sorted(hits))}
        for path, hits in sorted(matches)
    ]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("path", "matched_terms"))
            writer.writeheader()
            writer.writerows(rows)

    for row in rows:
        print(f"{row['path']} => {row['matched_terms']}")
    print(f"MATCHES={len(rows)}")


if __name__ == "__main__":
    main()
