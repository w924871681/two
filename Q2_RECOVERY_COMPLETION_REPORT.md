# Q2 Crash Recovery Completion Report

完成时间：2026-09-09T14:29:21+08:00

## Final status

- Q2 complete trajectories: **7680 / 7680**
- Final status: **WAITING_FOR_MANUAL_POST_Q2_BENCHMARK_APPROVAL**
- Q3 formal outputs: **0**
- POST-Q2 benchmark: **not started**
- Active formal runner: **none; normal Q2 boundary exit**
- Recovery implementation commit: `e2ae48e14677ea2c6a5612a9e568e0c26624d83c`

## Failure and root cause

The original runner stopped at 6421 complete Q2 trajectories after `os.replace` raised `PermissionError [WinError 5]` while publishing `logs/execution_status.json`. The scientific trajectory CSV had already been atomically published; only its telemetry update failed. The external boundary watcher was reading `execution_status.json` every 100 ms and was the likely source of the transient Windows sharing conflict. That watcher exited with the failed runner and has been permanently disabled. No external watcher, process suspension, or process termination is used for the Q2/Q3 boundary now.

## Execution-only repair

- `core/status.py`: writes a process-unique temporary status file, flushes and closes it before replace, and retries Windows sharing violations after 50/100/200/400/800 ms. Persistent telemetry failure is logged without rolling back an already completed scientific CSV.
- `scripts/run_heldout.py`: uses the resilient telemetry writer, constructs the Q2 matrix programmatically, skips an explicit completed-key set, and honors the internal `STOP_AFTER_PHASE=Q2` gate.
- `scripts/q2_manifest.py`: defines the frozen 7680-key Q2 matrix used for recovery and auditing.
- `scripts/audit_q2_integrity.py`: performs the fail-closed Q2 boundary audit.
- `scripts/q2_recovery_freeze.py`: requires every P7 scientific/config file to retain its P7 hash while separately validating the approved execution-only recovery files.
- `scripts/resume_q2_after_crash.py`: resumes Q2 only and exits normally after the internal integrity gate.
- `tests/test_execution_status_windows_retry.py`, `tests/test_q2_manifest.py`, and `tests/test_q2_recovery_freeze.py`: five focused recovery tests passed.

The first recovery launch was rejected by the unchanged P7 freeze guard because `run_heldout.py` had an approved execution-only change. It generated zero new trajectories. The separate recovery freeze gate was then added so that all P7 scientific and configuration hashes remain mandatory while the recorded recovery executor hash is validated independently.

## Scientific equivalence and provenance

`audits/q2_resume_executor_equivalence.json` compared post-repair scratch replay with pre-crash formal Q2 trajectories for Always-FT, EWC, CLeaR-Predictor, and Proposed. Hashes, decisions, integer/categorical fields, and stage sequences were exact. The maximum floating difference was below `1.0e-16`, within the preregistered `1e-12` serialization tolerance.

Scientific core aggregate SHA-256 remained `b462520a80d611f3311a2326effa73bc159754e9ef243cd18e10412363823c33`. `core/engine.py`, `core/protocol.py`, `core/models.py`, `core/joint_dag.py`, all three frozen configuration files, and `pool_manifest.json` retained their P7 hashes. Scientific implementation, data, seeds, centers, conditions, methods, attacks, optimizers, and metrics were unchanged.

## Result preservation and recovery

The pre-crash audit verified all 6421 existing trajectory files before recovery: unique key count 6421, duplicate 0, unexpected 0, completed-prefix missing 0, and remaining frozen keys 1259. Every file was non-empty, had the complete schema, and contained exactly one copy of stages 1–24. Filename metadata and CSV metadata matched; data and attack-mask hashes matched across methods.

Recovery built the complete frozen 7680-key set and subtracted the verified completed-key set. The original 6421 Q2 files and all Q1 files were retained and skipped. Only the remaining 1259 keys were executed. No result was inferred from filename order, and no Q1/Q2 file was deleted or overwritten.

## Final Q2 integrity

The internal boundary audit `audits/q2_integrity.json` passed with:

- expected / completed / valid keys: `7680 / 7680 / 7680`
- duplicate key excess: `0`
- unexpected keys: `0`
- missing keys: `0`
- invalid, empty, partial, schema-invalid, or stage-invalid files: `0`
- temporary Q2 result files: `0`
- cross-method data or attack-hash mismatches: `0`
- P7 scientific/config hash mismatches: `0`
- Q3 formal result files: `0`
- execution status warnings during recovery: `0`
- recovery execution failures: `0`

The recovery runner exited normally through the internal phase gate at 14:29:21. The experiment is safely stopped at the Q2/Q3 boundary. No benchmark or Q3 work will start without manual approval.
