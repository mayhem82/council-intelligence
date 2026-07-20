# DFAPTI Target Discovery

## What this is

DFAPTI is not only a monitor of hand-picked cases. It also runs a target
acquisition layer: scanning approved Australian regulator, court,
government and audit sources for entities that may warrant investigation,
scoring them by public-interest category, and — fully automatically, no
manual approval step — promoting verified candidates into public DFAPTI
cases.

`DFAPTI-AU-2026-00198` (ASIC Sustainability Reporting Review) was the
first case, used to prove out the evidence/dashboard/Factualism machinery.
It is one case among however many this layer produces, not the whole of
DFAPTI.

## Pipeline

```text
Source monitoring
  -> Candidate extraction        (dfapti/scripts/discover_targets.py)
  -> Candidate scoring           (priority_score, dfapti/targets/schema.json)
  -> Target Visibility Gate      (dfapti/scripts/promote_candidates.py)
  -> Create DFAPTI case          (public, only past the gate)
  -> Evidence collection
  -> Factualism audit
  -> Findings dashboard
```

## The Target Visibility Gate

This is the one manual-approval step DFAPTI does *not* skip, and it is not
optional: **a candidate's name is never published — not on the dashboard,
not as a case, not anywhere in `dfapti/` that the public site reads —
until at least one `source_evidence` entry for it is independently
verified** to the same bar `evidence-schema.json` requires for
`ACCEPTED`: a real primary source, a verified issuing authority, and a
finding that directly supports the specific claim recorded, not just a
keyword or name match.

Practically:

- `dfapti/targets/candidates.json` is **not** referenced by
  `dfapti/index.html` or any case page. Nothing reads it publicly.
- `discover_targets.py` (crawling, on the GitHub Actions runner) and an
  agent-driven sweep (WebSearch cross-reference, in a Claude session) can
  both add candidates and can both mark a `source_evidence` entry
  `verified: true` — but only after doing the actual verification work,
  the same discipline already applied to E-001–E-013 in the evidence
  register. A bare keyword match is never enough to set `verified: true`.
- `promote_candidates.py` only promotes a candidate — creating a public
  case folder, adding it to `cases/index.json`, and appending its
  evidence to `dfapti/evidence/register.json` as `ACCEPTED` — once it has
  at least one verified `source_evidence` entry. Everything else stays a
  private, unpublished candidate indefinitely, however high its
  `priority_score`.
- This is why "fully automatic" and "no unsupported public naming" are
  both true at once: the automation never pauses for a human click, but
  it also never publishes an entity based only on an automated score.

## Scoring

`priority_score` is a simple weighted count of which public-interest
categories a candidate's source material matches (see
`dfapti/scripts/discover_targets.py` for the keyword lists), weighted
toward the categories listed first in the original spec: regulatory
action, public money, public safety, environmental impact, consumer harm,
government accountability, systemic failures. It is a triage aid for
where to look next, not evidence of anything about the entity itself.

## Rejecting a candidate

Set `status: "REJECTED"` and fill `rejection_reason` — for example, a name
collision, a candidate that turns out to be the complainant rather than
the entity of interest, or a match on a term used in an unrelated context.
Rejected candidates are kept (not deleted) for auditability, same
append-only discipline as the evidence register.
