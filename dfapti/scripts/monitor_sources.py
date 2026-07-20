"""DFAPTI hourly source monitor.

Crawls the approved source roots (dfapti/sources/source-map.txt), looks for
candidate primary-source documents relevant to open cases, checks for
duplicates against the existing evidence register, and appends new PENDING
evidence entries. It never edits or deletes an existing register entry.

Automated discovery can only ever produce PENDING evidence — promotion to
ACCEPTED/HELD/REJECTED under the Factualism Audit Rules requires human
review (see dfapti/rules/factualism-audit.md).
"""

import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_MAP = ROOT / "sources" / "source-map.txt"
REGISTER = ROOT / "evidence" / "register.json"
CASES_INDEX = ROOT / "cases" / "index.json"
LOG = ROOT / "automation" / "monitor-log.md"
UNASSIGNED_REPORT = ROOT / "reports" / "unassigned-candidates.md"

DOCUMENT_WORDS = [
    "media-release", "media release", "judgment", "judgement", "report",
    "inquiry", "bill", "hansard", "determination", "decision", "guidance",
    "consultation", "media centre", "news",
]

USER_AGENT = "DFAPTI-Monitor/1.0 (+https://mayhem82.github.io/council-intelligence/dfapti/)"


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_source_roots():
    roots = []
    if not SOURCE_MAP.exists():
        return roots
    for line in SOURCE_MAP.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            roots.append(line)
    return roots


def load_cases():
    if not CASES_INDEX.exists():
        return []
    case_ids = json.loads(CASES_INDEX.read_text(encoding="utf-8"))["cases"]
    cases = []
    for case_id in case_ids:
        keywords_path = ROOT / "cases" / case_id / "keywords.json"
        if keywords_path.exists():
            cases.append(json.loads(keywords_path.read_text(encoding="utf-8")))
    return cases


def load_register():
    return json.loads(REGISTER.read_text(encoding="utf-8"))


def save_register(register):
    REGISTER.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.geturl(), response.headers.get("Content-Type", "unknown"), response.read()


def looks_like_document(url, label=""):
    lower = (url + " " + label).lower()
    return any(word in lower for word in DOCUMENT_WORDS)


def extract_candidate_links(base_url, html_text):
    candidates = set()
    for href, label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html_text, flags=re.I | re.S):
        label_clean = re.sub(r"<[^>]+>", " ", label)
        label_clean = re.sub(r"\s+", " ", label_clean).strip()
        url = urllib.parse.urljoin(base_url, href.strip())
        if looks_like_document(url, label_clean):
            candidates.add((url, label_clean))
    return candidates


def match_case(url, label, cases):
    lower = (url + " " + label).lower()
    for case in cases:
        for term in case["terms"]:
            if term.lower() in lower:
                return case["case_id"], term
    return None, None


def next_evidence_id(register):
    max_number = 0
    for entry in register["entries"]:
        match = re.match(r"E-(\d+)$", entry["evidence_id"])
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number + 1


def already_known(register, url):
    return any(entry.get("source_url") == url for entry in register["entries"])


def append_pending_entry(register, case_id, source_authority, url, label, document_hash, next_id):
    now = utc_now_iso()
    entry = {
        "evidence_id": f"E-{next_id:03d}",
        "case_id": case_id,
        "source_authority": source_authority,
        "document_title": label or url,
        "publication_date": None,
        "capture_date": now,
        "source_url": url,
        "classification": "PENDING",
        "confidence": "LOW",
        "summary": f"Automatically discovered candidate document at {url}. Not yet reviewed against Factualism Audit Rules.",
        "verification_notes": "Automated discovery only. Requires human review to classify as ACCEPTED, HELD, or REJECTED.",
        "document_hash": document_hash,
        "proof_of_fact": {
            "score": 0,
            "rationale": "Unverified — automated discovery, pending human review.",
        },
        "superseded_by": None,
        "recorded_at": now,
    }
    register["entries"].append(entry)
    return entry


def source_authority_for_root(root_url):
    if "asic.gov.au" in root_url:
        return "ASIC"
    if "accc.gov.au" in root_url:
        return "ACCC"
    if "apra.gov.au" in root_url:
        return "APRA"
    if "aer.gov.au" in root_url:
        return "AER"
    if "fedcourt.gov.au" in root_url:
        return "Federal Court"
    if "hcourt.gov.au" in root_url:
        return "High Court"
    if "aph.gov.au" in root_url:
        return "Australian Parliament"
    if "legislation.gov.au" in root_url:
        return "Federal Register of Legislation"
    if "anao.gov.au" in root_url:
        return "ANAO"
    return "Unknown"


def main():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    UNASSIGNED_REPORT.parent.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    roots = load_source_roots()
    cases = load_cases()
    register = load_register()

    checked = []
    failures = []
    appended = []
    unassigned = []

    next_id = next_evidence_id(register)

    for root_url in roots:
        try:
            final_url, content_type, body = fetch(root_url)
            checked.append((root_url, final_url, content_type))
        except (urllib.error.URLError, OSError) as error:
            failures.append((root_url, str(error)))
            continue

        if "html" not in content_type.lower():
            continue

        text = body.decode("utf-8", errors="ignore")
        source_authority = source_authority_for_root(root_url)

        for url, label in extract_candidate_links(final_url, text):
            if already_known(register, url):
                continue
            case_id, matched_term = match_case(url, label, cases)
            if case_id is None:
                unassigned.append((source_authority, url, label))
                continue
            try:
                _, _, doc_body = fetch(url)
                document_hash = hashlib.sha256(doc_body).hexdigest()
            except (urllib.error.URLError, OSError):
                document_hash = None
            entry = append_pending_entry(
                register, case_id, source_authority, url, label, document_hash, next_id
            )
            next_id += 1
            appended.append(entry)

    if appended:
        save_register(register)

    log_lines = [
        f"\n## Monitor Run {run_id}",
        "",
        f"Run time UTC: {utc_now_iso()}",
        f"Source roots checked: {len(checked)}",
        f"Cases loaded: {len(cases)}",
        f"New PENDING evidence appended: {len(appended)}",
        f"Unassigned candidates (no matching open case): {len(unassigned)}",
        f"Fetch failures: {len(failures)}",
        "",
        "### Checked Roots",
    ]
    for original, final_url, content_type in checked:
        log_lines.append(f"- {original} -> {final_url} ({content_type})")
    log_lines.append("")
    log_lines.append("### Appended Evidence")
    for entry in appended:
        log_lines.append(f"- {entry['evidence_id']} ({entry['case_id']}): {entry['source_url']}")
    log_lines.append("")
    log_lines.append("### Failures")
    for url, error in failures:
        log_lines.append(f"- {url}: {error}")

    existing_log = LOG.read_text(encoding="utf-8") if LOG.exists() else "# DFAPTI Monitor Log\n"
    LOG.write_text(existing_log.rstrip() + "\n" + "\n".join(log_lines) + "\n", encoding="utf-8")

    if unassigned:
        report_lines = [f"\n## Unassigned Candidates — Run {run_id}", ""]
        for source_authority, url, label in unassigned:
            report_lines.append(f"- [{source_authority}] {label or '(no label)'} — {url}")
        existing_report = (
            UNASSIGNED_REPORT.read_text(encoding="utf-8")
            if UNASSIGNED_REPORT.exists()
            else "# DFAPTI Unassigned Candidates\n\nCandidate documents discovered by the monitor that did not match any open case's keyword scope. Review and either open a new case or extend an existing case's keywords.json.\n"
        )
        UNASSIGNED_REPORT.write_text(
            existing_report.rstrip() + "\n" + "\n".join(report_lines) + "\n", encoding="utf-8"
        )

    print(
        f"DFAPTI monitor run complete: {run_id}; "
        f"roots={len(checked)} appended={len(appended)} "
        f"unassigned={len(unassigned)} failures={len(failures)}"
    )


if __name__ == "__main__":
    main()
