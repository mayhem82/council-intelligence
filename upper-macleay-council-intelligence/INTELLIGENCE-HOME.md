# Upper Macleay Council Intelligence Home

Purpose: provide a single entry point for the council intelligence repository.

PF(H,E): 0 — repository outputs are automated unless independently reviewed against source records.

## Current Use

Start here before reading individual registers or matter files.

This file points to the active dashboard, source map, evidence registers, matter chronologies, audit reports and automation scripts.

## Primary Dashboard

- DASHBOARD.md

## Source Acquisition

- config/source-map.txt
- automation/source-targets.md
- automation/fetch-log.md
- automation/backfill-log.md
- registers/fetched-source-index.md
- registers/master-source-register.md
- registers/historic-backfill-source-register.md

## Preserved Records

- fetched/raw/
- fetched/text/

Raw records are preserved before analysis. Extracted PDF text is stored separately so analysis can work from readable text while the source file remains intact.

## Intelligence Reports

- reports/latest-intelligence-summary.md
- reports/matter-lifecycle.md
- reports/matter-evolution-summary.md
- reports/resolution-detection.md
- reports/matter-heatmap.md
- reports/duplicate-source-report.md
- reports/evidence-chain-audit.md
- reports/cross-meeting-linkage.md

## Registers

- registers/master-meeting-register.md
- registers/master-issue-register.md
- registers/master-action-register.md
- registers/master-decision-register.md
- registers/master-actor-register.md
- registers/master-mechanism-register.md

## Matter Files

- matters/

Each matter folder may contain a chronology.md file showing oldest-to-newest evolution.

## Core Matter Examples

- matters/flying-fox-camp/chronology.md
- matters/roads/chronology.md
- matters/bridges/chronology.md
- matters/water-security/chronology.md
- matters/grants-funding/chronology.md
- matters/public-health-safety/chronology.md
- matters/community-facilities/chronology.md
- matters/governance/chronology.md

## Automation Scripts

- scripts/fetch_council_records.py
- scripts/backfill_historic_records.py
- scripts/extract_pdf_text.py
- scripts/analyze_council_records.py
- scripts/link_matters.py
- scripts/build_matter_evolution.py
- scripts/build_lifecycle.py
- scripts/sort_historically.py
- scripts/audit_evidence_chain.py

## Interpretation Rules

1. Source records outrank derived summaries.
2. Automated classifications are not findings.
3. PF(H,E): 0 means unverified automated output requiring source review.
4. Matter status labels such as resolved-candidate, deferred-candidate or funding-candidate are signals only.
5. Duplicates must be reviewed before deletion or consolidation.
6. Historical ordering is mandatory: oldest records before newest records.

## Current Intelligence Flow

Source Map
↓
Historic and Current Fetch
↓
Raw Preservation
↓
PDF Text Extraction
↓
Issue, Action, Decision, Actor and Mechanism Detection
↓
Matter Linkage
↓
Matter Evolution
↓
Resolution Candidate Detection
↓
Heat Mapping
↓
Duplicate Detection
↓
Evidence Chain Audit
↓
Dashboard

## Known Weaknesses

- Historic data depth depends on successful fetch and backfill runs.
- Some source-map targets may redirect, fail, or move.
- Automated date inference can be wrong when filenames omit full dates.
- PDF extraction quality depends on readable embedded text.
- No automated output should be treated as submission-grade without source review.

## Operational Priority

The current priority is not adding more labels. The priority is increasing historic record coverage and preserving enough council records to let matter histories become complete.
