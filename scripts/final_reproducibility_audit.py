"""P16 fail-closed completeness and reproducibility audit."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import datetime,json,subprocess
import pandas as pd
from core.protocol import ROOT,POOLS,save_json
from core.freeze import require_frozen,hash_file
from scripts.run_heldout import METHODS

def count(folder,prefix=None):
    paths=list((ROOT/'results'/folder).glob('*.csv'));return len([p for p in paths if p.name not in {'raw_episode_results.csv','summary.csv','paired_bootstrap.csv'} and (prefix is None or p.name.startswith(prefix))])

def main():
    freeze=require_frozen();expected={
        'q1_overall':3*len(POOLS['heldout'])*2*len(METHODS),
        'q2_security':3*20*16*(len(METHODS)-1),
        'q4_ablation':3*10*2*6,
        'q5_sensitivity_cost':3*10*2*11,
        'q5_generality':3*6*10*2*5,
        'q5_runtime':5*10*(len(METHODS)-1),
        'q6_alibaba':3*40*2*len(METHODS)+3*40*2*2}
    actual={k:count(k) for k in expected};assert actual==expected,(actual,expected)
    assert count('alibaba_calibration')==405*20*3*2
    pools=list(POOLS.values())
    for i,a in enumerate(pools):
        for b in pools[i+1:]:assert not set(a)&set(b)
    readiness=json.loads((ROOT/'audits/heldout_readiness.json').read_text());assert readiness['status']=='approved_by_implementation_audit'
    p15=json.loads((ROOT/'audits/p15_figure_manifest.json').read_text());assert p15['status']=='passed' and len(p15['figures'])>=3
    pairs=pd.read_csv(ROOT/'results/tables/all_paired_comparisons.csv');assert len(pairs) and set(pairs.bootstrap_replicates.dropna().astype(int))=={4000}
    summaries=pd.read_csv(ROOT/'results/tables/all_summaries.csv');assert set(['q1_overall','q2_security','q3_benign_drift','q4_ablation','q5_sensitivity_cost','q5_generality','q5_runtime','q6_alibaba'])<=set(summaries.question)
    required=[ROOT/'calibration_grid.csv',ROOT/'calibration_summary.json',ROOT/'configs/frozen_candidate_config.yaml',ROOT/'configs/frozen_commit_config.yaml',ROOT/'configs/frozen_baseline_config.yaml']
    assert all(p.exists() and p.stat().st_size for p in required)
    report={'status':'passed','completed_at':datetime.datetime.now().isoformat(),'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'final_freeze_verified':True,'heldout_readiness_verified':True,'pool_disjointness':'passed','trajectory_files':actual,
        'alibaba_calibration_trajectories':count('alibaba_calibration'),'bootstrap_replicates':4000,'p15_manifest':'passed',
        'required_artifact_hashes':{str(p.relative_to(ROOT)).replace('\\','/'):hash_file(p) for p in required},
        'baseline_fidelity_notes':['CLeaR-Predictor is a declared predictor-only framework adaptation','MER-Reg-2026 omitted as implementation_unavailable_or_nonfaithful','OracleCommit is offline diagnostic only'],
        'reproduction_status':'complete exact frozen-code/config execution; stochastic uncertainty summarized by preregistered center-cluster bootstrap'}
    save_json(ROOT/'audits/final_reproducibility_audit.json',report);print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
