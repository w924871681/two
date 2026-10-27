"""Dynamic local CAS SHA, parallel deflate and independent clean extraction checks."""
from common import *
import sys,zipfile,zlib,threading,shutil,collections
sys.path.insert(0,str(ROOT/'engineering/throughput'))
from dispatch import execute
from safe_paths import validate_infos,prepare_paths

def frozen():
    seal=read(ROOT/'SCIENCE_EXECUTION.lock.json')
    assert sha(PRIOR/'D3F2_EXECUTION.lock.json')==seal['main_execution_lock_sha256']
    for rel,h in read(PRIOR/'D3F2_EXECUTION.lock.json')['code_sha256'].items():assert sha(PRIOR/rel)==h,rel
    for rel,h in seal['implementation_sha256'].items():assert sha(ROOT/rel)==h,rel
    return True
def insert(z,info,data):
    # Same insert primitive as the prior CRC/SHA/extraction-validated delivery.
    info.header_offset=z.fp.tell();z._writecheck(info);z._didModify=True;z.fp.write(info.FileHeader(False));z.fp.write(data);z.filelist.append(info);z.NameToInfo[info.filename]=info;z.start_dir=z.fp.tell()
def pool(jobs,fn,label,unit='工作项',weight=None):
    total=sum(weight(j)for j in jobs)if weight else len(jobs);state(status='RUNNING',phase='DELIVERY',work=label,completed=0,total=total,unit='字节'if weight else unit)
    return execute(jobs,fn,label,cpu=True,work_weight=weight,on_tick=lambda z:state(completed=z['completed_weighted_work']if weight else z['completed'],total=z['total_weighted_work']if weight else z['total'],active_workers=z['active_workers'],status='RUNNING' if z['active_workers'] else 'WAITING_FOR_RESOURCE'))
def ordered_sha(path,label):
    counter={'bytes':0};total=path.stat().st_size;state(status='RUNNING',phase='DELIVERY',work=label,completed=0,total=total,unit='字节')
    def hash_one(p):
        h=hashlib.sha256()
        with p.open('rb')as f:
            for b in iter(lambda:f.read(4*2**20),b''):h.update(b);counter['bytes']+=len(b)
        return h.hexdigest()
    return execute([path],hash_one,label,cpu=True,on_tick=lambda z:state(completed=counter['bytes'],total=total,active_workers=z['active_workers'],status='RUNNING'if z['active_workers']else'WAITING_FOR_RESOURCE'),progress_snapshot=lambda:(counter['bytes'],counter['bytes']))[0]
def external_index():
    from model_store import BLOB_ROOTS
    blobs=[]
    for base,_ in BLOB_ROOTS:
        if base.exists():blobs.extend(p for p in base.glob('*/*') if p.is_file())
    def check(p):
        h=sha(p);assert h==p.name
        return dict(path=str(p),sha256=h,bytes=p.stat().st_size,weight_bytes_in_zip=False)
    rows=pool(blobs,check,'CAS_EXTERNAL_SHA256',weight=lambda p:p.stat().st_size)
    index=dict(status='PASS',rows=rows,unique_files=len(rows),unique_bytes=sum(r['bytes']for r in rows),all_weight_files_rehashed=True,main_final_weights_separate_index=str(PRIOR/'CAS_EXTERNAL_INDEX.json'),main_final_index_sha256=sha(PRIOR/'CAS_EXTERNAL_INDEX.json'),local_only=True)
    atomic(ROOT/'CAS_EXTERNAL_INDEX.json',index);return index

def collect():
    result=[]
    for base,dirs,names in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in ('__pycache__','delivery','progress','process')]
        for n in names:
            p=Path(base)/n
            if n.endswith(('.tmp','.pyc')) or 'PRIVATE' in n.upper():continue
            result.append((p.relative_to(ROOT).as_posix(),p))
    # Snapshot mutable operational logs, so the ZIP has a durable boundary.
    snapshot=STORAGE/'delivery_snapshot';snapshot.mkdir(exist_ok=True)
    for sub in ('process','progress'):
        for p in (ROOT/sub).rglob('*'):
            if not p.is_file()or p.suffix not in ('.json','.jsonl','.log','.md'):continue
            target=snapshot/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes());result.append((p.relative_to(ROOT).as_posix(),target))
    for base in (STORAGE/'groups',STORAGE/'statistics',STORAGE/'figures'):
        for folder,dirs,names in os.walk(base):
            dirs[:]=[d for d in dirs if d not in ('models','__pycache__')]
            for name in names:
                if name.endswith('.tmp')or'PRIVATE'in name.upper():continue
                p=Path(folder)/name;result.append(('storage/'+p.relative_to(STORAGE).as_posix(),p))
    # The exact prior execution source is included, without embedding its 502MB ZIP.
    for rel in read(PRIOR/'D3F2_EXECUTION.lock.json')['code_sha256']:result.append(('reference_main_source/'+rel,PRIOR/rel))
    result.append(('reference_main_source/D3F2_EXECUTION.lock.json',PRIOR/'D3F2_EXECUTION.lock.json'))
    for name in ('prepare_alibaba.py',):result.append(('reference_external_source/'+name,Path('D:/dt-trustworthy-maintenance/scripts')/name))
    for rel in ('alibaba_pool_manifest.json','audits_v2_alibaba/alibaba_protocol_provenance_audit.json','audits_v2_alibaba/alibaba_output_hash_manifest.json'):result.append(('reference_external_source/'+rel,Path('D:/dt-trustworthy-maintenance')/rel))
    for folder in ('paper2_revision_execution_20261012','paper2_revision_round2_20261013'):
        source=ROOT.parent/folder
        for p in (source/'code').rglob('*.py'):
            result.append(('historical_temperature_source/'+folder+'/'+p.relative_to(source).as_posix(),p))
        for p in (source/'audit').glob('*protocol_locked.json'):result.append(('historical_temperature_source/'+folder+'/audit/'+p.name,p))
    inv=ROOT.parent/'paper2_revision_round2_20261013/audit/thermal_data_inventory.json';result.append(('historical_temperature_source/thermal_data_inventory.json',inv))
    # Registered external raw assets and source checkpoints have explicit hashes.
    raw=[]
    for p in (ROOT/'registered_groups').glob('*.json'):
        spec=read(p)
        for row in spec['sources'].values():raw.append(dict(path=row['path'],sha256=row['sha256'],bytes=Path(row['path']).stat().st_size,kind='source_checkpoint'))
        for row in spec.get('data_files',[]):raw.append(dict(**row,bytes=Path(row['path']).stat().st_size,kind='external_raw_data'))
    auth=ROOT/'assets/E3_ALIBABA_AUTH.json'
    if auth.exists():
        item=read(auth);p=Path(item['archive_path']);raw.append(dict(path=str(p),sha256=item['archive_sha256'],bytes=p.stat().st_size,kind='original_alibaba_raw_archive'))
    atomic(ROOT/'EXTERNAL_INPUT_ASSET_INDEX.json',dict(rows=raw,assets_in_zip=False,original_data_not_fabricated=True,scope='local reproducibility with pinned external assets; not a self-contained full model archive'))
    result.append(('EXTERNAL_INPUT_ASSET_INDEX.json',ROOT/'EXTERNAL_INPUT_ASSET_INDEX.json'))
    mapping={}
    for n,p in result:
        if n in mapping:assert mapping[n]==p
        mapping[n]=p
    return sorted(mapping.items())

def archive(files,name,cap=None):
    dest=STORAGE/'delivery';dest.mkdir(parents=True,exist_ok=True);target=dest/name
    assert not target.exists(),'Preserve an existing package; no silent overwrite'
    manifest={};mutex=threading.RLock()
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,allowZip64=True)as z:
        def pack(part):
            for n,p in part:
                assert p.stat().st_size<2**30,'Large raw asset must be separately indexed'
                wire=p.read_bytes();h=hashlib.sha256(wire).hexdigest();co=zlib.compressobj(6,zlib.DEFLATED,-15);data=co.compress(wire)+co.flush();i=zipfile.ZipInfo(n);i.compress_type=zipfile.ZIP_DEFLATED;i.file_size=len(wire);i.compress_size=len(data);i.CRC=zlib.crc32(wire)&0xffffffff;i.external_attr=0o600<<16
                with mutex:manifest[n]=dict(bytes=len(wire),sha256=h);insert(z,i,data)
            return len(part)
        pool([files[i:i+32]for i in range(0,len(files),32)],pack,'DEFLATE_'+name.split('.')[0],weight=lambda part:sum(p.stat().st_size for _,p in part))
        wire=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
        pool([0],lambda _:z.writestr('RETURN_MANIFEST_SHA256.json',wire),'DEFLATE_ORDERED_MANIFEST_'+target.stem)
    if cap is not None:assert target.stat().st_size<cap,'Review ZIP exceeds registered cap; preserve package and report failure'
    expected={**manifest,'RETURN_MANIFEST_SHA256.json':dict(bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())}
    with zipfile.ZipFile(target)as z:
        names=pool([0],lambda _:validate_infos(z.infolist()),'ZIP_PATH_SAFETY_'+name.split('.')[0])[0]
        assert set(names)==set(expected)
        # Short owned root avoids Windows path-length growth from nested groups.
        clean_parent=STORAGE/'cx';clean_parent.mkdir(exist_ok=True);clean=clean_parent/('v'+format(time.time_ns(),'x'))
        if os.name=='nt':clean=Path('\\\\?\\'+str(clean.absolute()))
        root,targets=pool([0],lambda _:prepare_paths(clean,names),'ZIP_PRECREATE_DIRECTORIES_'+target.stem)[0]
        def extract(part):
            for n in part:
                target_file=targets[n];assert target_file.parent.resolve().is_relative_to(root)
                h=hashlib.sha256();size=0
                # ZipExtFile verifies CRC while reaching EOF.
                with z.open(n)as source,target_file.open('xb')as out:
                    while True:
                        b=source.read(2**20)
                        if not b:break
                        h.update(b);size+=len(b);out.write(b)
                    out.flush();os.fsync(out.fileno())
                assert size==expected[n]['bytes'] and h.hexdigest()==expected[n]['sha256'] and sha(target_file)==expected[n]['sha256']
                # Bounded disk clean extraction: every member is written to a new safe
                # path, independently rehashed, then only that verified file is removed.
                assert target_file.resolve().is_relative_to(root);target_file.unlink()
            return len(part)
        pool([names[i:i+128]for i in range(0,len(names),128)],extract,'ZIP_CRC_CLEAN_EXTRACT_SHA_'+target.stem,weight=lambda part:sum(expected[n]['bytes']for n in part))
    digest=ordered_sha(target,'ZIP_ORDERED_SHA_'+target.stem)
    receipt=dict(status='PASS',path=str(target),bytes=target.stat().st_size,archive_mtime_ns=target.stat().st_mtime_ns,sha256=digest,members=len(names),crc_pass=True,all_member_sha256_pass=True,exact_archive_member_set_pass=True,path_safety_pass=True,clean_extraction_pass=True,clean_extraction_mode='each member newly extracted, independently rehashed, verified file removed to bound disk; no persistent coexisting full extraction tree',target_CAS_weight_bytes_in_zip=False,included_source_or_m0_weight_files=sum(n.endswith('.pt')for n in names),under_512000000_bytes=target.stat().st_size<512000000,local_only=True)
    target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n',encoding='ascii');atomic(dest/(target.stem+'_VERIFICATION.json'),receipt);return receipt

def run():
    pool([0],lambda _:frozen(),'FROZEN_SOURCES_PRE_DELIVERY');index=external_index();files=collect()
    full=archive(files,'RAVM_JOINT_CMC_ALL_EXPERIMENTS_RETURN.zip')
    review=[(n,p)for n,p in files if not n.startswith('storage/groups/') and (not n.startswith(('progress/','process/'))or n.endswith('_SGD_CALL_ACCOUNTING.jsonl')) and not n.endswith('.pdf')]
    # Include complete statistics and all failed attempts, without per-stage raw ledger duplication.
    small=archive(review,'RAVM_JOINT_CMC_ALL_EXPERIMENTS_GPT_REVIEW.zip',512000000)
    pool([0],lambda _:frozen(),'FROZEN_SOURCES_POST_DELIVERY')
    report=ROOT/'RAVM_JOINT_ALL_EXPERIMENTS_REPORT_ZH.md'
    receipt=dict(status='PASS',full=full,review=small,report_sha256=pool([report],sha,'CHINESE_REPORT_FINAL_SHA')[0],all_external_model_sha256_pass=True,external_model_files=index['unique_files'],external_model_bytes=index['unique_bytes'],scientific_decision=read(ROOT/'SCIENTIFIC_GO_NO_GO.json')['status'],integrity_is_not_scientific_efficacy=True,at_unix=time.time())
    atomic(ROOT/'delivery/PACKAGE_VERIFICATION.json',receipt);atomic(STORAGE/'delivery/PACKAGE_VERIFICATION.json',receipt)
    return receipt
if __name__=='__main__':run()
