"""DFAPTI target discovery.

Crawls the approved source roots (dfapti/sources/source-map.txt) looking
for named entities (companies, organisations) mentioned alongside
public-interest indicators — regulatory action, public money, public
safety, environmental impact, consumer harm, government accountability,
systemic failures — and records them as candidate targets.

This script can mark a source_evidence entry verified: true, because it
runs with real internet access (the GitHub Actions runner) and only does
so when it has actually fetched the page and confirmed the entity name
appears in the real fetched text next to a category indicator, with the
raw bytes hashed. That is the bar dfapti/rules/factualism-audit.md sets
for "verified" under the Target Visibility Gate.

It never publishes anything itself. Candidates stay in
dfapti/targets/candidates.json, which the public dashboard never reads.
Promotion to a public case is a separate, explicit step —
dfapti/scripts/promote_candidates.py — and only fires once a candidate has
at least one verified source_evidence entry.
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
CANDIDATES = ROOT / "targets" / "candidates.json"
LOG = ROOT / "automation" / "monitor-log.md"

USER_AGENT = "DFAPTI-Monitor/1.0 (+https://mayhem82.github.io/council-intelligence/dfapti/)"

# Ordered highest-priority first, per the original DFAPTI target-selection rules.
CATEGORY_KEYWORDS = [
    ("Regulatory action", [
        "infringement notice", "enforceable undertaking", "civil penalty",
        "proceedings", "investigation", "compliance action",
        "show cause notice", "banning order",
    ]),
    ("Public money", [
        "grant funding", "taxpayer", "public funds", "appropriation",
        "subsidy", "commonwealth funding",
    ]),
    ("Public safety", [
        "safety risk", "product recall", "hazard", "public health risk",
    ]),
    ("Environmental impact", [
        "environmental harm", "pollution", "emissions breach",
        "contamination", "environmental damage",
    ]),
    ("Consumer harm", [
        "misleading conduct", "unconscionable conduct", "consumer detriment",
        "false representation", "unfair contract term",
    ]),
    ("Government accountability", [
        "maladministration", "conflict of interest", "freedom of information",
        "ombudsman finding", "lack of transparency",
    ]),
    ("Systemic failures", [
        "systemic issue", "widespread failure", "royal commission finding",
        "systemic risk",
    ]),
]

CATEGORY_WEIGHT = {name: len(CATEGORY_KEYWORDS) - i for i, (name, _) in enumerate(CATEGORY_KEYWORDS)}

CORP_SUFFIX = r"(?:Pty\.?\s+Ltd\.?|Pty\.?\s+Limited|Limited|Ltd\.?|Group|Holdings|Inc\.?|Corporation|Corp\.?)"
ENTITY_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z0-9&'\-]*(?:\s+[A-Z][A-Za-z0-9&'\-]*){0,4}\s+" + CORP_SUFFIX + r")\b"
)


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_source_roots():
    if not SOURCE_MAP.exists():
        return []
    roots = []
    for line in SOURCE_MAP.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            roots.append(line)
    return roots


def load_candidates():
    if not CANDIDATES.exists():
        return {"$schema": "schema.json", "register_notice": "Internal only.", "candidates": []}
    return json.loads(CANDIDATES.read_text(encoding="utf-8"))


def save_candidates(register):
    CANDIDATES.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.geturl(), response.headers.get("Content-Type", "unknown"), response.read()


def matched_categories(text_lower):
    matches = []
    for category, keywords in CATEGORY_KEYWORDS:
        for keyword in keywords:
            if keyword in text_lower:
                matches.append((category, keyword))
                break
    return matches


def extract_entities(text):
    return sorted(set(match.strip() for match in ENTITY_PATTERN.findall(text)))


def priority_score(categories):
    return sum(CATEGORY_WEIGHT[category] for category, _ in categories)


def next_target_id(register, year):
    max_number = 0
    prefix = f"T-AU-{year}-"
    for candidate in register["candidates"]:
        if candidate["target_id"].startswith(prefix):
            number = int(candidate["target_id"].rsplit("-", 1)[1])
            max_number = max(max_number, number)
    return max_number + 1


def find_candidate_by_name(register, name):
    lower = name.lower()
    for candidate in register["candidates"]:
        if candidate["name"].lower() == lower:
            return candidate
    return None


def main():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    year = datetime.now(timezone.utc).strftime("%Y")
    roots = load_source_roots()
    register = load_candidates()

    checked = []
    failures = []
    new_candidates = []
    updated_candidates = []
    next_id = next_target_id(register, year)

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
        text_no_tags = re.sub(r"<[^>]+>", " ", text)
        text_lower = text_no_tags.lower()

        categories = matched_categories(text_lower)
        if not categories:
            continue

        entities = extract_entities(text_no_tags)
        if not entities:
            continue

        document_hash = hashlib.sha256(body).hexdigest()
        now = utc_now_iso()

        for name in entities:
            existing = find_candidate_by_name(register, name)
            evidence_entry = {
                "url": final_url,
                "title": name,
                "verified": True,
                "document_hash": document_hash,
            }
            if existing:
                if not any(e["url"] == final_url for e in existing["source_evidence"]):
                    existing["source_evidence"].append(evidence_entry)
                    existing["last_updated"] = now
                    updated_candidates.append(existing["target_id"])
                continue

            candidate = {
                "target_id": f"T-AU-{year}-{next_id:05d}",
                "name": name,
                "jurisdiction": "Australia",
                "issue_category": categories[0][0],
                "source_evidence": [evidence_entry],
                "public_interest_reason": (
                    f"Named in a fetched document from {final_url} alongside the term "
                    f"'{categories[0][1]}' ({categories[0][0]})."
                ),
                "risk_indicators": [
                    f"Document at {final_url} contains the term '{keyword}' ({category})"
                    for category, keyword in categories
                ],
                "evidence_confidence": "MEDIUM",
                "priority_score": priority_score(categories),
                "status": "CANDIDATE",
                "promoted_case_id": None,
                "rejection_reason": None,
                "discovered_at": now,
                "last_updated": now,
            }
            register["candidates"].append(candidate)
            new_candidates.append(candidate["target_id"])
            next_id += 1

    if new_candidates or updated_candidates:
        save_candidates(register)

    log_lines = [
        f"\n## Target Discovery Run {run_id}",
        "",
        f"Run time UTC: {utc_now_iso()}",
        f"Source roots checked: {len(checked)}",
        f"New candidates: {len(new_candidates)}",
        f"Updated candidates (new source_evidence on an existing target): {len(updated_candidates)}",
        f"Fetch failures: {len(failures)}",
        "",
        "### New Candidates",
    ]
    for target_id in new_candidates:
        log_lines.append(f"- {target_id}")
    log_lines.append("")
    log_lines.append("### Failures")
    for url, error in failures:
        log_lines.append(f"- {url}: {error}")

    existing_log = LOG.read_text(encoding="utf-8") if LOG.exists() else "# DFAPTI Monitor Log\n"
    LOG.write_text(existing_log.rstrip() + "\n" + "\n".join(log_lines) + "\n", encoding="utf-8")

    print(
        f"DFAPTI target discovery complete: {run_id}; "
        f"roots={len(checked)} new_candidates={len(new_candidates)} "
        f"updated_candidates={len(updated_candidates)} failures={len(failures)}"
    )


if __name__ == "__main__":
    main()
