"""Freeze provenance, execution matrix, and analysis rules for final baselines."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import torch

from core.protocol import ROOT
from scripts.v2_runner import atomic_json

METHODS=["Always-FT","ER","EWC","Huber-FT","ValidationCommit","Frozen"]
CENTERS=list(range(14000,14030)); SEEDS=[7311,7312,7313]
STREAMS=[
 {"scenario_id":"clean","kind":"clean","alpha":0.0,"attack_location":"both"},
 {"scenario_id":"mixed_a010_both","kind":"mixed","alpha":0.1,"attack_location":"both"},
 {"scenario_id":"persistent_a010_verification_only","kind":"persistent_bias","alpha":0.1,"attack_location":"verification_only"},
 {"scenario_id":"replay_a010_verification_only","kind":"replay","alpha":0.1,"attack_location":"verification_only"},
]
REGIMES=["stationary","gradual","abrupt","recurring"]
HASHES={"configs/frozen_candidate_config.yaml":"4a9655cf427f41bb321dc5237008fa795f1fb3437c979206fd4784810bca74ea",
"configs/frozen_commit_config.yaml":"1da5f249d1a8c41afcc7d49f2bd30d288e2cdabd220b7840cfc0a3903bc9bf3a",
"configs/frozen_baseline_config.yaml":"765f58a595a156320caa3c4664657670968d4638e5bf15b7d430444b82581908",
"core/engine.py":"b143046aac84e62ab098c5cb5f1666dafe4fe24419ea8b164acdf2c8cbee23a6"}

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def runtime():
 a=bool(torch.cuda.is_available());return {"sys_executable":str(Path(sys.executable).resolve()),"python_version":platform.python_version(),"torch_version":torch.__version__,"torch_cuda_version":torch.version.cuda,"torch_cuda_available":a,"gpu_name":torch.cuda.get_device_name(0) if a else None}
def main():
 audit_dir=ROOT/"audits_v2_final_baselines";audit_dir.mkdir(exist_ok=True)
 final_integrity=json.loads((ROOT/"audits_v2_final/final_execution_integrity_audit.json").read_text(encoding="utf-8"))
 final_leakage=json.loads((ROOT/"audits_v2_final/final_leakage_audit.json").read_text(encoding="utf-8"))
 final_verdict=json.loads((ROOT/"audits_v2_final/final_confirmatory_verdict.json").read_text(encoding="utf-8"))
 frozen_manifest=json.loads((ROOT/"configs_v2_final/frozen_v2_minimal_confirmatory_manifest.json").read_text(encoding="utf-8"))
 index=pd.read_csv(ROOT/"results_v2_final/final_trajectory_index.csv")
 proposed=index[index.method_id=="Final_V2_SP_ShortDual"]
 v2_hash_bad=[]
 for row in proposed.itertuples():
  path=ROOT/"results_v2_final/trajectories"/row.source_file
  if not path.exists() or sha(path)!=row.source_file_sha256:v2_hash_bad.append(row.source_file)
 current_runtime=runtime(); existing=list((ROOT/"results_v2_final_baselines/trajectories").glob("*.csv")) if (ROOT/"results_v2_final_baselines/trajectories").exists() else []
 cfg={}
 for name in ["frozen_candidate_config.yaml","frozen_commit_config.yaml","frozen_baseline_config.yaml"]:cfg.update(json.loads((ROOT/"configs"/name).read_text(encoding="utf-8")))
 checks={
  "final_confirmatory_complete":final_integrity["status"]=="PASS" and final_integrity["valid"]==720 and final_leakage["status"]=="PASS" and final_verdict["verdict"]=="CONFIRMED",
  "proposed_360_hash_valid":len(proposed)==360 and proposed.center_id.nunique()==30 and proposed.model_seed.nunique()==3 and proposed.scenario_id.nunique()==4 and not v2_hash_bad,
  "frozen_regime_mapping_exact":frozen_manifest["center_regime_assignment"]=={str(c):REGIMES[(c-14000)%4] for c in CENTERS},
  "v1_frozen_hashes_exact":all(sha(ROOT/p)==h for p,h in HASHES.items()),
  "baseline_config_unique":cfg["ewc_lambda"]==10.0 and cfg["huber_delta"]==0.1 and cfg["ewc_gamma"]==0.9 and cfg["ewc_fisher_examples"]==32 and cfg["validation_retain_all"] is True,
  "runtime_exact":current_runtime["python_version"]=="3.11.15" and current_runtime["torch_version"]=="2.5.1+cu121" and current_runtime["torch_cuda_version"]=="12.1" and current_runtime["torch_cuda_available"] and current_runtime["gpu_name"]=="NVIDIA GeForce RTX 3060 Laptop GPU",
  "fresh_data_already_opened_exact":all((ROOT/"data"/f"center_{c}.npz").exists() for c in CENTERS),
  "no_preexisting_baseline_results":not existing,
 }
 provenance={"schema":"ravm-dt-v2-final-baseline-provenance-v1","status":"PASS" if all(checks.values()) else "BASELINE_PROVENANCE_UNRESOLVED","created_at":dt.datetime.now(dt.timezone.utc).isoformat(),"checks":checks,"failed_checks":[k for k,v in checks.items() if not v],"methods":METHODS,"frozen_hashes":HASHES,"resolved_config":cfg,"runtime":current_runtime,"v2_hash_mismatches":v2_hash_bad,"post_freeze_benchmark_completion":True,"proposed_method_changed":False}
 atomic_json(audit_dir/"baseline_provenance_audit.json",provenance)
 if not all(checks.values()):raise SystemExit(2)
 jobs=[]
 for c in CENTERS:
  for seed in SEEDS:
   for stream in STREAMS:
    for method in METHODS:
     jobs.append({"method":method,"center_id":c,"model_seed":seed,"stream":stream,"analysis_scenario":REGIMES[(c-14000)%4] if stream["scenario_id"]=="clean" else stream["scenario_id"],"stages":24,"filename":f"{method}__{stream['scenario_id']}__{c}__{seed}.csv"})
 assert len(jobs)==2160 and len({j["filename"] for j in jobs})==2160
 manifest={"schema":"ravm-dt-v2-final-baseline-manifest-v1","status":"FROZEN_BEFORE_BASELINE_EXECUTION","created_at":dt.datetime.now(dt.timezone.utc).isoformat(),"execution_implementation_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"scientific_engine_sha256":sha(ROOT/"core/engine.py"),"methods":METHODS,"centers":CENTERS,"seeds":SEEDS,"streams":STREAMS,"center_regime_assignment":frozen_manifest["center_regime_assignment"],"expected_trajectories":2160,"expected_stage_rows":51840,"stages_per_trajectory":24,"workers":2,"partition_unit":"complete center x scenario x seed x method lifecycle","scientific_key":["method","center_id","model_seed","scenario_id"],"frozen_config":cfg,"frozen_config_hashes":{p:h for p,h in HASHES.items() if p.startswith('configs/')},"analysis_plan":{"statistical_unit":"center","seed_handling":"average within center","paired_on":["center_id","model_seed","analysis_scenario"],"bootstrap":{"replicates":4000,"seed":2904,"interval":"percentile 95%"},"main_balanced_scenarios":["stationary","gradual","abrupt","recurring","mixed_a010_both","persistent_a010_verification_only","replay_a010_verification_only"],"confirmatory_utility_balanced_scenarios":["stationary","gradual","abrupt","recurring","mixed_a010_both"],"recovery_reference":"stagewise minimum of Frozen and Always-FT on the same center/seed clean trajectory, frozen before baseline results","metrics":["lifecycle_mse","lifecycle_mae","harmful_commit_rate","average_downside","conditional_harmful_rate","beneficial_commit_recall","commit_rate","post_drift_excess_loss_area","recovery_time","censored_recovery","maximum_retain_streak","maintenance_time_s"]},"jobs":jobs}
 path=audit_dir/"final_benchmark_manifest.json";atomic_json(path,manifest);path.with_suffix(".json.sha256").write_text(sha(path)+"\n",encoding="ascii")
 atomic_json(ROOT/"results_v2_final_baselines/execution_status.json",{"state":"FINAL_BASELINE_MANIFEST_FROZEN","completed":0,"expected":2160,"manifest_sha256":sha(path),"warning":None})
 print(json.dumps({"status":"PASS","expected":2160,"manifest_sha256":sha(path)},indent=2))
if __name__=="__main__":main()
