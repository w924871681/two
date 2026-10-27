"""Recheck historical registered/materialized identities immediately before sealing."""
from common import *
import re,subprocess
def verify():
    fresh=set(range(64000,64024))|set(range(64100,64124));conflicts=[];count=0
    old=read(ROOT/'assets/CENTER_IDENTITY_AUDIT.json');assert old['status']=='PASS';changed=[];errors=[];registries={}
    def ids_in(value):
        if isinstance(value,int)and not isinstance(value,bool):return {value}
        if isinstance(value,str):return {int(x)for x in re.findall(r'(?<!\d)(\d{5})(?!\d)',value)}
        if isinstance(value,(list,dict)):
            seq=value.values()if isinstance(value,dict)else value
            return set().union(*(ids_in(v)for v in seq))if value else set()
        return set()
    for base in (ROOT.parent,Path('D:/dt-trustworthy-maintenance')):
        p=subprocess.Popen(['rg','--files','--hidden','-g','!**/.git/**','-g','!**/node_modules/**','-g','!**/_parquet_deps/**',str(base)],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        for line in p.stdout:
            path=Path(line.strip())
            if path.is_relative_to(ROOT):continue
            count+=1
            ids={int(x)for x in path.parts if x.isdigit()}&fresh
            ids|={int(x)for x in re.findall(r'(?:center_|M0_[A-Za-z0-9_]*_)(64\d{3})(?:_|\.|$)',path.name)}&fresh
            if ids:conflicts.append(dict(path=str(path),ids=sorted(ids)))
            name=path.name.lower()
            if name in ('historical_id_registry.json','run_manifest.json','data_role_boundaries.json')or name.endswith(('identity_registry.json','center_registry.json')):
                try:
                    value=read(path);decl={k:v for k,v in value.items()if any(s in k.lower()for s in('center','pool','reserved','known_old_ids'))};ids=ids_in(decl)&fresh;digest=sha(path);registries[str(path)]=digest
                    if ids:conflicts.append(dict(path=str(path),ids=sorted(ids),kind='registered'))
                    if str(path)not in old['metadata']or old['metadata'][str(path)]['sha256']!=digest:changed.append(str(path))
                except Exception as e:errors.append(dict(path=str(path),error=str(e)))
        assert p.wait()==0
    receipt=dict(status='BLOCKED_UNREADABLE_REGISTRY'if errors else'PASS'if not conflicts else'COLLISION_STOP',paths=count,conflicts=conflicts,registry_sha256=registries,changed_or_new_registries_reauthenticated=changed,errors=errors,optimizer_steps=0,at_unix=time.time())
    atomic(ROOT/'assets/CENTER_IDENTITY_PRESEAL_REFRESH.json',receipt);return receipt
