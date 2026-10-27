"""One isolated group process. Independent methods; metered training or zero-SGD audit."""
from common import *
import sys,threading,traceback,shutil
sys.path.insert(0,str(ROOT/'engineering/throughput'))
from dispatch import execute

def td_path(spec,job):return Path(spec['root'])/'science'/spec['phase']/str(job['center'])/str(job['seed'])/job['stream']/job['arm']['id']

def main(group,mode):
    spec=read(ROOT/'registered_groups'/f'{group}.json');seal=read(ROOT/'SCIENCE_EXECUTION.lock.json')
    assert seal['status']=='SEALED_FOR_REGISTERED_COVERAGE' and sha(ROOT/'registered_groups'/f'{group}.json')==seal['registered_groups'][group]
    for rel,digest in seal['implementation_sha256'].items():assert sha(ROOT/rel)==digest,('Sealed implementation changed',rel)
    import bridge as b
    from e4_assets import attach,prepare_data
    from stage_specs import jobs,budget,prepare_layout
    import torch,psutil,platform
    torch.set_num_threads(1)
    atomic(ROOT/'process'/f'RUNTIME_{group}_{mode}.json',dict(group=group,mode=mode,python=sys.version,executable=sys.executable,torch=str(torch.__version__),cuda_version=torch.version.cuda,device=b.DEVICE,gpu_name=torch.cuda.get_device_name(0)if b.DEVICE=='cuda'else None,gpu_total_bytes=torch.cuda.get_device_properties(0).total_memory if b.DEVICE=='cuda'else 0,logical_cpu_count=os.cpu_count(),cpu=platform.processor(),system=platform.platform(),torch_cpu_threads=torch.get_num_threads(),cudnn_benchmark=torch.backends.cudnn.benchmark,cudnn_deterministic=torch.backends.cudnn.deterministic,total_host_ram=psutil.virtual_memory().total,at_unix=time.time()))
    # Source assets remain read only even if a later adapter accidentally writes.
    protected=[PRIOR,Path('D:/dt-trustworthy-maintenance'),ROOT.parent/'paper2_revision_execution_20261012',ROOT.parent/'paper2_revision_round2_20261013']
    def no_reference_writes(event,args):
        if event=='open':
            p,m,flags=args;writing=(isinstance(m,str) and any(c in m for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if writing and isinstance(p,(str,bytes,os.PathLike)) and any(Path(os.fsdecode(p)).resolve().is_relative_to(r) for r in protected):raise PermissionError('Frozen source is read-only')
    sys.addaudithook(no_reference_writes)
    counter=threading.RLock();counts={'stages':0.,'work':0.};weights=seal['work_weights'];me=psutil.Process()
    atomic(ROOT/'process/CURRENT_CHILD.json',dict(pid=me.pid,create_time=me.create_time(),group=group,mode=mode))
    alljobs=jobs(spec);planned=budget(spec)
    if mode=='prepare':
        prepare_layout(spec)
        from datasets import synthetic,external
        data_job=lambda _:(external(spec) if spec.get('cost_only') or spec['domain']=='alibaba' else synthetic(spec) if spec['domain']=='synthetic' else prepare_data(spec))
        state(status='RUNNING',phase=group,work='输入构建与身份校验（一次）',completed=0,total=1,unit='输入组')
        execute([group],data_job,group+'_INPUTS',cpu=True,on_tick=lambda z:state(completed=z['completed'],active_workers=z['active_workers'],status='RUNNING' if z['active_workers'] else 'WAITING_FOR_RESOURCE'))
        from meter import Meter
        meter=Meter(group,planned)
        pairs=[(c,s)for c in spec['centers']for s in spec['seeds']]
        state(status='RUNNING',phase=group,work='共享M0初始化；每对身份只执行一次',completed=0,total=len(pairs),unit='初始化模型')
        def initialize(pair):
            c,s=pair;path=Path(spec['root'])/'initial'/f'{c}_{s}.pt';side=path.with_suffix('.json')
            with b.context(attach(spec)):
                source=spec['sources'][str(s)];assert sha(source['path'])==source['sha256']
                warm=b.Timeline(c).warmup()
                if side.exists():
                    record=read(side);assert sha(path)==record['sha256'] and record['warmup_hash']==warm.hash;return record
                assert not path.exists(),'Partial M0 persistence; do not retrain'
                if spec.get('reuse_main_initial'):
                    oldpath=Path(spec['reuse_main_initial']);oldmeta=read(oldpath.with_suffix('.json'));assert sha(oldpath)==oldmeta['sha256'] and oldmeta['warmup_hash']==warm.hash and oldmeta['source_sha256']==source['sha256']
                    shutil.copyfile(oldpath,path);new_steps=0
                    model=b.Forecast().to(b.DEVICE);model.load_state_dict(torch.load(path,map_location=b.DEVICE,weights_only=True));assert b.state_hash(model)==oldmeta['state_hash']
                elif spec.get('existing_m0'):
                    old=next(x for x in spec['existing_m0'] if x['center']==c and x['seed']==s);assert sha(old['path'])==old['sha256']
                    assert old['sidecar']['source_checkpoint_hash']==source['sha256'] and old['sidecar']['warmup_segment_manifest']['hash']==warm.hash and old['sidecar']['smoke'] is False
                    shutil.copyfile(old['path'],path);new_steps=0;expected=old['sidecar']['initial_state_hash']
                    model=b.Forecast().to(b.DEVICE);model.load_state_dict(torch.load(path,map_location=b.DEVICE,weights_only=True));assert b.state_hash(model)==expected
                else:
                    from immutable_cache import state_dict
                    model=b.Forecast().to(b.DEVICE);model.load_state_dict(state_dict(source['path'],source['sha256']));assert b.state_hash(model)==source['state_hash']
                    with meter.scope('warmup',dict(center=c,seed=s)):
                        model=b.adapt(model,b.tensors(b.windows(warm)),steps=50,seed=b.training_seed(s,c,0))
                    torch.save(model.state_dict(),path);new_steps=50
                record=dict(sha256=sha(path),state_hash=b.state_hash(model),source_sha256=source['sha256'],warmup_steps=50,actual_new_optimizer_steps=new_steps,warmup_seed=b.training_seed(s,c,0),warmup_hash=warm.hash,execution_lock_sha256=sha(ROOT/'SCIENCE_EXECUTION.lock.json'))
                atomic(side,record);del model;return record
        result=execute(pairs,initialize,group+'_M0',on_tick=lambda z:state(completed=z['completed'],active_workers=z['active_workers'],status='RUNNING' if z['active_workers'] else 'WAITING_FOR_RESOURCE',actual_sgd_steps=sum(meter.actual.values())))
        atomic(ROOT/'process'/f'{group}_OPTIMIZER_PROGRESS.json',dict(group=group,actual=meter.actual,reserved=meter.reserved,budget=planned,at_unix=time.time()))
        atomic(ROOT/'receipts'/f'{group}_PREPARE.json',dict(status='PASS',models=len(result),budget=planned,actual_optimizer_steps=meter.actual))
        return
    audit=mode in ('audit_smoke','audit_full')
    if spec.get('cost_only') and not audit:
        import cost_instrument
        cost_instrument.install(b)
    if audit:
        def deny(*a,**k):raise PermissionError('Independent audit cannot call any optimizer')
        torch.optim.SGD.step=deny;torch.optim.Adam.step=deny;meter=None
    else:
        from meter import Meter
        meter=Meter(group,planned)
    smoke=[j for j in alljobs if j['center']==spec['centers'][0] and j['seed']==spec['seeds'][0] and j['stream'] in spec['stream_ids'][:2]]
    selection=smoke if mode in ('smoke','audit_smoke') else alljobs
    # Completed trajectories are reused; unfinished consumed native chains are never retrained.
    completed_before=sum(spec['stages'] for j in selection if (td_path(spec,j)/'DONE.json').exists()) if not audit else 0
    counts.update(stages=float(completed_before),work=float(completed_before))
    state(status='RUNNING',phase=group,work='独立全量审计（零SGD）' if audit else '冻结生命周期训练与封存',completed=completed_before,total=len(selection)*spec['stages'],unit='方法阶段',actual_sgd_steps=sum(meter.actual.values()) if meter else 0)
    def worker(job):
        td=td_path(spec,job);identity=dict(center=job['center'],seed=job['seed'],stream=job['stream'],arm=job['arm']['id'])
        try:
            with b.context(attach(spec)):
                if audit:
                    assert (td/'DONE.json').exists(),'Trajectory incomplete'
                    result=b.audit_trajectory(spec['phase'],td)
                    assert result.get('rows')==spec['stages'] and result.get('status')=='VALIDATED'
                    with counter:counts['stages']+=spec['stages'];counts['work']+=spec['stages']*weights.get(job['arm']['id'],1.)
                    atomic(td/'AUDIT.json',dict(**result,execution_lock_sha256=sha(ROOT/'SCIENCE_EXECUTION.lock.json'),audited_unix=time.time()))
                    return dict(status='PASS',**identity)
                if (td/'DONE.json').exists():
                    done=read(td/'DONE.json');assert done['stages']==spec['stages'] and done['result_sha256']==[sha(td/f'result_{t:03}.json')for t in range(1,spec['stages']+1)]
                    return dict(status='REUSED_COMPLETE',**identity)
                if td.exists():raise RuntimeError('PARTIAL_TRAJECTORY_PRESERVED_NO_AUTOMATIC_OPTIMIZER_REPLAY')
                def progress(**kw):
                    if spec.get('cost_only') and job['arm']['id'] not in b.LEGACY_NAMES:cost_instrument.finish(b,td,kw['stage'])
                    with counter:counts['stages']+=1;counts['work']+=weights.get(job['arm']['id'],1.)
                with meter.scope('candidate',identity):
                    fn=b.run_legacy if job['arm']['id'] in b.LEGACY_NAMES else b.run_trajectory
                    rows=fn(spec['phase'],job['center'],job['seed'],job['stream'],job['arm'],seal['run_id'],progress=progress)
                assert len(rows)==spec['stages'];return dict(status='PASS',**identity)
        except Exception:
            error=traceback.format_exc();atomic(ROOT/'failures'/group/(f"{job['center']}_{job['seed']}_{job['stream']}_{job['arm']['id']}_{mode}.json"),dict(status='INVALID' if td.exists() else 'BLOCKED',error=error,**identity,no_automatic_training_replay=True,at_unix=time.time()))
            return dict(status='FAILED',error=error,**identity)
    def tick(z):
        if meter:atomic(ROOT/'process'/f'{group}_OPTIMIZER_PROGRESS.json',dict(group=group,actual=meter.actual,reserved=meter.reserved,budget=planned,at_unix=time.time()))
        state(status='RUNNING' if z['active_workers'] else 'WAITING_FOR_RESOURCE',completed=int(counts['stages']),total=len(selection)*spec['stages'],active_workers=z['active_workers'],actual_sgd_steps=sum(meter.actual.values()) if meter else 0,phase_auditor_optimizer_steps=0 if audit else None)
    if spec.get('cost_timing_serial_ready_graph') and not audit:
        # Timing replicas require identical no-concurrent-lifecycle boundaries.
        # Every ready set still uses the same resource and throughput dispatcher.
        results=[]
        for index,job in enumerate(selection):
            results.extend(execute([job],worker,group+'_'+mode.upper()+f'_READY_{index:02}',on_tick=tick,progress_snapshot=lambda:(counts['work'],counts['stages'])))
    else:results=execute(selection,worker,group+'_'+mode.upper(),on_tick=tick,progress_snapshot=lambda:(counts['work'],counts['stages']))
    failures=[r for r in results if r['status']=='FAILED']
    receipt=dict(status='PASS' if not failures else 'INVALID',group=group,mode=mode,jobs=len(selection),failed_jobs=len(failures),results=results,execution_lock_sha256=sha(ROOT/'SCIENCE_EXECUTION.lock.json'),actual_optimizer_steps=meter.actual if meter else {'auditor':0},reserved_optimizer_steps=meter.reserved if meter else {},uncertain_optimizer_scopes=meter.uncertain if meter else [],at_unix=time.time())
    atomic(ROOT/'receipts'/f'{group}_{mode.upper()}.json',receipt)
    if failures:raise RuntimeError(f'{group}/{mode}: {len(failures)} invalid independent jobs; evidence preserved')

if __name__=='__main__':
    try:main(sys.argv[1],sys.argv[2])
    except BaseException:
        atomic(ROOT/'failures'/f'{sys.argv[1]}_{sys.argv[2]}_PROCESS.json',dict(error=traceback.format_exc(),at_unix=time.time(),no_automatic_training_retry=True));raise
