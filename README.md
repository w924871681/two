# RAVM_DT experiment execution

Independent project for the supplied 2026-09-07 execution specification.
The first paper checkout and release are read-only. Exact reused files and SHA-256
digests are in `audits/provenance.json`; the original specification is archived in
`EXPERIMENT_SPEC.md`.

Python: `C:/Users/92487/anaconda3/envs/rcf-dti-py311/python.exe`.

Execution order:

1. `python scripts/bootstrap.py`
2. `python scripts/verify_repository.py`
3. `python scripts/run_smoke.py`
4. `python scripts/verify_repository.py`
5. `python scripts/run_development.py`
6. `python scripts/run_calibration.py`
7. Full pre-heldout audit and config/code freeze.
8. `python scripts/run_heldout.py`

`scripts/prepare_alibaba.py` independently checks and reads the original local
archive without writing to it. No future interpolation is performed.

All `.yaml` configurations use JSON syntax (a valid YAML subset), allowing the
standard-library parser to load their exact bytes deterministically.

Window/block and burst-definition clarifications approved by the user are in
`configs/protocol_amendments.json`. Candidate blocks partition forecast origins;
raw segment boundaries are never crossed. Multi-horizon boundary origins are
discarded when needed to keep their targets disjoint. Attack masks are shared
across methods, model seeds, and candidate settings. Burst means short contiguous
corruption within each of ten fixed raw-observation strata.

Smoke checkpoints and results are visibly prefixed `smoke` and cannot be loaded
by formal runs. Heldout generation is deferred until development and calibration
complete and a final freeze manifest passes verification.

Baseline fidelity:

- Frozen, Always-FT, raw ER, online EWC, Huber-FT, ValidationCommit: controlled baselines.
- CLeaR-Predictor: explicit predictor-only, stage-batched CLeaR framework adaptation;
  novelty/familiarity buffers, adaptive error threshold, novelty-capacity trigger,
  and online EWC. It is not a reproduction of the original autoencoder experiments.
- MER-Reg-2026: `implementation_unavailable_or_nonfaithful`; no substitute is
  reported under the original method name. MDN, adaptive target partitioning and
  XuILVQ prototype replay have not been reproduced or independently validated.
- OracleCommit: evaluation-only diagnostic; never rank as deployable.

Reference sources verified: https://arxiv.org/html/2101.00926v3 and
https://arxiv.org/html/2602.09720v1 .

Long-running jobs report progress to `logs/`. A completed smoke run is not a
formal scientific result. All negative findings and calibration failures must
remain in the final report.
