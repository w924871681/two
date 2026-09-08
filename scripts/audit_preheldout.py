import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,itertools,subprocess,hashlib
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
    acceleration=json.loads((ROOT/'audits/acceleration_equivalence.json').read_text())
    assert acceleration['status']=='passed' and acceleration['cache_paths_bit_exact']
    concurrency=json.loads((ROOT/'audits/cache_concurrency.json').read_text())
    assert concurrency['status']=='passed' and concurrency['outputs_identical']
    equivalence=json.loads((ROOT/'audits/joint_dag_equivalence.json').read_text());assert equivalence['status']=='passed' and equivalence['all_scientific_equivalence_pass']
    protocol=json.loads((ROOT/'audits/joint_dag_protocol.json').read_text());assert protocol['status']=='passed' and protocol['checks']['formal_runner_switched_to_joint_dag']
    migration=json.loads((ROOT/'audits/cache_migration.json').read_text());assert migration['status']=='passed'
    identity=json.loads((ROOT/'audits/formal_p6_implementation.json').read_text());assert identity['status']=='approved_for_formal_p6'
    manifest=json.loads((ROOT/'audits/execution_code_manifest.json').read_text())['files']
    for rel in ['core/joint_dag.py','core/engine.py','core/models.py','core/protocol.py']:
        assert hash_file(ROOT/rel)==manifest[rel],f'formal P6 implementation changed during calibration: {rel}'
    for rel in ['scripts/run_calibration_joint_dag.py','scripts/run_calibration_joint_dag_parallel.py','scripts/run_calibration.py']:
        committed=subprocess.check_output(['git','show',f"{identity['git_sha']}:{rel}"],cwd=ROOT)
        assert hashlib.sha256(committed).hexdigest()==manifest[rel],f'formal P6 commit provenance mismatch: {rel}'
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
        assert set(d.implementation_git_sha)=={identity['git_sha']}
        assert set(d.joint_dag_implementation_sha256)=={identity['joint_dag_sha256']}
        count+=1
    assert count==405*20*3*2
    # Independent execution comparison of cached/uncached candidate transitions.
    from core.engine import run
    a=pd.DataFrame(run(11000,7311,'Proposed','mixed',.1,cfg={'calibration_candidate_cache':False,'calibration_evidence_cache':False},stages=2,smoke=True))
    b=pd.DataFrame(run(11000,7311,'Proposed','mixed',.1,cfg={'calibration_candidate_cache':True,'calibration_evidence_cache':True},stages=2,smoke=True))
    c=pd.DataFrame(run(11000,7311,'Proposed','mixed',.1,cfg={'calibration_candidate_cache':True,'calibration_evidence_cache':True},stages=2,smoke=True))
    cols=['parent_state_hash','candidate_state_hash','commit','U_rec','U_hist','deployed_service_mse','service_data_hash','attack_mask_hash']
    pd.testing.assert_frame_equal(a[cols],b[cols]);pd.testing.assert_frame_equal(a[cols],c[cols])
    assert not (ROOT/'results/heldout').exists()
    frozen=json.loads((ROOT/'configs/frozen_commit_config.yaml').read_text());frozen_hash=hash_file(ROOT/'configs/frozen_commit_config.yaml')
    selected_details={'status':'passed','selected_configuration':frozen,'selected_kappa_rec':frozen.get('kappa_rec'),'selected_kappa_hist':frozen.get('kappa_hist'),
        'selected_delta_imp':frozen.get('delta_imp'),'selected_delta_ret':frozen.get('delta_ret'),'calibration_objective':'minimum lifecycle_mse among eligible policies, tie broken by policy index',
        'feasibility_criterion':json.loads((ROOT/'configs/calibration_protocol.yaml').read_text())['eligibility'],
        'fallback_triggered':bool(frozen.get('retain_all') or frozen.get('validation_retain_all')),'frozen_config_sha256':frozen_hash,
        'formal_p6_git_sha':identity['git_sha'],'heldout_accessed':False}
    save_json(ROOT/'audits/calibration_selection_provenance.json',selected_details)
    results.update({'calibration_complete_trajectories':count,'candidate_and_evidence_cache_equivalence':'passed','all_14_protocol_tests':'passed',
        'legacy_pool_collision_scan':'passed','acceleration_equivalence':'passed','cache_concurrency':'passed','joint_dag_equivalence':'passed',
        'joint_dag_protocol':'passed','cache_migration':'passed','single_implementation_git_sha':identity['git_sha'],
        'calibration_selection_provenance':'passed','frozen_commit_config_sha256':frozen_hash,'heldout_accessed_before_audit':False})
    save_json(ROOT/'audits/heldout_readiness.json',{'status':'approved_by_implementation_audit','heldout_may_start':True,'checks':results,'baseline_limitations':['CLeaR predictor-only framework adaptation','MER-Reg-2026 unavailable, omitted as preregistered'],'scope':'Executable integrity and completeness audit, not external scientific peer review'})
    subprocess.run([sys.executable,str(ROOT/'scripts/profile_remaining_matrix.py')],cwd=ROOT,check=True)

if __name__=='__main__':main()
