"""Zero-SGD forward/backward allocation fixtures; no weights/data outcomes are produced."""
from common import *
import psutil,threading,concurrent.futures as cf,math
def run(b):
    process=psutil.Process();peak={'rss':0,'private':0};mutex=threading.Lock();stop=threading.Event()
    def sample():
        m=process.memory_info()
        with mutex:peak['rss']=max(peak['rss'],m.rss);peak['private']=max(peak['private'],getattr(m,'private',m.rss))
    # Import/init overhead is shared process state, never charged as N interpreters.
    warm=b.NativeForecast('GRU',1,24).to(b.DEVICE);optimizer=b.torch.optim.SGD(warm.parameters(),lr=.01);del warm,optimizer;b.sync()
    def watch():
        while not stop.wait(.02):sample()
    rows=[]
    def fixture(cell):
        arch,h,features=cell;model=b.NativeForecast(arch,h,features).to(b.DEVICE);identity=b.state_hash(model)
        x=b.torch.zeros(64,96,features,device=b.DEVICE);y=b.torch.zeros(64,h,device=b.DEVICE);loss=(model(x)-y).square().mean();loss.backward();sample()
        # Larger verification batches exercise inference allocations too.
        batch=b.Batch(b.torch.zeros(540,96,features,device=b.DEVICE),b.torch.zeros(540,h,device=b.DEVICE),'verification');b.errors(model,batch);b.sync();sample()
        assert b.state_hash(model)==identity;return dict(architecture=arch,horizon=h,features=features,optimizer_steps=0,weight_state_unchanged=True)
    cells=[(a,h,24)for a in('MLP','TCN','GRU')for h in(1,4)]+[('GRU',1,40),('GRU',1,26)]
    for cell in cells:fixture(cell)
    b.gc.collect();b.sync();base=process.memory_info();baseline={'rss':base.rss,'private':getattr(base,'private',base.rss)};peak.update(baseline)
    sampler=threading.Thread(target=watch,daemon=True);sampler.start()
    try:
        for cell in cells:
            with cf.ThreadPoolExecutor(max_workers=2)as pool:rows.extend(list(pool.map(fixture,[cell,cell])))
    finally:stop.set();sampler.join();sample()
    delta=max(peak[k]-baseline[k]for k in peak);recommended=max(128*2**20,math.ceil((2*max(0,delta)/2+32*2**20)/(32*2**20))*32*2**20)
    receipt=dict(status='PASS',optimizer_steps=0,fixture_workers=2,baseline=baseline,peak=peak,incremental_peak_bytes=delta,recommended_ram_per_worker_bytes=recommended,
        allowance_rule='max128MiB, round32MiB(2x max observed RSS/private incremental bytes /2 workers +32MiB); shared initialized interpreter separate; live RAM/VRAM admission remains mandatory',
        coverage=rows,scope='engineering allocation fixtures; no real experiment data, optimizer step, or performance result',at_unix=time.time())
    atomic(ROOT/'engineering/EXECUTOR_MEMORY_PROFILE.json',receipt);return receipt
