"""Prove that acceleration changes physical reuse only, not scientific outputs."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,time
import numpy as np
import pandas as pd
from core.protocol import ROOT,save_json
from core.engine import run
from scripts.run_calibration import calibration_definition

EXCLUDED={'run_id','candidate_update_time_s','verification_time_s','maintenance_time_s','peak_gpu_memory_bytes'}

def assert_equal(a,b,label,exact=True):
    cols=[c for c in a.columns if c not in EXCLUDED]
    assert cols==[c for c in b.columns if c not in EXCLUDED]
    pd.testing.assert_frame_equal(a[cols],b[cols],check_exact=exact,rtol=0,atol=0 if exact else 1e-14,check_dtype=False,obj=label)
    return len(cols)

def main():
    archives=sorted((ROOT/'archive').glob('pre_acceleration_*'))
    assert archives,'pre-acceleration archive missing'
    archive=archives[-1];candidate,_,_,_,jobs=calibration_definition('synthetic')
    cases=[(0,'clean',0.),(189,'mixed',.1)]
    report={'status':'running','archive':str(archive),'cases':[],'excluded_non_scientific_columns':sorted(EXCLUDED)}
    for policy,kind,alpha in cases:
        method,settings=jobs[policy]
        old=pd.read_csv(archive/'results/calibration'/f'policy{policy:03d}_7311_12000_{kind}.csv')
        timings=[];frames=[]
        for cache in [False,True,True]:
            start=time.perf_counter()
            frames.append(pd.DataFrame(run(12000,7311,method,kind,alpha,
                cfg={**candidate,**settings,'calibration_candidate_cache':cache,'calibration_evidence_cache':cache},
                run_id=f'acceleration_audit_{policy}_{cache}')))
            timings.append(time.perf_counter()-start)
        checked=assert_equal(old,frames[0],f'archive_vs_uncached_policy_{policy}',exact=False)
        assert_equal(frames[0],frames[1],f'uncached_vs_cold_cache_policy_{policy}')
        assert_equal(frames[0],frames[2],f'uncached_vs_warm_cache_policy_{policy}')
        report['cases'].append({'policy':policy,'condition':kind,'stages':len(old),'scientific_columns_checked':checked,
            'archive_vs_uncached':'equal_within_1e-14_csv_roundtrip_tolerance','uncached_vs_cold_cache':'bit_exact','uncached_vs_warm_cache':'bit_exact',
            'elapsed_s':{'uncached':timings[0],'cold_cache':timings[1],'warm_cache':timings[2]},
            'warm_cache_speedup':timings[0]/timings[2]})
        save_json(ROOT/'audits/acceleration_equivalence.json',report)
    report['status']='passed';report['cache_paths_bit_exact']=True;report['archive_comparison_tolerance']=1e-14
    save_json(ROOT/'audits/acceleration_equivalence.json',report)
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
