"""DFAPTI Target Visibility Gate.

Reads dfapti/targets/candidates.json (internal-only, never read by the
public dashboard) and promotes any candidate that has at least one
verified source_evidence entry into a full, public DFAPTI case: a new
case folder under dfapti/cases/, ACCEPTED evidence entries appended to
dfapti/evidence/register.json for each verified source, and the new
case_id added to dfapti/cases/index.json (which is what actually makes it
visible on the dashboard).

Candidates with no verified source_evidence are left untouched — however
high their priority_score. This is the one check DFAPTI's automation does
not skip: see dfapti/rules/factualism-audit.md, "Target Visibility Gate".
"""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "targets" / "candidates.json"
REGISTER = ROOT / "evidence" / "register.json"
CASES_INDEX = ROOT / "cases" / "index.json"
CASES_DIR = ROOT / "cases"
TEMPLATE_HTML = ROOT / "cases" / "_template" / "index.html"
LOG = ROOT / "automation" / "monitor-log.md"


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def source_authority_for_url(url):
    if "asic.gov.au" in url:
        return "ASIC"
    if "accc.gov.au" in url:
        return "ACCC"
    if "apra.gov.au" in url:
        return "APRA"
    if "aer.gov.au" in url:
        return "AER"
    if "fedcourt.gov.au" in url:
        return "Federal Court"
    if "hcourt.gov.au" in url:
        return "High Court"
    if "aph.gov.au" in url:
        return "Australian Parliament"
    if "legislation.gov.au" in url:
        return "Federal Register of Legislation"
    if "anao.gov.au" in url:
        return "ANAO"
    return "Unknown"


def next_evidence_id(register):
    max_number = 0
    for entry in register["entries"]:
        match = re.match(r"E-(\d+)$", entry["evidence_id"])
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number + 1


def next_case_number(cases_index, year):
    prefix = f"DFAPTI-AU-{year}-"
    max_number = 0
    for case_id in cases_index["cases"]:
        if case_id.startswith(prefix):
            try:
                max_number = max(max_number, int(case_id.rsplit("-", 1)[1]))
            except ValueError:
                continue
    if max_number == 0:
        # First auto-promoted case in a year with an existing hand-seeded
        # case still starts past it, so IDs never collide.
        max_number = 198
    return max_number + 1


def slugify(name):
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return slug or "target"


def create_case_files(case_id, candidate, verified_evidence, evidence_ids):
    case_dir = CASES_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    primary_sources = sorted({source_authority_for_url(e["url"]) for e in verified_evidence})

    case_data = {
        "$schema": "../../schemas/case-schema.json",
        "case_id": case_id,
        "title": f"{candidate['name']} — {candidate['issue_category']}",
        "created_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "status": "ACTIVE",
        "category": candidate["issue_category"],
        "jurisdiction": candidate["jurisdiction"],
        "investigation_objective": candidate["public_interest_reason"],
        "scope": "; ".join(candidate["risk_indicators"]),
        "responsible_module": "dfapti",
        "primary_sources": primary_sources,
    }
    save_json(case_dir / "case.json", case_data)

    timeline_data = {
        "case_id": case_id,
        "events": [
            {
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "event": (
                    f"Case auto-created by the Target Visibility Gate, promoted from candidate "
                    f"{candidate['target_id']} ({candidate['name']}). Promotion required at least "
                    f"one independently verified source_evidence entry — see "
                    f"dfapti/rules/factualism-audit.md."
                ),
                "evidence_ids": evidence_ids,
                "status_change": "CANDIDATE -> ACTIVE",
            }
        ],
    }
    save_json(case_dir / "timeline.json", timeline_data)

    keywords_data = {
        "case_id": case_id,
        "source_authorities": primary_sources,
        "terms": [candidate["name"].lower()],
    }
    save_json(case_dir / "keywords.json", keywords_data)

    shutil.copyfile(TEMPLATE_HTML, case_dir / "index.html")


def promote(register, cases_index, candidate, year):
    verified_evidence = [e for e in candidate["source_evidence"] if e.get("verified")]
    if not verified_evidence:
        return None

    case_number = next_case_number(cases_index, year)
    case_id = f"DFAPTI-AU-{year}-{case_number:05d}"

    next_id = next_evidence_id(register)
    evidence_ids = []
    for source in verified_evidence:
        entry = {
            "evidence_id": f"E-{next_id:03d}",
            "case_id": case_id,
            "source_authority": source_authority_for_url(source["url"]),
            "document_title": source.get("title") or candidate["name"],
            "publication_date": None,
            "capture_date": utc_now_iso(),
            "source_url": source["url"],
            "classification": "ACCEPTED",
            "confidence": "HIGH",
            "summary": (
                f"{candidate['name']} is named in this document, fetched and independently "
                f"verified by the DFAPTI target discovery script (dfapti/scripts/discover_targets.py) "
                f"alongside a public-interest indicator: {candidate['public_interest_reason']}"
            ),
            "verification_notes": (
                "Verified by automated direct fetch and document_hash computation "
                "(discover_targets.py, run on the GitHub Actions runner), not by a human. "
                "Meets the ACCEPTED bar (primary source, verified authority, directly supports "
                "the specific claim), but proof_of_fact stays 0 until a human independently "
                "confirms the summary against the document."
            ),
            "document_hash": source.get("document_hash"),
            "proof_of_fact": {
                "score": 0,
                "rationale": "Automated verification (fetch + hash) only; no human has confirmed this yet.",
            },
            "superseded_by": None,
            "recorded_at": utc_now_iso(),
        }
        register["entries"].append(entry)
        evidence_ids.append(entry["evidence_id"])
        next_id += 1

    create_case_files(case_id, candidate, verified_evidence, evidence_ids)

    cases_index["cases"].append(case_id)

    candidate["status"] = "PROMOTED"
    candidate["promoted_case_id"] = case_id
    candidate["last_updated"] = utc_now_iso()

    return case_id, evidence_ids


def main():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    year = datetime.now(timezone.utc).strftime("%Y")

    candidates_register = load_json(CANDIDATES, {"candidates": []})
    register = load_json(REGISTER, {"entries": []})
    cases_index = load_json(CASES_INDEX, {"cases": []})

    promoted = []
    for candidate in candidates_register["candidates"]:
        if candidate["status"] != "CANDIDATE":
            continue
        result = promote(register, cases_index, candidate, year)
        if result:
            case_id, evidence_ids = result
            promoted.append((candidate["target_id"], candidate["name"], case_id, evidence_ids))

    if promoted:
        save_json(REGISTER, register)
        save_json(CASES_INDEX, cases_index)
        save_json(CANDIDATES, candidates_register)

    log_lines = [
        f"\n## Target Promotion Run {run_id}",
        "",
        f"Run time UTC: {utc_now_iso()}",
        f"Candidates promoted: {len(promoted)}",
    ]
    for target_id, name, case_id, evidence_ids in promoted:
        log_lines.append(f"- {target_id} ({name}) -> {case_id}, evidence: {', '.join(evidence_ids)}")

    existing_log = LOG.read_text(encoding="utf-8") if LOG.exists() else "# DFAPTI Monitor Log\n"
    LOG.write_text(existing_log.rstrip() + "\n" + "\n".join(log_lines) + "\n", encoding="utf-8")

    print(f"DFAPTI target promotion complete: {run_id}; promoted={len(promoted)}")


if __name__ == "__main__":
    main()
