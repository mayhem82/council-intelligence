# Automated Fetch Pipeline

## Purpose

This repository must automatically fetch council records and turn them into structured MAYHEM-compliant intelligence paths.

Manual upload is allowed only as a fallback. The primary workflow is automated source discovery, scheduled fetch, source preservation, meeting extraction, issue branching, decision tracking, action tracking, actor mapping, and mechanism detection.

## Core Pipeline

```text
Source Discovery
  -> Scheduled Fetch
  -> Source Preservation
  -> Meeting Folder Creation
  -> Extraction Queue
  -> Issue Path Creation or Update
  -> Decision Register Update
  -> Action Register Update
  -> Actor Register Update
  -> Mechanism Candidate Detection
  -> Output Queue
```

## Primary Rule

No automated extraction may overwrite the preserved source record.

Fetched sources must be stored first, then analysed.

## Fetch Targets

Initial source targets:

- Kempsey Shire Council meeting minutes
- Kempsey Shire Council meeting agendas
- Kempsey Shire Council business papers
- Kempsey Shire Council attachments
- Kempsey Shire Council notices of motion
- Kempsey Shire Council extraordinary meeting records
- Kempsey Shire Council media releases
- Relevant NSW agency records where linked from council material

## Fetch Frequency

Default schedule:

- Weekly fetch for new council meeting records
- Daily fetch during active investigation periods
- Manual trigger available for urgent checks

## Fetch Output Structure

Each fetched meeting record creates or updates:

```text
meetings/YYYY-MM-DD/
├── source-register.md
├── source-links.md
├── raw/
│   ├── agenda.pdf
│   ├── minutes.pdf
│   ├── business-paper.pdf
│   └── attachments/
├── extracted/
│   ├── issues-discussed.md
│   ├── decisions.md
│   ├── actions.md
│   ├── actors.md
│   ├── policies.md
│   ├── funding.md
│   ├── contradictions.md
│   └── unresolved-items.md
└── extraction-log.md
```

## Source Preservation Rules

Each fetched source must record:

- Source URL
- Fetch date and time
- File name
- File type
- Meeting date
- Meeting type
- Source status
- Checksum if available
- Fetch result
- Error state if failed

## Automated Issue Branching

For every meeting extraction:

1. Identify each issue discussed.
2. Check `registers/master-issue-register.md`.
3. If issue exists, append the meeting reference to the existing issue path.
4. If issue is new, create a new issue path under `issues/`.
5. Add the issue to the master issue register.
6. Preserve the source meeting link.

## Automated Action Tracking

Every extracted action must enter:

```text
actions/open.md
registers/master-action-register.md
issues/[issue-slug]/actions.md
```

An action remains open unless later source evidence proves:

- Completed
- Superseded
- Cancelled by later decision
- Not enough evidence

## Automated Actor Mapping

Every named or role-based actor must enter:

```text
actors/[actor-slug].md
registers/master-actor-register.md
```

Actor responsibility must not be inferred from appearance alone.

## Automated Mechanism Detection

The fetch system should flag mechanism candidates, not declare them proven.

Candidate pathways include:

- Repeated review without resolution
- Report requested but no completion evidence found
- Consultation promised but not evidenced
- Funding mentioned without delivery evidence
- Issue repeatedly deferred
- Action transferred without closure
- Public harm recorded without operational remedy

Mechanism candidates must be marked:

Proof of Fact (Human plus Evidence) = 0
Unverified — fails factual verification, requires independent audit.

until a full evidence chain supports verification.

## Required Automation Files

```text
automation/
├── fetch-sources.md
├── fetch-schedule.md
├── source-targets.md
├── extraction-rules.md
├── issue-branching-rules.md
├── action-status-rules.md
├── actor-mapping-rules.md
├── mechanism-detection-rules.md
└── fetch-log.md
```

## Fetch Log Fields

Each run must record:

- Run ID
- Date and time
- Source group checked
- URL checked
- Result
- New files found
- Existing files skipped
- Files changed
- Files failed
- Reason for failure
- Next action

## Failure Handling

If a source cannot be fetched:

- Do not silently fail.
- Record failure in `automation/fetch-log.md`.
- Preserve URL and error reason.
- Mark related extraction as incomplete.

## MAYHEM Compliance Test

The automated fetch system is compliant only if it can answer:

1. What source was checked?
2. When was it checked?
3. What was found?
4. What was excluded?
5. What failed?
6. What meeting folder was created?
7. What issues were extracted?
8. What actions were created?
9. What actors were mapped?
10. What remains unresolved?

If any answer lacks a source path, it remains unverified.
