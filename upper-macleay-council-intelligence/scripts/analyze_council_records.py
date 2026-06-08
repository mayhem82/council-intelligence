from datetime import datetime, timezone
from pathlib import Path
import re

ROOT = Path('upper-macleay-council-intelligence')
RAW = ROOT / 'fetched' / 'raw'
REGISTERS = ROOT / 'registers'
REPORTS = ROOT / 'reports'
INTEL_REPORT = REPORTS / 'latest-intelligence-summary.md'
TIMELINE = ROOT / 'timelines' / 'master-timeline.md'

ISSUE_TERMS = {
    'flying-fox-camp': ['flying fox', 'flying-fox', 'bat camp', 'grey-headed flying-fox'],
    'roads': ['road maintenance', 'pothole', 'sealed road', 'unsealed road', 'armidale road', 'main street'],
    'bridges': ['bridge', 'causeway', 'flood crossing'],
    'water-security': ['water supply', 'water security', 'water carting', 'potable water'],
    'grants-funding': ['grant', 'funding', 'budget allocation', 'funded'],
    'planning-development': ['development application', 'planning proposal', 'rezoning'],
    'public-health-safety': ['public health', 'safety risk', 'work health safety', 'hazard'],
    'community-facilities': ['hall', 'playground', 'park', 'public toilet', 'community facility'],
    'governance': ['notice of motion', 'councillor', 'resolution', 'ordinary meeting']
}

ACTION_TERMS = ['resolved', 'recommended', 'request', 'report', 'review', 'consultation', 'investigate', 'prepare', 'endorse', 'approve', 'defer']
DECISION_TERMS = ['resolved', 'carried', 'lost', 'adopted', 'approved', 'endorsed', 'deferred']
ACTOR_TERMS = {
    'kempsey-shire-council': ['kempsey shire council', 'council'],
    'councillors': ['councillor', 'mayor', 'deputy mayor'],
    'general-manager': ['general manager'],
    'nsw-government': ['nsw government', 'department of', 'dccceew', 'environment and heritage'],
    'community': ['community', 'residents', 'public submissions'],
    'funding-body': ['grant', 'funding body', 'program funding']
}
MECHANISM_TERMS = {
    'repeated-review-without-resolution': ['review', 'report', 'defer'],
    'consultation-promised-not-yet-evidenced': ['consultation', 'community'],
    'funding-mentioned-without-delivery-evidence': ['funding', 'grant'],
    'public-harm-recorded-without-remedy-evidence': ['hazard', 'public health', 'safety risk'],
    'action-created-status-open': ['resolved', 'request', 'prepare', 'investigate']
}


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_text(path):
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except UnicodeDecodeError:
        return ''


def hit_terms(text, mapping):
    lower = text.lower()
    hits = []
    for key, terms in mapping.items():
        for term in terms:
            if term in lower:
                hits.append((key, term))
                break
    return hits


def word_hits(text, terms):
    lower = text.lower()
    return [term for term in terms if term in lower]


def infer_date(text):
    patterns = [
        r'(20\d{2})[-_/ ](0?[1-9]|1[0-2])[-_/ ](0?[1-9]|[12]\d|3[01])',
        r'(0?[1-9]|[12]\d|3[01])[-_/ ](0?[1-9]|1[0-2])[-_/ ](20\d{2})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            parts = match.groups()
            if len(parts[0]) == 4:
                return f'{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}'
            return f'{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}'
    return 'unknown-date'


def append(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding='utf-8') if path.exists() else ''
    path.write_text(existing.rstrip() + '\n' + '\n'.join(lines) + '\n', encoding='utf-8')


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    REGISTERS.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    files = sorted(RAW.glob('*')) if RAW.exists() else []
    issue_count = action_count = decision_count = actor_count = mechanism_count = 0
    timeline_lines = [f'\n## Analysis Run {run_id}', f'Run time UTC: {now()}', '']
    report_lines = ['# Latest Council Intelligence Summary', '', f'Updated UTC: {now()}', '', '## Summary', '']

    for path in files:
        text = path.name + '\n' + read_text(path)[:100000]
        source = str(path)
        date = infer_date(text)
        issues = hit_terms(text, ISSUE_TERMS)
        actions = word_hits(text, ACTION_TERMS)
        decisions = word_hits(text, DECISION_TERMS)
        actors = hit_terms(text, ACTOR_TERMS)
        mechanisms = hit_terms(text, MECHANISM_TERMS)
        if not any([issues, actions, decisions, actors, mechanisms]):
            continue
        timeline_lines.append(f'- {date}: {source}')
        for issue, trigger in issues:
            issue_count += 1
            append(REGISTERS / 'master-issue-register.md', [f'- Issue: {issue}', f'  Source: {source}', f'  Date inferred: {date}', f'  Trigger: {trigger}', '  PF(H,E): 0 — unverified automated detection.', ''])
            append(ROOT / 'issues' / issue / 'evidence.md', [f'\n## Evidence candidate {run_id}', f'Source: {source}', f'Date inferred: {date}', f'Trigger: {trigger}', 'Status: requires review'])
        for index, trigger in enumerate(actions, start=1):
            action_count += 1
            action_id = f'ACT-AUTO-{run_id}-{action_count:04d}'
            append(REGISTERS / 'master-action-register.md', [f'- Action ID: {action_id}', f'  Source: {source}', f'  Date inferred: {date}', f'  Trigger: {trigger}', '  Status: Open', '  PF(H,E): 0 — unverified automated detection.', ''])
            append(ROOT / 'actions' / 'open.md', [f'\n## {action_id}', f'Source: {source}', f'Date inferred: {date}', f'Trigger: {trigger}', 'Status: Open'])
        for index, trigger in enumerate(decisions, start=1):
            decision_count += 1
            decision_id = f'DEC-AUTO-{run_id}-{decision_count:04d}'
            append(REGISTERS / 'master-decision-register.md', [f'- Decision ID: {decision_id}', f'  Source: {source}', f'  Date inferred: {date}', f'  Trigger: {trigger}', '  Status: decision signal only; requires review.', ''])
        for actor, trigger in actors:
            actor_count += 1
            append(REGISTERS / 'master-actor-register.md', [f'- Actor: {actor}', f'  Source: {source}', f'  Date inferred: {date}', f'  Trigger: {trigger}', '  Responsibility: not inferred.', ''])
            append(ROOT / 'actors' / actor / 'references.md', [f'\n## Reference {run_id}', f'Source: {source}', f'Date inferred: {date}', f'Trigger: {trigger}', 'Responsibility: not inferred'])
        for mechanism, trigger in mechanisms:
            mechanism_count += 1
            append(REGISTERS / 'master-mechanism-register.md', [f'- Mechanism candidate: {mechanism}', f'  Source: {source}', f'  Date inferred: {date}', f'  Trigger: {trigger}', '  PF(H,E): 0 — candidate only; not a finding.', ''])
            append(ROOT / 'mechanisms' / mechanism / 'candidate-evidence.md', [f'\n## Candidate {run_id}', f'Source: {source}', f'Date inferred: {date}', f'Trigger: {trigger}', 'PF(H,E): 0 — candidate only; not a finding.'])

    report_lines.extend([
        f'- Raw files scanned: {len(files)}',
        f'- Issue detections: {issue_count}',
        f'- Action detections: {action_count}',
        f'- Decision detections: {decision_count}',
        f'- Actor detections: {actor_count}',
        f'- Mechanism candidates: {mechanism_count}',
        '',
        '## Compliance Position',
        '',
        'All automated detections are marked PF(H,E): 0 until independently reviewed against the preserved source record.',
        'No automated candidate is treated as a proven finding.'
    ])
    INTEL_REPORT.write_text('\n'.join(report_lines) + '\n', encoding='utf-8')
    append(TIMELINE, timeline_lines)
    print(f'MAYHEM analysis complete: files={len(files)} issues={issue_count} actions={action_count} decisions={decision_count} actors={actor_count} mechanisms={mechanism_count}')


if __name__ == '__main__':
    main()
