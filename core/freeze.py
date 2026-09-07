import hashlib,json
from core.protocol import ROOT,save_json

def hash_file(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def freeze_file(name,cfg):
    p=ROOT/'configs'/name
    if p.exists():assert json.loads(p.read_text())==cfg,'refuse to change frozen configuration'
    else:save_json(p,cfg)
    p.with_suffix('.sha256').write_text(hash_file(p)+'\n')
    return hash_file(p)

def require_frozen(manifest=None):
    path=manifest or ROOT/'audits/final_freeze.json'
    obj=json.loads(path.read_text())
    for rel,h in obj['files'].items():assert hash_file(ROOT/rel)==h,'frozen file changed: '+rel
    audits=json.loads((ROOT/'audits/protocol_tests.json').read_text())
    assert audits['status']=='passed' and not audits['skipped']
    assert obj['status']=='ready_for_heldout'
    return obj
