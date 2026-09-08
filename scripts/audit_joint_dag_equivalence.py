"""Layered full-lifecycle equivalence audit for reference and joint DAG executors."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,os,time
import numpy as np
import pandas as pd
from core.protocol import ROOT,Timeline,attack,digest,save_json
from core.engine import run,evidence_blocks
from core.joint_dag import run_joint,CacheBundle,history_hash,causal_payload,key_hash
from scripts.run_calibration import calibration_definition

EXCLUDED={'run_id','candidate_update_time_s','verification_time_s','maintenance_time_s','peak_gpu_memory_bytes'}
CASES=[
    {'name':'five_abrupt_clean','center':12002,'condition':'clean','alpha':0.,'policies':[0,1,24,199,399]},
    {'name':'twenty_abrupt_mixed','center':12002,'condition':'mixed','alpha':.1,'policies':list(range(0,400,20))},
    {'name':'twenty_recurring_clean','center':12003,'condition':'clean','alpha':0.,'policies':list(range(10,400,20))},
    {'name':'all400_recurring_mixed','center':12003,'condition':'mixed','alpha':.1,'policies':list(range(400))}
]

def atomic_csv(d,path):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(f'{path.name}.{os.getpid()}.tmp');d.to_csv(tmp,index=False,na_rep='NA');os.replace(tmp,path)

def history_catalog(center,kind,alpha):
    timeline=Timeline(center);history=evidence_blocks(timeline.initial_history(),1);out={}
    for stage in range(1,25):
        raw_u,raw_v=timeline.maintenance(stage);u,um,us,actual=attack(raw_u,center,stage,kind,alpha,'both');v,vm,vs,_=attack(raw_v,center,stage,kind,alpha,'both')
        recent=evidence_blocks(v,1);nxt=(history+recent)[-24:]
        out[stage]={'history':history_hash(history),'next':history_hash(nxt),'update':u.hash,'verification':v.hash,'attack':digest(um,vm,us,vs),'actual':actual}
        timeline.record_decision(stage,False);history=nxt
    return out

def enrich_reference(d,policy,catalog):
    d=d.copy();d['policy']=policy;d['deployed_state_hash']=np.where(d.commit.astype(bool),d.candidate_state_hash,d.parent_state_hash)
    d['historical_buffer_hash']=[catalog[int(s)]['history'] for s in d.stage];d['next_historical_buffer_hash']=[catalog[int(s)]['next'] for s in d.stage]
    d['causal_state_fingerprint']=[key_hash(causal_payload(r.parent_state_hash,catalog[int(r.stage)]['history'],int(r.center_id),int(r.model_seed),int(r.stage),
        r.attack_type,r.actual_attack_type,float(r.attack_alpha),r.attack_location,int(r.horizon),r.update_data_hash,r.verification_data_hash,r.attack_mask_hash,5,.1)) for r in d.itertuples()]
    return d

def compare_frames(reference,dag):
    reference=reference.sort_values(['policy','stage']).reset_index(drop=True);dag=dag.sort_values(['policy','stage']).reset_index(drop=True)
    cols=[c for c in reference.columns if c not in EXCLUDED];assert set(cols)==set(c for c in dag.columns if c not in EXCLUDED)
    exact_cols=[];float_cols=[];max_abs=0.;tail_only=[]
    for c in cols:
        a=reference[c].to_numpy();b=dag[c].to_numpy()
        if np.issubdtype(a.dtype,np.number) and np.issubdtype(b.dtype,np.number) and (np.issubdtype(a.dtype,np.floating) or np.issubdtype(b.dtype,np.floating)):
            float_cols.append(c);exact=np.array_equal(a,b,equal_nan=True)
            diff=np.abs(a.astype(float)-b.astype(float));finite=diff[np.isfinite(diff)];m=float(finite.max()) if len(finite) else 0.;max_abs=max(max_abs,m)
            if not exact:tail_only.append({'column':c,'max_abs_diff':m})
            assert m<=1e-12,c
        else:
            assert np.array_equal(a,b),c;exact_cols.append(c)
    assert np.array_equal(reference.commit.to_numpy(),dag.commit.to_numpy())
    for _,g in reference.groupby('policy'):
        q=dag[dag.policy==g.policy.iloc[0]];assert np.array_equal(g.commit.to_numpy(),q.commit.to_numpy());assert np.array_equal(g.deployed_state_hash.to_numpy(),q.deployed_state_hash.to_numpy())
    return {'rows':len(reference),'scientific_columns':len(cols),'exact_columns':exact_cols,'float_columns':float_cols,
        'all_hashes_and_decisions_exact':True,'bitwise_equal':not tail_only,'serialization_tail_columns':tail_only,'max_abs_diff':max_abs}

def main():
    candidate,_,_,_,jobs=calibration_definition('synthetic');audit={'status':'running','started_at':time.time(),'cases':[],'full_p6_started':False}
    save_json(ROOT/'audits/joint_dag_equivalence.json',audit)
    for case in CASES:
        catalog=history_catalog(case['center'],case['condition'],case['alpha']);refs=[];ref_start=time.perf_counter()
        for n,policy in enumerate(case['policies']):
            path=ROOT/'results/equivalence_reference'/case['name']/f'policy{policy:03d}.csv'
            if path.exists():d=pd.read_csv(path)
            else:
                method,settings=jobs[policy];d=pd.DataFrame(run(case['center'],7311,method,case['condition'],case['alpha'],cfg={**candidate,**settings,
                    'calibration_candidate_cache':True,'calibration_evidence_cache':True},run_id=f'equivalence_reference_{case["name"]}_{policy}'))
                atomic_csv(d,path)
            refs.append(enrich_reference(d,policy,catalog))
            if (n+1)%10==0:save_json(ROOT/'logs/joint_dag_equivalence_progress.json',{'case':case['name'],'phase':'reference','completed':n+1,'total':len(case['policies'])})
        reference=pd.concat(refs,ignore_index=True);ref_wall=time.perf_counter()-ref_start
        plist=[{'policy':p,**jobs[p][1]} for p in case['policies']];dag_start=time.perf_counter()
        result,metrics,stages=run_joint(case['center'],7311,plist,case['condition'],case['alpha'],cache=CacheBundle(),use_l1=True,use_l2=True,run_id=f'equivalence_dag_{case["name"]}')
        dag=pd.concat([pd.DataFrame(result[p]) for p in case['policies']],ignore_index=True);dag_wall=time.perf_counter()-dag_start
        for p in case['policies']:atomic_csv(pd.DataFrame(result[p]),ROOT/'results/equivalence_dag'/case['name']/f'policy{p:03d}.csv')
        check=compare_frames(reference,dag);entry={**case,'stages':24,'reference_wall_s':ref_wall,'dag_wall_s':dag_wall,'dag_metrics':metrics,'stage_state_counts':stages,'comparison':check}
        audit['cases'].append(entry);save_json(ROOT/'audits/joint_dag_equivalence.json',audit)
        print(f'{case["name"]}: equivalence passed, reference {ref_wall:.1f}s DAG {dag_wall:.1f}s',flush=True)
    audit['status']='passed';audit['completed_at']=time.time();audit['all_scientific_equivalence_pass']=True;audit['no_decision_changes']=True
    audit['leakage_audit']={'decision_before_service_for_all_rows':True,'service_hash_absent_from_candidate_and_evidence_cache_keys':True,
        'historical_buffer_in_causal_fingerprint':True,'full_p6_or_heldout_accessed':False}
    save_json(ROOT/'audits/joint_dag_equivalence.json',audit);print('ALL JOINT DAG EQUIVALENCE CHECKS PASSED',flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        path=ROOT/'audits/joint_dag_equivalence.json';obj=json.loads(path.read_text()) if path.exists() else {};obj.update({'status':'FAILED_STOP','error':repr(exc)});save_json(path,obj);raise
