from __future__ import annotations

import argparse
import csv
import html
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin
from urllib.request import Request, urlopen


LOGGER = logging.getLogger("nmg_policy")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class PolicyColumn:
    province: str
    source_site: str
    category: str
    url: str


@dataclass
class PolicyRecord:
    province: str
    source_site: str
    category: str
    title: str
    url: str
    page_url: str
    pub_date: str = ""
    issue_date: str = ""
    doc_no: str = ""
    agency: str = ""
    subject: str = ""
    content: str = ""
    content_len: int = 0
    crawl_status: str = "list_only"


BASE = "https://www.nmg.gov.cn/zwgk/zfxxgk/zfxxgkml/"

NMG_COLUMNS = (
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "政府文件", urljoin(BASE, "zzqzfjbgtwj/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "政府令", urljoin(BASE, "zzqzfgz/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "行政规范性文件", urljoin(BASE, "gzxzgfxwj/xzgfxwj/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "行政规范性文件目录", urljoin(BASE, "gzxzgfxwj/xzgfxwwj/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "财政、金融、审计", urljoin(BASE, "gzxzgfxwj/czjrsj/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "自然资源、能源", urljoin(BASE, "gzxzgfxwj/zrzyny/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "农牧业、林业、水利", urljoin(BASE, "gzxzgfxwj/nmls/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "工业、交通、信息化", urljoin(BASE, "gzxzgfxwj/gyjtxxh/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "商贸、海关", urljoin(BASE, "gzxzgfxwj/smhg/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "市场监管、安全生产监管", urljoin(BASE, "gzxzgfxwj/scaq/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "城乡建设、生态环境", urljoin(BASE, "gzxzgfxwj/cxhj/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "科技、教育、卫生、医疗", urljoin(BASE, "gzxzgfxwj/kjjywsyl/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "文化、旅游、广电、体育", urljoin(BASE, "gzxzgfxwj/wlgt/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "人力资源、公共服务", urljoin(BASE, "gzxzgfxwj/rlzyggfw/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "公安、司法", urljoin(BASE, "gzxzgfxwj/gasf/")),
    PolicyColumn("内蒙古", "内蒙古自治区人民政府", "民政、乡村振兴、应急及其他", urljoin(BASE, "gzxzgfxwj/mzfpjz/")),
)

TOPIC_LEXICON: Dict[str, List[str]] = {
    "green_finance": [
        "绿色金融",
        "绿色信贷",
        "绿色贷款",
        "转型金融",
        "绿色债券",
        "低碳转型挂钩债券",
        "可持续发展挂钩债券",
        "信贷支持",
        "金融支持",
    ],
    "coal_clean": [
        "煤炭",
        "煤矿",
        "煤电",
        "焦化",
        "煤化工",
        "煤矸石",
        "清洁高效",
        "智能化矿山",
        "先进产能",
        "超低排放改造",
    ],
    "pollution_control": [
        "污染治理",
        "污染物",
        "二氧化硫",
        "氮氧化物",
        "烟粉尘",
        "颗粒物",
        "减污",
        "超低排放",
        "节能改造",
        "生态修复",
    ],
    "renewable": [
        "新能源",
        "风电",
        "光伏",
        "太阳能",
        "可再生能源",
        "绿电",
        "储能",
        "源网荷储",
        "外送",
        "特高压",
        "绿色电力",
        "氢能",
        "绿氢",
    ],
}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: List[str] = []

    def handle_data(self, data: str) -> None:
        text = html.unescape(data)
        if text.strip():
            self.parts.append(text.strip())

    def handle_entityref(self, name: str) -> None:
        self.parts.append(html.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.parts.append(html.unescape(f"&#{name};"))

    def get_text(self) -> str:
        text = "\n".join(self.parts)
        text = re.sub(r"[ \t\r\f\v]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()


def fetch_text(url: str, timeout: int = 20, retries: int = 3) -> str:
    last_error: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            for encoding in ("utf-8", "gb18030", "gbk"):
                try:
                    return raw.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="ignore")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            LOGGER.warning("fetch failed attempt=%s url=%s error=%s", attempt, url, exc)
            time.sleep(0.8 * attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def clean_html_text(fragment: str) -> str:
    fragment = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", fragment)
    fragment = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>", "\n", fragment)
    parser = TextExtractor()
    parser.feed(fragment)
    return parser.get_text()


def normalize_label(value: str) -> str:
    return re.sub(r"[\s:：　]+", "", value or "")


def normalize_date(value: str) -> str:
    value = html.unescape(value or "").strip()
    value = re.sub(r"\s+", "", value)
    if not value:
        return ""
    m = re.search(r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})", value)
    if m:
        y, mo, d = map(int, m.groups())
        return f"{y:04d}-{mo:02d}-{d:02d}"
    m = re.search(r"(\d{4})(\d{2})(\d{2})", value)
    if m:
        y, mo, d = map(int, m.groups())
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return value


def year_of(date_value: str) -> Optional[int]:
    m = re.match(r"(\d{4})", date_value or "")
    return int(m.group(1)) if m else None


def extract_count_page(page_html: str) -> int:
    counts = [int(x) for x in re.findall(r"countPage\s*=\s*(\d+)", page_html)]
    return max(counts) if counts else 1


def page_url_for(column_url: str, index: int) -> str:
    if index == 0:
        return column_url
    return urljoin(column_url, f"index_{index}.html")


def parse_list_page(page_html: str, page_url: str, column: PolicyColumn) -> List[PolicyRecord]:
    records: List[PolicyRecord] = []
    for row in re.findall(r"(?is)<tr>\s*<td>\s*\d+\s*</td>(.*?)</tr>", page_html):
        link = re.search(r'(?is)<td>\s*<a\s+href="([^"]+)"[^>]*>(.*?)</a>\s*</td>', row)
        if not link:
            continue
        href, title_html = link.groups()
        cells = [clean_html_text(cell) for cell in re.findall(r"(?is)<td[^>]*>(.*?)</td>", row)]
        desktop_cells = [cell for cell in cells if cell and not cell.startswith(clean_html_text(title_html)[:10])]
        doc_no = desktop_cells[-3] if len(desktop_cells) >= 3 else ""
        issue_date = normalize_date(desktop_cells[-2]) if len(desktop_cells) >= 2 else ""
        pub_date = normalize_date(desktop_cells[-1]) if desktop_cells else ""
        records.append(
            PolicyRecord(
                province=column.province,
                source_site=column.source_site,
                category=column.category,
                title=clean_html_text(title_html),
                url=urljoin(page_url, href),
                page_url=page_url,
                pub_date=pub_date,
                issue_date=issue_date,
                doc_no=doc_no,
            )
        )
    return records


def extract_meta(page_html: str, name: str) -> str:
    m = re.search(rf'(?is)<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"', page_html)
    return html.unescape(m.group(1)).strip() if m else ""


def extract_table_field(page_html: str, field_names: List[str]) -> str:
    cells = [clean_html_text(cell) for cell in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", page_html)]
    targets = {normalize_label(name) for name in field_names}
    for idx, cell in enumerate(cells[:-1]):
        if normalize_label(cell) in targets:
            return cells[idx + 1].strip()
    return ""


def extract_detail(page_html: str) -> Dict[str, str]:
    title = extract_meta(page_html, "ArticleTitle")
    pub_date = normalize_date(extract_meta(page_html, "PubDate"))
    agency = extract_meta(page_html, "ContentSource")
    issue_date = normalize_date(extract_table_field(page_html, ["成文日期"]))
    doc_no = extract_table_field(page_html, ["文号", "文　　号", "发文字号"])
    subject = extract_table_field(page_html, ["主题分类"])

    content = ""
    candidates = re.findall(
        r'(?is)<div[^>]*class="[^"]*(?:trs_editor_view|TRS_UEDITOR)[^"]*"[^>]*>(.*?)</div>',
        page_html,
    )
    candidates.extend(
        re.findall(
            r'(?is)<div[^>]*id="docContent"[^>]*>(.*?)</div>\s*</div>\s*<div class="zfwjxl-box-right',
            page_html,
        )
    )
    if candidates:
        content = max((clean_html_text(part) for part in candidates), key=len)

    return {
        "title": title,
        "pub_date": pub_date,
        "issue_date": issue_date,
        "doc_no": doc_no,
        "agency": agency,
        "subject": subject,
        "content": content,
    }


def score_topics(text: str) -> Dict[str, int]:
    return {topic: sum(text.count(term) for term in terms) for topic, terms in TOPIC_LEXICON.items()}


def crawl_column(
    column: PolicyColumn,
    start_year: int,
    end_year: int,
    fetch_details: bool,
    delay: float,
    max_pages: Optional[int],
    max_details: Optional[int],
) -> List[PolicyRecord]:
    first_html = fetch_text(column.url)
    count_page = extract_count_page(first_html)
    if max_pages is not None:
        count_page = min(count_page, max_pages)
    LOGGER.info("%s %s pages=%s", column.province, column.category, count_page)

    records: List[PolicyRecord] = []
    for page_index in range(count_page):
        page_url = page_url_for(column.url, page_index)
        page_html = first_html if page_index == 0 else fetch_text(page_url)
        page_records = parse_list_page(page_html, page_url, column)
        LOGGER.info("list %s page=%s records=%s", column.category, page_index, len(page_records))
        records.extend(page_records)
        time.sleep(delay)

    dedup = {record.url: record for record in records}
    filtered: List[PolicyRecord] = []
    for record in dedup.values():
        y = year_of(record.pub_date or record.issue_date)
        if y is not None and start_year <= y <= end_year:
            filtered.append(record)

    if not fetch_details:
        return filtered

    detail_records = filtered if max_details is None else filtered[:max_details]
    for idx, record in enumerate(detail_records, start=1):
        try:
            detail_html = fetch_text(record.url)
            detail = extract_detail(detail_html)
            record.title = detail["title"] or record.title
            record.pub_date = record.pub_date or detail["pub_date"]
            record.issue_date = record.issue_date or detail["issue_date"]
            record.doc_no = detail["doc_no"] or record.doc_no
            record.agency = detail["agency"] or record.agency
            record.subject = detail["subject"] or record.subject
            record.content = detail["content"]
            record.content_len = len(record.content)
            record.crawl_status = "ok" if record.content else "detail_no_content"
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("detail failed %s %s", record.url, exc)
            record.crawl_status = f"detail_error: {exc}"
        LOGGER.info("details %s/%s %s", idx, len(detail_records), column.category)
        time.sleep(delay)
    return filtered


def write_outputs(records: List[PolicyRecord], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "province",
        "source_site",
        "category",
        "year",
        "title",
        "url",
        "page_url",
        "pub_date",
        "issue_date",
        "doc_no",
        "agency",
        "subject",
        "content_len",
        "crawl_status",
        "green_finance",
        "coal_clean",
        "pollution_control",
        "renewable",
        "content",
    ]
    records_path = output_dir / "nmg_policy_documents_2000_2023.csv"
    with records_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            scores = score_topics(f"{record.title}\n{record.subject}\n{record.content}")
            writer.writerow(
                {
                    "province": record.province,
                    "source_site": record.source_site,
                    "category": record.category,
                    "year": year_of(record.pub_date or record.issue_date) or "",
                    "title": record.title,
                    "url": record.url,
                    "page_url": record.page_url,
                    "pub_date": record.pub_date,
                    "issue_date": record.issue_date,
                    "doc_no": record.doc_no,
                    "agency": record.agency,
                    "subject": record.subject,
                    "content_len": record.content_len,
                    "crawl_status": record.crawl_status,
                    **scores,
                    "content": record.content,
                }
            )

    panel: Dict[tuple, Dict[str, int]] = {}
    for record in records:
        y = year_of(record.pub_date or record.issue_date)
        if y is None:
            continue
        key = (record.province, y)
        if key not in panel:
            panel[key] = {
                "policy_count": 0,
                "docs_with_content": 0,
                "content_chars": 0,
                "green_finance": 0,
                "coal_clean": 0,
                "pollution_control": 0,
                "renewable": 0,
            }
        row = panel[key]
        row["policy_count"] += 1
        row["docs_with_content"] += int(record.content_len > 0)
        row["content_chars"] += record.content_len
        for topic, count in score_topics(f"{record.title}\n{record.subject}\n{record.content}").items():
            row[topic] += count

    panel_path = output_dir / "nmg_policy_year_panel_2000_2023.csv"
    with panel_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "province",
                "year",
                "policy_count",
                "docs_with_content",
                "content_chars",
                "green_finance",
                "coal_clean",
                "pollution_control",
                "renewable",
            ],
        )
        writer.writeheader()
        for (province, year), row in sorted(panel.items()):
            writer.writerow({"province": province, "year": year, **row})

    LOGGER.info("wrote %s and %s", records_path, panel_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl Inner Mongolia policy texts for Jin-Meng transition project.")
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument("--output-dir", default="data/policy_texts")
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--list-only", action="store_true")
    parser.add_argument("--max-pages-per-column", type=int, default=None)
    parser.add_argument("--max-details", type=int, default=None)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(asctime)s %(levelname)s %(message)s")
    started = datetime.now()
    all_records: List[PolicyRecord] = []
    for column in NMG_COLUMNS:
        all_records.extend(
            crawl_column(
                column=column,
                start_year=args.start_year,
                end_year=args.end_year,
                fetch_details=not args.list_only,
                delay=args.delay,
                max_pages=args.max_pages_per_column,
                max_details=args.max_details,
            )
        )
    write_outputs(all_records, Path(args.output_dir))
    LOGGER.info("done records=%s elapsed=%s", len(all_records), datetime.now() - started)


if __name__ == "__main__":
    main()
