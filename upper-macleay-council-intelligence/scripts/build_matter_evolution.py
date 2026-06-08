from collections import defaultdict
from pathlib import Path
import re

ROOT = Path('upper-macleay-council-intelligence')
MATTERS = ROOT / 'matters'
REGISTERS = ROOT / 'registers'
REPORTS = ROOT / 'reports'
EVOLUTION_REPORT = REPORTS / 'matter-evolution-summary.md'
ISSUE_REGISTER = REGISTERS / 'master-issue-register.md'
ACTION_REGISTER = REGISTERS / 'master-action-register.md'
DECISION_REGISTER = REGISTERS / 'master-decision-register.md'

STATUS_TERMS = {
    'resolved': ['completed', 'resolved', 'closed', 'finalised', 'works completed'],
    'escalated': ['referred', 'escalated', 'ombudsman', 'minister', 'state government'],
    'under-review': ['review', 'report', 'investigate', 'assessment', 'consultation'],
    'funding-stage': ['grant', 'funding', 'budget', 'allocation'],
    'decision-made': ['resolved', 'adopted', 'approved', 'endorsed', 'carried'],
    'deferred': ['deferred', 'pending', 'further report'],
}


def read(path):
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def blocks_for(label, text):
    current = []
    for line in text.splitlines():
        if line.startswith(label) and current:
            yield current
            current = [line]
        elif line.startswith(label):
            current = [line]
        elif current:
            current.append(line)
    if current:
        yield current


def field(block, name):
    marker = name + ':'
    for line in block:
        if marker in line:
            return line.split(marker, 1)[1].strip()
    return ''


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'unknown'


def status_from(text):
    lower = text.lower()
    hits = []
    for status, terms in STATUS_TERMS.items():
        if any(term in lower for term in terms):
            hits.append(status)
    if not hits:
        return 'watch'
    if 'resolved' in hits:
        return 'resolved-candidate'
    if 'deferred' in hits:
        return 'deferred-candidate'
    if 'decision-made' in hits:
        return 'decision-candidate'
    if 'funding-stage' in hits:
        return 'funding-candidate'
    if 'escalated' in hits:
        return 'escalated-candidate'
    return hits[0]


def sort_key(entry):
    date = entry.get('date') or '9999-99-99'
    return (date, entry.get('source', ''), entry.get('kind', ''))


def collect_entries():
    entries = defaultdict(list)
    for block in blocks_for('- Issue:', read(ISSUE_REGISTER)):
        issue = field(block, '- Issue') or block[0].split(':', 1)[1].strip()
        matter = slug(issue)
        text = '\n'.join(block)
        entries[matter].append({
            'kind': 'issue-signal',
            'date': field(block, 'Meeting date') or field(block, 'Date inferred'),
            'source': field(block, 'Source'),
            'trigger': field(block, 'Trigger'),
            'status': status_from(text),
            'text': text,
        })
    for block in blocks_for('- Action ID:', read(ACTION_REGISTER)):
        text = '\n'.join(block)
        matter = 'unassigned-action'
        for known in entries.keys():
            if known.replace('-', ' ') in text.lower() or known in text.lower():
                matter = known
                break
        entries[matter].append({
            'kind': 'action-signal',
            'date': field(block, 'Meeting date') or field(block, 'Date inferred'),
            'source': field(block, 'Source'),
            'trigger': field(block, 'Trigger'),
            'status': status_from(text),
            'text': text,
        })
    for block in blocks_for('- Decision ID:', read(DECISION_REGISTER)):
        text = '\n'.join(block)
        matter = 'unassigned-decision'
        for known in entries.keys():
            if known.replace('-', ' ') in text.lower() or known in text.lower():
                matter = known
                break
        entries[matter].append({
            'kind': 'decision-signal',
            'date': field(block, 'Meeting date') or field(block, 'Date inferred'),
            'source': field(block, 'Source'),
            'trigger': field(block, 'Trigger'),
            'status': status_from(text),
            'text': text,
        })
    return entries


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    MATTERS.mkdir(parents=True, exist_ok=True)
    entries = collect_entries()
    summary = ['# Matter Evolution Summary', '', 'Purpose: build oldest-to-newest matter evolution from issue/action/decision signals.', '', 'PF(H,E): 0 — automated evolution only; not a finding.', '']
    for matter, records in sorted(entries.items()):
        records = sorted(records, key=sort_key)
        matter_dir = MATTERS / matter
        matter_dir.mkdir(parents=True, exist_ok=True)
        statuses = [r['status'] for r in records]
        current_status = 'open-watch'
        if any(s == 'resolved-candidate' for s in statuses):
            current_status = 'resolved-candidate'
        elif any(s == 'deferred-candidate' for s in statuses):
            current_status = 'deferred-candidate'
        elif any(s == 'decision-candidate' for s in statuses):
            current_status = 'decision-candidate'
        elif any(s == 'funding-candidate' for s in statuses):
            current_status = 'funding-candidate'
        chronology = [f'# Matter Evolution: {matter}', '', f'Current automated status: {current_status}', 'PF(H,E): 0 — automated status, requires source review.', '', '## Chronology', '']
        for r in records:
            chronology.extend([
                f'- Date: {r["date"] or "unknown-date"}',
                f'  Kind: {r["kind"]}',
                f'  Status signal: {r["status"]}',
                f'  Trigger: {r["trigger"]}',
                f'  Source: {r["source"]}',
                '',
            ])
        (matter_dir / 'chronology.md').write_text('\n'.join(chronology) + '\n', encoding='utf-8')
        summary.extend([f'- {matter}: {current_status} | events={len(records)}', ''])
    EVOLUTION_REPORT.write_text('\n'.join(summary) + '\n', encoding='utf-8')
    print(f'Matter evolution complete: matters={len(entries)}')


if __name__ == '__main__':
    main()
