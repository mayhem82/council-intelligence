# Upper Macleay Council Intelligence

## Purpose

This is the MAYHEM-compliant meeting-first repository for council minutes, agendas, decisions, actions, issue paths, actors, mechanisms, timelines, and outputs.

It is designed to convert each council meeting into traceable intelligence paths.

## Core Relationship

```text
Meeting
  -> Issue
  -> Decision
  -> Action
  -> Actor
  -> Mechanism
  -> Outcome
```

## Primary Rule

The meeting record is the intake source.

Every issue discussed in a meeting must either:

1. Link to an existing issue path, or
2. Create a new issue path.

Every action created in a meeting must enter the action register and remain open until later evidence proves completion, supersession, or closure.

## Root Folders

- meetings
- issues
- actions
- decisions
- actors
- timelines
- mechanisms
- outputs
- registers
- templates

## MAYHEM Compliance

This repository follows:

- Source-first extraction
- Issue-path branching
- Action accountability
- Actor mapping
- Mechanism detection
- Contradiction preservation
- Proof of Fact scoring
- Factual Strength rationale
- No unsupported allegation framing
- No closure without evidence
