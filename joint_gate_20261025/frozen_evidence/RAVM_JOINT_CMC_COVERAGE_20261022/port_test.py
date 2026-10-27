"""Zero-SGD port acceptance using sealed real Main states and shape fixtures."""
from common import *
import psutil,sys,time
me=psutil.Process();atomic(ROOT/'process/OWNER_IDENTITY.json',dict(pid=me.pid,create_time=me.create_time(),kind='ZERO_SGD_ENGINEERING_VALIDATION'))
while psutil.virtual_memory().available<2*2**30:
    atomic(ROOT/'engineering/PORT_PROGRESS.json',dict(status='WAITING_FOR_STARTUP_RAM',minimum_ram_bytes=2*2**30,at_unix=time.time()))
    state(status='WAITING_FOR_STARTUP_RAM',phase='ENGINEERING',work='零SGD一致性检查启动等待2 GiB内存',completed=0,total=192,unit='条封存记录',active_workers=0)
    time.sleep(3)
state(status='RUNNING',phase='ENGINEERING',work='冻结执行器零SGD一致性检查',completed=0,total=192,unit='条封存记录',active_workers=1)
def readonly_source(event,args):
    if event=='open':
        p,m,flags=args
        writing=(isinstance(m,str) and any(c in m for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if writing and isinstance(p,(str,bytes,os.PathLike)) and Path(os.fsdecode(p)).resolve().is_relative_to(PRIOR):raise PermissionError('Reference Main is read-only')
sys.addaudithook(readonly_source)
import bridge as b
import numpy as np
import torch
torch.set_num_threads(1)
def forbidden(*a,**k):raise PermissionError('Zero-SGD port acceptance')
torch.optim.SGD.step=forbidden
manifest=read(PRIOR/'RUN_MANIFEST.json');sources=read(PRIOR/'ASSET_IDENTITY.json')['sources']
spec=dict(root=str(PRIOR),group='REFERENCE_ONLY',centers=manifest['centers']['NewFinal'],sources=sources,architecture='GRU',horizon=1,features=24,
    domain='synthetic',stream_ids=['clean','mixed'],stream_specs={'clean':dict(kind='clean',alpha=0.,location='both'),'mixed':dict(kind='mixed',alpha=.1,location='both')})
checked=0
with b.context(spec):
    for center in manifest['centers']['NewFinal'][:4]:
        for stream in ('clean','mixed'):
            td=PRIOR/'science/NewFinal'/str(center)/'7311'/stream/'JOINT__l3__m0'
            timeline=b.Timeline(center);history=b.evidence_blocks(timeline.initial_history());cas=b.CAS(td/'models');gate=b.OriginalCMCGate()
            for t in range(1,25):
                seal=read(td/f'seal_{t:03}.json');u,v=timeline.maintenance(t);v=b.observed(v,center,t,stream)
                recent=b.evidence_blocks(v);parent=cas.load(seal['parent_entry']);candidate=cas.load(seal['candidate_entry'])
                scores=b.score(candidate,parent,recent,history,v,gate)
                assert scores==seal['scores'],('Exact real-state score mismatch',center,stream,t)
                action,_=b.joint_gate(scores['stage3']['recent_mean'],scores['parent_recent_verification_mean_loss'],scores['stage3']['mwu_p'],.3,5.6036475532487204e-5)
                assert action==seal['commit'];timeline.record_decision(t,action);history.extend(recent);checked+=1
                del parent,candidate
                if checked%24==0:
                    state(completed=checked,active_workers=1)
                    print(json.dumps(dict(real_sealed_stages=checked,optimizer_steps=0)),flush=True)
    for arch in ('MLP','TCN','GRU'):
        for h in (1,4):
            with b.context(dict(spec,architecture=arch,horizon=h)):
                x=np.arange(480*24,dtype='float32').reshape(480,24)/20000;y=np.arange(480,dtype='float32')/500;ts=np.arange(480)
                seg=b.Segment(x,y,ts,'verification');w=b.windows(seg)
                assert w[0].shape==(480-96-h+1,96,24) and w[1].shape==(480-96-h+1,h)
                np.testing.assert_array_equal(w[1][0],y[96:96+h])
                blocks=b.evidence_blocks(seg);assert len(blocks)==6
                previous=None
                for block in blocks:
                    bw=b.windows(block);assert bw[1].shape[1]==h
                    if previous is not None:assert previous<int(bw[2][0,0])
                    previous=int(bw[2][-1,-1])
                for d,p,mu in ((-.001,.01,.05),(-.00001,.9,.05),(.001,.01,.05),(0.,.2,0.)):
                    got,_=b.joint_gate(d,mu,p,.3,5.6036475532487204e-5)
                    assert got==bool(d<0 and d+.3*max(mu,1e-12)*(p-.2)<=-5.6036475532487204e-5)
receipt=dict(status='PASS',real_main_trajectories=8,real_main_stages=checked,all_score_fields_exact=True,all_joint_actions_exact=True,
    architecture_horizon_window_cells=6,target_shape_and_block_target_disjointness_pass=True,optimizer_steps=0,
    fixture_scope='deterministic shape/decision fixtures, not new scientific data',derivation=b.export_derivation(),at_unix=time.time())
atomic(ROOT/'engineering/PORT_EXACTNESS.json',receipt)
state(status='ENGINEERING_VALIDATED',phase='ENGINEERING',work='零SGD一致性检查通过',completed=checked,total=checked,active_workers=0)
print(json.dumps({k:v for k,v in receipt.items() if k!='derivation'}),flush=True)
