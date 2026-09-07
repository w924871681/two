import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,itertools
import numpy as np
import pandas as pd
from core.protocol import ROOT,save_json,POOLS
from core.freeze import hash_file

def main():
    results={}
    for name in ['frozen_candidate_config.yaml','frozen_commit_config.yaml','frozen_baseline_config.yaml','calibration_protocol.yaml']:
        p=ROOT/'configs'/name;assert hash_file(p)==p.with_suffix('.sha256').read_text().strip();results[name]='hash_verified'
    for name in ['protocol_tests.json','legacy_pool_scan.json']:
        obj=json.loads((ROOT/'audits'/name).read_text());assert obj['status']=='passed'
        if name=='protocol_tests.json':assert not obj['skipped'] and obj['tests_run']>=14
    grid=pd.read_csv(ROOT/'calibration_grid.csv');assert len(grid)==405
    assert set(grid.policy)==set(range(405))
    summary=json.loads((ROOT/'calibration_summary.json').read_text())
    for method in ['Proposed','ValidationCommit']:
        g=grid[(grid.method==method)&grid.eligible]
        selected=summary[method]
        if len(g):assert selected['selected_policy']==int(g.sort_values(['lifecycle_mse','policy']).iloc[0].policy)
        else:assert selected['status']=='calibration_failure_retain_all'
    # Check completeness at whole trajectories, not mere file existence.
    count=0
    for p in (ROOT/'results/calibration').glob('policy*.csv'):
        d=pd.read_csv(p)
        assert len(d)==24 and set(d.stage)==set(range(1,25))
        assert set(d.center_id)<=set(POOLS['calibration'])
        assert (d.decision_ts<d.service_start_ts).all()
        assert np.isfinite(d.deployed_service_mse).all()
        count+=1
    assert count==405*20*3*2
    # Independent execution comparison of cached/uncached candidate transitions.
    from core.engine import run
    a=pd.DataFrame(run(11000,7311,'Proposed','mixed',.1,cfg={'calibration_candidate_cache':False},stages=2,smoke=True))
    b=pd.DataFrame(run(11000,7311,'Proposed','mixed',.1,cfg={'calibration_candidate_cache':True},stages=2,smoke=True))
    c=pd.DataFrame(run(11000,7311,'Proposed','mixed',.1,cfg={'calibration_candidate_cache':True},stages=2,smoke=True))
    cols=['parent_state_hash','candidate_state_hash','commit','U_rec','U_hist','deployed_service_mse','service_data_hash','attack_mask_hash']
    pd.testing.assert_frame_equal(a[cols],b[cols]);pd.testing.assert_frame_equal(a[cols],c[cols])
    results.update({'calibration_complete_trajectories':count,'candidate_cache_equivalence':'passed','all_14_protocol_tests':'passed','legacy_pool_collision_scan':'passed'})
    save_json(ROOT/'audits/heldout_readiness.json',{'status':'approved_by_implementation_audit','heldout_may_start':True,'checks':results,'baseline_limitations':['CLeaR predictor-only framework adaptation','MER-Reg-2026 unavailable, omitted as preregistered'],'scope':'Executable integrity and completeness audit, not external scientific peer review'})

if __name__=='__main__':main()
