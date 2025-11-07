import re
from pathlib import Path

SCAN_DIRS = [Path('scripts'), Path('Global-Scripts')]
TARGET_EXTS = {'.ps1', '.sh', '.cmd', '.bat'}
CMD_PATTERN = re.compile(r'^\s*(?:&\s*)?([A-Za-z0-9_.-]+)')
VALID_RE = re.compile(r'[a-z0-9_.-]+$')

KEYWORDS = {
    'if', 'fi', 'then', 'else', 'elif', 'for', 'do', 'done', 'while', 'case', 'esac', 'select', 'until',
    'function', 'return', 'break', 'continue', 'in', 'time', 'local', 'export', 'trap', 'wait', 'shift',
    'try', 'catch', 'finally', 'throw', 'param', 'foreach', 'switch', 'default', 'begin', 'process', 'end',
    'true', 'false', 'echo', 'printf', 'read', 'alias', 'cd', 'pwd', 'set', 'unset', 'umask', 'typeset',
    'source', '.', 'test', '[', ']', 'functionName', 'write-host', 'write-output', 'write-error', 'write-warning',
    'write-information', 'new-item', 'set-content', 'get-content', 'remove-item', 'copy-item', 'move-item',
    'start-process', 'stop-process', 'get-process', 'get-date', 'get-childitem', 'set-location', 'get-location',
    'start-job', 'receive-job', 'wait-job', 'remove-job', 'cls', 'clear-host', 'sleep', 'start-sleep',
    'exit', 'return', 'continue'
}

commands: set[str] = set()

for scan_dir in SCAN_DIRS:
    if not scan_dir.exists():
        continue
    for path in scan_dir.rglob('*'):
        if path.suffix.lower() not in TARGET_EXTS or not path.is_file():
            continue
        try:
            lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
        except OSError:
            continue
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
            lower = line.lower()
            if lower.startswith('function ') or lower.startswith('param(') or lower.startswith('param ('):
                continue
            if line.startswith('.') and not line.startswith('./'):
                continue
            match = CMD_PATTERN.match(line)
            if not match:
                continue
            cmd = match.group(1)
            if cmd.startswith('-'):
                continue
            lc = cmd.lower()
            if lc != cmd:
                continue
            if not VALID_RE.fullmatch(cmd):
                continue
            if not any(ch.isalpha() for ch in cmd):
                continue
            if lc in KEYWORDS:
                continue
            commands.add(cmd)

for cmd in sorted(commands):
    print(cmd)
