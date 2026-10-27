"""Autonomous registered lifecycle -> independent audit -> statistics -> delivery."""
from common import *
import psutil,sys,subprocess,traceback,csv,statistics,collections

def identity():
    me=psutil.Process();atomic(ROOT/'process/OWNER_IDENTITY.json',dict(pid=me.pid,create_time=me.create_time(),kind='AUTONOMOUS_COVERAGE_OWNER',no_periodic_llm_supervision=True))
def alive(record):
    try:p=psutil.Process(record['pid']);return p.is_running()and abs(p.create_time()-record['create_time'])<.02
    except (psutil.Error,KeyError):return False
def child(script,*args,label=None,startup=False):
    if startup:
        while psutil.virtual_memory().available<2*2**30:
            state(status='WAITING_FOR_STARTUP_RAM',phase=label or script,work='等待2 GiB实验进程启动内存；worker准入仍为1.5 GiB',completed=0,total=1,unit='进程');identity();time.sleep(3)
    label=label or Path(script).stem;logs=ROOT/'process';out=(logs/(label+'.stdout.log')).open('a',encoding='utf8');err=(logs/(label+'.stderr.log')).open('a',encoding='utf8')
    try:
        p=subprocess.Popen([sys.executable,'-B','-X','utf8','-u',str(ROOT/script),*map(str,args)],cwd=ROOT,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        while p.poll()is None:
            atomic(ROOT/'process/SUPERVISOR_HEARTBEAT.json',dict(pid=os.getpid(),child_pid=p.pid,work=label,at_unix=time.time(),no_periodic_llm_supervision=True));identity();time.sleep(3)
        if p.returncode:raise RuntimeError(f'{label}: child exit {p.returncode}; see process/{label}.stderr.log')
    finally:out.close();err.close();identity()

def make_seal():
    if (ROOT/'SCIENCE_EXECUTION.lock.json').exists():return read(ROOT/'SCIENCE_EXECUTION.lock.json')
    from stage_specs import synthetic_specs,external_spec,cost_specs,budget,jobs
    specs=synthetic_specs();blocked=[]
    from identity_refresh import verify as verify_ids
    sys.path.insert(0,str(ROOT/'engineering/throughput'));from dispatch import execute
    state(status='RUNNING',phase='PREFLIGHT',work='科学封存前重新核验中心身份',completed=0,total=1,unit='身份扫描')
    fresh=execute([0],lambda _:verify_ids(),'PRESEAL_IDENTITY_REFRESH',cpu=True,on_tick=lambda z:state(completed=z['completed'],active_workers=z['active_workers'],status='RUNNING'if z['active_workers']else'WAITING_FOR_RESOURCE'))[0]
    collision_ids={x for row in fresh['conflicts']for x in row['ids']}
    if fresh['errors']:collision_ids|=set(range(64000,64024))|set(range(64100,64124))
    for spec in list(specs):
        if set(spec['centers'])&collision_ids:blocked.append(dict(stage=spec['stage'],group=spec['group'],reason='Historical center identity collision; no alternate IDs chosen'));specs.remove(spec)
    if (ROOT/'assets/E3_ALIBABA_AUTH.json').exists():
        from external_history import verify
        verify();specs=[external_spec()]+specs
    else:blocked.append(dict(stage='E3',reason='Original raw-to-input/source authentication did not pass',receipt=str(ROOT/'assets/E3_AUTH_FAILURE.json')))
    if (ROOT/'assets/E4_TEMPERATURE_AUTH.json').exists():specs+=read(ROOT/'assets/E4_TEMPERATURE_AUTH.json')['groups']
    else:blocked.append(dict(stage='E4',reason='Historical temperature data/source/interface authentication did not pass',receipt=str(ROOT/'assets/E4_AUTH_FAILURE.json')))
    specs+=cost_specs();folder=ROOT/'registered_groups';folder.mkdir(exist_ok=True);budgets={};matrix=[]
    for spec in specs:
        atomic(folder/(spec['group']+'.json'),spec);budgets[spec['group']]=budget(spec)
        for job in jobs(spec):matrix.append(dict(group=spec['group'],stage=spec['stage'],center=job['center'],seed=job['seed'],stream=job['stream'],arm=job['arm']['id'],architecture=spec['architecture'],horizon=spec['horizon'],stages=spec['stages'],domain=spec['domain'],new_scientific_sample=not spec.get('cost_only',False)))
    save_csv(ROOT/'REGISTERED_TRAJECTORY_MATRIX.csv',matrix)
    costs=collections.defaultdict(list)
    with (ROOT/'E0_MAIN_TABLES/RESOURCE_COSTS.csv').open(encoding='utf-8-sig',newline='')as f:
        for r in csv.DictReader(f):costs[r['arm']].append(float(r['maintenance_wall_seconds'])+float(r['post_seal_scientific_evaluation_seconds']))
    reference=statistics.median(costs['JOINT__l3__m0']);weights={arm:statistics.median(x)/reference for arm,x in costs.items()}
    implementation={p.relative_to(ROOT).as_posix():sha(p)for p in ROOT.rglob('*.py')if'__pycache__'not in p.parts}
    assert all(implementation[rel]==digest for rel,digest in read(ROOT/'engineering/FINAL_ACCEPTANCE.json')['implementation_sha256'].items()),'Implementation changed after acceptance; no training admitted'
    for p in (ROOT/'engineering/throughput/RESOURCE_POLICY.json',ROOT/'engineering/EXECUTOR_MEMORY_PROFILE.json',ROOT/'TASKBOOK_ZH.txt',ROOT/'01_COVERAGE_PROTOCOL_LOCK.json'):implementation[p.relative_to(ROOT).as_posix()]=sha(p)
    seal=dict(status='SEALED_FOR_REGISTERED_COVERAGE',run_id='RAVM_JOINT_CMC_COVERAGE_20261022',sealed_unix=time.time(),taskbook_sha256=sha(ROOT/'TASKBOOK_ZH.txt'),
        main_execution_lock_sha256=sha(PRIOR/'D3F2_EXECUTION.lock.json'),main_zip_sha256='bb7e55c1c40f0a7093cc97b50611b09cd5cebc05fad93b80b4290ff4fee3b6cc',main_retraining=False,
        registered_groups={p.stem:sha(p)for p in folder.glob('*.json')},execution_order=[s['group']for s in specs],budgets=budgets,blocked_groups=blocked,implementation_sha256=implementation,
        registered_matrix_sha256=sha(ROOT/'REGISTERED_TRAJECTORY_MATRIX.csv'),acceptance_sha256=sha(ROOT/'engineering/FINAL_ACCEPTANCE.json'),
        work_weights=weights,work_weight_source='fixed pre-existing Main median maintenance+Service wall time by arm; only scheduling timing proxy, no scientific result used to retune gates',
        smoke='first registered center and first seed, first two streams, all methods; retained in full matrix; no extra training',
        startup_ram_bytes=2*2**30,worker_ram_floor_bytes=1610612736,no_periodic_llm_supervision=True,checkpoint='each completed stage and work unit',
        scientific_negative_does_not_abort=True,unknown_or_partial_optimizer_scope_replay=False,bootstrap_replicates=4000,bootstrap_seed=20261022,primary_for_supplements='DUAL_MEAN__g12 fixed from passed Main; all baselines reported',multiple_comparison_adjustment='none; exploratory intervals, no familywise dominance claim',
        thermal_population_ci=False,source_pretraining_steps=0,cost_replicas_in_science_sample_size=False,at_unix=time.time())
    atomic(ROOT/'SCIENCE_EXECUTION.lock.json',seal);atomic(ROOT/'05_BUDGET_PRECHECK.json',dict(status='SEALED',budgets=budgets,total_new_optimizer_upper=sum(x['total_steps']for x in budgets.values()),blocked_groups=blocked,scientific_lock_sha256=sha(ROOT/'SCIENCE_EXECUTION.lock.json')))
    atomic(ROOT/'EXECUTION_READY.json',dict(status='READY',scientific_lock_sha256=sha(ROOT/'SCIENCE_EXECUTION.lock.json'),implementation_sha256=implementation,all_legal_normal_stages_authorized=True))
    return seal

def run():
    identity()
    # The readonly external authentication owner was already launched before science.
    while not (ROOT/'process/ASSET_OWNER_COMPLETE.json').exists():
        if (ROOT/'process/ASSET_OWNER_IDENTITY.json').exists()and not alive(read(ROOT/'process/ASSET_OWNER_IDENTITY.json')):raise RuntimeError('Authentication owner exited without terminal receipt; do not silently recreate assets')
        w=read(ROOT/'progress/WORKER_STATUS.json')if(ROOT/'progress/WORKER_STATUS.json').exists()else{}
        s=read(ROOT/'progress/progress_state.json')
        if time.time()-s.get('updated_unix',0)>10:
            state(status='WAITING_FOR_RESOURCE' if not w.get('active_workers')else'RUNNING',phase='ASSET_AUTH',work='外部数据认证等待资源准入' if not w.get('active_workers')else'外部数据原始认证',completed=s.get('completed',0)if s.get('phase')=='ASSET_AUTH'else 0,total=s.get('total',1)if s.get('phase')=='ASSET_AUTH'else 1,unit=s.get('unit','认证工作项')if s.get('phase')=='ASSET_AUTH'else'认证工作项')
        atomic(ROOT/'process/SUPERVISOR_HEARTBEAT.json',dict(pid=os.getpid(),work='WAIT_FOR_AUTH_OWNER',at_unix=time.time()));time.sleep(3)
    acceptance=ROOT/'engineering/FINAL_ACCEPTANCE.json'
    if acceptance.exists()and any(sha(ROOT/rel)!=digest for rel,digest in read(acceptance).get('implementation_sha256',{}).items()):
        acceptance.rename(ROOT/'engineering'/f'FINAL_ACCEPTANCE_SUPERSEDED_{int(time.time())}.json')
    if not acceptance.exists():child('engineering_acceptance.py',label='FINAL_ACCEPTANCE',startup=True)
    assert read(ROOT/'engineering/FINAL_ACCEPTANCE.json')['status']=='PASS'
    seal=make_seal()
    for name in seal['execution_order']:
        spec=read(ROOT/'registered_groups'/f'{name}.json');stage(spec['stage'],'RUNNING',detail=name)
        try:
            for mode,suffix in [('prepare','PREPARE'),('smoke','SMOKE'),('audit_smoke','AUDIT_SMOKE'),('full','FULL'),('audit_full','AUDIT_FULL')]:
                receipt=ROOT/'receipts'/f'{name}_{suffix}.json'
                if receipt.exists():
                    assert read(receipt)['status']=='PASS','Existing failed phase must not be automatically trained again'
                    continue
                child('stage_worker.py',name,mode,label=name+'_'+mode,startup=True)
            stage(name,'SCIENCE_AND_AUDIT_PASS',detail='矩阵完成，真实权重/评分/签名/因果/Service复算通过')
        except Exception as e:
            # Audit every finished independent chain even when another full-run
            # chain failed; neither audit nor reporting can trigger training.
            if (ROOT/'receipts'/f'{name}_FULL.json').exists()and not(ROOT/'receipts'/f'{name}_AUDIT_FULL.json').exists():
                try:child('stage_worker.py',name,'audit_full',label=name+'_AUDIT_COMPLETED_AFTER_PARTIAL',startup=True)
                except Exception:pass
            stage(name,'BLOCKED_OR_INVALID',detail=str(e));atomic(ROOT/'failures'/f'{name}_OWNER.json',dict(error=traceback.format_exc(),independent_groups_continue=True,training_not_replayed=True,at_unix=time.time()))
    for stage_name in ('E1','E2','E3','E4','E5'):
        members=[n for n in seal['execution_order']if read(ROOT/'registered_groups'/f'{n}.json')['stage']==stage_name]
        passed=bool(members)and all((ROOT/'receipts'/f'{n}_AUDIT_FULL.json').exists()and read(ROOT/'receipts'/f'{n}_AUDIT_FULL.json')['status']=='PASS'for n in members)
        stage(stage_name,'PASS'if passed else'BLOCKED_OR_INCOMPLETE',detail='生命周期和独立审计完成'if passed else'详见该组失败/阻塞回执；不会自动重训')
    child('coverage_statistics.py',label='ALL_STATISTICS')
    child('coverage_reports.py',label='CHINESE_REPORTS')
    # Plotting is isolated from science; failed rendering cannot trigger training.
    for name in ['E0','E5_COST']+[n for n in seal['execution_order']if not read(ROOT/'registered_groups'/f'{n}.json').get('cost_only')]:
        try:
            sys.path.insert(0,str(ROOT/'engineering/throughput'));from dispatch import execute
            state(status='RUNNING',phase='FIGURES',work='图表剖析、绘制与机器版式检查',completed=0,total=1,unit='图表组')
            execute([name],lambda n:child('render_figures.py',n,label='FIGURES_'+n),'FIGURES_'+name,cpu=True,on_tick=lambda z:state(completed=z['completed'],active_workers=z['active_workers'],status='RUNNING'if z['active_workers']else'WAITING_FOR_RESOURCE'))
        except Exception:atomic(ROOT/'failures'/f'FIGURES_{name}.json',dict(error=traceback.format_exc(),visual_review_pending=True))
    child('coverage_delivery.py',label='ZIP_DELIVERY_AND_VERIFICATION')
    decision=read(ROOT/'SCIENTIFIC_GO_NO_GO.json')['status'];state(status='COMPLETE_PENDING_ACADEMIC_VISUAL_REVIEW',phase='COMPLETE',work=decision+'；中文报告与ZIP完整性核验完成，图稿待视觉/学术复核',completed=1,total=1,unit='交付',active_workers=0)
    atomic(ROOT/'process/OWNER_COMPLETE.json',dict(status=decision,delivery_pass=True,visual_review_pending=True,at_unix=time.time()))

if __name__=='__main__':
    import msvcrt
    ownership=(ROOT/'process/COVERAGE_OWNER.lock').open('a+b');ownership.seek(0,2)
    if ownership.tell()==0:ownership.write(b'1');ownership.flush()
    ownership.seek(0)
    try:msvcrt.locking(ownership.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:raise SystemExit('Another coverage owner holds the execution lock')
    try:run()
    except BaseException:
        atomic(ROOT/'process/COVERAGE_OWNER_FAILURE.json',dict(error=traceback.format_exc(),at_unix=time.time(),no_automatic_optimizer_replay=True));state(status='FAILED',phase='OWNER',work='执行器异常，已保留证据；不会自动重训',error=traceback.format_exc(),active_workers=0);raise
