from pathlib import Path
import re

ROOT = Path('upper-macleay-council-intelligence')
REGISTERS = ROOT / 'registers'
TIMELINES = ROOT / 'timelines'
REPORTS = ROOT / 'reports'

SORT_TARGETS = [
    REGISTERS / 'master-meeting-register.md',
    REGISTERS / 'master-source-register.md',
    REGISTERS / 'master-issue-register.md',
    REGISTERS / 'master-action-register.md',
    REGISTERS / 'master-decision-register.md',
    REGISTERS / 'master-actor-register.md',
    REGISTERS / 'master-mechanism-register.md',
    TIMELINES / 'master-timeline.md',
    REPORTS / 'cross-meeting-linkage.md',
    REPORTS / 'matter-lifecycle.md',
]

DATE_PATTERNS = [
    r'(20\d{2})-(\d{2})-(\d{2})',
    r'(20\d{2})/(\d{2})/(\d{2})',
    r'(\d{1,2})/(\d{1,2})/(20\d{2})',
    r'(\d{1,2})-(\d{1,2})-(20\d{2})',
]


def read(path):
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def infer_date(text):
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if not match:
            continue
        parts = match.groups()
        if len(parts[0]) == 4:
            return f'{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}'
        return f'{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}'
    return '9999-99-99'


def split_blocks(text):
    blocks = []
    current = []
    for line in text.splitlines():
        starts = line.startswith('- ') or line.startswith('## ')
        if starts and current:
            blocks.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks


def sort_file(path):
    text = read(path)
    if not text.strip():
        return False
    lines = text.splitlines()
    heading = []
    body_start = 0
    for index, line in enumerate(lines):
        if line.startswith('- ') or line.startswith('## '):
            body_start = index
            break
        heading.append(line)
    body = '\n'.join(lines[body_start:])
    blocks = split_blocks(body)
    blocks.sort(key=lambda block: (infer_date('\n'.join(block)), '\n'.join(block)))
    out = []
    if heading:
        out.extend(heading)
        out.append('')
    for block in blocks:
        out.extend(block)
        out.append('')
    new_text = '\n'.join(out).rstrip() + '\n'
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
        return True
    return False


def main():
    changed = 0
    for path in SORT_TARGETS:
        if sort_file(path):
            changed += 1
    print(f'Historical sorting complete: files_changed={changed}')


if __name__ == '__main__':
    main()
