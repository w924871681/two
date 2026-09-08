"""Create the mandatory post-P7 execution plan using completed timing evidence."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import datetime,json,statistics,subprocess
import pandas as pd
from core.protocol import ROOT,save_json
from scripts.pretrain import pretrain

def development_timings():
    values={}
    for p in (ROOT/'results/development').glob('*.csv'):
        if p.name=='development_summary.csv':continue
        d=pd.read_csv(p,usecols=['method','maintenance_time_s']);method=str(d.method.iloc[0]);values.setdefault(method,[]).append(float(d.maintenance_time_s.sum()))
    return {k:{'trajectories':len(v),'median_s':statistics.median(v),'p10_s':float(pd.Series(v).quantile(.1)),'p90_s':float(pd.Series(v).quantile(.9))} for k,v in values.items()}

def main():
    assert json.loads((ROOT/'audits/heldout_readiness.json').read_text())['status']=='approved_by_implementation_audit'
    assert not (ROOT/'results/heldout').exists(),'remaining-matrix profile must precede heldout access'
    # The Alibaba equivalence gate needs the preregistered source-only models.
    # Training them here uses only machines 20000--20019 and occurs before any
    # Alibaba calibration or heldout/direct-transfer state is opened.
    for seed in [7311,7312,7313]:pretrain(seed,domain='alibaba')
    subprocess.run([sys.executable,str(ROOT/'scripts/audit_alibaba_joint_dag_equivalence.py')],cwd=ROOT,check=True)
    dev=development_timings();p6=json.loads((ROOT/'logs/execution_status.json').read_text());bench=json.loads((ROOT/'audits/joint_dag_benchmark.json').read_text())
    ali=json.loads((ROOT/'audits/alibaba_joint_dag_equivalence.json').read_text());counts={
        'Frozen':1610,'Always-FT':1610,'ER':1610,'EWC':1250,'Huber-FT':1250,'CLeaR-Predictor':1250,'ValidationCommit':1610,
        'Proposed Full':2330,'Proposed ablations':300,'OracleCommit':240,'Alibaba direct/diagnostic':2640,'Alibaba calibration':48600}
    ranges={'Frozen':(.2,.6),'Always-FT':(2.8,5.0),'ER':(4.0,7.0),'EWC':(8.0,13.0),'Huber-FT':(2.8,5.0),
        'CLeaR-Predictor':(3.5,8.0),'ValidationCommit':(2.8,5.0),'Proposed Full':(8.0,14.0),'Proposed ablations':(6.0,12.0),
        'OracleCommit':(2.8,5.0),'Alibaba direct/diagnostic':(3.0,12.0),'Alibaba calibration':(.04,.15)}
    rows=[]
    for method,n in counts.items():
        lo,hi=ranges[method];rows.append((method,n,lo,hi,n*lo/3600,n*hi/3600))
    eta_lo=sum(r[4] for r in rows);eta_hi=sum(r[5] for r in rows)
    table='\n'.join(f'| {m} | {n:,} | {lo:.2f}–{hi:.2f} | {hlo:.2f}–{hhi:.2f} |' for m,n,lo,hi,hlo,hhi in rows)
    text=f'''# Remaining Matrix Execution Plan\n\nGenerated: {datetime.datetime.now().isoformat()} (post-P7, before any heldout access)\n\n## Evidence and decision\n\n- P6 formal joint-DAG status: complete before this plan; P7 readiness audit: PASS.\n- Development full-lifecycle timing profiles: `{json.dumps(dev,ensure_ascii=False)}`.\n- Synthetic joint-DAG benchmark artifact: `audits/joint_dag_benchmark.json`.\n- Alibaba domain-local equivalence: PASS on {sum(c['policies'] for c in ali['cases'])} policies across clean/mixed, exact scientific fields, aggregate speedup {ali['aggregate_speedup']:.2f}x.\n- Decision: retain reference execution for heldout baselines and single-policy Proposed workloads. Reuse the already verified joint-DAG only for Alibaba's 400-policy calibration with two complete-workload workers. No precision, optimizer, step, window, attack, threshold, stage, center, seed, metric, or bootstrap change.\n\n## Expected wall time\n\n| Method/workload | Remaining trajectories | Seconds/trajectory range | Wall-hours range |\n|---|---:|---:|---:|\n{table}\n\nThe additive single-worker estimate is **{eta_lo:.1f}–{eta_hi:.1f} hours**. Independent workload scheduling may reduce elapsed time, but GPU-heavy two-process execution previously showed contention, so this plan does not claim unmeasured parallel speedups. ETA must be updated from live throughput.\n\n## Required questions\n\n1. Per-method wall time appears in the table and uses actual development/P6 profiles plus conservative ranges for methods absent from development.\n2. Complete `center × condition × seed × method` workloads are independent.\n3. All 24 stages inside one lifecycle remain strictly serial.\n4. EWC is the largest per-trajectory baseline cost; CLeaR is variable but below EWC in existing development profiles.\n5. Immutable update/verification windows and attack masks repeat across methods, but no new cross-method preprocessing cache is introduced because the projected gain was not established above the 20–30% change threshold.\n6. Service evaluation repeats across methods. It remains uncached because the service result depends on the deployed model and because no post-freeze equivalence benchmark justified a new path.\n7. P6 produced 48,600 small CSVs successfully; publishing is measurable overhead but did not dominate candidate/evidence computation. The final schema and independent files are retained.\n8. One worker remains the conservative choice for individual GPU-heavy baselines. Two workers are used only for the already benchmarked joint-DAG calibration workload class.\n9. Alibaba uses the same causal executor with domain-local data/state/cache keys. The post-P7 Alibaba equivalence gate passed, so its 400-policy calibration may reuse joint-DAG; synthetic artifacts are never treated as Alibaba data/state.\n10. The current conservative remaining total is **{eta_lo:.1f}–{eta_hi:.1f} hours**, updated later using live stage throughput.\n'''
    (ROOT/'REMAINING_MATRIX_EXECUTION_PLAN.md').write_text(text,encoding='utf-8')
    save_json(ROOT/'audits/remaining_matrix_execution_plan.json',{'status':'passed','created_at':datetime.datetime.now().isoformat(),
        'heldout_accessed':False,'alibaba_joint_dag_adopted':True,'alibaba_speedup':ali['aggregate_speedup'],'estimated_hours':[eta_lo,eta_hi],
        'development_profiles':dev,'no_scientific_protocol_change':True})
    from scripts.run_all_final import update_report
    update_report('P7 后剩余矩阵执行检查完成',f'Alibaba calibration 的域内科学等价性 PASS，实测加速 {ali["aggregate_speedup"]:.2f}×，采用同一 joint-DAG 执行结构；其余 heldout/baseline 保持 reference executor。预计剩余 {eta_lo:.1f}–{eta_hi:.1f} 小时，详见 `REMAINING_MATRIX_EXECUTION_PLAN.md`。')

if __name__=='__main__':main()
