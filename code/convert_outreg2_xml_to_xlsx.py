#!/usr/bin/env python3
"""Convert outreg2 SpreadsheetML output to a true XLSX workbook."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from openpyxl import Workbook


SS = "urn:schemas-microsoft-com:office:spreadsheet"


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: convert_outreg2_xml_to_xlsx.py INPUT.xls OUTPUT.xlsx")
    source, target = map(Path, sys.argv[1:])
    root = ET.fromstring(source.read_text(encoding="ascii"))
    rows: list[list[str]] = []
    for row in root.findall(f".//{{{SS}}}Worksheet/{{{SS}}}Table/{{{SS}}}Row"):
        values: list[str] = []
        next_col = 1
        for cell in row.findall(f"{{{SS}}}Cell"):
            index = cell.attrib.get(f"{{{SS}}}Index")
            if index:
                while next_col < int(index):
                    values.append("")
                    next_col += 1
            data = cell.find(f"{{{SS}}}Data")
            values.append(data.text if data is not None and data.text else "")
            next_col += 1
        rows.append(values)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "First stage"
    for row in rows:
        sheet.append(row)
    for column in sheet.columns:
        width = max(len(str(cell.value or "")) for cell in column) + 2
        sheet.column_dimensions[column[0].column_letter].width = min(max(width, 10), 42)
    target.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(target)
    print(f"Converted {source} -> {target}")


if __name__ == "__main__":
    main()
