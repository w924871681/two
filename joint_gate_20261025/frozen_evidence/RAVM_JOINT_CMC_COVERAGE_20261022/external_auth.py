"""Authenticate Alibaba raw-to-preprocessed identity; no model evaluation."""
from common import *
import numpy as np
import pandas as pd
import tarfile,sqlite3,io
class ForwardReader(io.RawIOBase):
    def __init__(self,source):self.source=source
    def readable(self):return True
    def readinto(self,b):
        value=self.source.read(len(b));b[:len(value)]=value;return len(value)

EXPECTED_ARCHIVE='3e6ee87fd204bb85b9e234c5c75a5096580fdabc8f085b224033080090753a7a'
EXPECTED_POOL='55918806ab6b71d206a944415465d449a2d0463a5befaa8adb06c90508df5d89'
EXPECTED_PREPARE='a102cace8dd79aba18bae57f2288de54d8f96e61826a4d830faa95fad1ad9075'

def authenticate():
    source=Path('D:/dt-trustworthy-maintenance')
    assert sha(source/'alibaba_pool_manifest.json')==EXPECTED_POOL
    assert sha(source/'scripts/prepare_alibaba.py')==EXPECTED_PREPARE
    pool=read(source/'alibaba_pool_manifest.json');machines=[m for m in pool['machines'] if m['pool']=='heldout']
    assert [m['center_id'] for m in machines]==list(range(20060,20100)) and len({m['machine_id_hash']for m in machines})==40
    archive=Path('D:/dt-talk/new_exercise_revised/data/real/alibaba2018/machine_usage.tar.gz')
    assert sha(archive)==EXPECTED_ARCHIVE,'Raw Alibaba archive identity mismatch'
    expected={m['machine_id_hash']:m for m in machines}
    output=META_OUTPUT=STORAGE/'asset_auth';output.mkdir(parents=True,exist_ok=True)
    database=output/'alibaba_raw_selected.sqlite'
    # A failed partial authentication is never treated as a complete selection.
    if database.exists() and not (ROOT/'assets/E3_ALIBABA_AUTH.json').exists():
        database=output/f'alibaba_raw_selected_attempt_{int(time.time())}.sqlite'
    if (ROOT/'assets/E3_ALIBABA_AUTH.json').exists():
        previous=read(ROOT/'assets/E3_ALIBABA_AUTH.json')
        if previous['status']=='PASS' and previous['archive_sha256']==EXPECTED_ARCHIVE:return previous
    conn=sqlite3.connect(database)
    conn.execute('CREATE TABLE IF NOT EXISTS obs(mid TEXT, ts REAL, a REAL,b REAL,c REAL,d REAL,e REAL,f REAL,g REAL,PRIMARY KEY(mid,ts)) WITHOUT ROWID')
    visited=0;selected=0;hashes={};batch=0
    stage('E3','AUTHENTICATING_RAW_DATA',detail='原始归档逐行核对40机器；不读旧方法科学结果')
    with archive.open('rb') as raw_archive,tarfile.open(fileobj=raw_archive,mode='r|gz') as tf:
        for member in tf:
            if not member.isfile() or Path(member.name).name!='machine_usage.csv':continue
            stream=io.BufferedReader(ForwardReader(tf.extractfile(member)))
            for frame in pd.read_csv(stream,header=None,usecols=list(range(9)),chunksize=100000):
                visited+=len(frame);batch+=1
                unique=frame[0].dropna().unique()
                for mid in unique:
                    key=str(mid)
                    if key not in hashes:hashes[key]=hashlib.sha256(key.encode()).hexdigest()
                mask=frame[0].map(lambda x:hashes.get(str(x))) .isin(expected)
                sub=frame.loc[mask].copy();sub[0]=sub[0].map(lambda x:hashes[str(x)]);sub=sub[sub[1].notna()]
                # SQLite keeps the first occurrence per machine/timestamp, including invalid targets,
                # matching original drop_duplicates(timestamp) before validity filtering.
                records=[]
                for row in sub.itertuples(index=False,name=None):records.append(tuple(None if pd.isna(x) else str(x) if i==0 else float(x) for i,x in enumerate(row)))
                if records:conn.executemany('INSERT OR IGNORE INTO obs VALUES (?,?,?,?,?,?,?,?,?)',records);selected+=len(records)
                if batch%10==0:conn.commit()
                atomic(ROOT/'engineering/E3_AUTH_PROGRESS.json',dict(status='STREAMING_RAW',raw_rows_scanned=visited,selected_rows_seen=selected,at_unix=time.time()))
                state(status='RUNNING',phase='ASSET_AUTH',work='Alibaba原始归档逐行认证（顺序解压单工作项）',completed=raw_archive.tell(),total=archive.stat().st_size,unit='压缩字节',raw_rows_scanned=visited)
            break
        else:raise FileNotFoundError('machine_usage.csv not found')
    conn.commit();rows=[]
    for machine_hash,item in expected.items():
        values=conn.execute('SELECT ts,a,b,c,d,e,f,g FROM obs WHERE mid=? AND a>=0 AND a<=100 ORDER BY ts LIMIT 17000',(machine_hash,)).fetchall()
        assert len(values)>=16760,(item['center_id'],'insufficient original valid observations')
        data=np.array([[np.nan if x is None else x for x in row] for row in values],dtype=np.float64)
        raw=data[:,1:].astype('float32');mask=np.isfinite(raw)&(raw>=0);mask[:,3]=False;mask &= raw<=100
        vals=np.where(mask,raw/100,0);xx=np.zeros((len(data),12),dtype='float32');mm=xx.copy();xx[:,:7]=vals;mm[:,:7]=mask
        x=np.concatenate([xx,mm],1);y=raw[:,0]/100;ts=data[:,0].astype('int64');assert np.all(np.diff(ts)>0)
        path=source/'data'/f'center_{item["center_id"]}.npz'
        with np.load(path,allow_pickle=False) as z:
            assert json.loads(str(z['meta']))==item
            assert np.array_equal(x,z['x']) and np.array_equal(y,z['y']) and np.array_equal(ts,z['ts']),('Raw derivation mismatch',item['center_id'])
        h=hashlib.sha256()
        for a in (x,y,ts):h.update(str(a.shape).encode());h.update(a.dtype.str.encode());h.update(a.tobytes())
        assert h.hexdigest()==item['clean_hash']
        rows.append(dict(center=item['center_id'],machine_id_hash=machine_hash,source_path=str(path),sha256=sha(path),clean_hash=item['clean_hash'],observations=len(data),features=24,physical_metrics=7,mask_channels=7,stages=24,last_service_end=16760))
    conn.close()
    sources={};m0=[]
    for seed in (7311,7312,7313):
        path=source/'checkpoints'/f'alibaba_source_GRU_H1_{seed}.pt';meta=read(path.with_suffix('.json'));digest=sha(path)
        for center in range(20060,20100):
            init=source/'checkpoints'/f'M0_GRU_H1_{seed}_{center}.pt';side=read(init.with_suffix('.json'))
            assert side['source_checkpoint_hash']==digest
            m0.append(dict(center=center,seed=seed,path=str(init),sha256=sha(init),sidecar=side))
        sources[str(seed)]=dict(path=str(path),sha256=digest,metadata=meta)
    result=dict(status='PASS',archive_path=str(archive),archive_sha256=EXPECTED_ARCHIVE,pool_sha256=EXPECTED_POOL,prepare_sha256=EXPECTED_PREPARE,
        rows=rows,sources=sources,existing_m0=m0,raw_rows_scanned=visited,independent_physical_machines=40,model_seeds=[7311,7312,7313],
        stages=24,original_validity_dedup_sort_and_units_exact=True,raw_machine_membership_exact=True,no_interpolation=True,
        seven_physical_metrics_mask_mkpi_unavailable_and_zero_padding_preserved=True,stage_schedule='original spans; 24th service ends at observation16760; prior service matures before next update',
        optimizer_steps=0,old_external_model_results_not_read=True,scope='historically exposed external machines; not new blind external confirmation',at_unix=time.time())
    atomic(ROOT/'assets/E3_ALIBABA_AUTH.json',result)
    stage('E3','AUTHENTICATED_DATA_PENDING_GATE_PORT_AUDIT',detail='40机器原始逐行复算匹配；不代表Joint已执行')
    return result
if __name__=='__main__':authenticate()
