# Remaining Matrix Execution Plan

Generated: 2026-09-09T03:26:44.959758 (post-P7, before any heldout access)

## Evidence and decision

- P6 formal joint-DAG status: complete before this plan; P7 readiness audit: PASS.
- Development full-lifecycle timing profiles: `{"RobustAlways": {"trajectories": 480, "median_s": 3.614195700007257, "p10_s": 2.9390761099988585, "p90_s": 9.902939830033576}, "CLeaR-Predictor": {"trajectories": 480, "median_s": 3.1159949000284533, "p10_s": 0.8936217899550671, "p90_s": 8.540113259968347}, "EWC": {"trajectories": 360, "median_s": 6.7014265499747125, "p10_s": 5.440226230080587, "p90_s": 16.851687499959375}, "Frozen": {"trajectories": 120, "median_s": 0.06863495001743905, "p10_s": 0.06481446995749046, "p90_s": 0.0931429799384193}, "Always-FT": {"trajectories": 120, "median_s": 2.8958060999721047, "p10_s": 2.642977379882358, "p90_s": 3.3075037499889723}}`.
- Synthetic joint-DAG benchmark artifact: `audits/joint_dag_benchmark.json`.
- Alibaba domain-local equivalence: PASS on 25 policies across clean/mixed, exact scientific fields, aggregate speedup 1.76x.
- Decision: retain reference execution for heldout baselines and single-policy Proposed workloads. Reuse the already verified joint-DAG only for Alibaba's 400-policy calibration with two complete-workload workers. No precision, optimizer, step, window, attack, threshold, stage, center, seed, metric, or bootstrap change.

## Expected wall time

| Method/workload | Remaining trajectories | Seconds/trajectory range | Wall-hours range |
|---|---:|---:|---:|
| Frozen | 1,610 | 0.20–0.60 | 0.09–0.27 |
| Always-FT | 1,610 | 2.80–5.00 | 1.25–2.24 |
| ER | 1,610 | 4.00–7.00 | 1.79–3.13 |
| EWC | 1,250 | 8.00–13.00 | 2.78–4.51 |
| Huber-FT | 1,250 | 2.80–5.00 | 0.97–1.74 |
| CLeaR-Predictor | 1,250 | 3.50–8.00 | 1.22–2.78 |
| ValidationCommit | 1,610 | 2.80–5.00 | 1.25–2.24 |
| Proposed Full | 2,330 | 8.00–14.00 | 5.18–9.06 |
| Proposed ablations | 300 | 6.00–12.00 | 0.50–1.00 |
| OracleCommit | 240 | 2.80–5.00 | 0.19–0.33 |
| Alibaba direct/diagnostic | 2,640 | 3.00–12.00 | 2.20–8.80 |
| Alibaba calibration | 48,600 | 0.04–0.15 | 0.54–2.02 |

The additive single-worker estimate is **18.0–38.1 hours**. Independent workload scheduling may reduce elapsed time, but GPU-heavy two-process execution previously showed contention, so this plan does not claim unmeasured parallel speedups. ETA must be updated from live throughput.

## Required questions

1. Per-method wall time appears in the table and uses actual development/P6 profiles plus conservative ranges for methods absent from development.
2. Complete `center × condition × seed × method` workloads are independent.
3. All 24 stages inside one lifecycle remain strictly serial.
4. EWC is the largest per-trajectory baseline cost; CLeaR is variable but below EWC in existing development profiles.
5. Immutable update/verification windows and attack masks repeat across methods, but no new cross-method preprocessing cache is introduced because the projected gain was not established above the 20–30% change threshold.
6. Service evaluation repeats across methods. It remains uncached because the service result depends on the deployed model and because no post-freeze equivalence benchmark justified a new path.
7. P6 produced 48,600 small CSVs successfully; publishing is measurable overhead but did not dominate candidate/evidence computation. The final schema and independent files are retained.
8. One worker remains the conservative choice for individual GPU-heavy baselines. Two workers are used only for the already benchmarked joint-DAG calibration workload class.
9. Alibaba uses the same causal executor with domain-local data/state/cache keys. The post-P7 Alibaba equivalence gate passed, so its 400-policy calibration may reuse joint-DAG; synthetic artifacts are never treated as Alibaba data/state.
10. The current conservative remaining total is **18.0–38.1 hours**, updated later using live stage throughput.
