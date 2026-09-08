"""Exact joint-policy executor for Proposed calibration policies.

This module preserves the reference lifecycle and groups policies only when every
dynamic input to future candidate/evidence computation is identical.
"""
from collections import OrderedDict
from pathlib import Path
import copy,hashlib,json,os,time
import numpy as np
import torch
from core.protocol import ROOT,Timeline,windows,attack,digest,save_json
from core.models import DEVICE,robust_candidate,tensors,errors,state_hash,sync
from core.engine import evidence_blocks,initial_model

CACHE_SCHEMA='joint-policy-dag-v1'
SCIENCE_FILES=['core/engine.py','core/models.py','core/protocol.py']

def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
SCIENCE_VERSION={p:file_hash(ROOT/p) for p in SCIENCE_FILES}

def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'))
def key_hash(obj):return hashlib.sha256(canonical(obj).encode()).hexdigest()
def history_hash(blocks):return key_hash([b.hash for b in blocks])

class LRU:
    def __init__(self,capacity=512):self.capacity=capacity;self.data=OrderedDict()
    def get(self,key):
        if key not in self.data:return None
        value=self.data.pop(key);self.data[key]=value;return value
    def put(self,key,value):
        if key in self.data:self.data.pop(key)
        self.data[key]=value
        while len(self.data)>self.capacity:self.data.popitem(last=False)

class CacheBundle:
    def __init__(self,root=None,l1_capacity=2048):
        self.root=Path(root or ROOT/'checkpoints');self.candidate_l1=LRU(l1_capacity);self.evidence_l1=LRU(l1_capacity*2)
        self.candidate_dir=self.root/'joint_dag_candidates';self.evidence_dir=self.root/'joint_dag_evidence'
        self.candidate_dir.mkdir(parents=True,exist_ok=True);self.evidence_dir.mkdir(parents=True,exist_ok=True)

def atomic_torch(obj,path):
    tmp=path.with_name(f'{path.name}.{os.getpid()}.tmp');torch.save(obj,tmp)
    try:
        if not path.exists():os.replace(tmp,path)
    except PermissionError:
        if not path.exists():raise
    finally:tmp.unlink(missing_ok=True)

def atomic_npz(path,**arrays):
    tmp=path.with_name(f'{path.name}.{os.getpid()}.tmp')
    with tmp.open('wb') as f:np.savez_compressed(f,**arrays)
    try:
        if not path.exists():os.replace(tmp,path)
    except PermissionError:
        if not path.exists():raise
    finally:tmp.unlink(missing_ok=True)

def candidate_payload(parent_hash,update_hash,center,seed,stage,kind,actual,alpha,location,backbone,H,B,beta):
    return {'schema':CACHE_SCHEMA,'science_version':SCIENCE_VERSION,'artifact':'candidate','parent_state_hash':parent_hash,
        'update_data_hash':update_hash,'center':center,'seed':seed,'stage':stage,'condition':kind,'actual_attack_type':actual,
        'attack_alpha':alpha,'attack_location':location,'backbone':backbone,'horizon':H,'B':B,'beta':beta,
        'candidate_rng_seed':seed+center+stage*100,'method':'Proposed'}

def evidence_payload(parent_hash,candidate_hash,blocks,center,seed,stage,kind,actual,alpha,location,H,evidence_kind):
    return {'schema':CACHE_SCHEMA,'science_version':SCIENCE_VERSION,'artifact':'verification_evidence','parent_state_hash':parent_hash,
        'candidate_state_hash':candidate_hash,'block_hashes':[b.hash for b in blocks],'center':center,'seed':seed,'stage':stage,
        'condition':kind,'actual_attack_type':actual,'attack_alpha':alpha,'attack_location':location,'horizon':H,'evidence_kind':evidence_kind}

def load_candidate(parent,payload,cache,use_l1,use_l2,metrics):
    key=key_hash(payload);state=cache.candidate_l1.get(key) if use_l1 else None
    if state is not None:
        metrics['candidate_l1_hits']+=1;model=copy.deepcopy(parent);model.load_state_dict(state);return model,key
    path=cache.candidate_dir/(key+'.pt');meta=cache.candidate_dir/(key+'.json')
    if use_l2 and path.exists() and meta.exists():
        obj=json.loads(meta.read_text());assert obj['key_payload']==payload
        model=copy.deepcopy(parent);model.load_state_dict(torch.load(path,map_location=DEVICE,weights_only=True));assert state_hash(model)==obj['candidate_state_hash']
        metrics['candidate_l2_hits']+=1
        if use_l1:cache.candidate_l1.put(key,{k:v.detach().clone() for k,v in model.state_dict().items()})
        return model,key
    return None,key

def store_candidate(model,key,payload,cache,use_l1,use_l2,metrics):
    state={k:v.detach().clone() for k,v in model.state_dict().items()};candidate_hash=state_hash(model)
    if use_l1:cache.candidate_l1.put(key,state)
    if use_l2:
        path=cache.candidate_dir/(key+'.pt');atomic_torch(state,path)
        save_json(cache.candidate_dir/(key+'.json'),{'key_payload':payload,'candidate_state_hash':candidate_hash})
        metrics['candidate_l2_writes']+=1

def raw_evidence(candidate,parent,blocks,H,payload,cache,use_l1,use_l2,metrics):
    key=key_hash(payload);item=cache.evidence_l1.get(key) if use_l1 else None
    if item is not None:metrics['evidence_l1_hits']+=1
    else:
        path=cache.evidence_dir/(key+'.npz')
        if use_l2 and path.exists():
            with np.load(path,allow_pickle=False) as z:
                assert str(z['key_json'])==canonical(payload)
                item=(z['vals'].astype(np.float64),z['weights'].astype(np.int64),int(z['calls']))
            metrics['evidence_l2_hits']+=1
        else:
            vals=[];weights=[];calls=0
            for block in blocks:
                xy=tensors(windows(block,H=H));a,_=errors(candidate,xy);b,_=errors(parent,xy)
                vals.append(float((a-b).mean()));weights.append(len(a));calls+=2*((len(a)+255)//256)
            item=(np.asarray(vals,dtype=np.float64),np.asarray(weights,dtype=np.int64),calls)
            metrics['evidence_computations']+=1;metrics['verification_forward_calls_physical']+=calls
            if use_l2:
                atomic_npz(path,vals=item[0],weights=item[1],calls=np.int64(calls),key_json=np.asarray(canonical(payload)))
                metrics['evidence_l2_writes']+=1
        if use_l1:cache.evidence_l1.put(key,item)
    vals,weights,calls=item
    if not len(vals):return float('nan'),float('nan'),calls,key
    median=float(np.median(vals));mad=float(np.median(np.abs(vals-median)))
    return median,mad,calls,key

def causal_payload(parent_hash,hist_hash,center,seed,stage,kind,actual,alpha,location,H,update_hash,verification_hash,attack_hash,B,beta):
    return {'schema':CACHE_SCHEMA,'science_version':SCIENCE_VERSION,'parent_state_hash':parent_hash,'historical_buffer_hash':hist_hash,
        'stage':stage,'center':center,'condition':kind,'actual_attack_type':actual,'attack_alpha':alpha,'attack_location':location,
        'seed':seed,'horizon':H,'update_data_hash':update_hash,'verification_data_hash':verification_hash,'attack_mask_hash':attack_hash,
        'candidate_rng_seed':seed+center+stage*100,'B':B,'beta':beta,'rolling_policy_state':None}

def run_joint(center,seed,policies,kind='clean',alpha=0.,location='both',stages=24,backbone='GRU',H=1,
              B=5,beta=.1,run_id='joint_dag',cache=None,use_l1=True,use_l2=True):
    """Return (policy_rows, metrics, stage_stats) for Proposed policies."""
    cache=cache or CacheBundle();timeline=Timeline(center);initial=initial_model(center,seed,backbone,H);initial_hash=state_hash(initial)
    history=evidence_blocks(timeline.initial_history(),H);groups={initial_hash:{'model':initial,'policies':list(policies)}}
    rows={int(p['policy']):[] for p in policies};metrics={k:0 for k in ['candidate_l1_hits','candidate_l2_hits','candidate_trainings','candidate_l2_writes',
        'evidence_l1_hits','evidence_l2_hits','evidence_computations','evidence_l2_writes','verification_forward_calls_physical','service_forward_calls_physical']}
    stage_stats=[];start_all=time.perf_counter()
    for stage in range(1,stages+1):
        raw_u,raw_v=timeline.maintenance(stage);u,um,us,actual=attack(raw_u,center,stage,kind,alpha,location);v,vm,vs,_=attack(raw_v,center,stage,kind,alpha,location)
        recent=evidence_blocks(v,H);hist_hash=history_hash(history);mask_hash=digest(um,vm,us,vs);xy=tensors(windows(u,H=H))
        decisions=[];computed=[];stage_start=time.perf_counter()
        for parent_hash,group in list(groups.items()):
            parent=group['model'];before=state_hash(parent);assert before==parent_hash
            causal=causal_payload(before,hist_hash,center,seed,stage,kind,actual,alpha,location,H,u.hash,v.hash,mask_hash,B,beta)
            cand_payload=candidate_payload(before,u.hash,center,seed,stage,kind,actual,alpha,location,backbone,H,B,beta)
            sync();cand_start=time.perf_counter();candidate,cand_key=load_candidate(parent,cand_payload,cache,use_l1,use_l2,metrics)
            if candidate is None:
                candidate=robust_candidate(parent,xy,B,beta,seed+center+stage*100,False,H);metrics['candidate_trainings']+=1
                store_candidate(candidate,cand_key,cand_payload,cache,use_l1,use_l2,metrics)
            sync();candidate_time=time.perf_counter()-cand_start;assert state_hash(parent)==before;candidate_hash=state_hash(candidate)
            sync();ver_start=time.perf_counter()
            rp=evidence_payload(before,candidate_hash,recent,center,seed,stage,kind,actual,alpha,location,H,'recent')
            hp=evidence_payload(before,candidate_hash,history,center,seed,stage,kind,actual,alpha,location,H,'historical')
            mr,rr,nr,_=raw_evidence(candidate,parent,recent,H,rp,cache,use_l1,use_l2,metrics)
            mh,rh,nh,_=raw_evidence(candidate,parent,history,H,hp,cache,use_l1,use_l2,metrics)
            sync();verification_time=time.perf_counter()-ver_start
            for policy in group['policies']:
                ur=mr+policy['kappa_rec']*rr;uh=mh+policy['kappa_hist']*rh
                commit=ur<=-policy['delta_imp'] and uh<=policy['delta_ret']
                decisions.append((policy,parent,candidate,before,candidate_hash,commit,ur,uh,mr,rr,mh,rh,nr+nh,candidate_time,verification_time,key_hash(causal)))
            computed.append((parent,candidate,before,candidate_hash))
        # All policy decisions exist before the service capability is opened.
        timeline.record_decision(stage,any(x[5] for x in decisions));service=timeline.service(stage);service_hash=service.hash;sxy=tensors(windows(service,H=H))
        service_cache={}
        for parent,candidate,before,candidate_hash in computed:
            if before not in service_cache:
                cur,cmae=errors(parent,sxy);metrics['service_forward_calls_physical']+=(len(cur)+255)//256;service_cache[before]=(cur,cmae)
            if candidate_hash not in service_cache:
                can,camae=errors(candidate,sxy);metrics['service_forward_calls_physical']+=(len(can)+255)//256;service_cache[candidate_hash]=(can,camae)
        next_history=(history+recent)[-24:];next_hist_hash=history_hash(next_history);next_groups={}
        for policy,parent,candidate,before,candidate_hash,commit,ur,uh,mr,rr,mh,rh,vf,candidate_time,verification_time,causal_hash in decisions:
            deployed_hash=candidate_hash if commit else before;deployed=candidate if commit else parent
            cur,cmae=service_cache[before];can,camae=service_cache[candidate_hash];mse,mae=(can,camae) if commit else (cur,cmae);delta=float(can.mean()-cur.mean())
            pid=int(policy['policy']);rows[pid].append(dict(run_id=run_id,policy=pid,center_id=center,center_type=timeline.meta['center_type'],model_seed=seed,
                horizon=H,backbone=backbone,stage=stage,drift_regime=timeline.meta['drift_regime'],attack_type=kind,actual_attack_type=actual,
                attack_alpha=alpha,attack_location=location,method='Proposed',parent_state_hash=before,candidate_state_hash=candidate_hash,
                deployed_state_hash=deployed_hash,initial_state_hash=initial_hash,causal_state_fingerprint=causal_hash,historical_buffer_hash=hist_hash,
                next_historical_buffer_hash=next_hist_hash,commit=int(commit),current_service_mse=float(cur.mean()),candidate_service_mse=float(can.mean()),
                deployed_service_mse=float(mse.mean()),deployed_service_mae=float(mae.mean()),delta_srv=delta,harmful_commit=int(commit and delta>0),
                downside=float(commit)*max(0,delta),beneficial_candidate=int(delta<0),U_rec=ur,U_hist=uh,median_rec=mr,mad_rec=rr,
                median_hist=mh,mad_hist=rh,candidate_update_time_s=candidate_time,verification_time_s=verification_time,
                maintenance_time_s=time.perf_counter()-stage_start,peak_gpu_memory_bytes=torch.cuda.max_memory_allocated() if DEVICE=='cuda' else 0,
                persistent_buffer_bytes=sum(x.x.nbytes+x.y.nbytes+x.ts.nbytes for x in next_history),number_of_forward_passes=50+vf,
                number_of_backward_updates=50,number_of_fisher_backward_passes=0,update_start_ts=int(u.ts[0]),update_end_ts=int(u.ts[-1]),
                verification_start_ts=int(v.ts[0]),verification_end_ts=int(v.ts[-1]),decision_ts=int(v.ts[-1]),service_start_ts=int(service.ts[0]),
                service_end_ts=int(service.ts[-1]),attack_mask_hash=mask_hash,update_data_hash=u.hash,verification_data_hash=v.hash,service_data_hash=service_hash))
            if deployed_hash not in next_groups:next_groups[deployed_hash]={'model':deployed,'policies':[]}
            else:assert state_hash(next_groups[deployed_hash]['model'])==deployed_hash
            next_groups[deployed_hash]['policies'].append(policy)
        stage_stats.append({'stage':stage,'naive_policy_count':len(policies),'unique_deployed_model_states':len(next_groups),
            'unique_complete_causal_states':len(groups),'unique_candidate_computations':len(groups),'unique_verification_evidence_states':len(groups),
            'historical_buffer_hash':hist_hash,'next_historical_buffer_hash':next_hist_hash})
        groups=next_groups;history=next_history
    metrics['wall_s']=time.perf_counter()-start_all;metrics['policy_trajectories']=len(policies);metrics['trajectories_per_hour']=len(policies)*3600/metrics['wall_s']
    return rows,metrics,stage_stats
