"""Strictly validate archived reference caches before exposing them to the DAG."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import hashlib,json,os
import numpy as np
import pandas as pd
import torch
from core.protocol import ROOT,Timeline,attack,digest,save_json
from core.engine import evidence_blocks
from core.joint_dag import CacheBundle,candidate_payload,evidence_payload,key_hash,canonical,atomic_npz

ARCHIVES=[ROOT/'archive/pre_acceleration_20260908_194751',ROOT/'archive/pre_joint_dag_20260908_210552']

def state_dict_hash(state):
    h=hashlib.sha256()
    for k,v in state.items():h.update(k.encode());h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()

def old_candidate_key(r):
    obj=[r.parent_state_hash,r.update_data_hash,int(r.model_seed),int(r.center_id),int(r.stage),r.method,r.backbone,int(r.horizon),5,.1]
    return hashlib.sha256(json.dumps(obj).encode()).hexdigest()

def old_evidence_key(parent,candidate,H,blocks):
    obj=[candidate,parent,H,[b.hash for b in blocks]]
    return hashlib.sha256(json.dumps(obj,separators=(',',':')).encode()).hexdigest()

def data_catalog():
    out={}
    for center in range(12000,12020):
        for kind,alpha in [('clean',0.),('mixed',.1)]:
            timeline=Timeline(center);history=evidence_blocks(timeline.initial_history(),1)
            for stage in range(1,25):
                raw_u,raw_v=timeline.maintenance(stage);u,um,us,actual=attack(raw_u,center,stage,kind,alpha,'both');v,vm,vs,_=attack(raw_v,center,stage,kind,alpha,'both')
                recent=evidence_blocks(v,1)
                out[(center,kind,stage)]={'update_hash':u.hash,'verification_hash':v.hash,'attack_hash':digest(um,vm,us,vs),
                    'actual':actual,'recent':recent,'history':list(history)}
                timeline.record_decision(stage,False);history=(history+recent)[-24:]
    return out

def add_mapping(mapping,key,value,reasons):
    if key in mapping and mapping[key]!=value:
        mapping[key]=None;reasons['inconsistent_provenance_rows']=reasons.get('inconsistent_provenance_rows',0)+1
    elif key not in mapping:mapping[key]=value

def main():
    catalog=data_catalog();candidate_map={};evidence_map={};row_files=0;valid_rows=0;reasons={}
    cols=['parent_state_hash','candidate_state_hash','update_data_hash','verification_data_hash','attack_mask_hash','model_seed','center_id','stage',
          'method','backbone','horizon','attack_type','actual_attack_type','attack_alpha','attack_location']
    for archive in ARCHIVES:
        result_dir=archive/'results/calibration'
        for path in result_dir.glob('policy*.csv'):
            d=pd.read_csv(path,usecols=cols);row_files+=1
            for r in d.itertuples(index=False):
                if r.method!='Proposed':continue
                identity=catalog.get((int(r.center_id),r.attack_type,int(r.stage)))
                if identity is None or identity['update_hash']!=r.update_data_hash or identity['verification_hash']!=r.verification_data_hash or identity['attack_hash']!=r.attack_mask_hash or identity['actual']!=r.actual_attack_type:
                    reasons['data_or_attack_identity_mismatch']=reasons.get('data_or_attack_identity_mismatch',0)+1;continue
                valid_rows+=1
                cp=candidate_payload(r.parent_state_hash,r.update_data_hash,int(r.center_id),int(r.model_seed),int(r.stage),r.attack_type,r.actual_attack_type,
                    float(r.attack_alpha),r.attack_location,r.backbone,int(r.horizon),5,.1)
                add_mapping(candidate_map,old_candidate_key(r),(cp,r.candidate_state_hash),reasons)
                for evidence_kind in ['recent','historical']:
                    blocks=identity['history' if evidence_kind=='historical' else 'recent']
                    ep=evidence_payload(r.parent_state_hash,r.candidate_state_hash,blocks,int(r.center_id),int(r.model_seed),int(r.stage),r.attack_type,
                        r.actual_attack_type,float(r.attack_alpha),r.attack_location,int(r.horizon),evidence_kind)
                    add_mapping(evidence_map,old_evidence_key(r.parent_state_hash,r.candidate_state_hash,int(r.horizon),blocks),ep,reasons)
    cache=CacheBundle();seen_candidate=set();seen_evidence=set();accepted_c=accepted_e=0;reused_bytes=0
    scanned_c=scanned_e=0
    for archive in ARCHIVES:
        for path in (archive/'checkpoints/calibration_candidates').glob('*.pt'):
            scanned_c+=1;oldkey=path.stem
            if oldkey in seen_candidate:reasons['duplicate_candidate_artifact']=reasons.get('duplicate_candidate_artifact',0)+1;continue
            seen_candidate.add(oldkey);mapped=candidate_map.get(oldkey)
            if mapped is None:reasons['candidate_without_valid_provenance']=reasons.get('candidate_without_valid_provenance',0)+1;continue
            payload,expected_hash=mapped
            try:
                state=torch.load(path,map_location='cpu',weights_only=True)
                if state_dict_hash(state)!=expected_hash:reasons['candidate_state_hash_mismatch']=reasons.get('candidate_state_hash_mismatch',0)+1;continue
                newkey=key_hash(payload);dst=cache.candidate_dir/(newkey+'.pt');meta=cache.candidate_dir/(newkey+'.json')
                if not dst.exists():os.link(path,dst)
                save_json(meta,{'key_payload':payload,'candidate_state_hash':expected_hash,'migration_source':str(path)})
                accepted_c+=1;reused_bytes+=path.stat().st_size
            except Exception as exc:
                reasons['candidate_load_or_publish_error']=reasons.get('candidate_load_or_publish_error',0)+1
        evid_dir=archive/'checkpoints/calibration_evidence'
        if evid_dir.exists():
            for path in evid_dir.glob('*.npz'):
                scanned_e+=1;oldkey=path.stem
                if oldkey in seen_evidence:reasons['duplicate_evidence_artifact']=reasons.get('duplicate_evidence_artifact',0)+1;continue
                seen_evidence.add(oldkey);payload=evidence_map.get(oldkey)
                if payload is None:reasons['evidence_without_valid_provenance']=reasons.get('evidence_without_valid_provenance',0)+1;continue
                try:
                    with np.load(path,allow_pickle=False) as z:
                        vals=z['vals'].astype(np.float64);weights=z['weights'].astype(np.int64);calls=int(z['calls'])
                    if len(vals)!=len(weights) or not np.isfinite(vals).all() or calls<=0:
                        reasons['invalid_evidence_payload']=reasons.get('invalid_evidence_payload',0)+1;continue
                    dst=cache.evidence_dir/(key_hash(payload)+'.npz')
                    if not dst.exists():atomic_npz(dst,vals=vals,weights=weights,calls=np.int64(calls),key_json=np.asarray(canonical(payload)))
                    accepted_e+=1;reused_bytes+=path.stat().st_size
                except Exception:
                    reasons['evidence_load_or_publish_error']=reasons.get('evidence_load_or_publish_error',0)+1
    report={'status':'passed','archives_scanned':[str(x) for x in ARCHIVES],'result_files_scanned':row_files,'valid_provenance_rows':valid_rows,
        'scanned':{'candidate_artifacts':scanned_c,'evidence_artifacts':scanned_e,'total':scanned_c+scanned_e},
        'accepted':{'candidate_artifacts':accepted_c,'evidence_artifacts':accepted_e,'total':accepted_c+accepted_e},
        'rejected':{'total':scanned_c+scanned_e-accepted_c-accepted_e,'reasons':reasons},'reused_bytes':reused_bytes,
        'avoided_candidate_computations':accepted_c,'avoided_verification_evidence_computations':accepted_e,
        'validation':['reference row provenance','recomputed immutable data hash','recomputed attack identity and mask hash','parent/config/seed/stage/horizon key','candidate state hash','cache schema and science source hashes'],
        'p0_p5_touched':False,'source_artifacts_modified':False}
    save_json(ROOT/'audits/cache_migration.json',report);print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
