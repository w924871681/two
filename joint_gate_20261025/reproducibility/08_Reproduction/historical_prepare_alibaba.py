"""Read original archive in streaming mode; never interpolate using future telemetry."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import hashlib,json,tarfile,re,time,io
import numpy as np
import pandas as pd
from core.protocol import ROOT,save_json,digest

ARCHIVE=Path('D:/RCF_DTI_pre_submission/data/alibaba2018/raw/machine_usage.tar.gz')
EXPECTED='3e6ee87fd204bb85b9e234c5c75a5096580fdabc8f085b224033080090753a7a'

def chunks():
    class Reader(io.RawIOBase):
        def __init__(self,raw):self.raw=raw
        def readable(self):return True
        def readinto(self,b):
            a=self.raw.read(len(b));b[:len(a)]=a;return len(a)
    with tarfile.open(ARCHIVE,'r|gz') as tf:
        for member in tf:
            if member.isfile() and Path(member.name).name=='machine_usage.csv':
                reader=io.BufferedReader(Reader(tf.extractfile(member)))
                yield from pd.read_csv(reader,header=None,usecols=[0,1,2,3,4,5,6,7,8],chunksize=1000000)
                return
    raise FileNotFoundError('machine_usage.csv')

def main():
    h=hashlib.sha256()
    with ARCHIVE.open('rb') as f:
        while b:=f.read(8*1024*1024):h.update(b)
    assert h.hexdigest()==EXPECTED,'Alibaba archive checksum mismatch'
    save_json(ROOT/'audits/alibaba_archive.json',{'path':str(ARCHIVE),'sha256':h.hexdigest(),'status':'verified'})
    excluded=set()
    for p in Path('D:/dt-talk/v127_freeze_clean/results').rglob('*.json'):
        text=p.read_text(encoding='utf-8',errors='replace')
        excluded.update(re.findall(r'"machine_id_hash"\s*:\s*"([0-9a-f]{64})"',text))
    counts={};seen=0
    for d in chunks():
        valid=d[d[2].between(0,100)&d[1].notna()]
        for mid,n in valid[0].value_counts().items():counts[str(mid)]=counts.get(str(mid),0)+int(n)
        seen+=len(d);print('Alibaba count',seen,flush=True)
    # Old public split is hash-ranked; exclude its first 80 eligible machines too.
    eligible=[m for m,n in counts.items() if n>=16760]
    old_order=sorted(eligible,key=lambda m:hashlib.sha256(m.encode()).hexdigest())
    excluded.update(hashlib.sha256(m.encode()).hexdigest() for m in old_order[:80])
    selected=sorted([m for m in eligible if hashlib.sha256(m.encode()).hexdigest() not in excluded],key=lambda m:hashlib.sha256(('7311:'+m).encode()).hexdigest())[:100]
    if len(selected)<100:raise RuntimeError('Need 100 fresh eligible machines for fixed 24-stage external protocol; do not choose based on outcomes')
    blocks={m:[] for m in selected}
    for d in chunks():
        d=d[d[0].isin(selected)]
        for mid,g in d.groupby(0):blocks[mid].append(g)
    manifest=[]
    for i,mid in enumerate(selected):
        d=pd.concat(blocks[mid]).drop_duplicates(1).sort_values(1)
        d=d[d[2].between(0,100)&d[1].notna()].iloc[:17000]
        if len(d)<16760:raise RuntimeError('Insufficient unique valid timestamps after deduplication: '+mid)
        raw=d.iloc[:,2:9].to_numpy(dtype='float32');mask=np.isfinite(raw)&(raw>=0)
        # Known percentages only; mkpi has no declared scale, so leave that metric unavailable.
        mask[:,3]=False;mask&=raw<=100
        values=np.where(mask,raw/100,0)
        xx=np.zeros((len(d),12),dtype='float32');mm=xx.copy();xx[:,:7]=values;mm[:,:7]=mask
        x=np.concatenate([xx,mm],1);y=raw[:,0]/100;ts=d[1].to_numpy(dtype='int64')
        assert np.all(np.diff(ts)>0)
        pool='source' if i<20 else 'development' if i<40 else 'calibration' if i<60 else 'heldout'
        center=20000+i;meta={'center_id':center,'center_type':'external','drift_regime':'production','pool':pool,'domain':'alibaba','machine_id_hash':hashlib.sha256(mid.encode()).hexdigest(),'clean_hash':digest(x,y,ts)}
        np.savez_compressed(ROOT/'data'/f'center_{center}.npz',x=x,y=y,ts=ts,meta=json.dumps(meta));manifest.append(meta)
    save_json(ROOT/'alibaba_pool_manifest.json',{'machines':manifest,'excluded_hashes':sorted(excluded),'archive_sha256':EXPECTED,'stages':24,'normalization':'known percent metrics /100; mkpi unavailable; zero-fill missing with mask','time_handling':'sorted original unique valid-target observations, no interpolation, irregular timestamps retained'})

if __name__=='__main__':main()
