# DFAPTI — Deep Forensic All Paths Taken Investigation

⚠ **Private working record.** This module is not intended for public
distribution. Nothing here is submission-grade until independently
verified — see [rules/factualism-audit.md](rules/factualism-audit.md).

## Purpose

Continuous public-interest investigation and evidence management for
Australian regulatory, court, government and audit-office activity.
DFAPTI does not make unsupported allegations — every finding traces to a
primary-source evidence record.

## Layout

- `dashboard/` — dashboard assets (CSS/JS) shared by `index.html` and case pages.
- `cases/<CASE-ID>/` — one folder per case: `case.json` (overview), `timeline.json`,
  `keywords.json` (monitor relevance scope), `index.html` (case viewer).
- `evidence/register.json` — the append-only evidence register. See
  `schemas/evidence-schema.json`.
- `sources/` — approved source roots (`source-map.txt`) and the human-readable
  priority source register.
- `rules/factualism-audit.md` — the classification standard (ACCEPTED / HELD /
  REJECTED / PENDING) and Proof-of-Fact scoring.
- `reports/` — generated review aids (e.g. unassigned candidate documents).
- `schemas/` — JSON Schemas for case and evidence records.
- `scripts/monitor_sources.py` — the hourly monitor. Fetches approved source
  roots, finds candidate documents, hashes and appends new evidence as
  `PENDING`. It also runs a hash-capture pass over existing entries that
  already have a `source_url` but no `document_hash` (typically added by an
  agent-driven search sweep that could verify a URL but not fetch raw bytes
  from a sandboxed session) — since this script runs on a GitHub Actions
  runner with normal internet access, it fetches those URLs directly and
  fills in the SHA-256. That pass only ever sets `document_hash` and appends
  a note to `verification_notes`; it never touches classification, summary,
  or `proof_of_fact`. It never edits or deletes existing entries otherwise.
- `automation/monitor-log.md` — append-only run log.

## Dashboard

Open `index.html` for the live case register, or `cases/<CASE-ID>/index.html`
for a specific case (overview, timeline, filterable evidence register).
These are static pages that `fetch()` the JSON files above — no build step.

## Adding a case

1. Create `cases/<CASE-ID>/case.json` per `schemas/case-schema.json`.
2. Create `cases/<CASE-ID>/timeline.json` (start with an "opened" event).
3. Create `cases/<CASE-ID>/keywords.json` so the monitor knows which
   discovered documents belong to this case.
4. Create `cases/<CASE-ID>/index.html` (copy an existing case page and
   update the `CASE_ID` constant).
5. Add the case ID to `cases/index.json`.

## Current case

- **DFAPTI-AU-2026-00198** — ASIC Sustainability Reporting Review. Seeded
  with three evidence entries (E-001–E-003) directly from the case brief.
  These are recorded as `HELD`, not `ACCEPTED`: no source URL has yet been
  independently retrieved and hashed, and under the Factualism Audit Rules
  ACCEPTED requires a verified primary source. Run the monitor or manually
  confirm each item against asic.gov.au to promote them.
