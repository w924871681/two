"""One-shot integrity, leakage, and frozen scientific analysis for V2 final."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from core.protocol import ROOT
from scripts.v2_go_no_go import stratified_paired_ci
from scripts.v2_runner import atomic_json


V2 = "Final_V2_SP_ShortDual"
V1 = "V1_LegacyFull"
BOOTSTRAP = 4000
BOOTSTRAP_SEED = 2904
RHO = 0.05
EPSILON = 5.6036475532487204e-05
BENIGN = ["stationary", "gradual", "abrupt", "recurring"]
BALANCED = BENIGN + ["mixed_a010_both"]
SAFETY = ["mixed_a010_both", "persistent_a010_verification_only", "replay_a010_verification_only"]
METRICS = ["lifecycle_mse", "lifecycle_mae", "harmful_commit_rate", "average_downside",
           "conditional_harmful_rate", "beneficial_commit_recall", "commit_rate", "maximum_retain_streak"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def clean(value):
    if isinstance(value, dict): return {str(k): clean(v) for k,v in value.items()}
    if isinstance(value, list): return [clean(v) for v in value]
    if isinstance(value, (np.bool_, bool)): return bool(value)
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating, float)): return None if not np.isfinite(value) else float(value)
    return value


def longest_retain(values: pd.Series) -> int:
    best=current=0
    for commit in values.astype(int):
        current=0 if commit else current+1; best=max(best,current)
    return best


def ci_mean(frame: pd.DataFrame, column: str) -> tuple[float,float,float]:
    values=frame.groupby("center_id")[column].mean().dropna().to_numpy(float)
    if not len(values): return math.nan,math.nan,math.nan
    rng=np.random.default_rng(BOOTSTRAP_SEED)
    samples=values[rng.integers(len(values),size=(BOOTSTRAP,len(values)))].mean(axis=1)
    return float(values.mean()),*map(float,np.quantile(samples,[.025,.975]))


def read_and_integrity(manifest: dict) -> tuple[pd.DataFrame,dict]:
    folder=ROOT/"results_v2_final/trajectories"; expected={j["filename"]:j for j in manifest["jobs"]}
    paths=sorted(folder.glob("*.csv")); actual={p.name:p for p in paths}
    missing=sorted(set(expected)-set(actual)); unexpected=sorted(set(actual)-set(expected)); invalid=[]; frames=[]
    required={"method_id","center_id","model_seed","scenario_id","analysis_scenario","stage","commit","parent_state_hash",
              "candidate_state_hash","update_end_ts","verification_start_ts","verification_end_ts","decision_ts","service_start_ts",
              "update_data_hash","verification_data_hash","service_data_hash","attack_mask_hash","deployed_service_mse",
              "deployed_service_mae","harmful_commit","downside","beneficial_candidate"}
    for name in sorted(set(expected)&set(actual)):
        job=expected[name]
        try:
            f=pd.read_csv(actual[name]); ok=(required<=set(f.columns) and len(f)==24 and f.stage.is_unique and set(f.stage)==set(range(1,25))
                and f.method_id.nunique()==1 and f.method_id.iloc[0]==job["method_id"]
                and f.center_id.nunique()==1 and int(f.center_id.iloc[0])==job["center_id"]
                and f.model_seed.nunique()==1 and int(f.model_seed.iloc[0])==job["model_seed"]
                and f.scenario_id.nunique()==1 and f.scenario_id.iloc[0]==job["stream"]["scenario_id"]
                and f.analysis_scenario.nunique()==1 and f.analysis_scenario.iloc[0]==job["analysis_scenario"])
            if not ok: invalid.append(name)
            else: f["source_file"]=name; f["source_file_sha256"]=sha256(actual[name]); frames.append(f)
        except Exception as exc: invalid.append(f"{name}: {type(exc).__name__}: {exc}")
    data=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()
    dup=int(data.duplicated(["method_id","center_id","model_seed","scenario_id","stage"]).sum()) if len(data) else 0
    expected_keys={(j["method_id"],j["center_id"],j["model_seed"],j["stream"]["scenario_id"]) for j in manifest["jobs"]}
    actual_keys=set(zip(data.method_id,data.center_id.astype(int),data.model_seed.astype(int),data.scenario_id)) if len(data) else set()
    chain_errors=0
    for _,g in data.sort_values("stage").groupby(["method_id","center_id","model_seed","scenario_id"]):
        rows=list(g.itertuples())
        for previous,current in zip(rows,rows[1:]):
            expected_parent=previous.candidate_state_hash if int(previous.commit) else previous.parent_state_hash
            chain_errors += int(current.parent_state_hash != expected_parent)
    hash_group_cols=["center_id","scenario_id","stage"]
    hash_mismatches=0
    for _,g in data.groupby(hash_group_cols):
        for col in ["update_data_hash","verification_data_hash","service_data_hash","attack_mask_hash"]:
            hash_mismatches += int(g[col].nunique()!=1)
    ordering_errors=int((~((data.update_end_ts < data.verification_start_ts) & (data.verification_end_ts == data.decision_ts) & (data.decision_ts < data.service_start_ts))).sum()) if len(data) else 0
    audit={"schema":"ravm-dt-v2-final-execution-integrity-v1","status":"PASS","expected":720,"valid":len(frames),
        "missing":len(missing),"duplicate":dup,"unexpected":len(unexpected),"partial_invalid":len(invalid),"stage_rows":len(data),
        "expected_stage_rows":720*24,"invalid_state_chain_links":chain_errors,"data_attack_service_hash_mismatch_groups":hash_mismatches,
        "decision_ordering_errors":ordering_errors,"missing_files":missing,"unexpected_files":unexpected,"invalid_files":invalid}
    audit["status"]="PASS" if (len(frames)==720 and not missing and not unexpected and not invalid and not dup and len(actual_keys)==len(expected_keys)==720 and chain_errors==0 and hash_mismatches==0 and ordering_errors==0 and len(data)==720*24) else "FAIL"
    return data,audit


def trajectory_metrics(data: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    keys=["method_id","analysis_scenario","scenario_id","center_id","model_seed","drift_regime"]
    for vals,g in data.sort_values("stage").groupby(keys):
        ident=dict(zip(keys,vals)); commits=int(g.commit.sum()); beneficial=int(g.beneficial_candidate.sum())
        rows.append({**ident,"lifecycle_mse":float(g.deployed_service_mse.mean()),"lifecycle_mae":float(g.deployed_service_mae.mean()),
            "harmful_commit_rate":float(g.harmful_commit.mean()),"average_downside":float(g.downside.mean()),
            "conditional_harmful_rate":float(g.harmful_commit.sum()/commits) if commits else math.nan,
            "beneficial_commit_recall":float((g.commit*g.beneficial_candidate).sum()/beneficial) if beneficial else math.nan,
            "commit_rate":float(g.commit.mean()),"maximum_retain_streak":longest_retain(g.commit),
            "source_file":g.source_file.iloc[0],"source_file_sha256":g.source_file_sha256.iloc[0]})
    return pd.DataFrame(rows)


def scenario_summary(traj: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for (method,scenario),g in traj.groupby(["method_id","analysis_scenario"]):
        row={"method_id":method,"scenario":scenario,"centers":g.center_id.nunique(),"seeds":g.model_seed.nunique(),"trajectories":len(g)}
        for metric in METRICS:
            point,low,high=ci_mean(g,metric); row.update({metric:point,metric+"_ci_low":low,metric+"_ci_high":high})
        rows.append(row)
    return pd.DataFrame(rows)


def paired(traj: pd.DataFrame, metrics=METRICS) -> pd.DataFrame:
    rows=[]
    for scenario in sorted(traj.analysis_scenario.unique()):
        left=traj[(traj.method_id==V2)&(traj.analysis_scenario==scenario)]
        right=traj[(traj.method_id==V1)&(traj.analysis_scenario==scenario)]
        merged=left.merge(right,on=["analysis_scenario","center_id","model_seed"],suffixes=("_v2","_v1"),validate="one_to_one")
        for metric in metrics:
            merged["difference"]=merged[metric+"_v2"]-merged[metric+"_v1"]
            point,low,high=ci_mean(merged,"difference")
            v2=float(left.groupby("center_id")[metric].mean().mean()); v1=float(right.groupby("center_id")[metric].mean().mean())
            rows.append({"comparison":"Final V2 - V1 LegacyFull","scenario":scenario,"metric":metric,"v2_estimate":v2,"v1_estimate":v1,
                "difference":point,"ci_low":low,"ci_high":high,"relative_percent":(v2/v1-1)*100 if np.isfinite(v1) and v1!=0 else math.nan,
                "bootstrap_replicates":BOOTSTRAP,"bootstrap_seed":BOOTSTRAP_SEED,"unit":"center"})
    return pd.DataFrame(rows)


def recovery_metrics(data: pd.DataFrame) -> pd.DataFrame:
    clean=data[data.scenario_id=="clean"]
    pivot=clean.pivot(index=["center_id","model_seed","analysis_scenario","stage"],columns="method_id",values="deployed_service_mse").reset_index()
    rows=[]
    for (center,seed,scenario),g in pivot.groupby(["center_id","model_seed","analysis_scenario"]):
        if scenario=="stationary": continue
        onset=7 if scenario=="recurring" else 9; g=g[g.stage>=onset].sort_values("stage")
        base=g[V1].to_numpy(float); candidate=g[V2].to_numpy(float); within=candidate<=1.05*base
        hits=np.flatnonzero(within[:-1]&within[1:]); v2_time=float(hits[0]+1) if len(hits) else math.nan
        rows.extend([
            {"method_id":V2,"scenario":scenario,"center_id":center,"model_seed":seed,"post_drift_excess_loss_area":float(np.maximum(candidate-base,0).sum()),"recovery_time":v2_time,"censored_recovery":int(not len(hits))},
            {"method_id":V1,"scenario":scenario,"center_id":center,"model_seed":seed,"post_drift_excess_loss_area":0.0,"recovery_time":1.0,"censored_recovery":0},
        ])
    return pd.DataFrame(rows)


def recovery_pairs(recovery: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for scenario in ["gradual","abrupt","recurring"]:
        left=recovery[(recovery.method_id==V2)&(recovery.scenario==scenario)]
        right=recovery[(recovery.method_id==V1)&(recovery.scenario==scenario)]
        merged=left.merge(right,on=["scenario","center_id","model_seed"],suffixes=("_v2","_v1"))
        for metric in ["post_drift_excess_loss_area","censored_recovery"]:
            merged["difference"]=merged[metric+"_v2"]-merged[metric+"_v1"]; point,low,high=ci_mean(merged,"difference")
            rows.append({"comparison":"Final V2 - V1 LegacyFull","scenario":scenario,"metric":metric,"v2_estimate":float(left[metric].mean()),"v1_estimate":float(right[metric].mean()),"difference":point,"ci_low":low,"ci_high":high,"bootstrap_replicates":BOOTSTRAP,"bootstrap_seed":BOOTSTRAP_SEED,"unit":"center"})
        recovered=merged.dropna(subset=["recovery_time_v2","recovery_time_v1"]).copy()
        recovered["difference"]=recovered.recovery_time_v2-recovered.recovery_time_v1
        point,low,high=ci_mean(recovered,"difference")
        rows.append({"comparison":"Final V2 - V1 LegacyFull","scenario":scenario,"metric":"recovery_time_uncensored","v2_estimate":float(left.recovery_time.mean()),"v1_estimate":1.0,"difference":point,"ci_low":low,"ci_high":high,"bootstrap_replicates":BOOTSTRAP,"bootstrap_seed":BOOTSTRAP_SEED,"unit":"center"})
    return pd.DataFrame(rows)


def row_of(pairs: pd.DataFrame, scenario: str, metric: str) -> dict:
    return clean(pairs[(pairs.scenario==scenario)&(pairs.metric==metric)].iloc[0].to_dict())


def summary_of(summary: pd.DataFrame, method: str, scenario: str) -> dict:
    return clean(summary[(summary.method_id==method)&(summary.scenario==scenario)].iloc[0].to_dict())


def write_with_hash(path: Path, frame: pd.DataFrame, hashes: dict) -> None:
    frame.to_csv(path,index=False,na_rep="NA"); digest=sha256(path); path.with_suffix(path.suffix+".sha256").write_text(digest+"\n",encoding="ascii"); hashes[path.name]=digest


def main() -> None:
    manifest_path=ROOT/"configs_v2_final/frozen_v2_minimal_confirmatory_manifest.json"; plan_path=ROOT/"configs_v2_final/frozen_v2_minimal_analysis_plan.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8")); plan=json.loads(plan_path.read_text(encoding="utf-8"))
    complete=json.loads((ROOT/"audits_v2_final/final_execution_complete.json").read_text(encoding="utf-8"))
    access=json.loads((ROOT/"audits_v2_final/final_heldout_access_audit.json").read_text(encoding="utf-8"))
    if complete["status"]!="PASS" or complete["completed"]!=720: raise RuntimeError("execution is not 720/720 complete")
    data,integrity=read_and_integrity(manifest); atomic_json(ROOT/"audits_v2_final/final_execution_integrity_audit.json",integrity)
    if integrity["status"]!="PASS":
        atomic_json(ROOT/"results_v2_final/execution_status.json",{"state":"INVALID_CONFIRMATORY_EXECUTION","integrity":integrity,"heldout_accessed":True,"heldout_materialized":True})
        raise RuntimeError(f"final integrity failed: {integrity}")
    leakage_checks={"decision_precedes_service":integrity["decision_ordering_errors"]==0,"state_chain_valid":integrity["invalid_state_chain_links"]==0,
        "data_attack_service_hashes_method_seed_invariant":integrity["data_attack_service_hash_mismatch_groups"]==0,
        "scientific_core_hash_frozen":sha256(ROOT/"core/v2_engine.py")=="f27d0abb6fabb50453cb4e04684b8e7b5f99d27aca7ae1f1755990640f3ce024",
        "analysis_plan_hash_frozen":sha256(plan_path)==manifest["analysis_plan_sha256"],"first_access_recorded":access["heldout_accessed"] and access["heldout_materialized"]}
    leakage={"schema":"ravm-dt-v2-final-leakage-audit-v1","status":"PASS" if all(leakage_checks.values()) else "FAIL","checks":leakage_checks,
        "decision_order":"candidate -> verification -> immutable decision token -> service","service_use":"post-decision evaluation only","heldout_access":access}
    atomic_json(ROOT/"audits_v2_final/final_leakage_audit.json",leakage)
    if leakage["status"]!="PASS": raise RuntimeError("leakage audit failed")

    traj=trajectory_metrics(data); summary=scenario_summary(traj); pairs=paired(traj); recovery=recovery_metrics(data); recovery_pair=recovery_pairs(recovery)
    pairs=pd.concat([pairs,recovery_pair],ignore_index=True)
    primary_frame=traj.rename(columns={"method_id":"arm_id"}).copy(); primary_frame["arm_id"]=primary_frame.arm_id.map({V2:"V2_SP_ShortDual",V1:"V0_LegacyFull"})
    primary=stratified_paired_ci(primary_frame,"lifecycle_mse",BALANCED)
    v2_primary=float(np.mean([summary_of(summary,V2,s)["lifecycle_mse"] for s in BALANCED])); v1_primary=float(np.mean([summary_of(summary,V1,s)["lifecycle_mse"] for s in BALANCED]))
    primary.update({"v2_estimate":v2_primary,"v1_estimate":v1_primary,"relative_percent":(v2_primary/v1_primary-1)*100})
    risk={s:{"v2":summary_of(summary,V2,s),"v1":summary_of(summary,V1,s),"harmful_pair":row_of(pairs,s,"harmful_commit_rate"),"downside_pair":row_of(pairs,s,"average_downside")} for s in SAFETY}
    absolute_pass=all(risk[s]["v2"]["harmful_commit_rate"]<=RHO and risk[s]["v2"]["average_downside"]<=EPSILON for s in SAFETY)
    relative_pass=all(risk[s][m]["ci_low"]<=0 for s in SAFETY[1:] for m in ["harmful_pair","downside_pair"])
    benign_rows={s:row_of(pairs,s,"lifecycle_mse") for s in BENIGN}; benign_adverse=[s for s,r in benign_rows.items() if r["ci_low"]>0]
    recall_primary=stratified_paired_ci(primary_frame,"beneficial_commit_recall",BALANCED)
    rec_area=[]; rec_censor=[]
    for s in ["gradual","abrupt","recurring"]:
        rec_area.append(row_of(pairs,s,"post_drift_excess_loss_area")); rec_censor.append(row_of(pairs,s,"censored_recovery"))
    plasticity_clear=(recall_primary["ci_low"]>0 or any(r["ci_high"]<0 for r in rec_area) or any(r["ci_high"]<0 for r in rec_censor))
    primary_wholly_adverse=primary["ci_low"]>0; broad=len(benign_adverse)>=2 and primary["difference"]>=0
    if not absolute_pass or primary_wholly_adverse or broad: verdict="NOT_CONFIRMED"
    elif primary["ci_high"]<0 and relative_pass and not benign_adverse and plasticity_clear: verdict="CONFIRMED"
    else: verdict="PARTIALLY_CONFIRMED"
    replay_h=row_of(pairs,"replay_a010_verification_only","harmful_commit_rate"); replay_d=row_of(pairs,"replay_a010_verification_only","average_downside")
    replay_resolution="A" if replay_h["ci_low"]>0 or replay_d["ci_low"]>0 else ("B" if replay_h["difference"]<=0 and replay_d["difference"]<=0 else "C")
    pivot=primary_frame[primary_frame.analysis_scenario.isin(BALANCED)].pivot_table(index=["analysis_scenario","center_id","model_seed"],columns="arm_id",values="lifecycle_mse").dropna().reset_index()
    pivot["difference"]=pivot["V2_SP_ShortDual"]-pivot["V0_LegacyFull"]
    seedwise={str(int(seed)):float(g.groupby("analysis_scenario").difference.mean().mean()) for seed,g in pivot.groupby("model_seed")}
    centers=pivot.groupby("center_id").difference.mean().sort_values()
    center_summary=pd.DataFrame({"center_id":centers.index,"balanced_lifecycle_mse_difference":centers.values})

    out=ROOT/"results_v2_final"; hashes={}
    write_with_hash(out/"final_trajectory_index.csv",traj,hashes); write_with_hash(out/"final_center_level_summary.csv",center_summary,hashes)
    write_with_hash(out/"final_paired_comparisons.csv",pairs,hashes); write_with_hash(out/"final_scenario_summary.csv",summary,hashes)
    verdict_audit=clean({"schema":"ravm-dt-v2-final-confirmatory-verdict-v1","status":"PASS","verdict":verdict,"generated_at":now(),
        "frozen_analysis_plan_sha256":sha256(plan_path),"primary_balanced_lifecycle_mse":primary,"absolute_safety_pass":absolute_pass,
        "relative_verification_safety_pass":relative_pass,"benign_adverse_regimes":benign_adverse,"plasticity_clear_favorable":plasticity_clear,
        "risk":risk,"balanced_beneficial_recall_paired":recall_primary,"replay_discordance_resolution":replay_resolution,
        "seed_wise_balanced_differences":seedwise,"center_distribution":{"count":len(centers),"min":centers.min(),"q25":centers.quantile(.25),"median":centers.median(),"q75":centers.quantile(.75),"max":centers.max(),"negative_fraction":float((centers<0).mean())},
        "output_hashes":hashes,"evidence_pools_separate":True})
    atomic_json(ROOT/"audits_v2_final/final_confirmatory_verdict.json",verdict_audit)

    def fmt(v): return "NA" if v is None or not np.isfinite(float(v)) else f"{float(v):.10g}"
    def fmtpair(r): return f"{fmt(r['difference'])} [{fmt(r['ci_low'])}, {fmt(r['ci_high'])}]"
    scenario_lines=[]
    for s in BENIGN+SAFETY:
        sv2=summary_of(summary,V2,s); sv1=summary_of(summary,V1,s)
        scenario_lines.append(f"| {s} | {fmt(sv2['lifecycle_mse'])} | {fmt(sv1['lifecycle_mse'])} | {fmtpair(row_of(pairs,s,'lifecycle_mse'))} | {fmtpair(row_of(pairs,s,'harmful_commit_rate'))} | {fmtpair(row_of(pairs,s,'average_downside'))} | {fmtpair(row_of(pairs,s,'beneficial_commit_recall'))} | {fmtpair(row_of(pairs,s,'commit_rate'))} |")
    prior_v21=json.loads((ROOT/"audits_v2_dev/v2_1_security_aware_calibration.json").read_text(encoding="utf-8")); prior_go5=json.loads((ROOT/"audits_v2_dev/v2_post_calibration_go5_audit.json").read_text(encoding="utf-8"))
    report=f"""# V2 Final Minimal Confirmatory Report

Generated: {now()}

## Material Passport

This is the single frozen analysis of 720 fresh confirmatory trajectories: 30 centers × 3 model seeds × 4 preassigned streams × 2 methods. Every trajectory contains 24 unique lifecycle stages. Statistical inference treats center as the unit and averages model seeds within center; all paired 95% CIs use 4,000 center-cluster bootstrap replicates with seed 2904.

- Final method: `V2_SP_ShortDual`, SinglePath, 50 adaptation steps, history capacity 12, κ_rec=0, κ_hist=0.5.
- Scientific implementation commit: `7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3`.
- Final config SHA-256: `{sha256(ROOT/'configs_v2_final/frozen_v2_final_commit_config.yaml')}`.
- Confirmatory manifest SHA-256: `{sha256(manifest_path)}`.
- Analysis plan SHA-256: `{sha256(plan_path)}`.
- First heldout access: `{access['first_heldout_access_utc']}`; first materialization: `{access['first_heldout_materialization_utc']}`.
- Environment: Python {complete['runtime']['python_version']}, PyTorch {complete['runtime']['torch_version']}, CUDA {complete['runtime']['torch_cuda_version']}, {complete['runtime']['gpu_name']}.

## Integrity and leakage

Integrity **{integrity['status']}**: expected/valid=720/720, missing={integrity['missing']}, duplicate={integrity['duplicate']}, unexpected={integrity['unexpected']}, partial/invalid={integrity['partial_invalid']}, stage rows={integrity['stage_rows']}. Decision-order errors={integrity['decision_ordering_errors']}; state-chain errors={integrity['invalid_state_chain_links']}; data/attack/service hash mismatch groups={integrity['data_attack_service_hash_mismatch_groups']}. Leakage audit: **{leakage['status']}**. Service data remained reachable only after the immutable decision token.

Center-to-regime assignment was frozen as `REGIMES[(center_id-14000) % 4]`: stationary 14000,14004,…; gradual 14001,14005,…; abrupt 14002,14006,…; recurring 14003,14007,… .

## Primary balanced lifecycle MSE

Final V2={fmt(v2_primary)}, V1 LegacyFull={fmt(v1_primary)}. Paired Final V2−V1 difference={fmtpair(primary)}, relative difference={primary['relative_percent']:+.3f}%. The primary CI upper bound is {'below' if primary['ci_high']<0 else 'not below'} zero.

## Scenario results

All differences are Final V2−V1 paired center-cluster estimates. Harmful/downside, beneficial recall, and commit columns report paired differences and 95% CI.

| Scenario | V2 MSE | V1 MSE | Δ lifecycle MSE [95% CI] | Δ harmful [95% CI] | Δ downside [95% CI] | Δ beneficial recall [95% CI] | Δ commit [95% CI] |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(scenario_lines)}

The machine-readable scenario table also reports MAE, conditional harmful among commits, and maximum retain streak with center-cluster CIs. Absolute safety passed={str(absolute_pass).lower()} against harmful≤{RHO} and downside≤{EPSILON:.12g} for mixed, persistent verification-only, and replay verification-only. Relative verification safety passed={str(relative_pass).lower()}.

## Benign drift and plasticity

Benign lifecycle-MSE regimes with a wholly adverse paired CI: `{benign_adverse}`. Balanced beneficial-recall difference={fmtpair(recall_primary)}. Fresh excess-loss/recovery uses the pre-access frozen two-method diagnostic: V1 is the contemporaneous reference envelope, so it remains separate from development recovery estimates that used Frozen/Always-FT. Plasticity clear-favorable evidence={str(plasticity_clear).lower()}.

Seed-wise balanced MSE differences: `{json.dumps(seedwise)}`. Across 30 centers, median paired difference={fmt(float(centers.median()))}, range=[{fmt(float(centers.min()))}, {fmt(float(centers.max()))}], favorable fraction={float((centers<0).mean()):.3f}.

## Evidence pools and replay discordance

Development, calibration, and fresh confirmatory evidence remain separate. Development post-calibration GO-5 retained the replay adverse relative-safety signal (verdict `{prior_go5['resulting_overall_verdict']}`); V2.1 calibration found 14/16 feasible configurations and selected `{prior_v21['selection']['selected']['arm_id']}` with GO-5 PASS. Fresh replay resolution is **{replay_resolution}**: A supports the development adverse signal, B supports calibration acceptable safety, and C remains inconclusive under the frozen rule.

Other V1 baselines are prior/development evidence only. No fresh paired superiority claim is made against Always-FT, ER, EWC, Huber-FT, ValidationCommit, Frozen, or CLeaR.

## Negative and inconclusive findings

Any confidence interval crossing zero remains inconclusive and is not described as equivalence. Any adverse regime, relative-safety result, or failed plasticity criterion is retained in the tables and in the verdict audit. This fresh pool will not be used to modify or recalibrate V2.

## Claim boundary and final verdict

Allowed claim: the frozen Final V2 is **{verdict}** relative to V1 LegacyFull on this predeclared 30-center minimal fresh confirmatory matrix, under the exact endpoint and safety rules above. Forbidden claims include fresh superiority over baselines not rerun here, pooled inference across development/calibration/heldout, or proof of equivalence from a CI crossing zero.

**Final verdict: {verdict}.**
"""
    report_path=ROOT/"V2_FINAL_MINIMAL_CONFIRMATORY_REPORT.md"; report_path.write_text(report,encoding="utf-8")
    report_hash=sha256(report_path); report_path.with_suffix(report_path.suffix+".sha256").write_text(report_hash+"\n",encoding="ascii")
    verdict_audit["report_sha256"]=report_hash; atomic_json(ROOT/"audits_v2_final/final_confirmatory_verdict.json",verdict_audit)
    audit_hashes={p.name:sha256(p) for p in sorted((ROOT/"audits_v2_final").glob("*.json"))}
    atomic_json(ROOT/"audits_v2_final/final_output_hash_manifest.json",{"status":"PASS","generated_at":now(),"report":{"path":str(report_path),"sha256":report_hash},"results":hashes,"audits":audit_hashes})
    atomic_json(ROOT/"results_v2_final/execution_status.json",{"state":"V2_FINAL_CONFIRMATORY_COMPLETE","phase":"v2_final_analysis_complete","completed":720,"expected":720,"verdict":verdict,"integrity":"PASS","leakage":"PASS","report":str(report_path),"report_sha256":report_hash,"warning":None,"heldout_accessed":True,"heldout_materialized":True,"updated_at":now()})
    print(json.dumps({"state":"V2_FINAL_CONFIRMATORY_COMPLETE","verdict":verdict,"report":str(report_path)},indent=2))


if __name__ == "__main__": main()
