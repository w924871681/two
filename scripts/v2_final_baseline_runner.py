"""Two-worker idempotent executor for the frozen final baseline manifest."""
from __future__ import annotations
import concurrent.futures as cf
import datetime as dt
import hashlib,json,os,platform,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import torch
from core.engine import run
from core.protocol import ROOT
from scripts.v2_runner import atomic_json

EXPECTED=2160
def sha(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def runtime():
 a=bool(torch.cuda.is_available());return {"pid":os.getpid(),"sys_executable":str(Path(sys.executable).resolve()),"python_version":platform.python_version(),"torch_version":torch.__version__,"torch_cuda_version":torch.version.cuda,"torch_cuda_available":a,"gpu_name":torch.cuda.get_device_name(0) if a else None}
def valid(path:Path,job:dict):
 try:
  f=pd.read_csv(path)
  return len(f)==24 and f.stage.tolist()==list(range(1,25)) and f.method.nunique()==1 and f.method.iloc[0]==job["method"] and f.center_id.nunique()==1 and int(f.center_id.iloc[0])==job["center_id"] and f.model_seed.nunique()==1 and int(f.model_seed.iloc[0])==job["model_seed"] and f.scenario_id.nunique()==1 and f.scenario_id.iloc[0]==job["stream"]["scenario_id"]
 except Exception:return False
def worker_init(prov:str):atomic_json(Path(prov)/f"worker_{os.getpid()}.json",runtime()|{"role":"baseline_worker"})
def execute(job:dict,cfg:dict):
 out=ROOT/"results_v2_final_baselines/trajectories"/job["filename"]
 if out.exists() and valid(out,job):return {"status":"skipped","pid":os.getpid(),"runtime":runtime()}
 if out.exists():raise RuntimeError(f"invalid pre-existing trajectory: {out}")
 stream=job["stream"];started=time.perf_counter()
 rows=run(job["center_id"],job["model_seed"],job["method"],stream["kind"],stream["alpha"],stream["attack_location"],cfg,stages=24,backbone="GRU",H=1,run_id=out.stem)
 for row in rows:row.update({"scenario_id":stream["scenario_id"],"analysis_scenario":job["analysis_scenario"],"execution_phase":"v2_final_baseline_benchmark"})
 out.parent.mkdir(parents=True,exist_ok=True);tmp=out.with_name(out.name+f".{os.getpid()}.tmp");pd.DataFrame(rows).to_csv(tmp,index=False,na_rep="NA");os.replace(tmp,out)
 if not valid(out,job):raise RuntimeError(f"published trajectory invalid: {out}")
 return {"status":"completed","pid":os.getpid(),"runtime":runtime(),"wall_s":time.perf_counter()-started}
def main():
 manifest_path=ROOT/"audits_v2_final_baselines/final_benchmark_manifest.json";manifest=json.loads(manifest_path.read_text(encoding="utf-8"));prov=json.loads((ROOT/"audits_v2_final_baselines/baseline_provenance_audit.json").read_text(encoding="utf-8"));rt=runtime()
 checks={"manifest_frozen":manifest["status"]=="FROZEN_BEFORE_BASELINE_EXECUTION" and len(manifest["jobs"])==EXPECTED,"provenance_pass":prov["status"]=="PASS","engine_hash":sha(ROOT/"core/engine.py")==manifest["scientific_engine_sha256"],"runtime":rt["python_version"]=="3.11.15" and rt["torch_version"]=="2.5.1+cu121" and rt["torch_cuda_available"] and rt["gpu_name"]=="NVIDIA GeForce RTX 3060 Laptop GPU"}
 if not all(checks.values()):raise RuntimeError(f"baseline runner preflight failed: {checks}")
 jobs=manifest["jobs"];cfg=manifest["frozen_config"];folder=ROOT/"results_v2_final_baselines/trajectories";existing=sum(valid(folder/j["filename"],j) for j in jobs);pending=[j for j in jobs if not valid(folder/j["filename"],j)]
 completed=existing;started=time.time();pids=set();worker_runtimes={};status_path=ROOT/"results_v2_final_baselines/execution_status.json";failure=ROOT/"results_v2_final_baselines/execution_failure.json";failure.unlink(missing_ok=True);provdir=ROOT/"results_v2_final_baselines/provenance";provdir.mkdir(parents=True,exist_ok=True)
 def status(state,warning=None):
  elapsed=max(time.time()-started,1e-9);new=completed-existing;rate=new/elapsed*3600 if new else None;remain=EXPECTED-completed
  atomic_json(status_path,{"state":state,"phase":"v2_final_baseline_benchmark","completed":completed,"expected":EXPECTED,"remaining":remain,"throughput_trajectories_per_hour":rate,"eta_seconds":remain/rate*3600 if rate else None,"runner_pid":os.getpid(),"worker_pids":sorted(pids),"updated_at":now(),"warning":warning,"runtime":rt,"worker_runtimes":worker_runtimes,"partial_scientific_analysis":False})
 status("FINAL_BASELINE_BENCHMARK_RUNNING")
 try:
  with cf.ProcessPoolExecutor(max_workers=2,initializer=worker_init,initargs=(str(provdir),)) as pool:
   futures=[pool.submit(execute,j,cfg) for j in pending]
   for future in cf.as_completed(futures):
    result=future.result();completed+=1;pids.add(int(result["pid"]));worker_runtimes[str(result["pid"])]=result["runtime"]
    if completed%20==0 or completed==EXPECTED:
     status("FINAL_BASELINE_BENCHMARK_RUNNING" if completed<EXPECTED else "BASELINE_EXECUTION_COMPLETE_PENDING_AUDIT")
     elapsed=max(time.time()-started,1e-9);rate=(completed-existing)/elapsed*3600 if completed>existing else 0;print(f"baseline {completed}/{EXPECTED} rate={rate:.1f}/h workers={sorted(pids)}",flush=True)
  status("BASELINE_EXECUTION_COMPLETE_PENDING_AUDIT")
  atomic_json(ROOT/"audits_v2_final_baselines/baseline_execution_complete.json",{"status":"PASS","completed":completed,"expected":EXPECTED,"existing_valid":existing,"executed_now":completed-existing,"elapsed_s":time.time()-started,"runner_pid":os.getpid(),"worker_pids":sorted(pids),"manifest_sha256":sha(manifest_path),"runtime":rt})
 except Exception as exc:
  msg=f"{type(exc).__name__}: {exc}";status("BASELINE_EXECUTION_FAILURE",msg);atomic_json(failure,{"status":"FAIL","error":msg,"completed":completed,"expected":EXPECTED,"at":now()});raise
if __name__=="__main__":main()
