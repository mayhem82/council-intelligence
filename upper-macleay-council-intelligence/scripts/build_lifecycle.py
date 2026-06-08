from datetime import datetime, timezone
from pathlib import Path
import re

ROOT = Path('upper-macleay-council-intelligence')
REGISTERS = ROOT / 'registers'
ISSUES = ROOT / 'issues'
ACTIONS = ROOT / 'actions'
REPORTS = ROOT / 'reports'
DASHBOARD = ROOT / 'DASHBOARD.md'
LIFECYCLE = REPORTS / 'matter-lifecycle.md'


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read(path):
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def count_issue_refs(issue_dir):
    total = 0
    for path in issue_dir.glob('*.md'):
        total += read(path).count('Source:') + read(path).count('Reference')
    return total


def action_count_for_issue(issue):
    text = read(ACTIONS / 'open.md').lower()
    return text.count(issue.replace('-', ' ')) + text.count(issue)


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    issue_dirs = sorted([p for p in ISSUES.iterdir() if p.is_dir()]) if ISSUES.exists() else []
    lifecycle_lines = ['# Matter Lifecycle Register', '', f'Updated UTC: {now()}', '']
    dashboard_lines = ['# Upper Macleay Council Intelligence Dashboard', '', f'Updated UTC: {now()}', '', '## Matter Status', '']
    open_count = 0
    watch_count = 0
    for issue_dir in issue_dirs:
        issue = issue_dir.name
        refs = count_issue_refs(issue_dir)
        actions = action_count_for_issue(issue)
        if refs == 0:
            status = 'Dormant candidate'
        elif actions > 0:
            status = 'Open — action signal detected'
            open_count += 1
        else:
            status = 'Watch — evidence signal detected'
            watch_count += 1
        lifecycle_lines.extend([
            f'## {issue}',
            f'Status: {status}',
            f'Evidence references: {refs}',
            f'Open action signals: {actions}',
            'PF(H,E): 0 — automated lifecycle classification, requires review.',
            ''
        ])
        dashboard_lines.append(f'- {issue}: {status} | refs={refs} | action-signals={actions}')
    dashboard_lines.extend(['', '## System Summary', '', f'- Issues tracked: {len(issue_dirs)}', f'- Open-action issue signals: {open_count}', f'- Watch issue signals: {watch_count}', '', '## Key Files', '', '- reports/latest-intelligence-summary.md', '- reports/matter-lifecycle.md', '- timelines/master-timeline.md', '- registers/master-issue-register.md', '- registers/master-action-register.md', '- registers/master-decision-register.md', '- registers/master-actor-register.md', '- registers/master-mechanism-register.md'])
    LIFECYCLE.write_text('\n'.join(lifecycle_lines) + '\n', encoding='utf-8')
    DASHBOARD.write_text('\n'.join(dashboard_lines) + '\n', encoding='utf-8')
    print(f'MAYHEM lifecycle build complete: issues={len(issue_dirs)} open={open_count} watch={watch_count}')


if __name__ == '__main__':
    main()
