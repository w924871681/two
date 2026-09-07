import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import itertools,json,time
import pandas as pd
from core.protocol import ROOT,POOLS,save_json
from core.engine import run
from core.freeze import freeze_file
from scripts.pretrain import pretrain

def main():
    specs=[('RobustAlways',{'B':b,'beta':beta},f'candidate_B{b}_beta{beta}') for b,beta in itertools.product([5,10],[.1,.2])]
    specs += [('Frozen',{},'reference_frozen'),('Always-FT',{},'reference_ft')]
    specs += [('EWC',{'ewc_lambda':lam},f'ewc_{lam}') for lam in [10.,200.,1000.]]
    specs += [('CLeaR-Predictor',{'clear_factor':f,'clear_capacity':n},f'clear_{f}_{n}') for f,n in itertools.product([.75,1.5],[64,128])]
    out=ROOT/'results/development';out.mkdir(exist_ok=True,parents=True)
    start=time.time()
    for seed in [7311,7312,7313]:
        pretrain(seed)
        for method,cfg,key in specs:
            for center in POOLS['development']:
                for kind,alpha in [('clean',0.),('mixed',.1)]:
                    path=out/f'{key}_{seed}_{center}_{kind}.csv'
                    if path.exists():continue
                    rows=run(center,seed,method,kind,alpha,cfg=cfg,run_id=key)
                    pd.DataFrame(rows).to_csv(path,index=False,na_rep='NA')
                    print('development',key,seed,center,kind,'elapsed_s',round(time.time()-start),flush=True)
                    save_json(ROOT/'logs/execution_status.json',{'phase':'P4 development','last_completed':path.name,'elapsed_s':time.time()-start,'heldout_started':False})
    frames=[]
    for path in sorted(out.glob('*.csv')):
        if path.name=='development_summary.csv':continue
        d=pd.read_csv(path);frames.append(d)
    df=pd.concat(frames,ignore_index=True)
    scores=df.groupby('run_id').deployed_service_mse.mean()
    candidates=scores[scores.index.str.startswith('candidate_')];best=candidates.idxmin()
    selected=next(cfg for _,cfg,key in specs if key==best)
    freeze_file('frozen_candidate_config.yaml',selected)
    reference=float(scores['reference_frozen']);scale=[reference*x for x in [0,.001,.005,.01,.05]]
    freeze_file('calibration_protocol.yaml',{'kappas':[0.,.5,1.,1.5],'delta_imp_grid':scale,'delta_ret_grid':scale,'epsilon':reference*.01,'rho':.05,'reference_lifecycle_MSE_dev':reference,'eligibility':'Both clean and mixed condition individually satisfy unconditional harmful-commit rate <= rho and mean downside <= epsilon','fallback':'retain_all'})
    ewc=scores[scores.index.str.startswith('ewc_')].idxmin()
    clear=scores[scores.index.str.startswith('clear_')].idxmin().split('_')
    freeze_file('frozen_baseline_config.yaml',{'ewc_lambda':float(ewc.split('_')[1]),'huber_delta':.1,'ewc_gamma':.9,'ewc_fisher_examples':32,'clear_factor':float(clear[1]),'clear_capacity':int(clear[2]),'clear_ewc_lambda':200.})
    scores.to_csv(out/'development_summary.csv')
    save_json(ROOT/'logs/execution_status.json',{'phase':'P5 candidate frozen','selected':selected,'heldout_started':False})

if __name__=='__main__':main()
