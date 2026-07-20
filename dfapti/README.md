# DFAPTI — Deep Forensic All Paths Taken Investigation

⚠ **Private working record.** This module is not intended for public
distribution. Nothing here is submission-grade until independently
verified — see [rules/factualism-audit.md](rules/factualism-audit.md).

## Purpose

DFAPTI is a continuous public-interest investigation engine for Australian
regulatory, court, government and audit-office activity — not a monitor
of one hand-picked case. It has two layers:

1. **Case tracking** (`cases/`, `evidence/`) — the original layer.
   DFAPTI-AU-2026-00198 was the first case, used to prove out the
   evidence/dashboard/Factualism machinery. It is one case among however
   many the target discovery layer below produces, not the whole system.
2. **Target discovery** (`targets/`) — scans approved sources for named
   entities associated with public-interest indicators, scores them, and
   fully automatically promotes verified candidates into new public cases.
   See `targets/README.md` for the pipeline and the **Target Visibility
   Gate**: no candidate's name reaches the public dashboard until at
   least one piece of evidence about it independently clears the same bar
   as `ACCEPTED` — this is the one check the automation never skips.

DFAPTI does not make unsupported allegations — every finding traces to a
primary-source evidence record.

## Layout

- `dashboard/` — dashboard assets (CSS/JS/`case-viewer.js`) shared by
  `index.html` and every case page.
- `cases/<CASE-ID>/` — one folder per case: `case.json` (overview), `timeline.json`,
  `keywords.json` (monitor relevance scope), `index.html` (case viewer, a
  copy of `cases/_template/index.html` — it derives its case ID from the
  URL path, so it never needs per-case editing).
- `cases/_template/` — the generic case-viewer page auto-promoted cases
  are created from.
- `cases/index.json` — the list that actually makes a case public; nothing
  in `cases/<ID>/` is visible on the dashboard until its ID is in here.
- `evidence/register.json` — the append-only evidence register. See
  `schemas/evidence-schema.json`.
- `targets/` — the candidate-target discovery layer. `candidates.json` is
  **internal only**, never read by the public dashboard. See
  `targets/README.md` and the Target Visibility Gate in
  `rules/factualism-audit.md`.
- `sources/` — approved source roots (`source-map.txt`) and the human-readable
  priority source register.
- `rules/factualism-audit.md` — the classification standard (ACCEPTED / HELD /
  REJECTED / PENDING), Proof-of-Fact scoring, and the Target Visibility Gate.
- `reports/` — generated review aids (e.g. unassigned candidate documents).
- `schemas/` — JSON Schemas for case, evidence, and target records.
- `scripts/monitor_sources.py` — the hourly case-evidence monitor. Fetches
  approved source roots, finds candidate documents, hashes and appends new
  evidence as `PENDING`. Also runs a hash-capture pass over existing
  entries that already have a `source_url` but no `document_hash`
  (typically added by an agent-driven search sweep that could verify a
  URL but not fetch raw bytes from a sandboxed session) — since this
  script runs on a GitHub Actions runner with normal internet access, it
  fetches those URLs directly and fills in the SHA-256. That pass only
  ever sets `document_hash` and appends a note to `verification_notes`;
  it never touches classification, summary, or `proof_of_fact`.
- `scripts/discover_targets.py` — the target acquisition layer. Crawls
  source roots for named entities alongside public-interest indicators,
  scores them, and records them in `targets/candidates.json`. Can mark a
  `source_evidence` entry `verified: true` because it runs with real
  internet access and only does so after an actual fetch+hash confirms
  the entity is named in the real document text.
- `scripts/promote_candidates.py` — the Target Visibility Gate. Promotes
  any candidate with at least one verified `source_evidence` entry into a
  new public case (creates `cases/<new-ID>/`, appends `ACCEPTED` evidence,
  adds the ID to `cases/index.json`). Candidates with no verified evidence
  are left untouched, however high their `priority_score`.
- `automation/monitor-log.md` — append-only run log for all of the above.

## Dashboard

Open `index.html` for the live case register, or `cases/<CASE-ID>/index.html`
for a specific case (overview, timeline, filterable evidence register).
These are static pages that `fetch()` the JSON files above — no build step.

## Adding a case

Cases are usually created automatically by `promote_candidates.py`. To add
one by hand:

1. Create `cases/<CASE-ID>/case.json` per `schemas/case-schema.json`.
2. Create `cases/<CASE-ID>/timeline.json` (start with an "opened" event).
3. Create `cases/<CASE-ID>/keywords.json` so the monitor knows which
   discovered documents belong to this case.
4. Copy `cases/_template/index.html` to `cases/<CASE-ID>/index.html` — it
   needs no editing, it derives the case ID from its own URL path.
5. Add the case ID to `cases/index.json`.

## Current case

- **DFAPTI-AU-2026-00198** — ASIC Sustainability Reporting Review. Seeded
  with three evidence entries (E-001–E-003) directly from the case brief.
  These are recorded as `HELD`, not `ACCEPTED`: no source URL has yet been
  independently retrieved and hashed, and under the Factualism Audit Rules
  ACCEPTED requires a verified primary source. Run the monitor or manually
  confirm each item against asic.gov.au to promote them.
