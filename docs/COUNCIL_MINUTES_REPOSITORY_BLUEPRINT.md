# Council Minutes Repository Blueprint

## Purpose

Create a structured repository for collecting, preserving, indexing, and auditing council minutes, agendas, attachments, notices of motion, correspondence, and related public records.

This repository is not just storage. It is an evidence system for tracking what council knew, when it knew it, what decisions were made, what actions were promised, and what remains unresolved.

## Core Function

The repository should support:

1. Source preservation
2. Chronology building
3. Decision tracking
4. Promise-to-action comparison
5. Evidence extraction
6. Issue mapping
7. Public accountability reporting
8. Complaint and escalation preparation

## Repository Structure

```text
council-minutes-repository/
├── README.md
├── SOURCES_REGISTER.md
├── SEARCH_REGISTER.md
├── EVIDENCE_REGISTER.md
├── DECISION_REGISTER.md
├── ISSUE_MAP.md
├── TIMELINE.md
├── councils/
│   └── kempsey-shire-council/
│       ├── minutes/
│       ├── agendas/
│       ├── attachments/
│       ├── correspondence/
│       ├── media-releases/
│       └── extracted-findings/
├── matters/
│   └── bellbrook-flying-fox/
│       ├── evidence/
│       ├── chronology/
│       ├── council-actions/
│       ├── unresolved-items/
│       └── draft-outputs/
└── templates/
    ├── evidence-entry-template.md
    ├── decision-entry-template.md
    ├── meeting-minutes-summary-template.md
    └── search-register-template.md
```

## Required Registers

### 1. Sources Register

Tracks each source location checked.

Fields:

- Source ID
- Council or authority
- Page title
- URL
- Date accessed
- Source type
- Coverage period
- Notes

### 2. Search Register

Records what was searched before conclusions are drawn.

Fields:

- Search ID
- Search date and time
- Search terms used
- Source group checked
- Items found
- Items excluded
- Exclusion reasons
- Accepted count
- Rejected count

### 3. Evidence Register

Tracks every extracted evidence item.

Fields:

- Evidence ID
- Source document
- Meeting date
- Page or item reference
- Extracted fact
- Direct quote if available
- Relevance
- Reliability
- Open questions

### 4. Decision Register

Tracks formal council action.

Fields:

- Decision ID
- Meeting date
- Motion or resolution
- Mover and seconder if available
- Decision outcome
- Required action
- Responsible party
- Due date
- Follow-up evidence
- Status

### 5. Issue Map

Groups repeated issues across documents.

Initial categories:

- Flying-fox camp management
- Public health and amenity
- Playground and public space impact
- Tree damage and canopy condition
- Grant funding and budget handling
- Council response delay
- Community consultation
- Risk management
- State agency involvement
- Unresolved action items

## Bellbrook Flying-Fox Matter

Initial matter folder:

`matters/bellbrook-flying-fox/`

Purpose:

Track all public-record evidence relevant to the Bellbrook flying-fox camp, including council awareness, community reports, meeting decisions, policy references, grant pathways, and unresolved actions.

## Governance Rules

### No Conclusion Before Search Register

Every audit must begin with a Search Register entry.

### Evidence Before Claim

No finding should be recorded unless it links back to a source document, meeting item, correspondence record, or public statement.

### Preserve Exclusions

Excluded items must still be logged with reasons.

### Chronology Preservation

Events must be recorded in date order. Later documents must not rewrite earlier facts without noting the contradiction.

### Silence Handling

Silence or absence of action may only be treated as evidence when tied to a known duty, deadline, resolution, correspondence trail, or repeated notice.

### Separation of Record Types

Keep these separate:

- Council minutes
- Agendas
- Attachments
- Staff reports
- Public statements
- Media reporting
- Community testimony
- State policy
- Legal or regulatory material

## First Build Target

Create the repository as a clean evidence framework before adding automation.

First files to create:

1. `README.md`
2. `SOURCES_REGISTER.md`
3. `SEARCH_REGISTER.md`
4. `EVIDENCE_REGISTER.md`
5. `DECISION_REGISTER.md`
6. `ISSUE_MAP.md`
7. `TIMELINE.md`
8. `templates/evidence-entry-template.md`
9. `templates/decision-entry-template.md`
10. `matters/bellbrook-flying-fox/README.md`

## Future Automation Target

Later automation can:

- Download new council minutes when published
- Extract meeting dates and agenda item numbers
- Search for recurring terms
- Flag repeated unresolved items
- Generate plain-text audit summaries
- Produce complaint-ready evidence bundles

## Initial Search Terms

Start with:

- Bellbrook
- flying-fox
- flying fox
- bat
- camp management
- public health
- playground
- tree damage
- canopy
- community meeting
- notice of motion
- grant
- environmental management
- Kempsey Shire Council
