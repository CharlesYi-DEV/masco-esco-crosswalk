"""Verify immutable aggregate experiment snapshots without private source data."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / 'experiments'
MANIFEST = EXPERIMENTS / 'SHA256SUMS'

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def snapshot_files():
    return sorted(p for p in EXPERIMENTS.rglob('*')
                  if p.is_file() and p != MANIFEST and '__pycache__' not in p.parts)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true', help='Freeze reviewed snapshot additions')
    args = parser.parse_args()
    registry = json.loads((EXPERIMENTS / 'index.json').read_text())
    ids = {e['id'] for e in registry['experiments']}
    if len(ids) != len(registry['experiments']):
        raise ValueError('Duplicate experiment ID')
    for e in registry['experiments']:
        if not (EXPERIMENTS / e['path'] / 'README.md').is_file():
            raise ValueError('Missing experiment documentation')
        if e['parent'] is not None and e['parent'] not in ids:
            raise ValueError('Unknown parent experiment')
    # Historical run hashes must resolve to retained executed source snapshots.
    for e in registry['experiments']:
        folder = EXPERIMENTS / e['path'] / 'provenance'
        sources = {digest(p) for p in (folder / 'executed-source').glob('*.py')}
        runfiles = list((folder / 'runs').glob('*.json'))
        if (folder / 'run.json').exists():
            runfiles.append(folder / 'run.json')
        for p in runfiles:
            record = json.loads(p.read_text())
            if record['script_sha256'] not in sources:
                raise ValueError(f'No executed source matching {p.relative_to(ROOT)}')
    actual = {str(p.relative_to(ROOT)): digest(p) for p in snapshot_files()}
    if args.write:
        MANIFEST.write_text(''.join(f'{h}  {p}\n' for p, h in actual.items()))
    else:
        expected = {}
        for line in MANIFEST.read_text().splitlines():
            h, p = line.split(None, 1)
            expected[p] = h
        if actual != expected:
            changed = sorted(p for p in actual.keys() | expected.keys() if actual.get(p) != expected.get(p))
            raise ValueError('Snapshot mismatch: ' + ', '.join(changed))
    print(f'Verified {len(registry["experiments"])} experiments and {len(actual)} snapshot files')

if __name__ == '__main__':
    main()
