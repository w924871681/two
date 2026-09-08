"""Formal P6 orchestration: two complete-workload joint-DAG workers, then P7 freeze."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import datetime,json,subprocess,time
import numpy as np
import pandas as pd
from core.protocol import ROOT,save_json
from core.freeze import freeze_file
from scripts.run_calibration import calibration_definition,SEEDS,CONDITIONS,atomic_csv

def aggregate_and_freeze(domain='synthetic'):
    candidate,protocol,prefix,centers,jobs=calibration_definition(domain);out=ROOT/'results'/f'{prefix}calibration';summaries=[]
    for policy,(method,settings) in enumerate(jobs):
        frames=[]
        for seed in SEEDS:
            for center in centers:
                for kind,_ in CONDITIONS:
                    p=out/f'policy{policy:03d}_{seed}_{center}_{kind}.csv';assert p.exists(),p
                    d=pd.read_csv(p);assert len(d)==24 and set(d.stage)==set(range(1,25)),p;frames.append(d)
        d=pd.concat(frames,ignore_index=True);g=d.groupby('attack_type')[['harmful_commit','downside','deployed_service_mse']].mean()
        eligible=bool((g.harmful_commit<=protocol['rho']).all() and (g.downside<=protocol['epsilon']).all())
        summaries.append({'policy':policy,'method':method,**settings,'eligible':eligible,'lifecycle_mse':float(d.deployed_service_mse.mean()),
            'worst_condition_harmful_rate':float(g.harmful_commit.max()),'worst_condition_downside':float(g.downside.max())})
        if (policy+1)%25==0:print(f'P7 aggregation {policy+1}/{len(jobs)}',flush=True)
    summaries=pd.DataFrame(summaries).sort_values('policy');assert len(summaries)==len(jobs)
    atomic_csv(summaries,ROOT/f'{prefix}calibration_grid.csv');selected={};status={}
    for method in ['Proposed','ValidationCommit']:
        eligible=summaries[(summaries.method==method)&summaries.eligible]
        if len(eligible):
            best=eligible.sort_values(['lifecycle_mse','policy']).iloc[0];selected.update(jobs[int(best.policy)][1]);status[method]={'status':'calibrated','selected_policy':int(best.policy)}
        else:
            selected['retain_all' if method=='Proposed' else 'validation_retain_all']=True;status[method]={'status':'calibration_failure_retain_all'}
    config_hash=freeze_file(f'{prefix}frozen_commit_config.yaml',selected);save_json(ROOT/f'{prefix}calibration_summary.json',status)
    save_json(ROOT/'logs/execution_status.json',{'phase':'P7 commit frozen; pre-heldout audit pending','domain':domain,'heldout_started':False,
        'calibration':status,'frozen_commit_config_sha256':config_hash,'updated_at':datetime.datetime.now().isoformat()})
    return status,config_hash

def main(domain='synthetic',workers=2):
    assert domain=='synthetic';assert int(workers)==2,'formal P6 is approved for exactly two workload workers'
    _,_,prefix,centers,jobs=calibration_definition(domain);out=ROOT/'results'/f'{prefix}calibration';out.mkdir(parents=True,exist_ok=True)
    assert not list(out.iterdir()),'formal calibration directory must be empty at initial launch'
    assert not (ROOT/'results/heldout').exists(),'heldout must not exist before P6/P7 audits'
    processes=[];started=time.time()
    for i in range(workers):
        cmd=[sys.executable,str(ROOT/'scripts/run_calibration_joint_dag.py'),'--domain',domain,'--worker-index',str(i),'--num-workers',str(workers),'--output-name','calibration','--formal']
        processes.append(subprocess.Popen(cmd,cwd=ROOT))
    total=len(jobs)*len(SEEDS)*len(centers)*len(CONDITIONS)
    try:
        while True:
            codes=[p.poll() for p in processes];completed=sum(1 for _ in out.glob('policy*.csv'));elapsed=time.time()-started
            cache={k:0 for k in ['candidate_l1_hits','candidate_l2_hits','candidate_trainings','candidate_l2_writes','evidence_l1_hits','evidence_l2_hits','evidence_computations','evidence_l2_writes']}
            worker_status=[]
            for i in range(workers):
                p=ROOT/f'logs/{prefix}calibration_worker{i}.json'
                if p.exists():
                    q=json.loads(p.read_text());worker_status.append(q)
                    for k in cache:cache[k]+=q.get('cache_metrics',{}).get(k,0)
            rate=completed/elapsed if elapsed else 0.;eta=(total-completed)/rate if rate else None
            save_json(ROOT/'logs/execution_status.json',{'phase':'P6 formal joint DAG calibration','domain':domain,'workers':workers,
                'worker_pids':[p.pid for p in processes],'completed_trajectories':completed,'total_trajectories':total,'elapsed_s':elapsed,
                'trajectory_rate_per_s':rate,'eta_s':eta,'cache_metrics':cache,'worker_status':worker_status,
                'updated_at':datetime.datetime.now().isoformat(),'heldout_started':False})
            failed=[(i,c) for i,c in enumerate(codes) if c not in (None,0)]
            if failed:raise RuntimeError(f'joint DAG calibration worker failed: {failed}')
            if all(c==0 for c in codes):break
            time.sleep(10)
    except BaseException:
        for p in processes:
            if p.poll() is None:p.terminate()
        for p in processes:
            try:p.wait(timeout=30)
            except subprocess.TimeoutExpired:p.kill()
        raise
    assert sum(1 for _ in out.glob('policy*.csv'))==total
    return aggregate_and_freeze(domain)

if __name__=='__main__':main()
