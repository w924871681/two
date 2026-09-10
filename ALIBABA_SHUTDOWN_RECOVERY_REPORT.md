# Alibaba shutdown recovery report

## Recovery decision

The interruption was a confirmed planned Windows update restart. Recovery is
approved automatically under the user-authorized external-shutdown rule because
all scientific integrity and executor-equivalence checks passed.

## Pre-recovery state

| Item | Count / result |
|---|---:|
| Frozen expected trajectories | 48,600 |
| Valid trajectories preserved | 28,755 |
| Missing trajectories | 19,845 |
| Invalid or partial trajectories | 0 |
| Duplicate scientific keys | 0 |
| Unexpected scientific keys | 0 |
| Scientific provenance/hash mismatches | 0 |
| Complete preserved workloads | 71 |
| Complete workloads to recover | 49 |
| Recovery queue | 19,845 |

The manifest is generated from 405 policies × 3 seeds × 20 calibration centers
× 2 conditions. Every preserved CSV has exactly 24 unique stages (1–24), valid
schema and metadata, consistent data/attack hashes, a valid state chain, and the
original Alibaba joint-DAG provenance. There are no temporary or half-written
formal result files. All 49 incomplete workloads contain zero formal policy
outputs, so the recovery queue consists of whole workload bundles; none of the
28,755 valid trajectories will be recomputed.

## Cache recovery

| Cache | Accepted | Invalid |
|---|---:|---:|
| Candidate cache | 34,305 | 0 |
| Evidence cache | 68,608 | 0 |
| Total relevant artifacts | 102,913 | 0 |

The audit fully deserialized the Alibaba-relevant candidate/evidence artifacts,
validated cache keys, schemas, scientific versions and numeric contents, and
found no orphan temporary artifacts. The most recent 100 artifacts of each type
also passed checksum/deserialize validation. Valid cache entries remain in
place; no global cache reset or scientific recomputation is required.

## Scientific invariants

| Artifact | SHA-256 / commit |
|---|---|
| Scientific executor commit | `d6d33075cb3afa55a24878e2343f1bc1d1c9368a` |
| Scientific core aggregate | `b462520a80d611f3311a2326effa73bc159754e9ef243cd18e10412363823c33` |
| Frozen candidate config | `4a9655cf427f41bb321dc5237008fa795f1fb3437c979206fd4784810bca74ea` |
| Frozen commit config | `1da5f249d1a8c41afcc7d49f2bd30d288e2cdabd220b7840cfc0a3903bc9bf3a` |
| Frozen baseline config | `765f58a595a156320caa3c4664657670968d4638e5bf15b7d430444b82581908` |
| Calibration protocol | `e08902bbf8edefe975b8f55be5d3aeda0dcbe033326c40f6d1dcfd9b6aa6b461` |
| Pool manifest | `f5550a641384625746ec8fd36791c37e00be5610ed67097c1c5ec69d722ee8fe` |
| Alibaba pool/data manifest | `55918806ab6b71d206a944415465d449a2d0463a5befaa8adb06c90508df5d89` |

The recovery-equivalence replay covered two complete Alibaba workloads (clean
and mixed), all 400 Proposed policies, all five ValidationCommit configurations,
and all 24 lifecycle stages. Hash/integer/categorical fields and all decisions
were exact; the maximum floating-point difference was
`9.996344030316351e-17`, below the `1e-12` limit. No scientific implementation
changed.

## Recovery execution

The execution-only recovery wrapper launches the same two original joint-DAG
workers, with the same complete `center × condition × seed` workload partition
and serial 24-stage lifecycles. Existing exact filenames are skipped by the
original executor. Resilient telemetry reports progress every 15 seconds and is
independent of scientific CSV publication.

After recovery reaches 48,600, the wrapper runs the full result audit, performs
the original Alibaba aggregation and configuration selection/freeze, and only
continues to Alibaba diagnostic, bootstrap/final aggregation, P15 and P16 when
all required checks pass. A scientific hash/config/data mismatch, non-equivalent
duplicate, protocol/leakage failure, or resume-equivalence failure stops the
queue.

Machine-readable audits:

- `audits/alibaba_calibration_exit_diagnosis.json`
- `audits/alibaba_shutdown_recovery_integrity.json`
- `audits/alibaba_shutdown_cache_recovery.json`
- `audits/alibaba_calibration_resume_equivalence.json`

The recovery commit and live PID/cache/throughput fields are recorded at launch
in `logs/alibaba_shutdown_recovery_launch.json` and
`logs/execution_status.json`.
