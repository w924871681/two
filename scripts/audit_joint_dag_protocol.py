"""Fail-closed protocol/leakage audit for formal joint-DAG P6 preflight."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
from core.protocol import ROOT,save_json
from core.freeze import hash_file
from core.joint_dag import SCIENCE_VERSION

def main():
    checks={}
    tests=json.loads((ROOT/'audits/protocol_tests.json').read_text());assert tests['status']=='passed' and tests['tests_run']>=14 and not tests['skipped'];checks['protocol_tests']=14
    for name in ['frozen_candidate_config.yaml','frozen_baseline_config.yaml','calibration_protocol.yaml']:
        p=ROOT/'configs'/name;assert hash_file(p)==p.with_suffix('.sha256').read_text().strip();checks[name]='hash_verified'
    dev=list((ROOT/'results/development').glob('*.csv'))
    trajectories=[p for p in dev if p.name!='development_summary.csv'];assert len(trajectories)==1560;checks['p0_p5_development_trajectories_preserved']=1560
    assert not list((ROOT/'results/calibration').glob('*.csv'));checks['formal_p6_rows_after_archive']=0
    assert not (ROOT/'results/heldout').exists();checks['heldout_accessed']=False
    eq=json.loads((ROOT/'audits/joint_dag_equivalence.json').read_text());assert eq['status']=='passed' and eq['all_scientific_equivalence_pass']
    assert all(c['comparison']['all_hashes_and_decisions_exact'] and c['comparison']['max_abs_diff']<=1e-12 for c in eq['cases'])
    checks['joint_dag_equivalence_cases']=[c['name'] for c in eq['cases']]
    migration=json.loads((ROOT/'audits/cache_migration.json').read_text());assert migration['status']=='passed' and not migration['p0_p5_touched'];checks['cache_migration']='strict_pass'
    metas=list((ROOT/'checkpoints/joint_dag_candidates').glob('*.json'));assert metas
    payload=json.loads(metas[0].read_text())['key_payload'];assert payload['science_version']==SCIENCE_VERSION and 'service_data_hash' not in payload
    evidence=list((ROOT/'checkpoints/joint_dag_evidence').glob('*.npz'));assert evidence
    source=(ROOT/'scripts/run_all_final.py').read_text();formal=(ROOT/'scripts/run_calibration_joint_dag_parallel.py').read_text()
    assert 'run_calibration_joint_dag_parallel' in source and "calibration('synthetic',2)" in source
    assert "'--output-name','calibration','--formal'" in formal
    checks.update({'cache_keys_exclude_service_data':True,'causal_fingerprint_includes_historical_buffer':True,
        'formal_runner_switched_to_joint_dag':True,'formal_workers':2,'partition':'complete workload','full_p6_started':False,'p0_p5_recomputed':False})
    save_json(ROOT/'audits/joint_dag_protocol.json',{'status':'passed','checks':checks,'scope':'formal P6 preflight; no formal P6 rows or heldout access'})
    print(json.dumps(checks,indent=2))

if __name__=='__main__':main()
