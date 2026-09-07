import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import itertools,json,time
import pandas as pd
from core.protocol import ROOT,POOLS,save_json
from core.engine import run
from core.freeze import require_frozen
from scripts.bootstrap import generate
from scripts.pretrain import pretrain

METHODS=['Frozen','Always-FT','ER','EWC','Huber-FT','CLeaR-Predictor','ValidationCommit','Proposed','OracleCommit']

def case(out,center,seed,method,kind,alpha,loc,cfg,backbone='GRU',H=1,key='base',repeat=0):
    out=ROOT/'results'/out;out.mkdir(parents=True,exist_ok=True)
    name=f'{key}_{center}_{seed}_{backbone}_H{H}_{method}_{kind}_{alpha}_{loc}_r{repeat}.csv'
    path=out/name
    if path.exists():return
    rows=run(center,seed,method,kind,alpha,loc,cfg,backbone=backbone,H=H,run_id=name[:-4])
    tmp=path.with_suffix('.tmp');pd.DataFrame(rows).to_csv(tmp,index=False,na_rep='NA');tmp.replace(path)
    print(out.name,name,flush=True)
    save_json(ROOT/'logs/execution_status.json',{'phase':out.name,'last_completed':name,'heldout_started':True})

def main():
    require_frozen()
    cfg={}
    for f in ['frozen_candidate_config.yaml','frozen_commit_config.yaml','frozen_baseline_config.yaml']:
        cfg.update(json.loads((ROOT/'configs'/f).read_text()))
    if not all((ROOT/'data'/f'center_{c}.npz').exists() for c in POOLS['heldout']):generate('heldout')
    seeds=[7311,7312,7313]
    for seed,c,(kind,alpha),method in itertools.product(seeds,POOLS['heldout'],[('clean',0.),('mixed',.1)],METHODS):
        case('q1_overall',c,seed,method,kind,alpha,'both',cfg)
    conditions=[(a,p,'both') for a,p in itertools.product(['random','persistent_bias','burst','replay'],[.05,.1,.2])]
    conditions+=list(itertools.product(['persistent_bias','replay'],[.1],['update_only','verification_only']))
    for seed,c,(kind,alpha,loc),method in itertools.product(seeds,POOLS['heldout'][:20],conditions,[m for m in METHODS if m!='OracleCommit']):
        case('q2_security',c,seed,method,kind,alpha,loc,cfg)
    # Q3 uses exact clean Q1 trajectories; no redundant retraining.
    q1=pd.concat([pd.read_csv(p) for p in (ROOT/'results/q1_overall').glob('base_*.csv')],ignore_index=True)
    q3=ROOT/'results/q3_benign_drift';q3.mkdir(exist_ok=True);q1[q1.attack_alpha==0].to_csv(q3/'raw_episode_results.csv',index=False,na_rep='NA')
    for seed,c,(kind,alpha),method in itertools.product(seeds,POOLS['heldout'][:10],[('clean',0.),('mixed',.1)],['Proposed','SinglePath','MeanDelta','RecentOnly','MeanVerification','RobustAlways']):
        case('q4_ablation',c,seed,method,kind,alpha,'both',cfg)
    variants=[(f'B{b}_beta{beta}',{'B':b,'beta':beta}) for b,beta in itertools.product([5,10],[.1,.2])]
    variants += [(f'capacity{c}',{'capacity':c}) for c in [12,24,48]]
    for q in ['kappa_rec','kappa_hist']:
        for sign in [-1,1]:variants.append((f'{q}_{sign}',{q:max(0.,cfg.get(q,1.)+sign*.5)}))
    for seed,c,(kind,alpha),(key,overrides) in itertools.product(seeds,POOLS['heldout'][:10],[('clean',0.),('mixed',.1)],variants):
        case('q5_sensitivity_cost',c,seed,'Proposed',kind,alpha,'both',{**cfg,**overrides},key=key)
    for seed,backbone,H in itertools.product(seeds,['MLP','TCN','GRU'],[1,4]):
        pretrain(seed,backbone,H)
        for c,(kind,alpha),method in itertools.product(POOLS['heldout'][:10],[('clean',0.),('mixed',.1)],['Frozen','Always-FT','ER','ValidationCommit','Proposed']):
            case('q5_generality',c,seed,method,kind,alpha,'both',cfg,backbone,H,key='generality')
    # Five repeats on all preregistered ten centers, same state/data each repeat.
    for repeat,c,method in itertools.product(range(5),POOLS['heldout'][:10],METHODS[:-1]):
        case('q5_runtime',c,7311,method,'mixed',.1,'both',cfg,key='runtime',repeat=repeat)

if __name__=='__main__':main()
