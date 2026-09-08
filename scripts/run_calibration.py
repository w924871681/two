import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse,itertools,json,os
import numpy as np
import pandas as pd
from core.protocol import ROOT,POOLS,save_json
from core.engine import run
from core.freeze import freeze_file

SEEDS=[7311,7312,7313]
CONDITIONS=[('clean',0.),('mixed',.1)]

def calibration_definition(domain='synthetic'):
    candidate=json.loads((ROOT/'configs/frozen_candidate_config.yaml').read_text())
    protocol=json.loads((ROOT/'configs/calibration_protocol.yaml').read_text())
    prefix='alibaba_' if domain=='alibaba' else ''
    centers=list(range(20040,20060)) if domain=='alibaba' else POOLS['calibration']
    grid=[dict(kappa_rec=kr,kappa_hist=kh,delta_imp=di,delta_ret=dr)
          for kr,kh,di,dr in itertools.product(protocol['kappas'],protocol['kappas'],protocol['delta_imp_grid'],protocol['delta_ret_grid'])]
    jobs=[('Proposed',cfg) for cfg in grid]+[('ValidationCommit',{'validation_threshold':v}) for v in protocol['delta_imp_grid']]
    return candidate,protocol,prefix,centers,jobs

def atomic_csv(frame,path):
    tmp=path.with_name(f'{path.name}.{os.getpid()}.tmp')
    frame.to_csv(tmp,index=False,na_rep='NA')
    try:os.replace(tmp,path)
    finally:tmp.unlink(missing_ok=True)

def run_worker(domain='synthetic',worker_index=0,num_workers=1):
    candidate,protocol,prefix,centers,jobs=calibration_definition(domain)
    out=ROOT/'results'/f'{prefix}calibration';out.mkdir(parents=True,exist_ok=True)
    assignments=np.array_split(np.arange(len(jobs)),num_workers)[worker_index].tolist()
    summaries=[]
    status_path=ROOT/f'logs/{prefix}calibration_worker{worker_index}.json'
    grid_path=ROOT/f'{prefix}calibration_grid_worker{worker_index}.csv'
    completed=0;total=len(assignments)*len(SEEDS)*len(centers)*len(CONDITIONS)
    for i in assignments:
        method,settings=jobs[i];allrows=[]
        for seed in SEEDS:
            for c in centers:
                for kind,alpha in CONDITIONS:
                    path=out/f'policy{i:03d}_{seed}_{c}_{kind}.csv'
                    if path.exists():d=pd.read_csv(path)
                    else:
                        d=pd.DataFrame(run(c,seed,method,kind,alpha,
                            cfg={**candidate,**settings,'calibration_candidate_cache':True,'calibration_evidence_cache':True},
                            run_id=f'calibration_policy{i:03d}'))
                        atomic_csv(d,path)
                    allrows.append(d);completed+=1
                    save_json(status_path,{'phase':'P6 calibration','domain':domain,'worker':worker_index,'workers':num_workers,
                        'policy':i,'assigned_policies':len(assignments),'completed_trajectories':completed,
                        'total_trajectories':total,'center':c,'seed':seed,'condition':kind,'heldout_started':False})
        d=pd.concat(allrows,ignore_index=True);g=d.groupby('attack_type')[['harmful_commit','downside','deployed_service_mse']].mean()
        eligible=bool((g.harmful_commit<=protocol['rho']).all() and (g.downside<=protocol['epsilon']).all())
        summaries.append({'policy':i,'method':method,**settings,'eligible':eligible,
            'lifecycle_mse':float(d.deployed_service_mse.mean()),
            'worst_condition_harmful_rate':float(g.harmful_commit.max()),
            'worst_condition_downside':float(g.downside.max())})
        atomic_csv(pd.DataFrame(summaries),grid_path)
        print(f'calibration worker {worker_index} policy {i+1}/{len(jobs)} eligible {eligible}',flush=True)
    save_json(status_path,{'phase':'P6 calibration worker complete','domain':domain,'worker':worker_index,
        'workers':num_workers,'completed_trajectories':completed,'total_trajectories':total,'heldout_started':False})

def finalize(domain='synthetic',num_workers=1):
    _,_,prefix,_,jobs=calibration_definition(domain)
    paths=[ROOT/f'{prefix}calibration_grid_worker{i}.csv' for i in range(num_workers)]
    summaries=pd.concat([pd.read_csv(p) for p in paths],ignore_index=True).sort_values('policy')
    assert len(summaries)==len(jobs) and summaries.policy.nunique()==len(jobs)
    atomic_csv(summaries,ROOT/f'{prefix}calibration_grid.csv')
    selected={};status={}
    for method in ['Proposed','ValidationCommit']:
        eligible=summaries[(summaries.method==method)&summaries.eligible]
        if len(eligible):
            best=eligible.sort_values(['lifecycle_mse','policy']).iloc[0]
            selected.update(jobs[int(best.policy)][1]);status[method]={'status':'calibrated','selected_policy':int(best.policy)}
        else:
            selected['retain_all' if method=='Proposed' else 'validation_retain_all']=True
            status[method]={'status':'calibration_failure_retain_all'}
    freeze_file(f'{prefix}frozen_commit_config.yaml',selected)
    save_json(ROOT/f'{prefix}calibration_summary.json',status)
    save_json(ROOT/'logs/execution_status.json',{'phase':'P7 commit frozen','domain':domain,'heldout_started':False,'calibration':status})
    return status

def main(domain='synthetic'):
    run_worker(domain,0,1)
    return finalize(domain,1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--domain',choices=['synthetic','alibaba'],default='synthetic')
    p.add_argument('--worker-index',type=int);p.add_argument('--num-workers',type=int,default=1);p.add_argument('--finalize-only',action='store_true')
    a=p.parse_args()
    if a.finalize_only:finalize(a.domain,a.num_workers)
    elif a.worker_index is None:main(a.domain)
    else:run_worker(a.domain,a.worker_index,a.num_workers)
