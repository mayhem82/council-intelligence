# MAYHEM Compliance Control — Council Minutes and Actions Repository

## Purpose

This repository must operate as a MAYHEM-compliant council-records system.

It is not only a filing system. It is a source-first accountability structure for extracting what was discussed, what was decided, what action was created, what remains unresolved, and how issues branch across time.

## Core Architecture

Meeting first.
Issue paths second.
Actions third.
Outcomes last.

```text
Meeting
  -> Issues Discussed
  -> Decisions Made
  -> Actions Created
  -> Follow-up Evidence
  -> Outcome Status
```

## Core Rule

Every meeting is a primary intake point.
Every issue discussed becomes either:

1. A reference to an existing issue path, or
2. A new issue path.

No issue is allowed to disappear just because it was mentioned once.

## Required Repository Structure

```text
council-records/
├── meetings/
│   └── YYYY-MM-DD/
│       ├── source-register.md
│       ├── issues-discussed.md
│       ├── decisions.md
│       ├── actions.md
│       ├── extraction-log.md
│       └── source-links.md
│
├── issues/
│   └── issue-slug/
│       ├── README.md
│       ├── meeting-references.md
│       ├── chronology.md
│       ├── decisions.md
│       ├── actions.md
│       ├── unresolved-items.md
│       ├── evidence.md
│       └── outputs.md
│
├── actions/
│   ├── open.md
│   ├── overdue.md
│   ├── completed.md
│   └── unresolved.md
│
├── registers/
│   ├── master-meeting-register.md
│   ├── master-issue-register.md
│   ├── master-action-register.md
│   └── master-decision-register.md
│
└── templates/
```

## MAYHEM Compliance Requirements

### 1. Source Primacy

The meeting record is the first authority.

Each extraction must preserve:

- Meeting date
- Document title
- Agenda or minutes status
- Source URL or file path
- Page number or item number where available
- Exact wording where needed
- Extraction date

### 2. Issue Path Creation

When a meeting raises a new topic, a new issue path must be created unless an existing issue path clearly covers it.

Each issue path must keep:

- First appearance
- Later appearances
- Decisions linked to the issue
- Actions linked to the issue
- Unresolved items
- Outcome evidence

### 3. Action Accountability

Any motion, resolution, instruction, report request, promised review, funding referral, consultation promise, or operational task becomes an action entry.

Each action must record:

- Action ID
- Meeting date
- Source item
- Action wording
- Responsible body or role if stated
- Due date if stated
- Follow-up evidence
- Status

Valid action statuses:

- Open
- Completed
- Overdue
- Superseded
- Unresolved
- Not enough evidence

### 4. Fact Separation

The repository must separate:

- Direct source fact
- Extracted interpretation
- User-supplied statement
- Inference
- Assumption
- Unverified claim
- Missing evidence

No finding may mix these categories without labelling them.

### 5. No Allegation Framing

Findings must describe structural behaviour and documented sequence.

Use:

- The record shows
- The decision created
- The action remained unresolved in the available record
- No follow-up evidence has yet been located

Avoid unsupported claims about intent, motive, corruption, bad faith, or personal culpability unless separately proven by direct evidence.

### 6. Proof of Fact Scoring

Where a finding is created, apply:

Proof of Fact (Human plus Evidence) = 1
Verified — evidence confirms compliance and truth.

or

Proof of Fact (Human plus Evidence) = 0
Unverified — fails factual verification, requires independent audit.

Every score must include a short rationale.

### 7. Factual Strength Rationale

Any Factual Strength rating must include a reason.

Minimum fields:

- Source quality
- Directness
- Recency
- Corroboration
- Contradictions
- Missing evidence

### 8. Contradiction Preservation

Contradictions must not be erased or harmonised.

If later records conflict with earlier records, both remain visible and the contradiction is logged.

### 9. Silence Handling

Absence of action may only be treated as evidence when connected to:

- A recorded action
- A deadline
- A statutory duty
- A council resolution
- A promised report
- Repeated notice
- A follow-up request

Silence by itself is not proof.

### 10. Containment Standard

When the repository identifies a structural harm mechanism, it does not speculate.

It names the mechanism, documents how it appears in the record, links source evidence, and makes the pattern visible.

Containment means visibility, not guaranteed remedy.

## Intake Workflow

For every new meeting:

1. Create meeting folder.
2. Add source details.
3. Extract issues discussed.
4. Create or update issue paths.
5. Extract decisions.
6. Extract actions.
7. Add action status.
8. Update master registers.
9. Log unresolved items.
10. Do not create findings until evidence supports them.

## Issue Path Workflow

For every issue:

1. Record first known appearance.
2. Link all meetings where it appears.
3. Track all decisions.
4. Track all actions.
5. Track all claimed outcomes.
6. Preserve unresolved gaps.
7. Produce outputs only after source chain is established.

## Repository Compliance Test

A matter is MAYHEM-compliant only if it can answer:

1. Where did this issue first appear?
2. Which meetings discussed it?
3. What decision was made?
4. What action was created?
5. Who or what body was responsible, if recorded?
6. Was a deadline set?
7. Was completion proven?
8. What evidence supports that answer?
9. What remains unresolved?
10. What has not yet been searched?

If any answer lacks a source path, it remains unverified.
