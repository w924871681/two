import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,math
import numpy as np
import pandas as pd
from core.protocol import ROOT,save_json
from core.statistics import cluster_bootstrap,paired_bootstrap

def metrics(d):
    a=d.deployed_service_mse.to_numpy();c=d.groupby('center_id').deployed_service_mse.mean().to_numpy()
    committed=int(d.commit.sum());beneficial=int(d.beneficial_candidate.sum())
    return {'lifecycle_mse':float(a.mean()),'lifecycle_mae':float(d.deployed_service_mae.mean()),'final_stage_mse':float(d[d.stage==d.stage.max()].deployed_service_mse.mean()),'harmful_commit_rate':float(d.harmful_commit.mean()),'average_downside':float(d.downside.mean()),'conditional_harmful_rate':float(d.harmful_commit.sum()/committed) if committed else np.nan,'beneficial_commit_recall':float((d.commit*d.beneficial_candidate).sum()/beneficial) if beneficial else np.nan,'commit_rate':float(d.commit.mean()),'worst_10pct_stage_mse':float(np.sort(a)[-max(1,math.ceil(.1*len(a))):].mean()),'cvar90_center_mse':float(np.sort(c)[-max(1,math.ceil(.1*len(c))):].mean())}

def all_clustered_metrics(g):
    g=g.copy();g['beneficial_committed']=g.commit*g.beneficial_candidate
    columns=['deployed_service_mse','deployed_service_mae','commit','harmful_commit','downside','beneficial_candidate','beneficial_committed']
    h=g.groupby(['center_id','stage'])[columns].mean().reset_index()
    a=np.stack([d.sort_values('stage')[columns].to_numpy() for _,d in h.groupby('center_id')])
    def vector(s):
        avg=s.mean(axis=(1,2));flat=s[:,:,:,0].reshape(len(s),-1);center=s[:,:,:,0].mean(2)
        def ratio(x,y):return np.divide(x,y,out=np.full_like(x,np.nan),where=y>0)
        return {'lifecycle_mse':avg[:,0],'lifecycle_mae':avg[:,1],'final_stage_mse':s[:,:,-1,0].mean(1),'commit_rate':avg[:,2],'harmful_commit_rate':avg[:,3],'average_downside':avg[:,4],'conditional_harmful_rate':ratio(avg[:,3],avg[:,2]),'beneficial_commit_recall':ratio(avg[:,6],avg[:,5]),'worst_10pct_stage_mse':np.sort(flat,axis=1)[:,-max(1,math.ceil(.1*flat.shape[1])):].mean(1),'cvar90_center_mse':np.sort(center,axis=1)[:,-max(1,math.ceil(.1*center.shape[1])):].mean(1)}
    point=vector(a[None]);rng=np.random.default_rng(2904);samples=vector(a[rng.integers(len(a),size=(4000,len(a)))])
    out={}
    for k,v in point.items():
        out[k]=float(v[0]);valid=samples[k][np.isfinite(samples[k])]
        lo,hi=np.quantile(valid,[.025,.975]) if len(valid) else (np.nan,np.nan)
        out[k+'_ci_low']=lo;out[k+'_ci_high']=hi
    return out

def main():
    summary=[];pairs=[]
    for folder in ['q1_overall','q2_security','q3_benign_drift','q4_ablation','q5_sensitivity_cost','q5_generality','q5_runtime','q6_alibaba']:
        p=ROOT/'results'/folder
        if not p.exists():continue
        paths=[f for f in p.glob('*.csv') if f.name not in ['raw_episode_results.csv','summary.csv','paired_bootstrap.csv']]
        if paths:d=pd.concat([pd.read_csv(f) for f in paths],ignore_index=True)
        elif (p/'raw_episode_results.csv').exists():d=pd.read_csv(p/'raw_episode_results.csv')
        else:continue
        d.to_csv(p/'raw_episode_results.csv',index=False,na_rep='NA')
        # Keep sensitivity keys and transfer modes separate.
        d['variant']=d.run_id.str.replace(r'_\d{5}_.*','',regex=True)
        groups=['variant','backbone','horizon','attack_type','attack_alpha','attack_location']
        local=[];paired=[]
        for keys,condition in d.groupby(groups,dropna=False):
            identity=dict(zip(groups,keys))
            for method,g in condition.groupby('method'):
                point=all_clustered_metrics(g)
                entry={**identity,'method':method,**point,'centers':g.center_id.nunique(),'seeds':g.model_seed.nunique()}
                local.append(entry)
            if 'Proposed' in set(condition.method):
                means=condition[~condition.method.isin(['Proposed','OracleCommit'])].groupby('method').deployed_service_mse.mean()
                refs=list(dict.fromkeys(['Always-FT','ValidationCommit']+([means.idxmin()] if len(means) else [])))
                for ref in refs:
                    if ref not in set(condition.method):continue
                    for col in ['deployed_service_mse','harmful_commit','downside']:
                        mean,lo,hi=paired_bootstrap(condition,'Proposed',ref,col)
                        paired.append({**identity,'method':'Proposed','reference':ref,'metric':col,'difference':mean,'ci_low':lo,'ci_high':hi,'bootstrap_replicates':4000,'unit':'center'})
        pd.DataFrame(local).to_csv(p/'summary.csv',index=False,na_rep='NA')
        pd.DataFrame(paired).to_csv(p/'paired_bootstrap.csv',index=False,na_rep='NA')
        summary.extend([{'question':folder,**r} for r in local]);pairs.extend([{'question':folder,**r} for r in paired])
    (ROOT/'results/tables').mkdir(exist_ok=True,parents=True)
    pd.DataFrame(summary).to_csv(ROOT/'results/tables/all_summaries.csv',index=False,na_rep='NA')
    pd.DataFrame(pairs).to_csv(ROOT/'results/tables/all_paired_comparisons.csv',index=False,na_rep='NA')

if __name__=='__main__':main()
