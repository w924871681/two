"""Read-only analysis of archived P6 executor results and cache request structure."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import hashlib,json
import numpy as np
import pandas as pd
from core.protocol import ROOT,Timeline
from scripts.run_calibration import calibration_definition

def candidate_key(row,B=5,beta=.1):
    key=json.dumps([row.parent_state_hash,row.update_data_hash,int(row.model_seed),int(row.center_id),
        int(row.stage),row.method,row.backbone,int(row.horizon),B,beta])
    return hashlib.sha256(key.encode()).hexdigest()

def deployed_hash(d):
    return np.where(d.commit.astype(bool),d.candidate_state_hash,d.parent_state_hash)

def read_files(path):
    frames=[];meta=[]
    for p in sorted(path.glob('policy*.csv')):
        d=pd.read_csv(p);d['source_file']=p.name
        policy=int(p.name[6:9]);d['policy']=policy;frames.append(d)
        meta.append({'file':p.name,'policy':policy,'mtime':p.stat().st_mtime,'rows':len(d)})
    return pd.concat(frames,ignore_index=True),pd.DataFrame(meta)

def stage_states(d):
    out=[]
    d=d.copy();d['deployed_state_hash']=deployed_hash(d)
    for stage,g in d.groupby('stage'):
        out.append({'stage':int(stage),'observed_policies':int(g.policy.nunique()),
            'unique_parent_states':int(g.parent_state_hash.nunique()),
            'unique_deployed_states':int(g.deployed_state_hash.nunique()),
            'unique_candidate_computations':int(g[['parent_state_hash','update_data_hash']].drop_duplicates().shape[0]),
            'unique_verification_evidence_states':int(g[['parent_state_hash','candidate_state_hash','verification_data_hash']].drop_duplicates().shape[0])})
    return out

def main():
    old=ROOT/'archive/pre_acceleration_20260908_194751/results/calibration'
    dual=ROOT/'archive/pre_joint_dag_20260908_210552/results/calibration'
    old_d,old_m=read_files(old);dual_d,dual_m=read_files(dual)
    for d in [old_d,dual_d]:d['candidate_key']=d.apply(candidate_key,axis=1)
    complete=dual_m[dual_m.rows==24]
    wall=(complete.mtime.max()-complete.mtime.min()) if len(complete)>1 else np.nan
    sums=dual_d.groupby('source_file').agg(candidate_s=('candidate_update_time_s','sum'),verification_s=('verification_time_s','sum'),maintenance_s=('maintenance_time_s','sum'))
    med=sums.median();maintenance_other=med.maintenance_s-med.candidate_s-med.verification_s
    requests=len(dual_d);unique=dual_d.candidate_key.nunique()
    a=set(dual_d[dual_d.policy<203].candidate_key);b=set(dual_d[dual_d.policy>=203].candidate_key)
    # The old archive supplies 192 complete policies for one representative workload.
    representative=old_d[(old_d.center_id==12002)&(old_d.model_seed==7311)&(old_d.attack_type=='clean')&
                         (old_d.policy<192)&(old_d.stage<=24)]
    counts=representative.groupby('policy').stage.nunique();representative=representative[representative.policy.isin(counts[counts==24].index)]
    report={
        'status':'complete','scientific_code_modified':False,
        'archives':{'old_trajectories':int(old_m.rows.eq(24).sum()),'dual_trajectories':int(dual_m.rows.eq(24).sum())},
        'dual_executor_timing':{
            'median_candidate_s_per_trajectory':float(med.candidate_s),
            'median_verification_s_per_trajectory':float(med.verification_s),
            'median_maintenance_s_per_trajectory':float(med.maintenance_s),
            'median_python_inside_maintenance_s':float(maintenance_other),
            'candidate_percent_of_maintenance':float(100*med.candidate_s/med.maintenance_s),
            'verification_percent_of_maintenance':float(100*med.verification_s/med.maintenance_s),
            'other_percent_of_maintenance':float(100*maintenance_other/med.maintenance_s),
            'observed_file_interval_s':float(wall),
            'complete_trajectory_files':int(len(complete))},
        'candidate_cache_structure':{
            'stage_requests':requests,'unique_keys':unique,
            'theoretical_hit_rate':float(1-unique/requests),
            'keys_requested_by_both_workers':len(a&b),
            'worker0_unique_keys':len(a),'worker1_unique_keys':len(b),
            'cross_worker_overlap_fraction':float(len(a&b)/max(1,min(len(a),len(b))))},
        'representative_workload':{
            'center':12002,'drift_regime':Timeline(12002).meta['drift_regime'],'condition':'clean','seed':7311,
            'complete_policies_observed':int(representative.policy.nunique()),
            'stage_state_counts':stage_states(representative)}
    }
    out=ROOT/'audits/p6_archive_diagnostic.json';out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
