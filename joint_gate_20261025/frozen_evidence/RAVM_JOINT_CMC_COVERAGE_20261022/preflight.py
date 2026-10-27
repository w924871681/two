"""Read-only authentication; no data generation, optimizer update or parameter selection."""
from common import *
import csv,re,subprocess,sys,threading,zipfile
sys.path.insert(0,str(ROOT/'engineering/throughput'))
from dispatch import execute

def run():
    stage('PREFLIGHT','RUNNING');state(status='RUNNING',phase='PREFLIGHT',work='主Final ZIP 身份核验',completed=0,total=1,unit='个文件')
    archive=PRIOR/'delivery/NEW_FINAL_EXPERIMENT_RETURN.zip';expected='bb7e55c1c40f0a7093cc97b50611b09cd5cebc05fad93b80b4290ff4fee3b6cc'
    actual=sha(archive);assert actual==expected,'STOP_ASSET_IDENTITY_MISMATCH'
    completed=read(PRIOR/'delivery/PACKAGE_VERIFICATION.json');assert completed['status']=='PASS' and completed['sha256']==actual
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read('RETURN_MANIFEST_SHA256.json'))
        assert set(z.namelist())==set(manifest)|{'RETURN_MANIFEST_SHA256.json'}
        assert len(z.namelist())==completed['members']
        for n in ('NEW_FINAL_MAIN_REPORT_ZH.md','NEW_FINAL_MAIN_GATE.json','FINAL_COVERAGE_STATUS.json','D3F2_EXECUTION.lock.json','DEVCAL_SELECTED_LOCK.json'):
            data=z.read(n);assert hashlib.sha256(data).hexdigest()==manifest[n]['sha256']==sha(PRIOR/n)
    # The closed ZipFile still retains 247,959 directory entries; release before CAS work.
    del z,manifest,data
    import gc
    gc.collect()
    passport=dict(status='AUTHENTICATING',at_unix=time.time(),main_zip=dict(path=str(archive),sha256=actual,bytes=archive.stat().st_size,members=completed['members']),source_assets={},checkpoint_sources={})
    atomic(ROOT/'00_ASSET_PASSPORT.json',passport)
    source=read(PRIOR/'DEVCAL_SELECTED_LOCK.json')
    baseline=dict(status='FROZEN_FROM_PASSED_MAIN',parent_execution_lock_sha256=sha(PRIOR/'D3F2_EXECUTION.lock.json'),
        selected_lock_sha256=sha(PRIOR/'DEVCAL_SELECTED_LOCK.json'),joint=source['candidate'],baselines=source['baseline_selection'],
        legacy=read(PRIOR/'reference/LEGACY_BASELINE_IMPLEMENTATION_IDENTITY.json'),new_parameter_selection=False)
    atomic(ROOT/'03_BASELINE_IDENTITY_LOCK.json',baseline)
    index=read(PRIOR/'CAS_EXTERNAL_INDEX.json');weights=index['rows'];assert len(weights)==87696
    count=0;verified_bytes=0;mutex=threading.RLock()
    def check(part):
        nonlocal count,verified_bytes
        for row in part:
            path=(PRIOR/row['path']).resolve();assert path.is_relative_to(PRIOR.resolve())
            assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256']
        with mutex:count+=len(part);verified_bytes+=sum(x['bytes'] for x in part)
        return len(part)
    def tick(q):state(phase='PREFLIGHT',work='外置模型 SHA256 核验',completed=count,total=len(weights),unit='个模型文件',active_workers=q['active_workers'],eta_seconds=q['eta_seconds'])
    execute([weights[i:i+64] for i in range(0,len(weights),64)],check,'PREFLIGHT_EXTERNAL_CAS_SHA',on_tick=tick,cpu=True,progress_snapshot=lambda:(verified_bytes,count))
    passport['external_CAS']=dict(status='PASS',index_sha256=sha(PRIOR/'CAS_EXTERNAL_INDEX.json'),verified_files=count,verified_bytes=verified_bytes)
    atomic(ROOT/'00_ASSET_PASSPORT.json',passport)
    state(work='历史中心身份扫描',completed=0,total=0,unit='个路径')
    fresh=set(range(64000,64024))|set(range(64100,64124));conflicts=[];metadata={};path_count=0
    def declared_ids(value):
        if isinstance(value,int) and not isinstance(value,bool):return {value}
        if isinstance(value,str):return {int(x) for x in re.findall(r'(?<!\d)(\d{5})(?!\d)',value)}
        if isinstance(value,list):return set().union(*(declared_ids(x) for x in value)) if value else set()
        if isinstance(value,dict):return set().union(*(declared_ids(x) for x in value.values())) if value else set()
        return set()
    for base in (ROOT.parent,Path('D:/dt-trustworthy-maintenance')):
        proc=subprocess.Popen(['rg','--files','--hidden','-g','!**/.git/**','-g','!**/node_modules/**','-g','!**/_parquet_deps/**',str(base)],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        for line in proc.stdout:
            path=Path(line.strip())
            if path.is_relative_to(ROOT):continue
            path_count+=1
            found={int(x) for x in path.parts if x.isdigit()}&fresh
            found|={int(x) for x in re.findall(r'(?:center_|M0_[A-Za-z0-9_]*_)(64\d{3})(?:_|\.|$)',path.name)}&fresh
            if found:conflicts.append(dict(path=str(path),ids=sorted(found),kind='materialized'))
            if path.name.lower() in ('historical_id_registry.json','run_manifest.json','data_role_boundaries.json') or path.name.lower().endswith(('identity_registry.json','center_registry.json')):
                value=read(path);decl={k:v for k,v in value.items() if any(s in k.lower() for s in ('center','pool','reserved','known_old_ids'))}
                found=declared_ids(decl)&fresh;metadata[str(path)]=dict(sha256=sha(path),conflicts=sorted(found))
                if found:conflicts.append(dict(path=str(path),ids=sorted(found),kind='registered'))
            if path_count%25000==0:state(completed=path_count,total=0,unit='个路径')
        assert proc.wait()==0
    center_receipt=dict(status='PASS' if not conflicts else 'COLLISION_STOP',planned_ids=sorted(fresh),path_count=path_count,metadata=metadata,conflicts=conflicts,metrics_not_read=True)
    atomic(ROOT/'assets/CENTER_IDENTITY_AUDIT.json',center_receipt)
    passport['center_identity']=dict(status=center_receipt['status'],conflicts=conflicts,path_count=path_count)
    # Fully read source modules/configurations; never execute their training runners.
    dirs=[Path('D:/dt-trustworthy-maintenance/core'),Path('D:/dt-trustworthy-maintenance/scripts'),Path('D:/dt-trustworthy-maintenance/configs_v2_final')]
    selected=[]
    for base in dirs:
        selected += [p for p in base.glob('*') if p.is_file() and p.suffix in ('.py','.yaml','.json')]
    selected += list((ROOT/'assets/original14').rglob('*.tex'))
    selected += [ROOT.parent/'paper2_revision_execution_20261012/code/revision_building.py',ROOT.parent/'paper2_revision_round2_20261013/code/thermal_study.py']
    for path in selected:
        wire=path.read_bytes();passport['source_assets'][str(path)]=dict(sha256=hashlib.sha256(wire).hexdigest(),bytes=len(wire),read_complete=True)
    state(work='跨架构源 checkpoint 与 PDF 认证',completed=0,total=18,unit='份 checkpoint')
    # Independent child imports the original model definition, with every optimizer step forbidden.
    p=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'authenticate_interfaces.py')],cwd=ROOT,capture_output=True,text=True,encoding='utf8')
    (ROOT/'process/interface_auth.stdout.log').write_text(p.stdout,encoding='utf8');(ROOT/'process/interface_auth.stderr.log').write_text(p.stderr,encoding='utf8')
    assert p.returncode==0,p.stderr[-4000:]
    passport['interfaces']=read(ROOT/'assets/INTERFACE_AUTH.json')
    passport['pdfs']=read(ROOT/'assets/PDF_READ_RECEIPT.json')
    passport.update(status='PASS_FOR_E0',at_unix=time.time(),optimizer_steps=0)
    atomic(ROOT/'00_ASSET_PASSPORT.json',passport)
    stage('PREFLIGHT','PASS',center_identity=center_receipt['status'],optimizer_steps=0)
    atomic(ROOT/'PREFLIGHT_RECEIPT.json',dict(status='PASS_FOR_E0',at_unix=time.time(),passport_sha256=sha(ROOT/'00_ASSET_PASSPORT.json'),no_training=True))
    return passport
if __name__=='__main__':run()
