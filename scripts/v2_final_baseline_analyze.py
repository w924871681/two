"""Final integrity, pairing, leakage, and scientific baseline benchmark analysis."""
from __future__ import annotations
import datetime as dt
import hashlib,json,math,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from core.protocol import ROOT
from scripts.v2_runner import atomic_json

PROPOSED="Proposed";BASELINES=["Always-FT","ER","EWC","Huber-FT","ValidationCommit","Frozen"];METHODS=[PROPOSED]+BASELINES
SCENARIOS=["stationary","gradual","abrupt","recurring","mixed_a010_both","persistent_a010_verification_only","replay_a010_verification_only"]
UTILITY=SCENARIOS[:5];DRIFT=["gradual","abrupt","recurring"];BOOT=4000;SEED=2904
METRICS=["lifecycle_mse","lifecycle_mae","harmful_commit_rate","average_downside","conditional_harmful_rate","beneficial_commit_recall","commit_rate","maximum_retain_streak","mean_maintenance_time_s"]
def sha(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def clean(v):
 if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
 if isinstance(v,list):return [clean(x) for x in v]
 if isinstance(v,(np.bool_,bool)):return bool(v)
 if isinstance(v,(np.integer,)):return int(v)
 if isinstance(v,(float,np.floating)):return None if not np.isfinite(v) else float(v)
 return v
def longest(s):
 best=cur=0
 for x in s.astype(int):cur=0 if x else cur+1;best=max(best,cur)
 return best
def ci(frame,col):
 a=frame.groupby("center_id")[col].mean().dropna().to_numpy(float)
 if not len(a):return math.nan,math.nan,math.nan
 rng=np.random.default_rng(SEED);sample=a[rng.integers(len(a),size=(BOOT,len(a)))].mean(1);return float(a.mean()),*map(float,np.quantile(sample,[.025,.975]))
def stratified_diff(frame,baseline,metric,scenarios):
 arrays=[]
 for scenario in scenarios:
  a=frame[(frame.method_id==PROPOSED)&(frame.analysis_scenario==scenario)];b=frame[(frame.method_id==baseline)&(frame.analysis_scenario==scenario)]
  m=a.merge(b,on=["analysis_scenario","center_id","model_seed"],suffixes=("_p","_b"),validate="one_to_one");m["d"]=m[metric+"_p"]-m[metric+"_b"];arrays.append(m.groupby("center_id").d.mean().dropna().to_numpy(float))
  if any(len(x)==0 for x in arrays):return math.nan,math.nan,math.nan
  point=float(np.mean([x.mean() for x in arrays]));rng=np.random.default_rng(SEED);sample=np.zeros(BOOT)
 for x in arrays:sample+=x[rng.integers(len(x),size=(BOOT,len(x)))].mean(1)
 sample/=len(arrays);lo,hi=np.quantile(sample,[.025,.975]);return point,float(lo),float(hi)
def trajectory(raw):
 rows=[];keys=["method_id","analysis_scenario","scenario_id","center_id","model_seed","drift_regime"]
 for vals,g in raw.sort_values("stage").groupby(keys):
  d=dict(zip(keys,vals));commits=int(g.commit.sum());beneficial=int(g.beneficial_candidate.sum())
  rows.append({**d,"lifecycle_mse":g.deployed_service_mse.mean(),"lifecycle_mae":g.deployed_service_mae.mean(),"harmful_commit_rate":g.harmful_commit.mean(),"average_downside":g.downside.mean(),"conditional_harmful_rate":g.harmful_commit.sum()/commits if commits else math.nan,"beneficial_commit_recall":(g.commit*g.beneficial_candidate).sum()/beneficial if beneficial else math.nan,"commit_rate":g.commit.mean(),"maximum_retain_streak":longest(g.commit),"mean_maintenance_time_s":g.maintenance_time_s.mean(),"peak_gpu_memory_bytes":g.peak_gpu_memory_bytes.max(),"persistent_buffer_bytes":g.persistent_buffer_bytes.max(),"source_file":g.source_file.iloc[0],"source_file_sha256":g.source_file_sha256.iloc[0]})
 return pd.DataFrame(rows)
def main():
 ad=ROOT/"audits_v2_final_baselines";out=ROOT/"results_v2_final_baselines";mp=ad/"final_benchmark_manifest.json";manifest=json.loads(mp.read_text(encoding="utf-8"));complete=json.loads((ad/"baseline_execution_complete.json").read_text(encoding="utf-8"))
 if complete["status"]!="PASS" or complete["completed"]!=2160:raise RuntimeError("baseline execution incomplete")
 expected={j["filename"]:j for j in manifest["jobs"]};folder=out/"trajectories";paths={p.name:p for p in folder.glob("*.csv")};missing=sorted(set(expected)-set(paths));unexpected=sorted(set(paths)-set(expected));invalid=[];frames=[]
 required={"method","center_id","model_seed","stage","commit","parent_state_hash","candidate_state_hash","initial_state_hash","update_end_ts","verification_start_ts","verification_end_ts","decision_ts","service_start_ts","update_data_hash","verification_data_hash","service_data_hash","attack_mask_hash","deployed_service_mse","deployed_service_mae","harmful_commit","downside","beneficial_candidate","maintenance_time_s"}
 for name in sorted(set(expected)&set(paths)):
  j=expected[name]
  try:
   f=pd.read_csv(paths[name]);ok=required<=set(f) and len(f)==24 and f.stage.tolist()==list(range(1,25)) and f.method.nunique()==1 and f.method.iloc[0]==j["method"] and f.center_id.nunique()==1 and int(f.center_id.iloc[0])==j["center_id"] and f.model_seed.nunique()==1 and int(f.model_seed.iloc[0])==j["model_seed"] and f.scenario_id.nunique()==1 and f.scenario_id.iloc[0]==j["stream"]["scenario_id"]
   if not ok:invalid.append(name)
   else:f["method_id"]=f.method;f["source_file"]=name;f["source_file_sha256"]=sha(paths[name]);frames.append(f)
  except Exception as e:invalid.append(f"{name}: {type(e).__name__}: {e}")
 base_raw=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame();dup=int(base_raw.duplicated(["method_id","center_id","model_seed","scenario_id","stage"]).sum()) if len(base_raw) else 0
 ordering=int((~((base_raw.update_end_ts<base_raw.verification_start_ts)&(base_raw.verification_end_ts==base_raw.decision_ts)&(base_raw.decision_ts<base_raw.service_start_ts))).sum()) if len(base_raw) else 0;chain=0
 for _,g in base_raw.sort_values("stage").groupby(["method_id","center_id","model_seed","scenario_id"]):
  rows=list(g.itertuples())
  for a,b in zip(rows,rows[1:]):chain+=int(b.parent_state_hash!=(a.candidate_state_hash if int(a.commit) else a.parent_state_hash))
 integrity={"schema":"ravm-dt-v2-final-baseline-integrity-v1","status":"PASS","expected":2160,"valid":len(frames),"missing":len(missing),"duplicate":dup,"unexpected":len(unexpected),"partial_invalid":len(invalid),"stage_rows":len(base_raw),"expected_stage_rows":51840,"decision_ordering_errors":ordering,"state_chain_errors":chain,"missing_files":missing,"unexpected_files":unexpected,"invalid_files":invalid}
 integrity["status"]="PASS" if len(frames)==2160 and len(base_raw)==51840 and not missing and not unexpected and not invalid and not dup and not ordering and not chain else "FAIL";atomic_json(ad/"baseline_execution_integrity_audit.json",integrity)
 if integrity["status"]!="PASS":atomic_json(out/"execution_status.json",{"state":"INVALID_FINAL_BASELINE_BENCHMARK","integrity":integrity});raise RuntimeError("integrity failed")
 pframes=[]
 for p in sorted((ROOT/"results_v2_final/trajectories").glob("Final_V2_SP_ShortDual__*.csv")):
  f=pd.read_csv(p);f["method_id"]=PROPOSED;f["source_file"]=p.name;f["source_file_sha256"]=sha(p);pframes.append(f)
 proposed_raw=pd.concat(pframes,ignore_index=True);raw=pd.concat([proposed_raw,base_raw],ignore_index=True)
 keys=["center_id","model_seed","scenario_id","stage"];ref=proposed_raw[keys+["update_data_hash","verification_data_hash","service_data_hash","attack_mask_hash","initial_state_hash"]]
 paired=base_raw.merge(ref,on=keys,suffixes=("_baseline","_proposed"),validate="many_to_one");mismatch={c:int((paired[c+"_baseline"]!=paired[c+"_proposed"]).sum()) for c in ["update_data_hash","verification_data_hash","service_data_hash","attack_mask_hash","initial_state_hash"]}
 pairing={"schema":"ravm-dt-v2-final-baseline-pairing-v1","status":"PASS" if not any(mismatch.values()) and len(paired)==51840 else "INVALID_PAIRING","paired_stage_rows":len(paired),"expected":51840,"mismatch_rows":mismatch,"replay_mapping_check":"attack_mask_hash includes attack source timestamps and is exact","persistent_and_mixed_realization_check":"attack_mask_hash exact"};atomic_json(ad/"baseline_pairing_hash_audit.json",pairing)
 leakage={"schema":"ravm-dt-v2-final-baseline-leakage-v1","status":"PASS" if not ordering and not chain and pairing["status"]=="PASS" else "FAIL","decision_precedes_service":ordering==0,"state_chain_valid":chain==0,"service_data_post_decision_only":"enforced by frozen core.engine Timeline capability","scientific_engine_sha256":manifest["scientific_engine_sha256"]};atomic_json(ad/"baseline_leakage_audit.json",leakage)
 if pairing["status"]!="PASS" or leakage["status"]!="PASS":atomic_json(out/"execution_status.json",{"state":"INVALID_FINAL_BASELINE_BENCHMARK","pairing":pairing["status"],"leakage":leakage["status"]});raise RuntimeError("pairing/leakage failed")
 traj=trajectory(raw)
 center=traj.groupby(["method_id","analysis_scenario","center_id"],as_index=False)[[x for x in METRICS if x in traj]+["peak_gpu_memory_bytes","persistent_buffer_bytes"]].mean()
 srows=[]
 for (method,scenario),g in traj.groupby(["method_id","analysis_scenario"]):
  r={"method":method,"scenario":scenario,"centers":g.center_id.nunique(),"seeds":g.model_seed.nunique()}
  for metric in METRICS:
   point,lo,hi=ci(g,metric);r.update({metric:point,metric+"_ci_low":lo,metric+"_ci_high":hi})
  r["peak_gpu_memory_bytes"]=g.groupby("center_id").peak_gpu_memory_bytes.mean().mean();r["persistent_buffer_bytes"]=g.groupby("center_id").persistent_buffer_bytes.mean().mean();srows.append(r)
 summary=pd.DataFrame(srows)
 prows=[]
 for baseline in BASELINES:
  for scenario in SCENARIOS:
   a=traj[(traj.method_id==PROPOSED)&(traj.analysis_scenario==scenario)];b=traj[(traj.method_id==baseline)&(traj.analysis_scenario==scenario)];m=a.merge(b,on=["analysis_scenario","center_id","model_seed"],suffixes=("_p","_b"),validate="one_to_one")
   for metric in METRICS:
    m["difference"]=m[metric+"_p"]-m[metric+"_b"];point,lo,hi=ci(m,"difference");pv=a.groupby("center_id")[metric].mean().mean();bv=b.groupby("center_id")[metric].mean().mean();prows.append({"baseline":baseline,"scope":scenario,"metric":metric,"proposed_estimate":pv,"baseline_estimate":bv,"difference":point,"ci_low":lo,"ci_high":hi,"relative_percent":(pv/bv-1)*100 if np.isfinite(bv) and bv!=0 else math.nan,"bootstrap_replicates":BOOT,"bootstrap_seed":SEED,"unit":"center"})
  for scope,scens in [("balanced_all_7",SCENARIOS),("confirmatory_utility_balanced_5",UTILITY)]:
   for metric in METRICS:
    point,lo,hi=stratified_diff(traj,baseline,metric,scens);pv=summary[(summary.method==PROPOSED)&summary.scenario.isin(scens)].groupby("scenario")[metric].mean().mean();bv=summary[(summary.method==baseline)&summary.scenario.isin(scens)].groupby("scenario")[metric].mean().mean();prows.append({"baseline":baseline,"scope":scope,"metric":metric,"proposed_estimate":pv,"baseline_estimate":bv,"difference":point,"ci_low":lo,"ci_high":hi,"relative_percent":(pv/bv-1)*100 if np.isfinite(bv) and bv!=0 else math.nan,"bootstrap_replicates":BOOT,"bootstrap_seed":SEED,"unit":"center"})
 pairs=pd.DataFrame(prows)
 clean=raw[raw.scenario_id=="clean"];wide=clean.pivot(index=["center_id","model_seed","analysis_scenario","stage"],columns="method_id",values="deployed_service_mse").reset_index();wide["reference"]=wide[["Frozen","Always-FT"]].min(axis=1);recovery=[]
 for (c,seed,scenario),g in wide.groupby(["center_id","model_seed","analysis_scenario"]):
  if scenario not in DRIFT:continue
  onset=7 if scenario=="recurring" else 9;g=g[g.stage>=onset].sort_values("stage");refv=g.reference.to_numpy(float)
  for method in METHODS:
   v=g[method].to_numpy(float);within=v<=1.05*refv;hits=np.flatnonzero(within[:-1]&within[1:]);recovery.append({"method_id":method,"analysis_scenario":scenario,"center_id":c,"model_seed":seed,"post_drift_excess_loss_area":float(np.maximum(v-refv,0).sum()),"recovery_time":float(hits[0]+1) if len(hits) else math.nan,"censored_recovery":int(not len(hits))})
 recovery=pd.DataFrame(recovery)
 for baseline in BASELINES:
  for scenario in DRIFT:
   a=recovery[(recovery.method_id==PROPOSED)&(recovery.analysis_scenario==scenario)];b=recovery[(recovery.method_id==baseline)&(recovery.analysis_scenario==scenario)];m=a.merge(b,on=["analysis_scenario","center_id","model_seed"],suffixes=("_p","_b"))
   for metric in ["post_drift_excess_loss_area","censored_recovery"]:
    m["difference"]=m[metric+"_p"]-m[metric+"_b"];point,lo,hi=ci(m,"difference");pairs.loc[len(pairs)]={"baseline":baseline,"scope":scenario,"metric":metric,"proposed_estimate":a[metric].mean(),"baseline_estimate":b[metric].mean(),"difference":point,"ci_low":lo,"ci_high":hi,"relative_percent":math.nan,"bootstrap_replicates":BOOT,"bootstrap_seed":SEED,"unit":"center"}
   recovered=m.dropna(subset=["recovery_time_p","recovery_time_b"]).copy();recovered["difference"]=recovered.recovery_time_p-recovered.recovery_time_b;point,lo,hi=ci(recovered,"difference")
   pairs.loc[len(pairs)]={"baseline":baseline,"scope":scenario,"metric":"recovery_time_uncensored","proposed_estimate":a.recovery_time.mean(),"baseline_estimate":b.recovery_time.mean(),"difference":point,"ci_low":lo,"ci_high":hi,"relative_percent":math.nan,"bootstrap_replicates":BOOT,"bootstrap_seed":SEED,"unit":"center"}
 main=[]
 for method in METHODS:
  r={"method":method}
  for metric in METRICS:
   r[metric+"_balanced_all_7"]=summary[(summary.method==method)&summary.scenario.isin(SCENARIOS)][metric].mean();r[metric+"_utility_balanced_5"]=summary[(summary.method==method)&summary.scenario.isin(UTILITY)][metric].mean()
  r["peak_gpu_memory_bytes"]=summary[summary.method==method].peak_gpu_memory_bytes.mean();r["persistent_buffer_bytes"]=summary[summary.method==method].persistent_buffer_bytes.mean();main.append(r)
 main=pd.DataFrame(main)
 hashes={}
 for name,frame in [("baseline_trajectory_index.csv",traj[traj.method_id!=PROPOSED]),("baseline_center_level_summary.csv",center),("baseline_scenario_summary.csv",summary),("proposed_vs_baseline_paired.csv",pairs),("final_main_table.csv",main)]:
  path=out/name;frame.to_csv(path,index=False,na_rep="NA");hashes[name]=sha(path);path.with_suffix(path.suffix+".sha256").write_text(hashes[name]+"\n",encoding="ascii")
 def fmt(x):return "NA" if pd.isna(x) else f"{float(x):.8g}"
 mainlines=[]
 for r in main.itertuples():mainlines.append(f"| {r.method} | {fmt(r.lifecycle_mse_balanced_all_7)} | {fmt(r.lifecycle_mae_balanced_all_7)} | {fmt(r.harmful_commit_rate_balanced_all_7)} | {fmt(r.average_downside_balanced_all_7)} | {fmt(r.conditional_harmful_rate_balanced_all_7)} | {fmt(r.beneficial_commit_recall_balanced_all_7)} | {fmt(r.commit_rate_balanced_all_7)} | {fmt(r.mean_maintenance_time_s_balanced_all_7)} | {fmt(r.peak_gpu_memory_bytes)} | {fmt(r.persistent_buffer_bytes)} |")
 scenelines=[]
 for scenario in SCENARIOS:
  for method in METHODS:
   r=summary[(summary.method==method)&(summary.scenario==scenario)].iloc[0];scenelines.append(f"| {scenario} | {method} | {fmt(r.lifecycle_mse)} [{fmt(r.lifecycle_mse_ci_low)}, {fmt(r.lifecycle_mse_ci_high)}] | {fmt(r.lifecycle_mae)} | {fmt(r.harmful_commit_rate)} | {fmt(r.average_downside)} | {fmt(r.conditional_harmful_rate)} | {fmt(r.beneficial_commit_recall)} | {fmt(r.commit_rate)} |")
 compare=[]
 for baseline in BASELINES:
  for metric in ["lifecycle_mse","lifecycle_mae","harmful_commit_rate","average_downside","beneficial_commit_recall","commit_rate"]:
   r=pairs[(pairs.baseline==baseline)&(pairs.scope=="balanced_all_7")&(pairs.metric==metric)].iloc[0];compare.append(f"| {baseline} | {metric} | {fmt(r.proposed_estimate)} | {fmt(r.baseline_estimate)} | {fmt(r.difference)} [{fmt(r.ci_low)}, {fmt(r.ci_high)}] | {fmt(r.relative_percent)}% |")
 report=f"""# V2 Final Baseline Benchmark Report

Generated: {now()}

## Material Passport and provenance

This post-freeze benchmark completion uses the already opened final test pool (centers 14000–14029) after Final V2 was permanently frozen and confirmed. It is not method development, calibration, tuning, or a new fresh-heldout selection. The benchmark adds exactly six frozen baselines: Always-FT, ER, EWC, Huber-FT, ValidationCommit, and Frozen. Final V2 was reused from its 360 hash-valid trajectories and was not rerun. V1 LegacyFull is excluded from the main table.

Frozen baseline engine SHA-256: `{manifest['scientific_engine_sha256']}`. Frozen manifest SHA-256: `{sha(mp)}`. Runtime: Python {complete['runtime']['python_version']}, PyTorch {complete['runtime']['torch_version']}, CUDA {complete['runtime']['torch_cuda_version']}, GPU {complete['runtime']['gpu_name']}. The clean regime assignment exactly reuses `REGIMES[(center_id-14000)%4]` from the Final V2 manifest.

## Integrity, pairing, and leakage

Execution integrity **{integrity['status']}**: expected/valid=2160/2160, missing={integrity['missing']}, duplicate={integrity['duplicate']}, unexpected={integrity['unexpected']}, partial-invalid={integrity['partial_invalid']}, stage rows={integrity['stage_rows']}. Pairing **{pairing['status']}** with mismatch rows `{json.dumps(mismatch)}`. Leakage **{leakage['status']}**; decision-order errors={ordering}, state-chain errors={chain}.

## Main overall table

Balanced values give equal weight to stationary, gradual, abrupt, recurring, mixed, persistent verification-only, and replay verification-only. Runtime is mean maintenance seconds per stage.

| Method | MSE | MAE | Harmful | Downside | Conditional harmful | Beneficial recall | Commit rate | Runtime/stage s | Peak GPU bytes | Buffer bytes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(mainlines)}

## Scenario results

No unfavorable scenario is omitted. Intervals shown for MSE are center-cluster bootstrap 95% CIs; the machine-readable scenario table contains CIs for every reported metric.

| Scenario | Method | Lifecycle MSE [95% CI] | MAE | Harmful | Downside | Conditional harmful | Beneficial recall | Commit rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(scenelines)}

## Proposed versus each baseline

All rows are Proposed−baseline on identical center, seed, and scenario realizations. CIs crossing zero are inconclusive and are not evidence of equivalence.

| Baseline | Metric | Proposed | Baseline | Difference [95% CI] | Relative difference |
|---|---|---:|---:|---:|---:|
{chr(10).join(compare)}

## Runtime, recovery, and trade-off interpretation

Runtime, peak GPU memory, and persistent-buffer costs are reported without hiding maintenance overhead. Recovery and post-drift excess-loss use the pre-execution frozen stagewise minimum of Frozen and Always-FT as the common reference. Detailed paired recovery rows are in `proposed_vs_baseline_paired.csv`.

The scientific interpretation is the observed safety–utility–plasticity trade-off rather than a claim that Proposed must minimize every metric. Always-FT may improve adaptation while accepting harmful transitions; Frozen may minimize transition harm while sacrificing adaptation; Huber-FT may help under corruption without explicit transition control; strong ValidationCommit results remain visible. Negative and inconclusive paired results are retained in full.

## Claim boundary and conclusion

Allowed wording: “On the common final test pool, the frozen Proposed method was compared with six representative baselines under identical center/seed/scenario realizations.” This report does not claim superiority over CLeaR, MER-Reg, every continual-learning method, universal robustness, or universal optimality. V1 remains separate method-evolution evidence.

The benchmark is complete and auditable. Scientific claims must follow the direction and confidence intervals in the tables; no baseline result may be used to modify Final V2.
"""
 rp=ROOT/"V2_FINAL_BASELINE_BENCHMARK_REPORT.md";rp.write_text(report,encoding="utf-8");rh=sha(rp);rp.with_suffix(rp.suffix+".sha256").write_text(rh+"\n",encoding="ascii")
 audit_hashes={p.name:sha(p) for p in ad.glob("*.json")};atomic_json(ad/"final_baseline_output_hash_manifest.json",{"status":"PASS","report_sha256":rh,"result_hashes":hashes,"audit_hashes":audit_hashes})
 atomic_json(out/"execution_status.json",{"state":"FINAL_BASELINE_BENCHMARK_COMPLETE","completed":2160,"expected":2160,"integrity":"PASS","pairing":"PASS","leakage":"PASS","report":str(rp),"report_sha256":rh,"warning":None,"updated_at":now()})
 print(json.dumps({"state":"FINAL_BASELINE_BENCHMARK_COMPLETE","report":str(rp)},indent=2))
if __name__=="__main__":main()
