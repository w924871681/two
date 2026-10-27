"""No-SGD interface acceptance; dispatch decisions have deterministic clock fixtures."""
from common import *
import sys,subprocess,psutil
while psutil.virtual_memory().available<2*2**30:
    state(status='WAITING_FOR_STARTUP_RAM',phase='ENGINEERING',work='等待2 GiB启动内存进行最终零SGD接口核验',completed=0,total=1,unit='工程检查');time.sleep(3)
result=subprocess.run([sys.executable,'-B','-X','utf8','-u',str(ROOT/'port_test.py')],cwd=ROOT,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
import bridge as b
import numpy as np
b.torch.optim.SGD.step=lambda *a,**k:(_ for _ in ()).throw(PermissionError('No-SGD acceptance'))
from e4_assets import original
from core.protocol import WindowSet
spec=dict(domain='thermbuild',architecture='GRU',horizon=1,features=26)
with b.context(spec):
    x=np.zeros((200,26),dtype='float32');y=np.arange(200,dtype='float32');y[[97,111,142]]=np.nan;ts=np.arange(200)
    seg=b.Segment(x,y,ts,'verification');raw=b.native_windows(seg);w=b.windows(seg);valid=np.isfinite(raw[1]).all(1)
    assert np.array_equal(w[0],raw[0][valid]) and np.array_equal(w[1],raw[1][valid]) and np.array_equal(w[2],raw[2][valid])
    blocks=b.evidence_blocks(seg)
    b.native.windows=b.native_windows
    try:original_blocks=b.native_blocks(seg)
    finally:b.native.windows=b.windows
    assert [s.hash for s in blocks]==[s.hash for s in original_blocks]
    assert sum(len(b.windows(s)[0])for s in blocks)==len(w[0])
    parent=b.NativeForecast('GRU',1,26).to(b.DEVICE);candidate=b.copy.deepcopy(parent)
    with b.torch.no_grad():candidate.head.bias.add_(.001)
    history=b.evidence_blocks(b.Segment(x,y,ts,'verification'))
    z=b.score(candidate,parent,blocks,history,seg,b.OriginalCMCGate())
    assert np.isfinite(z['stage3']['recent_mean']) and 0<=z['stage3']['mwu_p']<=1
    assert z['original_commit']==bool(z['recent_score']<=-2.8018237766243602e-5 and z['history_score']<=0)
sys.path.insert(0,str(ROOT/'engineering/throughput_v3'))
from tuner import ThroughputTuner
t=ThroughputTuner(4,1,window_seconds=10,min_stages=1,max_window_seconds=10)
t.tick(1,0,0,0,4,0);t.tick(1,10,10,10,4,10);assert t.target==4
t.tick(4,10,10,10,4,11);t.tick(4,15,15,15,4,21);assert t.target==1 and t.retry_after[4]>21
assert t.best(4)[0]==1
policy=read(ROOT/'engineering/throughput/RESOURCE_POLICY.json');assert policy['ram_reserve_bytes']==1610612736
from memory_profile import run as profile_memory
memory=profile_memory(b)
atomic(ROOT/'engineering/FINAL_ACCEPTANCE.json',dict(status='PASS',optimizer_steps=0,main_real_record_port=read(ROOT/'engineering/PORT_EXACTNESS.json'),
    thermbuild_nan_target_filter_preserves_chronological_block_boundaries=True,thermal_gate_scores_finite=True,slower_concurrency_rolls_back_and_retries=True,
    no_frozen_source_bytes_changed=True,memory_profile=memory,fixture_scope='engineering only, excluded from science',implementation_sha256={p.relative_to(ROOT).as_posix():sha(p)for p in ROOT.rglob('*.py')if'__pycache__'not in p.parts},at_unix=time.time()))
