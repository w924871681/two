"""Joint-DAG calibration workload worker used by staged audits and formal P6."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse,json,os,time
import numpy as np
import pandas as pd
from core.protocol import ROOT,save_json
from core.engine import run
from core.joint_dag import run_joint,CacheBundle
from scripts.run_calibration import calibration_definition,SEEDS,CONDITIONS

def atomic_csv(d,path):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(f'{path.name}.{os.getpid()}.tmp');d.to_csv(tmp,index=False,na_rep='NA');os.replace(tmp,path)

def workload_definitions(domain):
    candidate,protocol,prefix,centers,jobs=calibration_definition(domain)
    work=[(seed,center,kind,alpha) for seed in SEEDS for center in centers for kind,alpha in CONDITIONS]
    proposed=[{'policy':i,**jobs[i][1]} for i in range(400)]
    return candidate,protocol,prefix,jobs,work,proposed

def implementation_identity():
    p=ROOT/'audits/formal_p6_implementation.json'
    obj=json.loads(p.read_text())
    assert obj['status']=='approved_for_formal_p6'
    return obj['git_sha'],obj['joint_dag_sha256']

def add_provenance(frame,git_sha,implementation_hash):
    frame=frame.copy();frame['implementation_git_sha']=git_sha;frame['joint_dag_implementation_sha256']=implementation_hash
    return frame

def worker(domain,worker_index,num_workers,output_name,formal=False):
    candidate,_,prefix,jobs,workloads,policies=workload_definitions(domain);assigned=np.array_split(np.arange(len(workloads)),num_workers)[worker_index].tolist()
    if formal:
        assert domain=='synthetic' and output_name=='calibration'
        assert not (ROOT/'results/heldout').exists(),'heldout must not exist before formal P6'
        git_sha,implementation_hash=implementation_identity()
    else:git_sha=implementation_hash=None
    out=ROOT/'results'/output_name;out.mkdir(parents=True,exist_ok=True);cache=CacheBundle();start=time.time();completed=0
    totals={k:0 for k in ['candidate_l1_hits','candidate_l2_hits','candidate_trainings','candidate_l2_writes','evidence_l1_hits','evidence_l2_hits','evidence_computations','evidence_l2_writes','verification_forward_calls_physical','service_forward_calls_physical']}
    for wi in assigned:
        seed,center,kind,alpha=workloads[wi]
        missing=[p for p in policies if not (out/f'policy{p["policy"]:03d}_{seed}_{center}_{kind}.csv').exists()]
        if missing:
            result,metrics,stages=run_joint(center,seed,missing,kind,alpha,cache=cache,use_l1=True,use_l2=True,run_id=f'joint_dag_policy_bundle_{seed}_{center}_{kind}')
            for k in totals:totals[k]+=metrics[k]
            for p in missing:
                frame=pd.DataFrame(result[p['policy']])
                if formal:frame=add_provenance(frame,git_sha,implementation_hash)
                atomic_csv(frame,out/f'policy{p["policy"]:03d}_{seed}_{center}_{kind}.csv')
        # Five ValidationCommit policies retain the unchanged reference executor.
        for policy in range(400,405):
            path=out/f'policy{policy:03d}_{seed}_{center}_{kind}.csv'
            if not path.exists():
                method,settings=jobs[policy];d=pd.DataFrame(run(center,seed,method,kind,alpha,cfg={**candidate,**settings,
                    'calibration_candidate_cache':True,'calibration_evidence_cache':True},run_id=f'joint_dag_validation_policy{policy:03d}'))
                if formal:d=add_provenance(d,git_sha,implementation_hash)
                atomic_csv(d,path)
        completed+=1;status={'phase':'P6 formal joint DAG calibration' if formal else 'joint DAG staged calibration','domain':domain,
            'worker':worker_index,'workers':num_workers,'workload_index':wi,'completed_workloads':completed,'assigned_workloads':len(assigned),
            'completed_trajectories':completed*len(jobs),'total_trajectories':len(assigned)*len(jobs),'center':center,'seed':seed,
            'condition':kind,'elapsed_s':time.time()-start,'formal_p6':formal,'heldout_started':False,'cache_metrics':totals}
        save_json(ROOT/f'logs/{prefix}calibration_worker{worker_index}.json',status)
        print(f'worker {worker_index} workload {completed}/{len(assigned)} center={center} seed={seed} condition={kind}',flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--domain',choices=['synthetic','alibaba'],default='synthetic');p.add_argument('--worker-index',type=int,required=True)
    p.add_argument('--num-workers',type=int,default=1);p.add_argument('--output-name',default='joint_dag_staging');p.add_argument('--formal',action='store_true');a=p.parse_args()
    assert (a.output_name=='calibration')==a.formal,'formal calibration output requires --formal and staged output must remain separate'
    worker(a.domain,a.worker_index,a.num_workers,a.output_name,a.formal)

if __name__=='__main__':main()
