#!/usr/bin/env python3
"""
CouncilWatch historical acquisition crawler.

Purpose:
- Discover Kempsey Shire Council meeting pages from the public meeting index.
- Crawl discovered meeting pages for agendas, minutes, business papers and attachments.
- Preserve source manifests and historical coverage data.
- Preserve discovered public documents into records/raw/YYYY/.
- Avoid factual findings until source records are preserved and reviewed.

Target window: 2016 through 2026 inclusive.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
RAW = ROOT / "records" / "raw"
TEXT = ROOT / "records" / "text"

BASE = "https://www.kempsey.nsw.gov.au"
SOURCE_INDEX = "https://www.kempsey.nsw.gov.au/Your-Council/Council-meetings-forums-catchups/Council-meeting-agendas-minutes"
YEAR_RANGE = range(2016, 2027)
MAX_PAGES = 250
MAX_DOCUMENTS_TO_PRESERVE = 300

MEETING_HINTS = [
    "ordinary-council-meeting",
    "extraordinary-council-meeting",
    "council-meeting",
    "meeting-agendas-minutes",
]

DOCUMENT_HINTS = [
    "agenda",
    "minutes",
    "business-paper",
    "business papers",
    "attachment",
    "attachments",
    ".pdf",
    ".doc",
    ".docx",
]

@dataclass
class SourceTarget:
    targetId: str
    year: int | None
    label: str
    url: str
    recordType: str
    sourcePage: str
    status: str
    rawPath: str | None = None
    sha256: str | None = None
    bytes: int | None = None


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "CouncilWatch/0.4 ten-year-preservation-crawler"})
    with urlopen(request, timeout=45) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8", errors="replace")


def normalise_url(href: str, source: str) -> str | None:
    if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
        return None
    url = urljoin(source, href)
    parsed = urlparse(url)
    if parsed.netloc and "kempsey.nsw.gov.au" not in parsed.netloc:
        return None
    return url.split("#", 1)[0]


def extract_links(html: str, source: str) -> list[str]:
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
    links: list[str] = []
    for href in hrefs:
        url = normalise_url(href, source)
        if url:
            links.append(url)
    return sorted(set(links))


def infer_year(text: str) -> int | None:
    years = [int(y) for y in re.findall(r"(20[1-2][0-9])", text)]
    for year in years:
        if year in YEAR_RANGE:
            return year
    return None


def infer_record_type(url: str, label: str = "") -> str:
    low = f"{url} {label}".lower()
    if "confirmed-minutes" in low or "minutes" in low:
        return "minutes"
    if "agenda" in low:
        return "agenda"
    if "business-paper" in low or "business papers" in low:
        return "business-paper"
    if "attachment" in low:
        return "attachment"
    if low.endswith(".pdf"):
        return "pdf-source"
    if low.endswith(".doc") or low.endswith(".docx"):
        return "word-source"
    return "source-target"


def label_from_url(url: str) -> str:
    last = url.rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"[_-]+", " ", last)[:160] or url[:160]


def safe_filename(url: str, target_id: str) -> str:
    parsed = urlparse(url)
    last = parsed.path.rstrip("/").rsplit("/", 1)[-1] or target_id
    last = re.sub(r"[^A-Za-z0-9._-]+", "-", last)[:120]
    if "." not in last:
        last += ".bin"
    return f"{target_id}-{last}"


def looks_like_meeting_page(url: str) -> bool:
    low = url.lower()
    return any(hint in low for hint in MEETING_HINTS) and not is_document_url(url)


def is_document_url(url: str) -> bool:
    low = url.lower()
    return any(low.endswith(ext) for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx"])


def looks_like_document(url: str) -> bool:
    low = url.lower()
    return is_document_url(url) or any(hint in low for hint in DOCUMENT_HINTS)


def crawl_source_targets() -> tuple[list[str], list[str], dict[str, str]]:
    visited: set[str] = set()
    queue: list[str] = [SOURCE_INDEX]
    meeting_pages: set[str] = set()
    documents: set[str] = set()
    page_status: dict[str, str] = {}

    while queue and len(visited) < MAX_PAGES:
        page = queue.pop(0)
        if page in visited:
            continue
        visited.add(page)
        try:
            html = fetch_text(page)
            page_status[page] = "fetched"
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as exc:
            page_status[page] = f"fetch-failed: {type(exc).__name__}"
            continue

        links = extract_links(html, page)
        for link in links:
            if looks_like_document(link):
                documents.add(link)
                continue
            if looks_like_meeting_page(link):
                meeting_pages.add(link)
                if link not in visited and link not in queue:
                    queue.append(link)

    return sorted(meeting_pages), sorted(documents), page_status


def build_targets(meeting_pages: Iterable[str], documents: Iterable[str]) -> list[SourceTarget]:
    targets: list[SourceTarget] = []
    idx = 1
    for url in sorted(set(meeting_pages)):
        targets.append(SourceTarget(
            targetId=f"KSC-PAGE-{idx:05d}",
            year=infer_year(url),
            label=label_from_url(url),
            url=url,
            recordType="meeting-page",
            sourcePage=SOURCE_INDEX,
            status="discovered-unverified",
        ))
        idx += 1
    for url in sorted(set(documents)):
        label = label_from_url(url)
        targets.append(SourceTarget(
            targetId=f"KSC-DOC-{idx:05d}",
            year=infer_year(url),
            label=label,
            url=url,
            recordType=infer_record_type(url, label),
            sourcePage="recursive-crawl",
            status="discovered-unverified",
        ))
        idx += 1
    return targets


def preserve_documents(targets: list[SourceTarget]) -> dict[str, str]:
    preservation_status: dict[str, str] = {}
    preserved = 0
    for target in targets:
        if target.recordType == "meeting-page":
            continue
        if preserved >= MAX_DOCUMENTS_TO_PRESERVE:
            preservation_status[target.targetId] = "skipped-limit-reached"
            continue
        year = target.year or 0
        try:
            data = fetch_bytes(target.url)
        except (HTTPError, URLError, TimeoutError) as exc:
            target.status = f"preservation-failed-{type(exc).__name__}"
            preservation_status[target.targetId] = target.status
            continue
        sha = hashlib.sha256(data).hexdigest()
        out_dir = RAW / str(year)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / safe_filename(target.url, target.targetId)
        out_path.write_bytes(data)
        target.rawPath = str(out_path.relative_to(ROOT))
        target.sha256 = sha
        target.bytes = len(data)
        target.status = "raw-preserved-unverified"
        preservation_status[target.targetId] = "raw-preserved-unverified"
        preserved += 1
    return preservation_status


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_historical_coverage(targets: list[SourceTarget]) -> None:
    years = []
    for year in YEAR_RANGE:
        year_targets = [t for t in targets if t.year == year]
        agenda_targets = [t for t in year_targets if t.recordType == "agenda"]
        minute_targets = [t for t in year_targets if t.recordType == "minutes"]
        raw_preserved = [t for t in year_targets if t.rawPath]
        years.append({
            "year": year,
            "status": "raw-preserved" if raw_preserved else ("source-targeted" if year_targets else "not-started"),
            "agendaTargets": len(agenda_targets),
            "minuteTargets": len(minute_targets),
            "sourceTargets": len(year_targets),
            "rawPreserved": len(raw_preserved),
            "textExtracted": 0,
            "pairsChecked": 0,
        })

    payload = {
        "updatedUtc": now_utc(),
        "proofOfFact": 0,
        "verificationState": "raw-preserved-unverified" if any(t.rawPath for t in targets) else "source-targets-unverified",
        "purpose": "Track ten-year historical council-record coverage by year, source type, preservation status and extraction status.",
        "council": "Kempsey Shire Council",
        "coverageStartYear": min(YEAR_RANGE),
        "coverageEndYear": max(YEAR_RANGE),
        "summary": {
            "yearsTargeted": len(list(YEAR_RANGE)),
            "yearsWithAnyRecords": sum(1 for y in years if y["sourceTargets"]),
            "sourceTargetsListed": len(targets),
            "rawRecordsPreserved": sum(1 for t in targets if t.rawPath),
            "textRecordsExtracted": 0,
            "agendaMinutePairsChecked": 0,
            "disappearanceChecksCompleted": 0,
        },
        "years": years,
        "sourceTargets": [asdict(t) for t in targets],
    }
    write_json(PUBLIC / "historical-coverage.json", payload)


def write_manifest(targets: list[SourceTarget], meeting_pages: list[str], documents: list[str], page_status: dict[str, str], preservation_status: dict[str, str]) -> None:
    manifest = {
        "updatedUtc": now_utc(),
        "sourceIndex": SOURCE_INDEX,
        "targetWindow": "2016-2026",
        "crawlLimits": {"maxPages": MAX_PAGES, "maxDocumentsToPreserve": MAX_DOCUMENTS_TO_PRESERVE},
        "meetingPagesFound": len(meeting_pages),
        "documentsFound": len(documents),
        "targetsFound": len(targets),
        "rawPreserved": sum(1 for t in targets if t.rawPath),
        "pageStatus": page_status,
        "preservationStatus": preservation_status,
        "targets": [asdict(t) for t in targets],
    }
    write_json(PUBLIC / "source-target-manifest.json", manifest)


def main() -> int:
    meeting_pages, documents, page_status = crawl_source_targets()
    targets = build_targets(meeting_pages, documents)
    preservation_status = preserve_documents(targets)
    update_historical_coverage(targets)
    write_manifest(targets, meeting_pages, documents, page_status, preservation_status)
    print(f"CouncilWatch acquisition crawl complete. Meeting pages: {len(meeting_pages)} Documents: {len(documents)} Raw preserved: {sum(1 for t in targets if t.rawPath)} Targets: {len(targets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
