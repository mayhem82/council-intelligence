from collections import defaultdict
from pathlib import Path
import re

ROOT = Path('upper-macleay-council-intelligence')
REGISTERS = ROOT / 'registers'
MATTERS = ROOT / 'matters'
REPORTS = ROOT / 'reports'
LINK_REPORT = REPORTS / 'cross-meeting-linkage.md'
ISSUE_REGISTER = REGISTERS / 'master-issue-register.md'
ACTION_REGISTER = REGISTERS / 'master-action-register.md'
DECISION_REGISTER = REGISTERS / 'master-decision-register.md'


def read(path):
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def blocks(text):
    current = []
    for line in text.splitlines():
        if line.startswith('- Issue:') and current:
            yield current
            current = [line]
        elif line.startswith('- Issue:'):
            current = [line]
        elif current:
            current.append(line)
    if current:
        yield current


def get_field(block, label):
    for line in block:
        marker = label + ':'
        if marker in line:
            return line.split(marker, 1)[1].strip()
    return ''


def slug(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text or 'unknown'


def append(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding='utf-8') if path.exists() else ''
    path.write_text(existing.rstrip() + '\n' + '\n'.join(lines) + '\n', encoding='utf-8')


def action_signals_for(issue):
    text = read(ACTION_REGISTER).lower()
    issue_text = issue.replace('-', ' ')
    return text.count(issue.lower()) + text.count(issue_text)


def decision_signals_for(issue):
    text = read(DECISION_REGISTER).lower()
    issue_text = issue.replace('-', ' ')
    return text.count(issue.lower()) + text.count(issue_text)


def main():
    MATTERS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    groups = defaultdict(list)
    for block in blocks(read(ISSUE_REGISTER)):
        issue = get_field(block, '- Issue') or block[0].split(':', 1)[1].strip()
        source = get_field(block, 'Source')
        date = get_field(block, 'Date inferred') or get_field(block, 'Meeting date')
        trigger = get_field(block, 'Trigger')
        groups[slug(issue)].append({'issue': issue, 'source': source, 'date': date, 'trigger': trigger})

    report = ['# Cross-Meeting Matter Linkage', '', 'Automated linkage groups repeated issue detections into matter histories.', '', 'PF(H,E): 0 for all automated linkages until source review.', '']
    for matter, entries in sorted(groups.items()):
        matter_dir = MATTERS / matter
        matter_dir.mkdir(parents=True, exist_ok=True)
        dates = sorted(set(e['date'] for e in entries if e['date']))
        sources = sorted(set(e['source'] for e in entries if e['source']))
        action_count = action_signals_for(matter)
        decision_count = decision_signals_for(matter)
        status = 'Open' if action_count else 'Watch'
        history = [f'# Matter: {matter}', '', f'Status: {status}', f'Issue detections: {len(entries)}', f'Unique source records: {len(sources)}', f'Action signal count: {action_count}', f'Decision signal count: {decision_count}', 'PF(H,E): 0 — automated linkage, requires review.', '', '## Detections', '']
        for e in entries:
            history.extend([f'- Date inferred: {e["date"]}', f'  Issue label: {e["issue"]}', f'  Trigger: {e["trigger"]}', f'  Source: {e["source"]}', ''])
        history.extend(['## Source List', ''])
        for source in sources:
            history.append(f'- {source}')
        (matter_dir / 'history.md').write_text('\n'.join(history) + '\n', encoding='utf-8')
        report.extend([f'## {matter}', f'- Status: {status}', f'- Detections: {len(entries)}', f'- Sources: {len(sources)}', f'- Action signals: {action_count}', f'- Decision signals: {decision_count}', ''])
    LINK_REPORT.write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(f'Matter linkage complete: matters={len(groups)}')


if __name__ == '__main__':
    main()
