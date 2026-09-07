import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from core.protocol import ROOT,POOLS,save_json

def main():
    ids=set(sum(POOLS.values(),[]));checked=[];collisions=[];errors=[]
    roots=[Path('D:/dt-talk/repository/results'),Path('D:/dt-talk/v127_freeze_clean/results')]
    for root in roots:
        for p in root.rglob('*.csv'):
            try:
                columns=pd.read_csv(p,nrows=0).columns
                wanted=[c for c in columns if c.lower() in ['center_id','target_center_id','source_center_id']]
                if not wanted:continue
                for chunk in pd.read_csv(p,usecols=wanted,chunksize=100000):
                    for c in wanted:
                        overlap=set(pd.to_numeric(chunk[c],errors='coerce').dropna().astype(int))&ids
                        if overlap:collisions.append({'path':str(p),'column':c,'ids':sorted(overlap)})
                checked.append(str(p))
            except pd.errors.EmptyDataError:continue
            except Exception as e:errors.append({'path':str(p),'error':str(e)})
    save_json(ROOT/'audits/legacy_pool_scan.json',{'roots':[str(r) for r in roots],'checked_files':checked,'collisions':collisions,'read_errors':errors,'status':'passed' if not collisions and not errors else 'STOP'})
    print('legacy pool scan',len(checked),'files',len(collisions),'collisions',len(errors),'errors',flush=True)
    assert not collisions and not errors,'legacy pool conflict/unreadable inputs'

if __name__=='__main__':main()
