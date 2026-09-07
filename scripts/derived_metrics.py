import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import math
import numpy as np
import pandas as pd
from core.protocol import ROOT

def main():
    out=ROOT/'results/figure_data';out.mkdir(exist_ok=True,parents=True)
    q1=pd.read_csv(ROOT/'results/q1_overall/raw_episode_results.csv')
    clean=q1[q1.attack_alpha==0]
    keys=['center_id','model_seed','method','backbone','horizon']
    cols=['deployed_service_mse','harmful_commit','downside']
    base=clean.groupby(keys)[cols].mean().add_suffix('_clean').reset_index()
    for folder in ['q1_overall','q2_security']:
        d=pd.read_csv(ROOT/'results'/folder/'raw_episode_results.csv')
        attacked=d[d.attack_alpha>0].groupby(keys+['attack_type','attack_alpha','attack_location'])[cols].mean().reset_index()
        joined=attacked.merge(base,on=keys,validate='many_to_one')
        for col in cols:joined[col+'_attack_increase']=joined[col]-joined[col+'_clean']
        joined.to_csv(out/(folder+'_attack_increases.csv'),index=False,na_rep='NA')
    reference=clean[clean.method.isin(['Frozen','Always-FT','ER','OracleCommit'])].groupby(['center_id','model_seed','stage']).deployed_service_mse.min().rename('observed_best_reference')
    curve=clean.join(reference,on=['center_id','model_seed','stage'])
    curve['excess_loss']=(curve.deployed_service_mse-curve.observed_best_reference).clip(lower=0)
    curve.to_csv(out/'q3_lifecycle_curves.csv',index=False,na_rep='NA')
    recovery=[]
    for values,g in curve.groupby(keys+['drift_regime']):
        identity=dict(zip(keys+['drift_regime'],values));regime=identity['drift_regime']
        if regime=='stationary':continue
        onset=7 if regime=='recurring' else 9;g=g[g.stage>=onset].sort_values('stage')
        within=(g.deployed_service_mse<=1.05*g.observed_best_reference).to_numpy()
        hits=np.flatnonzero(within[:-1]&within[1:]);delay=int(hits[0]+1) if len(hits) else np.nan
        recovery.append({**identity,'post_drift_excess_loss_area':g.excess_loss.sum(),'recovery_episodes_exploratory':delay,'censored':not len(hits),'reference_definition':'per-stage observed minimum across Frozen/Always-FT/ER/Oracle; diagnostic, not known attainable optimum'})
    pd.DataFrame(recovery).to_csv(out/'q3_drift_adaptation.csv',index=False,na_rep='NA')
    runtime=pd.read_csv(ROOT/'results/q5_runtime/raw_episode_results.csv')
    timing=runtime.groupby(['center_id','method']).agg(repeats=('run_id','nunique'),update_time_s=('candidate_update_time_s','mean'),verification_time_s=('verification_time_s','mean'),total_time_s=('maintenance_time_s','mean'),peak_gpu_bytes=('peak_gpu_memory_bytes','max'),persistent_bytes=('persistent_buffer_bytes','max')).reset_index()
    assert (timing.repeats>=5).all();timing.to_csv(out/'q5_runtime.csv',index=False)

if __name__=='__main__':main()
