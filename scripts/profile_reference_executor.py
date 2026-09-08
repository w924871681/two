"""Component and system profile for the unchanged reference executor."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ctypes,json,subprocess,threading,time
import numpy as np
import torch
import core.engine as engine
from core.protocol import ROOT,save_json
from scripts.run_calibration import calibration_definition

class IO_COUNTERS(ctypes.Structure):
    _fields_=[('ReadOperationCount',ctypes.c_ulonglong),('WriteOperationCount',ctypes.c_ulonglong),
              ('OtherOperationCount',ctypes.c_ulonglong),('ReadTransferCount',ctypes.c_ulonglong),
              ('WriteTransferCount',ctypes.c_ulonglong),('OtherTransferCount',ctypes.c_ulonglong)]

def io_counters():
    c=IO_COUNTERS();ctypes.windll.kernel32.GetProcessIoCounters(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(c))
    return {'read_ops':c.ReadOperationCount,'write_ops':c.WriteOperationCount,'read_bytes':c.ReadTransferCount,'write_bytes':c.WriteTransferCount}

class GpuSampler:
    def __init__(self):self.stop=False;self.samples=[]
    def loop(self):
        while not self.stop:
            try:
                x=subprocess.check_output(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,power.draw','--format=csv,noheader,nounits'],text=True,creationflags=0x08000000).strip().split(',')
                self.samples.append(tuple(float(v.strip()) for v in x))
            except Exception:pass
            time.sleep(.25)
    def start(self):self.thread=threading.Thread(target=self.loop,daemon=True);self.thread.start()
    def finish(self):
        self.stop=True;self.thread.join(timeout=2)
        a=np.asarray(self.samples) if self.samples else np.empty((0,3))
        return {'samples':len(a),'gpu_util_mean_percent':float(a[:,0].mean()) if len(a) else None,
            'gpu_util_max_percent':float(a[:,0].max()) if len(a) else None,
            'gpu_memory_mean_mb':float(a[:,1].mean()) if len(a) else None,
            'gpu_memory_max_mb':float(a[:,1].max()) if len(a) else None,
            'gpu_power_mean_w':float(a[:,2].mean()) if len(a) else None}

def profile_once(label,cache):
    candidate,_,_,_,jobs=calibration_definition('synthetic');method,settings=jobs[0]
    stats={'candidate_compute_s':0.,'candidate_compute_calls':0,'recent_verification_s':0.,'historical_verification_s':0.,
           'recent_score_calls':0,'historical_score_calls':0,'service_evaluation_s':0.,'service_error_calls':0,
           'verification_error_calls':0,'torch_load_s':0.,'torch_load_calls':0,'torch_save_s':0.,'torch_save_calls':0,
           'evidence_np_load_s':0.,'evidence_np_load_calls':0,'evidence_np_write_s':0.,'evidence_np_write_calls':0}
    context={'score':None,'score_index':0}
    originals={'robust':engine.robust_candidate,'score':engine.score,'errors':engine.errors,'torch_load':torch.load,
               'torch_save':torch.save,'np_load':np.load,'np_savez':np.savez_compressed}
    def robust(*a,**k):
        t=time.perf_counter();x=originals['robust'](*a,**k);stats['candidate_compute_s']+=time.perf_counter()-t;stats['candidate_compute_calls']+=1;return x
    def score(*a,**k):
        kind='recent' if context['score_index']%2==0 else 'historical';context['score_index']+=1;context['score']=kind;t=time.perf_counter()
        try:return originals['score'](*a,**k)
        finally:
            stats[f'{kind}_verification_s']+=time.perf_counter()-t;stats[f'{kind}_score_calls']+=1;context['score']=None
    def errors(*a,**k):
        t=time.perf_counter();x=originals['errors'](*a,**k);dt=time.perf_counter()-t
        if context['score'] is None:stats['service_evaluation_s']+=dt;stats['service_error_calls']+=1
        else:stats['verification_error_calls']+=1
        return x
    def torch_load(*a,**k):
        t=time.perf_counter();x=originals['torch_load'](*a,**k);stats['torch_load_s']+=time.perf_counter()-t;stats['torch_load_calls']+=1;return x
    def torch_save(*a,**k):
        t=time.perf_counter();x=originals['torch_save'](*a,**k);stats['torch_save_s']+=time.perf_counter()-t;stats['torch_save_calls']+=1;return x
    def np_load(*a,**k):
        t=time.perf_counter();x=originals['np_load'](*a,**k);dt=time.perf_counter()-t
        if context['score'] is not None:stats['evidence_np_load_s']+=dt;stats['evidence_np_load_calls']+=1
        return x
    def np_savez(*a,**k):
        t=time.perf_counter();x=originals['np_savez'](*a,**k);dt=time.perf_counter()-t
        if context['score'] is not None:stats['evidence_np_write_s']+=dt;stats['evidence_np_write_calls']+=1
        return x
    engine.robust_candidate=robust;engine.score=score;engine.errors=errors;torch.load=torch_load;torch.save=torch_save;np.load=np_load;np.savez_compressed=np_savez
    cand_dir=ROOT/'checkpoints/calibration_candidates';evid_dir=ROOT/'checkpoints/calibration_evidence'
    before_c=len(list(cand_dir.glob('*.pt')));before_e=len(list(evid_dir.glob('*.npz')));io0=io_counters();cpu0=time.process_time();sampler=GpuSampler();sampler.start();start=time.perf_counter()
    try:
        rows=engine.run(12002,7311,method,'clean',0.,cfg={**candidate,**settings,
            'calibration_candidate_cache':cache,'calibration_evidence_cache':cache},run_id=f'profile_{label}')
    finally:
        wall=time.perf_counter()-start;gpu=sampler.finish();cpu=time.process_time()-cpu0;io1=io_counters()
        engine.robust_candidate=originals['robust'];engine.score=originals['score'];engine.errors=originals['errors'];torch.load=originals['torch_load'];torch.save=originals['torch_save'];np.load=originals['np_load'];np.savez_compressed=originals['np_savez']
    after_c=len(list(cand_dir.glob('*.pt')));after_e=len(list(evid_dir.glob('*.npz')))
    accounted=stats['candidate_compute_s']+stats['recent_verification_s']+stats['historical_verification_s']+stats['service_evaluation_s']
    stats.update({'label':label,'cache_enabled':cache,'wall_s':wall,'trajectories_per_hour':3600/wall,
        'python_orchestration_and_hashing_s':max(0.,wall-accounted),'python_orchestration_and_hashing_percent':100*max(0.,wall-accounted)/wall,
        'candidate_percent_wall':100*stats['candidate_compute_s']/wall,'recent_verification_percent_wall':100*stats['recent_verification_s']/wall,
        'historical_verification_percent_wall':100*stats['historical_verification_s']/wall,'service_evaluation_percent_wall':100*stats['service_evaluation_s']/wall,
        'candidate_new_files':after_c-before_c,'candidate_cache_hits':24-(after_c-before_c) if cache else 0,
        'evidence_new_files':after_e-before_e,'evidence_cache_hits':48-(after_e-before_e) if cache else 0,
        'cpu_time_s':cpu,'cpu_percent_one_core':100*cpu/wall,'logical_cpu_percent':100*cpu/wall/(os.cpu_count() or 1),
        'disk_read_bytes':io1['read_bytes']-io0['read_bytes'],'disk_write_bytes':io1['write_bytes']-io0['write_bytes'],
        'disk_read_ops':io1['read_ops']-io0['read_ops'],'disk_write_ops':io1['write_ops']-io0['write_ops'],**gpu})
    return stats

def main():
    global os
    import os
    runs=[profile_once('uncached_reference',False),profile_once('cold_persistent_cache',True),profile_once('warm_persistent_cache',True)]
    save_json(ROOT/'audits/reference_executor_profile.json',{'status':'passed','workload':{'center':12002,'condition':'clean','seed':7311,'stages':24,'policy':0},'runs':runs})
    print(json.dumps(runs,indent=2),flush=True)

if __name__=='__main__':main()
