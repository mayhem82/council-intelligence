# Upper Macleay Council Intelligence Repository

This repository contains the Upper Macleay Council Intelligence system.

Primary browser dashboard:

- https://mayhem82.github.io/council-intelligence/

GitHub repository dashboard file:

- [index.html](index.html)

Primary evidence entry point:

- [INTELLIGENCE-HOME.md](upper-macleay-council-intelligence/INTELLIGENCE-HOME.md)

Primary Markdown dashboard:

- [DASHBOARD.md](upper-macleay-council-intelligence/DASHBOARD.md)

## GitHub Pages

The static dashboard is deployed by:

- [.github/workflows/pages.yml](.github/workflows/pages.yml)

Use this repo setting:

Settings -> Pages -> Build and deployment -> Source: GitHub Actions

On the current GitHub mobile screen, that means use the Static HTML option only if GitHub asks you to configure a workflow. This repository already contains the workflow, so a push to `main` can deploy the page.

## Purpose

The system collects, preserves, extracts, analyses and organises public Kempsey Shire Council records into issue, action, decision, actor, mechanism, matter and outcome pathways.

The operational architecture is:

Source Map
↓
Historic and Current Fetch
↓
Raw Record Preservation
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
Matter Heat Mapping
↓
Duplicate Detection
↓
Evidence Chain Audit
↓
Dashboard

## Verification Warning

Proof of Fact (Human plus Evidence): 0

Meaning: Unverified - automated outputs require independent source review before use as evidence, complaint material, or submission-grade findings.

Factual Strength: Medium

Rationale: The repository contains source-preservation and audit structures, but factual strength depends on successful record harvesting and manual review against preserved source records.

## Main Navigation

- [Browser Dashboard](index.html)
- [Dashboard Data](public/council-dashboard-data.json)
- [Intelligence Home](upper-macleay-council-intelligence/INTELLIGENCE-HOME.md)
- [Dashboard](upper-macleay-council-intelligence/DASHBOARD.md)
- [Source Map](upper-macleay-council-intelligence/config/source-map.txt)
- [Fetched Source Index](upper-macleay-council-intelligence/registers/fetched-source-index.md)
- [Matter Lifecycle](upper-macleay-council-intelligence/reports/matter-lifecycle.md)
- [Matter Evolution Summary](upper-macleay-council-intelligence/reports/matter-evolution-summary.md)
- [Resolution Detection](upper-macleay-council-intelligence/reports/resolution-detection.md)
- [Matter Heatmap](upper-macleay-council-intelligence/reports/matter-heatmap.md)
- [Duplicate Source Report](upper-macleay-council-intelligence/reports/duplicate-source-report.md)
- [Evidence Chain Audit](upper-macleay-council-intelligence/reports/evidence-chain-audit.md)

## Registers

- [Master Meeting Register](upper-macleay-council-intelligence/registers/master-meeting-register.md)
- [Master Source Register](upper-macleay-council-intelligence/registers/master-source-register.md)
- [Master Issue Register](upper-macleay-council-intelligence/registers/master-issue-register.md)
- [Master Action Register](upper-macleay-council-intelligence/registers/master-action-register.md)
- [Master Decision Register](upper-macleay-council-intelligence/registers/master-decision-register.md)
- [Master Actor Register](upper-macleay-council-intelligence/registers/master-actor-register.md)
- [Master Mechanism Register](upper-macleay-council-intelligence/registers/master-mechanism-register.md)

## Matter Files

Matter chronologies are stored under:

- [matters/](upper-macleay-council-intelligence/matters/)

Each matter folder may contain a `chronology.md` file sorted from oldest to newest.

## Automation

The active GitHub workflows are:

- [.github/workflows/pages.yml](.github/workflows/pages.yml)
- [.github/workflows/council-records-fetch.yml](.github/workflows/council-records-fetch.yml)

Core scripts:

- `upper-macleay-council-intelligence/scripts/fetch_council_records.py`
- `upper-macleay-council-intelligence/scripts/backfill_historic_records.py`
- `upper-macleay-council-intelligence/scripts/extract_pdf_text.py`
- `upper-macleay-council-intelligence/scripts/analyze_council_records.py`
- `upper-macleay-council-intelligence/scripts/link_matters.py`
- `upper-macleay-council-intelligence/scripts/build_lifecycle.py`
- `upper-macleay-council-intelligence/scripts/sort_historically.py`
- `upper-macleay-council-intelligence/scripts/audit_evidence_chain.py`

## Operating Rules

1. Source records outrank derived summaries.
2. Automated classifications are not findings.
3. Historical ordering is mandatory.
4. Duplicate reports are review aids, not deletion instructions.
5. Resolution labels are candidates until reviewed against source documents.
6. All automated outputs remain Proof of Fact (Human plus Evidence): 0 unless independently verified.

## Current Priority

The system architecture is now established. The highest-value work is increasing historic record coverage so matter histories become complete across 2022, 2023, 2024, 2025 and 2026.
