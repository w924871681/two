"""Supplemental dispatcher: resource admission + measured useful-work throughput."""
from pathlib import Path
import collections,concurrent.futures as cf,importlib.util,json,os,sys,time
import psutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent;sys.path.insert(0,str(ROOT))
from r_common import atomic
sys.path.insert(0,str(ROOT/'engineering/throughput_v3'))
from tuner import ThroughputTuner

def resource_floor():
    value=json.loads((HERE/'RESOURCE_POLICY.json').read_text(encoding='utf8'))['ram_reserve_bytes']
    assert isinstance(value,int) and value>0
    return value


def execute(jobs,worker,label,on_tick=None,cpu=False,progress_snapshot=None,work_weight=None):
    RAM_FLOOR=resource_floor()
    spec=importlib.util.spec_from_file_location('_resource_'+label,ROOT/'dynamic_worker_resources_v2.py')
    policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy);policy.RAM_RESERVE=RAM_FLOOR
    profile_path=ROOT/'engineering/EXECUTOR_MEMORY_PROFILE.json'
    if not cpu and profile_path.exists():
        profile=json.loads(profile_path.read_text(encoding='utf8'));assert profile['status']=='PASS'and profile['optimizer_steps']==0
        policy.RAM_PER_WORKER=max(128*2**20,int(profile['recommended_ram_per_worker_bytes']))
    if cpu:
        policy.RAM_PER_WORKER=32*2**20
        def snapshot():
            m=psutil.virtual_memory();return dict(available_ram_bytes=m.available,total_ram_bytes=m.total,
                logical_cpu_count=os.cpu_count() or 1,free_vram_bytes=0,total_vram_bytes=0)
        policy.snapshot=snapshot
        policy.physical_limit=lambda s:max(1,min(s['logical_cpu_count'],int((s['total_ram_bytes']-policy.RAM_RESERVE)//policy.RAM_PER_WORKER)))
        policy.memory_capacity=lambda s,a:max(0,min(policy.physical_limit(s),int((s['available_ram_bytes']+a*policy.RAM_PER_WORKER-policy.RAM_RESERVE)//policy.RAM_PER_WORKER)))
    jobs=list(jobs)
    if not jobs:return []
    resource=policy.snapshot();maximum=min(len(jobs),policy.physical_limit(resource))
    initial=policy.memory_capacity(resource,0)
    tuner=ThroughputTuner(maximum,start=max(1,min(maximum,initial)))
    pending=iter(enumerate(jobs));active={};results={};exhausted=False
    total_weight=sum(float(work_weight(job))for job in jobs)if work_weight else float(len(jobs))
    started=time.monotonic();last_resource=0.;last_publish=0.;resource_age=0.;history=collections.deque();completed_work=0.
    while_results=lambda:(completed_work,float(len(results)))
    def measure():return progress_snapshot() if progress_snapshot else while_results()
    with cf.ThreadPoolExecutor(max_workers=maximum,thread_name_prefix=label+'_V3') as pool:
        while not exhausted or active:
            now=time.monotonic()
            if now-last_resource>=3:
                RAM_FLOOR=resource_floor();policy.RAM_RESERVE=RAM_FLOOR
                resource=policy.snapshot();last_resource=now
            funded=policy.memory_capacity(resource,len(active))
            if resource['available_ram_bytes']<RAM_FLOOR:funded=0
            cap=min(tuner.target,funded)
            while not exhausted and len(active)<cap and psutil.virtual_memory().available>=RAM_FLOOR:
                try:i,job=next(pending)
                except StopIteration:exhausted=True;break
                active[pool.submit(worker,job)]=i
                # Exhaustion is a queue fact, never contingent on another RAM-
                # funded admission after the final result has already returned.
                if i+1==len(jobs):exhausted=True
            work,stages=measure()
            if not exhausted:tuner.tick(len(active),len(results),work,stages,funded,now)
            if tuner.last_event:
                event=dict(**tuner.last_event,label=label,at_unix=time.time())
                with (HERE/'MEASUREMENTS.jsonl').open('a',encoding='utf8') as f:
                    f.write(json.dumps(event,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
                tuner.last_event=None
            if now-last_publish>=1:
                measured_count=completed_work if work_weight else len(results)
                history.append((now,measured_count))
                while len(history)>1 and history[1][0]<=now-300:history.popleft()
                span=now-history[0][0] if history else 0
                rate=(measured_count-history[0][1])/span if span>=20 else 0
                eta=((total_weight-completed_work)if work_weight else(len(jobs)-len(results)))/rate if rate>0 and (active or funded) else None
                z=dict(completed=len(results),total=len(jobs),active_workers=len(active),elapsed_seconds=now-started,
                       completed_weighted_work=completed_work,total_weighted_work=total_weight,eta_seconds=eta,status='RUNNING',updated_unix=time.time(),runtime_dispatch='COVERAGE_THROUGHPUT_V1')
                atomic(ROOT/f'progress/{label}_PROGRESS.json',z)
                meta=tuner.metadata(funded,now)
                res=dict(**resource,**meta,resource_capacity=funded,physical_resource_ceiling=maximum,
                    hardware_resource_ceiling=policy.physical_limit(resource),ready_job_ceiling=len(jobs),
                    ram_reserve_bytes=RAM_FLOOR,vram_reserve_bytes=0 if cpu else policy.VRAM_RESERVE,
                    ram_allowance_per_worker_bytes=policy.RAM_PER_WORKER,
                    throughput_limit=meta['best_measured_workers'],retry_cooldown_remaining_seconds=meta['next_recheck_seconds'],retry_failures=sum(tuner.failures.values()))
                atomic(ROOT/'progress/WORKER_STATUS.json',dict(mode=label,kind='CPU_FILE' if cpu else 'GPU_SCIENCE',
                    active_workers=len(active),admission_capacity=min(tuner.target,funded),maximum=maximum,
                    resources=res,ram_admission_min_bytes=RAM_FLOOR,no_fixed_worker_count_cap=True,
                    runtime_dispatch='COVERAGE_THROUGHPUT_V1',updated_unix=time.time()))
                if on_tick:on_tick(z)
                last_publish=now
            if active:
                done,_=cf.wait(active,timeout=.2,return_when=cf.FIRST_COMPLETED)
                for f in done:
                    i=active.pop(f);results[i]=f.result();completed_work+=float(work_weight(jobs[i]))if work_weight else 1
            else:time.sleep(.2)
    z=dict(completed=len(results),total=len(jobs),active_workers=0,elapsed_seconds=time.monotonic()-started,
           completed_weighted_work=completed_work,total_weighted_work=total_weight,eta_seconds=0,status='DONE',updated_unix=time.time(),runtime_dispatch='COVERAGE_THROUGHPUT_V1')
    atomic(ROOT/f'progress/{label}_PROGRESS.json',z)
    if on_tick:on_tick(z)
    atomic(ROOT/'progress/WORKER_STATUS.json',dict(mode=label+'_COMPLETE',active_workers=0,admission_capacity=0,
        runtime_dispatch='COVERAGE_THROUGHPUT_V1',updated_unix=time.time()))
    return [results[i] for i in range(len(jobs))]
