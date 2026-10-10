"""Read-only verification of the published source and experiment snapshot."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    manifest = json.loads((ROOT / 'docs/source_snapshot_manifest.json').read_text(encoding='utf-8'))

    def check(item):
        path = ROOT / item['path']
        if not path.is_file():
            return 'missing: ' + item['path']
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            return 'hash mismatch: ' + item['path']
        return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        errors = [result for result in pool.map(check, manifest['files']) if result]
    counts = {}
    for directory, expected in manifest['formal_trajectory_csv_counts'].items():
        counts[directory] = len(list((ROOT / directory / 'trajectories').glob('*.csv')))
        if counts[directory] != expected:
            errors.append(f'{directory}: expected {expected}, got {counts[directory]}')
    archive = ROOT / 'paper/RAVM_DT_CMC_14Pages_Final_Contrib.zip'
    with zipfile.ZipFile(archive) as z:
        embedded = z.read('RAVM_DT_CMC_14Pages_Final_Contrib/main.pdf')
        if hashlib.sha256(embedded).hexdigest() != digest(ROOT / 'paper/RAVM_DT.pdf'):
            errors.append('Paper PDF differs from the original submission ZIP')
    result = {'status': 'PASS' if not errors else 'FAIL',
              'snapshot_files_checked': len(manifest['files']),
              'formal_trajectory_counts': counts,
              'formal_trajectory_total': sum(counts.values()),
              'errors': errors}
    print(json.dumps(result, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
