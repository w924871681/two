"""Run exact calibration trajectories in independent processes and merge deterministically."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse,datetime,subprocess,time
from core.protocol import ROOT,save_json
from core.engine import initial_model
from scripts.run_calibration import calibration_definition,finalize,SEEDS

def main(domain='synthetic',workers=2):
    _,_,prefix,centers,jobs=calibration_definition(domain)
    workers=max(1,min(int(workers),len(jobs)))
    print(f'Preparing immutable M0 checkpoints for {domain} calibration',flush=True)
    for seed in SEEDS:
        for center in centers:initial_model(center,seed,'GRU',1)
    processes=[];started=time.time()
    for i in range(workers):
        cmd=[sys.executable,str(ROOT/'scripts/run_calibration.py'),'--domain',domain,'--worker-index',str(i),'--num-workers',str(workers)]
        processes.append(subprocess.Popen(cmd,cwd=ROOT))
    total=len(jobs)*len(SEEDS)*len(centers)*2
    try:
        while True:
            codes=[p.poll() for p in processes]
            completed=sum(1 for _ in (ROOT/'results'/f'{prefix}calibration').glob('policy*.csv'))
            elapsed=time.time()-started;rate=completed/elapsed if elapsed else 0.
            eta=(total-completed)/rate if rate else None
            save_json(ROOT/'logs/execution_status.json',{'phase':'P6 calibration parallel','domain':domain,
                'workers':workers,'worker_pids':[p.pid for p in processes],'completed_trajectories':completed,
                'total_trajectories':total,'elapsed_s':elapsed,'trajectory_rate_per_s':rate,'eta_s':eta,
                'updated_at':datetime.datetime.now().isoformat(),'heldout_started':False})
            failed=[(i,c) for i,c in enumerate(codes) if c not in (None,0)]
            if failed:raise RuntimeError(f'calibration worker failed: {failed}')
            if all(c==0 for c in codes):break
            time.sleep(10)
    except BaseException:
        for p in processes:
            if p.poll() is None:p.terminate()
        for p in processes:
            try:p.wait(timeout=30)
            except subprocess.TimeoutExpired:p.kill()
        raise
    return finalize(domain,workers)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--domain',choices=['synthetic','alibaba'],default='synthetic');p.add_argument('--workers',type=int,default=2)
    a=p.parse_args();main(a.domain,a.workers)
