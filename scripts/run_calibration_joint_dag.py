"""Staged joint-DAG calibration runner. It is not wired into run_all_final.py."""
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

def worker(domain,worker_index,num_workers,output_name):
    candidate,_,prefix,jobs,workloads,policies=workload_definitions(domain);assigned=np.array_split(np.arange(len(workloads)),num_workers)[worker_index].tolist()
    out=ROOT/'results'/output_name;cache=CacheBundle();start=time.time();completed=0
    for wi in assigned:
        seed,center,kind,alpha=workloads[wi]
        missing=[p for p in policies if not (out/f'policy{p["policy"]:03d}_{seed}_{center}_{kind}.csv').exists()]
        if missing:
            result,metrics,stages=run_joint(center,seed,missing,kind,alpha,cache=cache,use_l1=True,use_l2=True,run_id=f'joint_dag_policy_bundle_{seed}_{center}_{kind}')
            for p in missing:atomic_csv(pd.DataFrame(result[p['policy']]),out/f'policy{p["policy"]:03d}_{seed}_{center}_{kind}.csv')
        # Five ValidationCommit policies retain the unchanged reference executor.
        for policy in range(400,405):
            path=out/f'policy{policy:03d}_{seed}_{center}_{kind}.csv'
            if not path.exists():
                method,settings=jobs[policy];d=pd.DataFrame(run(center,seed,method,kind,alpha,cfg={**candidate,**settings,
                    'calibration_candidate_cache':True},run_id=f'joint_dag_validation_policy{policy:03d}'));atomic_csv(d,path)
        completed+=1;save_json(ROOT/f'logs/joint_dag_worker{worker_index}.json',{'phase':'joint DAG staged calibration','domain':domain,
            'worker':worker_index,'workers':num_workers,'workload_index':wi,'completed_workloads':completed,'assigned_workloads':len(assigned),
            'center':center,'seed':seed,'condition':kind,'elapsed_s':time.time()-start,'formal_p6':False})

def main():
    p=argparse.ArgumentParser();p.add_argument('--domain',choices=['synthetic','alibaba'],default='synthetic');p.add_argument('--worker-index',type=int,required=True)
    p.add_argument('--num-workers',type=int,default=1);p.add_argument('--output-name',default='joint_dag_staging');a=p.parse_args()
    assert a.output_name!='calibration','formal calibration output requires an explicit post-report switch change'
    worker(a.domain,a.worker_index,a.num_workers,a.output_name)

if __name__=='__main__':main()
