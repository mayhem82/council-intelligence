#!/usr/bin/env python3
"""
CouncilWatch historical ingestion scaffold.

Purpose:
- Discover Kempsey Shire Council agenda/minute source links.
- Preserve source targets into JSON registers.
- Prepare later extraction and disappearance comparison.

This first version is deliberately conservative:
- It does not claim factual findings.
- It records source targets and coverage state only.
- It avoids deleting or overwriting historical evidence.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
RAW = ROOT / "records" / "raw"
TEXT = ROOT / "records" / "text"

SOURCE_INDEX = "https://www.kempsey.nsw.gov.au/Your-Council/Council-meetings-forums-catchups/Council-meeting-agendas-minutes"
YEAR_RANGE = range(2019, 2027)

KEYWORDS = [
    "agenda",
    "minutes",
    "ordinary-council-meeting",
    "extraordinary-council-meeting",
    "business-paper",
    "attachments",
]

@dataclass
class SourceTarget:
    targetId: str
    year: int | None
    label: str
    url: str
    recordType: str
    status: str


def fetch_url(url: str) -> str:
    request = Request(url, headers={"User-Agent": "CouncilWatch/0.1 public-record-monitor"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_links(html: str) -> list[str]:
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
    out: list[str] = []
    for href in hrefs:
        if href.startswith("/"):
            href = "https://www.kempsey.nsw.gov.au" + href
        if not href.startswith("http"):
            continue
        low = href.lower()
        if any(k in low for k in KEYWORDS):
            out.append(href)
    return sorted(set(out))


def infer_year(url: str) -> int | None:
    m = re.search(r"(20[1-2][0-9])", url)
    if not m:
        return None
    year = int(m.group(1))
    return year if year in YEAR_RANGE else None


def infer_record_type(url: str) -> str:
    low = url.lower()
    if "minutes" in low:
        return "minutes"
    if "agenda" in low:
        return "agenda"
    if "business" in low:
        return "business-paper"
    if "attachment" in low:
        return "attachment"
    return "source-target"


def build_targets(links: Iterable[str]) -> list[SourceTarget]:
    targets: list[SourceTarget] = []
    for idx, url in enumerate(sorted(set(links)), start=1):
        year = infer_year(url)
        record_type = infer_record_type(url)
        targets.append(SourceTarget(
            targetId=f"KSC-SRC-{idx:05d}",
            year=year,
            label=url.rsplit("/", 1)[-1].replace("-", " ")[:120],
            url=url,
            recordType=record_type,
            status="discovered-unverified",
        ))
    return targets


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_historical_coverage(targets: list[SourceTarget]) -> None:
    years = []
    for year in YEAR_RANGE:
        year_targets = [t for t in targets if t.year == year]
        agenda_targets = [t for t in year_targets if t.recordType == "agenda"]
        minute_targets = [t for t in year_targets if t.recordType == "minutes"]
        years.append({
            "year": year,
            "status": "source-targeted" if year_targets else "not-started",
            "agendaTargets": len(agenda_targets),
            "minuteTargets": len(minute_targets),
            "rawPreserved": 0,
            "textExtracted": 0,
            "pairsChecked": 0,
        })

    payload = {
        "updatedUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "proofOfFact": 0,
        "verificationState": "source-targets-unverified",
        "purpose": "Track historical council-record coverage by year, source type, preservation status and extraction status.",
        "council": "Kempsey Shire Council",
        "coverageStartYear": min(YEAR_RANGE),
        "coverageEndYear": max(YEAR_RANGE),
        "summary": {
            "yearsTargeted": len(list(YEAR_RANGE)),
            "yearsWithAnyRecords": sum(1 for y in years if y["agendaTargets"] or y["minuteTargets"]),
            "sourceTargetsListed": len(targets),
            "rawRecordsPreserved": 0,
            "textRecordsExtracted": 0,
            "agendaMinutePairsChecked": 0,
            "disappearanceChecksCompleted": 0,
        },
        "years": years,
        "sourceTargets": [asdict(t) for t in targets],
    }
    write_json(PUBLIC / "historical-coverage.json", payload)


def main() -> int:
    try:
        html = fetch_url(SOURCE_INDEX)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"FETCH_FAILED: {exc}", file=sys.stderr)
        return 2

    links = extract_links(html)
    targets = build_targets(links)
    update_historical_coverage(targets)

    manifest = {
        "updatedUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "sourceIndex": SOURCE_INDEX,
        "targetsFound": len(targets),
        "targets": [asdict(t) for t in targets],
    }
    write_json(PUBLIC / "source-target-manifest.json", manifest)
    print(f"CouncilWatch ingestion complete. Targets found: {len(targets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
