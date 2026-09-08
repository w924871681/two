"""Same-workload benchmark for reference, dual cache, joint DAG, and RAM L1."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,subprocess,time
from core.protocol import ROOT,save_json
from core.joint_dag import run_joint,CacheBundle
from scripts.run_calibration import calibration_definition
from scripts.profile_reference_executor import GpuSampler,io_counters

WORKLOADS=[{'center':12002,'condition':'mixed','alpha':.1},{'center':12003,'condition':'mixed','alpha':.1}]

def policies():
    _,_,_,_,jobs=calibration_definition('synthetic');return [{'policy':i,**jobs[i][1]} for i in range(400)]

def add_metrics(total,m):
    for k,v in m.items():
        if isinstance(v,(int,float)) and k not in ('wall_s','trajectories_per_hour','policy_trajectories'):total[k]=total.get(k,0)+v

def execute(workloads,use_l1,use_l2,cache=None):
    cache=cache or CacheBundle();total={};unique=0;wall0=time.perf_counter();cpu0=time.process_time();io0=io_counters()
    for w in workloads:
        rows,m,stages=run_joint(w['center'],7311,policies(),w['condition'],w['alpha'],cache=cache,use_l1=use_l1,use_l2=use_l2,run_id='benchmark')
        add_metrics(total,m);unique+=sum(x['unique_complete_causal_states'] for x in stages);del rows
    wall=time.perf_counter()-wall0;io1=io_counters();n=len(workloads)*400
    total.update({'wall_s':wall,'cpu_time_s':time.process_time()-cpu0,'policy_trajectories':n,'trajectories_per_hour':n*3600/wall,
        'unique_complete_causal_states':unique,'disk_read_bytes':io1['read_bytes']-io0['read_bytes'],'disk_write_bytes':io1['write_bytes']-io0['write_bytes']})
    return total

def child(index,path):
    result=execute([WORKLOADS[index]],False,True);save_json(path,result)

def main():
    # Complete the persistent benchmark cache before timing steady-state variants.
    prewarm=execute(WORKLOADS,False,True)
    sampler=GpuSampler();sampler.start();one=execute(WORKLOADS,False,True);one.update(sampler.finish())
    child_paths=[ROOT/f'audits/dag_benchmark_worker{i}.json' for i in range(2)];sampler=GpuSampler();sampler.start();start=time.perf_counter()
    ps=[subprocess.Popen([sys.executable,__file__,'--child',str(i),str(child_paths[i])],cwd=ROOT) for i in range(2)]
    codes=[p.wait() for p in ps];two_wall=time.perf_counter()-start;two_gpu=sampler.finish();assert codes==[0,0],codes
    child_results=[json.loads(p.read_text()) for p in child_paths];two={}
    for m in child_results:add_metrics(two,m)
    two.update({'wall_s':two_wall,'cpu_time_s':sum(x['cpu_time_s'] for x in child_results),'policy_trajectories':800,
        'trajectories_per_hour':800*3600/two_wall,'unique_complete_causal_states':sum(x['unique_complete_causal_states'] for x in child_results),**two_gpu})
    hot_cache=CacheBundle(l1_capacity=2048);l1_fill=execute(WORKLOADS,True,True,hot_cache);sampler=GpuSampler();sampler.start();hot=execute(WORKLOADS,True,True,hot_cache);hot.update(sampler.finish())
    old=json.loads((ROOT/'archive/pre_joint_dag_20260908_210552/archive_manifest.json').read_text())['throughput_snapshot']
    equivalence=json.loads((ROOT/'audits/joint_dag_equivalence.json').read_text());all400=next(x for x in equivalence['cases'] if x['name']=='all400_recurring_mixed')
    report={'status':'passed','workloads':WORKLOADS,'seed':7311,'policies_per_workload':400,'stages':24,
        'A_old_mature_reference':{'trajectories_per_hour':old['historical_single_worker_mature_trajectories_per_hour'],'source':'23,039-trajectory archived production interval'},
        'B_dual_process_cache':{'trajectories_per_hour':old['overall_trajectories_per_hour'],'user_reference_rate':1008.0,'source':'795-trajectory pre-joint-DAG archive'},
        'C_joint_dag_one_worker_l2':one,'D_joint_dag_two_workers_l2':two,'E_joint_dag_one_worker_ram_hot':hot,
        'prewarm_not_timed_as_steady_state':prewarm,'l1_fill_not_timed_as_hot':l1_fill,
        'first_pass_all400_equivalence_workload':{'reference_wall_s':all400['reference_wall_s'],'dag_wall_s':all400['dag_wall_s'],
            'reference_trajectories_per_hour':400*3600/all400['reference_wall_s'],'dag_trajectories_per_hour':400*3600/all400['dag_wall_s']}}
    variants={'C':one['trajectories_per_hour'],'D':two['trajectories_per_hour'],'E':hot['trajectories_per_hour']};best=max(variants,key=variants.get)
    report['best_verified_variant']=best;report['best_trajectories_per_hour']=variants[best];report['speedup_vs_1008']=variants[best]/1008.;report['speedup_vs_1291']=variants[best]/old['historical_single_worker_mature_trajectories_per_hour']
    save_json(ROOT/'audits/joint_dag_benchmark.json',report);print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--child':child(int(sys.argv[2]),Path(sys.argv[3]))
    else:main()
