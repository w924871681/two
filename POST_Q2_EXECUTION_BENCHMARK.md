# POST-Q2 Execution Benchmark

Generated: 2026-09-09T17:12:00.724261+08:00

## Material Passport

- Artifact: `POST_Q2_EXECUTION_BENCHMARK.md`
- Mode: experiment execution / reproducibility validation
- Data: replay of completed Q2 only
- Formal outputs written: none
- Verification status: VERIFIED
- Runtime: `C:\Users\92487\anaconda3\envs\rcf-dti-py311\python.exe`, PyTorch 2.5.1+cu121, CUDA 12.1
- Machine: Intel Core i7-12700H (14 cores / 20 logical processors), NVIDIA RTX 3060 Laptop GPU 6 GiB

## Scope and workload

Each variant replayed 16 complete 24-stage trajectories: 2 centers × 2 conditions × 1 seed × 4 methods. The conditions were `random / 0.1 / both` and `persistent_bias / 0.1 / verification_only`; methods were EWC, Proposed, CLeaR-Predictor, and Always-FT. Workers received complete `center × condition × seed × method` lifecycles. No lifecycle stage was split across workers.

All benchmark CSVs and measurements are under `scratch/post_q2_executor_benchmark/`. Formal Q1/Q2 directory manifests, scientific core files, and frozen configuration hashes were identical before and after. Q3 remained absent.

An initial CPU-only pilot was excluded because it did not match the formal Q2 runtime. The authoritative CUDA pass below includes valid process I/O counters. A preceding CUDA pass had valid wall-clock and scientific outputs but an invalid Windows I/O counter; it is retained as timing robustness evidence.

## Wall-clock results

| Variant | Executor | Wall time (s) | Throughput (traj/h) | Wall/trajectory (s) | Speedup vs A | Scientific equivalence |
|---|---|---:|---:|---:|---:|---|
| A | current reference, 1 worker | 95.13 | 605.5 | 5.946 | 1.000× | PASS |
| B | 2 independent workload workers | 52.87 | 1089.5 | 3.304 | 1.799× | PASS |
| C | 1 worker + immutable preprocessing reuse | 86.62 | 665.0 | 5.414 | 1.098× | PASS |
| D | 2 workers + immutable preprocessing reuse | 49.64 | 1160.2 | 3.103 | 1.916× | PASS |

B was repeatably faster in both valid CUDA passes: 1.703–1.799×. C changed from 0.938× to 1.098×, so its small apparent gain was not stable. D was run because B and C both passed the 1.03× screen in the authoritative pass; D reached 1.916× versus A, but only 1.065× versus B.

## Reference method profile

| Method | Core wall/trajectory (s) | Serial throughput (traj/h) | Candidate/adaptation (s) | Verification (s) | Maintenance (s) | CSV publish (s) |
|---|---:|---:|---:|---:|---:|---:|
| EWC | 8.972 | 401.0 | 6.461 | 0.017 | 8.502 | 0.0062 |
| Proposed | 6.029 | 596.6 | 4.016 | 1.645 | 5.713 | 0.0056 |
| CLeaR-Predictor | 3.619 | 993.5 | 2.371 | 0.017 | 3.214 | 0.0050 |
| Always-FT | 3.898 | 913.4 | 3.576 | 0.017 | 3.639 | 0.0434 |

- **EWC:** the dominant extra work is the initial Fisher estimate plus a 32-example Fisher refresh after each stage, on top of 50-step EWC-regularized adaptation. Reference core wall was 8.972 s/trajectory.
- **Proposed:** five robust candidate branches total 50 optimizer steps, followed by recent and historical blockwise verification. Candidate construction used 4.016 s and verification 1.645 s/trajectory.
- **CLeaR-Predictor:** cost comes from novelty classification, buffer management, triggered EWC adaptation, and Fisher refresh on trigger stages. Reference core wall was 3.619 s/trajectory.
- **Always-FT:** its fixed 50-step adaptation dominates maintenance; it has no commit verification rule. Reference core wall was 3.898 s/trajectory.

The immutable reuse layer recorded 7,488 hits and 1,908 misses. Cache lookup/build time was 0.895 s across all 16 C trajectories. It retained about 651 MiB CPU and 521 MiB GPU data. Across the two valid CUDA passes, its end-to-end effect ranged from 0.938× to 1.098×; preprocessing/window construction is therefore not the stable bottleneck.

## Resource and file I/O profile

| Variant | CPU mean | CPU max | GPU mean | GPU max | GPU memory mean (MiB) | GPU memory max (MiB) | Process reads (MiB) | Process writes (MiB) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 17.9% | 32.1% | 28.3% | 56.0% | 301 | 339 | 34.13 | 0.34 |
| B | 21.6% | 40.9% | 72.3% | 94.0% | 554 | 618 | 56.68 | 0.34 |
| C | 17.0% | 26.1% | 27.6% | 52.0% | 569 | 829 | 25.49 | 0.34 |
| D | 22.4% | 48.1% | 76.9% | 96.0% | 894 | 1288 | 49.28 | 0.34 |

B raised mean GPU utilization from 28.3% to 72.3% and peak utilization from 56% to 94%. Peak GPU memory stayed low at 618 MiB. Individual B trajectories slowed modestly, but aggregate throughput still improved 1.799×, so contention is present but not dominant. D increased peak memory to 1288 MiB for only a 1.065× increment over B. CSV publishing remained below 0.0434 s/trajectory; serialization and file I/O are not primary bottlenecks. Exact component counters and per-trajectory records are in the audit JSON.

## Scientific equivalence

All 64 comparisons passed: formal Q2→A and A→B/C/D for every trajectory. Hash, integer, categorical, stage sequence, decision, data hash, attack-mask hash, ordering, and final deployed-state inputs were exact. The maximum absolute floating difference was 0.000e+00, within the required 1e-12 limit.

## Recommendation and remaining time

The recommended executor is **B: 2 independent workload workers**. B exceeded the 1.50× recommendation threshold in both valid CUDA passes and is scientifically exact. Immutable preprocessing reuse is not recommended because C was not repeatably faster, and D's single-pass increment over B was below 1.20× while retaining substantially more memory.

Using the authoritative A measurement, remaining Q3–Q6 plus Alibaba direct/diagnostic single-policy work is 10.57 h with A and approximately 5.87–6.21 h with B. This saves about 4.36–4.70 h. Alibaba calibration retains its separately verified joint-DAG estimate of 0.54–2.03 h. Combined remaining wall time under B is approximately 6.41–8.24 h. These are planning estimates; the wall-clock table is the executor decision evidence.

## Gate

Benchmark status: **PASS**. Current state: `WAITING_FOR_MANUAL_EXECUTOR_DECISION`. No formal executor was switched and no Q3, Q4, Q5, Q6, or Alibaba run was started.
