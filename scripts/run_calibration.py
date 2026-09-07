import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import itertools,json,time
import numpy as np
import pandas as pd
from core.protocol import ROOT,POOLS,save_json
from core.engine import run
from core.freeze import freeze_file

def main(domain='synthetic'):
    candidate=json.loads((ROOT/'configs/frozen_candidate_config.yaml').read_text())
    protocol=json.loads((ROOT/'configs/calibration_protocol.yaml').read_text())
    prefix='alibaba_' if domain=='alibaba' else ''
    centers=list(range(20040,20060)) if domain=='alibaba' else POOLS['calibration']
    out=ROOT/'results'/f'{prefix}calibration';out.mkdir(parents=True,exist_ok=True)
    grid=[dict(kappa_rec=kr,kappa_hist=kh,delta_imp=di,delta_ret=dr) for kr,kh,di,dr in itertools.product(protocol['kappas'],protocol['kappas'],protocol['delta_imp_grid'],protocol['delta_ret_grid'])]
    jobs=[('Proposed',cfg) for cfg in grid]+[('ValidationCommit',{'validation_threshold':v}) for v in protocol['delta_imp_grid']]
    summaries=[]
    for i,(method,settings) in enumerate(jobs):
        allrows=[]
        for seed in [7311,7312,7313]:
            for c in centers:
                for kind,alpha in [('clean',0.),('mixed',.1)]:
                    path=out/f'policy{i:03d}_{seed}_{c}_{kind}.csv'
                    if path.exists():d=pd.read_csv(path)
                    else:
                        d=pd.DataFrame(run(c,seed,method,kind,alpha,cfg={**candidate,**settings,'calibration_candidate_cache':True},run_id=f'calibration_policy{i:03d}'))
                        d.to_csv(path,index=False,na_rep='NA')
                    allrows.append(d)
                    save_json(ROOT/'logs/execution_status.json',{'phase':'P6 calibration','policy':i+1,'policies':len(jobs),'center':c,'seed':seed,'condition':kind,'heldout_started':False})
        d=pd.concat(allrows,ignore_index=True);g=d.groupby('attack_type')[['harmful_commit','downside','deployed_service_mse']].mean()
        eligible=bool((g.harmful_commit<=protocol['rho']).all() and (g.downside<=protocol['epsilon']).all())
        summaries.append({'policy':i,'method':method,**settings,'eligible':eligible,'lifecycle_mse':float(d.deployed_service_mse.mean()),'worst_condition_harmful_rate':float(g.harmful_commit.max()),'worst_condition_downside':float(g.downside.max())})
        pd.DataFrame(summaries).to_csv(ROOT/f'{prefix}calibration_grid.csv',index=False,na_rep='NA')
        print('calibration',i+1,'/',len(jobs),'eligible',eligible,flush=True)
    selected={};status={}
    for method in ['Proposed','ValidationCommit']:
        eligible=[s for s in summaries if s['method']==method and s['eligible']]
        if eligible:
            best=min(eligible,key=lambda r:(r['lifecycle_mse'],r['policy']));selected.update(jobs[best['policy']][1]);status[method]={'status':'calibrated','selected_policy':best['policy']}
        else:
            selected['retain_all' if method=='Proposed' else 'validation_retain_all']=True
            status[method]={'status':'calibration_failure_retain_all'}
    freeze_file(f'{prefix}frozen_commit_config.yaml',selected)
    save_json(ROOT/f'{prefix}calibration_summary.json',status)
    save_json(ROOT/'logs/execution_status.json',{'phase':'P7 commit frozen','heldout_started':False,'calibration':status})

if __name__=='__main__':main()
