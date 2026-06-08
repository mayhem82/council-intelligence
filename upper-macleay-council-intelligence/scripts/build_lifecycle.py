from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import re

ROOT = Path('upper-macleay-council-intelligence')
REGISTERS = ROOT / 'registers'
ISSUES = ROOT / 'issues'
ACTIONS = ROOT / 'actions'
MATTERS = ROOT / 'matters'
RAW = ROOT / 'fetched' / 'raw'
TEXT = ROOT / 'fetched' / 'text'
REPORTS = ROOT / 'reports'
DASHBOARD = ROOT / 'DASHBOARD.md'
LIFECYCLE = REPORTS / 'matter-lifecycle.md'
EVOLUTION = REPORTS / 'matter-evolution-summary.md'
RESOLUTION = REPORTS / 'resolution-detection.md'
HEATMAP = REPORTS / 'matter-heatmap.md'
DUPLICATES = REPORTS / 'duplicate-source-report.md'
EVIDENCE_AUDIT = REPORTS / 'evidence-chain-audit.md'
ISSUE_REGISTER = REGISTERS / 'master-issue-register.md'
ACTION_REGISTER = REGISTERS / 'master-action-register.md'
DECISION_REGISTER = REGISTERS / 'master-decision-register.md'
SOURCE_REGISTER = REGISTERS / 'master-source-register.md'
BACKFILL_REGISTER = REGISTERS / 'historic-backfill-source-register.md'
INDEX_REGISTER = REGISTERS / 'fetched-source-index.md'
MEETING_REGISTER = REGISTERS / 'master-meeting-register.md'
ACTOR_REGISTER = REGISTERS / 'master-actor-register.md'
MECHANISM_REGISTER = REGISTERS / 'master-mechanism-register.md'

RESOLUTION_TERMS = ['completed', 'resolved', 'closed', 'finalised', 'works completed', 'delivered']
DEFER_TERMS = ['deferred', 'pending', 'further report', 'awaiting', 'under review']
FUNDING_TERMS = ['grant', 'funding', 'budget', 'allocation', 'approved funding']
DECISION_TERMS = ['resolved', 'adopted', 'approved', 'endorsed', 'carried']
ESCALATION_TERMS = ['referred', 'escalated', 'ombudsman', 'minister', 'state government']
REGISTER_FILES = [SOURCE_REGISTER, BACKFILL_REGISTER, INDEX_REGISTER, MEETING_REGISTER, ISSUE_REGISTER, ACTION_REGISTER, DECISION_REGISTER, ACTOR_REGISTER, MECHANISM_REGISTER]


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read(path):
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'unknown'


def normalize_url(url):
    return url.strip().split('#', 1)[0].split('?', 1)[0].rstrip('/').lower()


def infer_date(text):
    patterns = [r'(20\d{2})-(\d{2})-(\d{2})', r'(20\d{2})/(\d{2})/(\d{2})', r'(\d{1,2})/(\d{1,2})/(20\d{2})', r'(\d{1,2})-(\d{1,2})-(20\d{2})', r'(20\d{2})']
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        parts = match.groups()
        if len(parts) == 1:
            return f'{parts[0]}-00-00'
        if len(parts[0]) == 4:
            return f'{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}'
        return f'{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}'
    return 'unknown-date'


def field(block, name):
    marker = name + ':'
    for line in block:
        if marker in line:
            return line.split(marker, 1)[1].strip()
    return ''


def blocks_for(prefix, text):
    current = []
    for line in text.splitlines():
        if line.startswith(prefix) and current:
            yield current
            current = [line]
        elif line.startswith(prefix):
            current = [line]
        elif current:
            current.append(line)
    if current:
        yield current


def status_signal(text):
    lower = text.lower()
    if any(term in lower for term in RESOLUTION_TERMS):
        return 'resolved-candidate'
    if any(term in lower for term in DEFER_TERMS):
        return 'deferred-candidate'
    if any(term in lower for term in FUNDING_TERMS):
        return 'funding-candidate'
    if any(term in lower for term in ESCALATION_TERMS):
        return 'escalated-candidate'
    if any(term in lower for term in DECISION_TERMS):
        return 'decision-candidate'
    return 'open-watch'


def count_issue_refs(issue_dir):
    total = 0
    for path in issue_dir.glob('*.md'):
        text = read(path)
        total += text.count('Source:') + text.count('Reference')
    return total


def action_count_for_issue(issue):
    text = read(ACTIONS / 'open.md').lower()
    return text.count(issue.replace('-', ' ')) + text.count(issue)


def collect_events():
    events = defaultdict(list)
    for block in blocks_for('- Issue:', read(ISSUE_REGISTER)):
        text = '\n'.join(block)
        issue = field(block, '- Issue') or block[0].split(':', 1)[1].strip()
        matter = slug(issue)
        events[matter].append({'kind': 'issue-signal', 'date': field(block, 'Meeting date') or field(block, 'Date inferred') or infer_date(text), 'source': field(block, 'Source'), 'trigger': field(block, 'Trigger'), 'status': status_signal(text), 'raw': text})
    known_matters = list(events.keys())
    for prefix, path, kind in [('- Action ID:', ACTION_REGISTER, 'action-signal'), ('- Decision ID:', DECISION_REGISTER, 'decision-signal')]:
        for block in blocks_for(prefix, read(path)):
            text = '\n'.join(block)
            matter = 'unassigned-' + kind.replace('-signal', '')
            for known in known_matters:
                if known in text.lower() or known.replace('-', ' ') in text.lower():
                    matter = known
                    break
            events[matter].append({'kind': kind, 'date': field(block, 'Meeting date') or field(block, 'Date inferred') or infer_date(text), 'source': field(block, 'Source'), 'trigger': field(block, 'Trigger'), 'status': status_signal(text), 'raw': text})
    return events


def current_status(records):
    statuses = [r['status'] for r in records]
    if 'resolved-candidate' in statuses:
        return 'resolved-candidate'
    if 'deferred-candidate' in statuses:
        return 'deferred-candidate'
    if 'funding-candidate' in statuses:
        return 'funding-candidate'
    if 'escalated-candidate' in statuses:
        return 'escalated-candidate'
    if 'decision-candidate' in statuses:
        return 'decision-candidate'
    return 'open-watch'


def duplicate_report():
    url_refs = defaultdict(list)
    for source in [SOURCE_REGISTER, BACKFILL_REGISTER, INDEX_REGISTER, ISSUE_REGISTER, ACTION_REGISTER, DECISION_REGISTER]:
        text = read(source)
        for line_no, line in enumerate(text.splitlines(), start=1):
            for url in re.findall(r'https://www\.kempsey\.nsw\.gov\.au/[^\s)]+', line):
                url_refs[normalize_url(url)].append(f'{source}:{line_no}')
    duplicate_urls = {url: refs for url, refs in url_refs.items() if len(refs) > 1}
    file_keys = defaultdict(list)
    if RAW.exists():
        for path in RAW.glob('*'):
            if path.is_file():
                stat = path.stat()
                base = re.sub(r'^(seed|meeting-record|historic)-[0-9TZA-Z-]+-?', '', path.name)
                file_keys[(base.lower(), stat.st_size)].append(str(path))
    duplicate_files = {key: paths for key, paths in file_keys.items() if len(paths) > 1}
    lines = ['# Duplicate Source Report', '', f'Updated UTC: {now()}', '', 'PF(H,E): 0 — automated duplicate detection; review before deletion or consolidation.', '', '## Duplicate URL Candidates', '']
    if duplicate_urls:
        for url, refs in sorted(duplicate_urls.items()):
            lines.append(f'- {url}')
            for ref in refs:
                lines.append(f'  - {ref}')
    else:
        lines.append('- None detected')
    lines.extend(['', '## Duplicate File Candidates', ''])
    if duplicate_files:
        for key, paths in sorted(duplicate_files.items(), key=lambda item: item[0][0]):
            lines.append(f'- File key: {key[0]} | size={key[1]}')
            for path in paths:
                lines.append(f'  - {path}')
    else:
        lines.append('- None detected')
    DUPLICATES.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return len(duplicate_urls), len(duplicate_files)


def evidence_chain_report():
    refs = set()
    for register in REGISTER_FILES:
        text = read(register)
        refs.update(re.findall(r'upper-macleay-council-intelligence/[^\s)]+', text))
    present = []
    missing = []
    for ref in sorted(refs):
        if Path(ref).exists():
            present.append(ref)
        else:
            missing.append(ref)
    raw_count = len(list(RAW.glob('*'))) if RAW.exists() else 0
    text_count = len(list(TEXT.glob('*'))) if TEXT.exists() else 0
    lines = ['# Evidence Chain Audit', '', f'Updated UTC: {now()}', '', 'Purpose: check whether register references point back to preserved local source files.', '', 'PF(H,E): 0 — automated audit, requires review before evidentiary use.', '', '## Counts', '', f'- Raw preserved files: {raw_count}', f'- Extracted text files: {text_count}', f'- Referenced local paths: {len(refs)}', f'- Referenced paths present: {len(present)}', f'- Referenced paths missing: {len(missing)}', '', '## Missing References', '']
    if missing:
        for item in missing:
            lines.append(f'- {item}')
    else:
        lines.append('- None detected')
    lines.extend(['', '## Present References', ''])
    for item in present[:500]:
        lines.append(f'- {item}')
    EVIDENCE_AUDIT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return raw_count, text_count, len(refs), len(missing)


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    MATTERS.mkdir(parents=True, exist_ok=True)
    issue_dirs = sorted([p for p in ISSUES.iterdir() if p.is_dir()]) if ISSUES.exists() else []
    events = collect_events()
    duplicate_url_count, duplicate_file_count = duplicate_report()
    raw_count, text_count, evidence_refs, evidence_missing = evidence_chain_report()

    lifecycle_lines = ['# Matter Lifecycle Register', '', f'Updated UTC: {now()}', '', 'PF(H,E): 0 — automated lifecycle classification, requires review.', '']
    evolution_lines = ['# Matter Evolution Summary', '', f'Updated UTC: {now()}', '', 'PF(H,E): 0 — automated evolution only; not a finding.', '']
    resolution_lines = ['# Resolution Detection Register', '', f'Updated UTC: {now()}', '', 'PF(H,E): 0 — automated resolution candidates require source review.', '']
    heat_rows = []
    dashboard_lines = ['# Upper Macleay Council Intelligence Dashboard', '', f'Updated UTC: {now()}', '', '## Matter Status', '']

    open_count = watch_count = resolved_count = 0
    matter_names = sorted(set([p.name for p in issue_dirs]) | set(events.keys()))
    for matter in matter_names:
        issue_dir = ISSUES / matter
        refs = count_issue_refs(issue_dir) if issue_dir.exists() else 0
        actions = action_count_for_issue(matter)
        records = sorted(events.get(matter, []), key=lambda r: (r.get('date') or '9999-99-99', r.get('kind', ''), r.get('source', '')))
        status = current_status(records) if records else ('Open — action signal detected' if actions else 'Watch — evidence signal detected')
        if status == 'resolved-candidate':
            resolved_count += 1
        elif actions > 0 or records:
            open_count += 1
        else:
            watch_count += 1
        lifecycle_lines.extend([f'## {matter}', f'Status: {status}', f'Evidence references: {refs}', f'Open action signals: {actions}', f'Evolution events: {len(records)}', 'PF(H,E): 0 — automated lifecycle classification, requires review.', ''])
        chronology = [f'# Matter Chronology: {matter}', '', f'Current automated status: {status}', 'PF(H,E): 0 — automated chronology, requires source review.', '', '## Oldest to Newest', '']
        for r in records:
            chronology.extend([f'- Date: {r["date"] or "unknown-date"}', f'  Kind: {r["kind"]}', f'  Status signal: {r["status"]}', f'  Trigger: {r["trigger"]}', f'  Source: {r["source"]}', ''])
        matter_dir = MATTERS / matter
        matter_dir.mkdir(parents=True, exist_ok=True)
        (matter_dir / 'chronology.md').write_text('\n'.join(chronology) + '\n', encoding='utf-8')
        evolution_lines.append(f'- {matter}: {status} | events={len(records)} | refs={refs} | actions={actions}')
        if status == 'resolved-candidate':
            resolution_lines.extend([f'## {matter}', 'Status: resolved-candidate', f'Events: {len(records)}', 'Review required before treating as resolved.', ''])
        heat_rows.append((len(records) + refs + actions, matter, status, refs, actions, len(records)))
        dashboard_lines.append(f'- {matter}: {status} | refs={refs} | action-signals={actions} | events={len(records)}')

    heat_rows.sort(reverse=True)
    heatmap_lines = ['# Matter Heatmap', '', f'Updated UTC: {now()}', '', 'Higher score means more automated evidence/action/evolution activity. PF(H,E): 0 until reviewed.', '']
    for score, matter, status, refs, actions, count in heat_rows:
        heatmap_lines.append(f'- Score {score}: {matter} | {status} | refs={refs} actions={actions} events={count}')

    dashboard_lines.extend(['', '## System Summary', '', f'- Matters tracked: {len(matter_names)}', f'- Open/watch matters: {open_count}', f'- Watch-only matter signals: {watch_count}', f'- Resolution candidates: {resolved_count}', f'- Duplicate URL candidates: {duplicate_url_count}', f'- Duplicate file candidates: {duplicate_file_count}', f'- Raw preserved files: {raw_count}', f'- Extracted text files: {text_count}', f'- Evidence references checked: {evidence_refs}', f'- Evidence references missing: {evidence_missing}', '', '## Key Files', '', '- reports/latest-intelligence-summary.md', '- reports/matter-lifecycle.md', '- reports/matter-evolution-summary.md', '- reports/resolution-detection.md', '- reports/matter-heatmap.md', '- reports/duplicate-source-report.md', '- reports/evidence-chain-audit.md', '- reports/cross-meeting-linkage.md', '- timelines/master-timeline.md', '- registers/master-issue-register.md', '- registers/master-action-register.md', '- registers/master-decision-register.md', '- registers/master-actor-register.md', '- registers/master-mechanism-register.md'])

    LIFECYCLE.write_text('\n'.join(lifecycle_lines) + '\n', encoding='utf-8')
    EVOLUTION.write_text('\n'.join(evolution_lines) + '\n', encoding='utf-8')
    RESOLUTION.write_text('\n'.join(resolution_lines) + '\n', encoding='utf-8')
    HEATMAP.write_text('\n'.join(heatmap_lines) + '\n', encoding='utf-8')
    DASHBOARD.write_text('\n'.join(dashboard_lines) + '\n', encoding='utf-8')
    print(f'MAYHEM lifecycle build complete: matters={len(matter_names)} open={open_count} watch={watch_count} resolved_candidates={resolved_count} duplicate_urls={duplicate_url_count} duplicate_files={duplicate_file_count} evidence_missing={evidence_missing}')


if __name__ == '__main__':
    main()
