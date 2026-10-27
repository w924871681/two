from pathlib import Path
import hashlib
root=Path(__file__).resolve().parent
count=0
for line in (root/'SHA256SUMS.txt').read_text('utf-8').splitlines():
    digest,name=line.split('  ',1)
    path=root/name
    with path.open('rb') as file: actual=hashlib.file_digest(file,'sha256').hexdigest()
    if actual!=digest: raise SystemExit('SHA256 mismatch: '+name)
    count+=1
print('PASS: '+str(count)+' files match SHA256SUMS.txt')
