# DFAPTI Factualism Audit Rules

## Purpose

Every DFAPTI finding must be traceable to primary-source evidence. DFAPTI does
not make unsupported allegations. This document is the classification
standard applied to every evidence register entry.

## Classifications

### ACCEPTED

Requirements (all must hold):

- The record is a primary source (the regulator, court, department, or audit
  office's own published document — not a secondary report about it).
- The source authority has been verified (correct domain, correct issuing
  body).
- The evidence directly supports the specific statement it is attached to,
  with no interpretive leap required.

### HELD

Requirements:

- Relevant information exists and has been captured.
- Verification is incomplete — for example, the source URL has not yet been
  independently confirmed, the document has not yet been hashed, or
  corroboration is still pending.
- HELD entries may be promoted to ACCEPTED once verification completes, or
  moved to REJECTED if verification fails. The original HELD record is never
  deleted or edited in place — a new entry is appended and the old one is
  marked `superseded_by`.

### REJECTED

Examples:

- Unsupported claims with no underlying document.
- Opinion presented without evidence.
- Secondary reporting (news coverage, commentary) without primary-source
  confirmation.
- Evidence contradicted by a later or higher-authority primary source.

### PENDING

- Automated discovery has surfaced a candidate document, but it has not yet
  been reviewed against any of the above criteria.

## Proof of Fact (Human plus Evidence)

Distinct from classification. Scored per entry:

- **1 — Verified**: a human has independently checked the source_url,
  confirmed the document_hash, and confirmed the summary accurately reflects
  the primary document.
- **0 — Unverified**: default for every automated or newly-seeded entry.
  Requires independent review before the entry is cited as submission-grade
  evidence.

Every score carries a short rationale.

## No Allegation Framing

Findings describe what the record shows, not motive or intent:

- "The record shows..."
- "The published document states..."
- "No corroborating primary source has yet been located."

Avoid language implying wrongdoing, bad faith, or culpability unless a
primary source directly and explicitly supports that specific characterization.

## Append-Only Discipline

- Evidence records are never deleted.
- Corrections and updates are new entries that reference the prior
  `evidence_id` via `superseded_by`.
- Every entry is timestamped at capture and at register append time.
- Document hashes (SHA-256) are recorded wherever the source document was
  actually fetched. A missing hash means the document has not yet been
  independently captured — it does not mean the finding is false.

## Target Visibility Gate

Applies to `dfapti/targets/` (the candidate-target discovery layer, see
`dfapti/targets/README.md` for the full pipeline). A candidate entity's
name is never published anywhere the public dashboard reads — not as a
case, not in `cases/index.json`, not in `evidence/register.json` — until
at least one piece of evidence about it independently clears the same bar
as ACCEPTED above: a real primary source, a verified issuing authority,
and a finding that directly supports the specific claim, not merely a
keyword or name match. Discovery, scoring, and promotion are otherwise
fully automatic — this is the one check that is never skipped, because
publishing an unverified match against a real, named entity is exactly
the unsupported-allegation risk this document exists to prevent.

## Duplicate Handling

Before appending a new entry, the source_url (and, where available, the
document_hash) is checked against existing register entries. Matches are
skipped rather than re-appended.
