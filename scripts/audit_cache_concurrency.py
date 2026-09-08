"""Exercise two Windows processes publishing the same candidate/evidence cache keys."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,subprocess
import pandas as pd
from core.protocol import ROOT,save_json
from core.engine import run
from scripts.run_calibration import calibration_definition

COLS=['parent_state_hash','candidate_state_hash','commit','U_rec','U_hist','deployed_service_mse',
      'service_data_hash','attack_mask_hash','number_of_forward_passes','number_of_backward_updates']

def worker(index):
    candidate,_,_,_,jobs=calibration_definition('synthetic');method,settings=jobs[0]
    d=pd.DataFrame(run(12010,7311,method,'clean',0.,cfg={**candidate,**settings,
        'calibration_candidate_cache':True,'calibration_evidence_cache':True},stages=2,run_id=f'cache_race_{index}'))
    save_json(ROOT/f'audits/cache_race_worker{index}.json',d[COLS].to_dict(orient='records'))

def main():
    ps=[subprocess.Popen([sys.executable,__file__,'--worker',str(i)],cwd=ROOT) for i in range(2)]
    codes=[p.wait() for p in ps];assert codes==[0,0],codes
    a=json.loads((ROOT/'audits/cache_race_worker0.json').read_text());b=json.loads((ROOT/'audits/cache_race_worker1.json').read_text())
    assert a==b
    save_json(ROOT/'audits/cache_concurrency.json',{'status':'passed','processes':2,'stages':2,
        'scientific_fields_compared':COLS,'outputs_identical':True})
    print('cache concurrency audit passed',flush=True)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--worker':worker(int(sys.argv[2]))
    else:main()
