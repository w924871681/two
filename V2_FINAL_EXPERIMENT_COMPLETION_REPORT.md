# V2 Final Experiment Completion Report

## Material Passport

- Generated: 2026-09-11T23:53:14.362551+00:00
- Purpose: scientific handoff after the permanently frozen Final V2 evaluation package. This is not a paper rewrite.
- Evidence pools remain labeled and separate; no result in this report changes the frozen method.

## 1. Final scientific method state

Final method `Final_V2_SP_ShortDual` uses `V2_SP_ShortDual`, `SinglePath`, 50 adaptation steps, history capacity 12, backbone GRU, horizon 1. Scientific implementation commit: `7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3`.

## 2. Frozen V2 configuration

`kappa_rec=0.0`, `kappa_hist=0.5`, `delta_imp=2.8018237766243602e-05`, `delta_ret=0.0`, `rho=0.05`, `epsilon=5.6036475532487204e-05`. Config SHA-256: `7275a287ee4a1f4602ed0a10a67362a1a61ffa398848d4529669b0584a127d13`.

## 3. Confirmatory result

Minimal final confirmatory: 720/720 valid, verdict **CONFIRMED**. Balanced five-scenario lifecycle-MSE difference versus V1 LegacyFull: -0.000342818 [-0.00046511, -0.000235486], -9.814%.

## 4. Main six-baseline benchmark

Across the seven balanced scenarios, Proposed MSE was 0.0031489, harmful rate 0.0215538, downside 2.00059e-06, beneficial recall 0.268184, and commit rate 0.236728.
Always-FT MSE was 0.00276429 and harmful rate 0.267642; Frozen MSE was 0.00481787 with zero commits. The benchmark therefore establishes a safety–utility–plasticity tradeoff rather than unqualified predictive superiority.

## 5. Robustness severity result

Phase A executed 2160 new alpha=.05/.20 trajectories and reused 1080 exact alpha=.10 trajectories. Integrity, pairing, leakage, and reuse audits passed.

| Attack | Alpha | Proposed MSE | Harmful | Downside | Commit rate |
|---|---:|---:|---:|---:|---:|
| mixed | 0.05 | 0.00313581 | 0.0425926 | 3.33737e-06 | 0.255093 |
| mixed | 0.10 | 0.00318898 | 0.0472222 | 5.88559e-06 | 0.234259 |
| mixed | 0.20 | 0.00339905 | 0.0439815 | 1.646e-05 | 0.190741 |
| persistent_bias | 0.05 | 0.00310712 | 0.0180556 | 1.40647e-06 | 0.236574 |
| persistent_bias | 0.10 | 0.00313935 | 0.0203704 | 1.21686e-06 | 0.221296 |
| persistent_bias | 0.20 | 0.00320081 | 0.0171296 | 9.98695e-07 | 0.199074 |
| replay | 0.05 | 0.00311044 | 0.0148148 | 1.29977e-06 | 0.22963 |
| replay | 0.10 | 0.00315133 | 0.0111111 | 1.17911e-06 | 0.209722 |
| replay | 0.20 | 0.00318761 | 0.0166667 | 1.52822e-06 | 0.19537 |

The full report retains every adverse or inconclusive Proposed–baseline CI and does not use the severity trend to fit a threshold.

## 6. External Alibaba result

The exact prior 40-machine Alibaba split was reconstructed and evaluated as an external-domain transfer check: 1200/1200 trajectories, with protocol, integrity, pairing, and leakage audits PASS.

| Scenario | Method | MSE | Harmful | Downside | Commit rate |
|---|---|---:|---:|---:|---:|
| clean | Always-FT | 0.00219892 | 0.341667 | 6.52402e-06 | 1 |
| clean | ER | 0.00221461 | 0.39375 | 3.44517e-06 | 1 |
| clean | Frozen | 0.00226406 | 0 | 0 | 0 |
| clean | Huber-FT | 0.00223555 | 0.35625 | 7.61486e-06 | 1 |
| clean | Proposed | 0.00223981 | 0.00763889 | 1.56258e-07 | 0.0611111 |
| mixed_a010_both | Always-FT | 0.00236695 | 0.469444 | 8.27518e-05 | 1 |
| mixed_a010_both | ER | 0.00230569 | 0.503819 | 1.8486e-05 | 1 |
| mixed_a010_both | Frozen | 0.00226406 | 0 | 0 | 0 |
| mixed_a010_both | Huber-FT | 0.00229462 | 0.480208 | 3.27386e-05 | 1 |
| mixed_a010_both | Proposed | 0.00228428 | 0.0649306 | 3.78829e-06 | 0.155208 |

## 7. Mechanism evidence

The consolidated evidence supports selective commit for transition safety and bounded temporal verification as the final mechanism. RecentOnly is insufficient under corruption; long history can create stale lockout; adaptive realignment was not selected.

## 8. Parameter sensitivity

The existing 16-cell kappa table was reused without rerunning. The frozen selected point is `(kappa_rec=0, kappa_hist=0.5)` on the observed safety–utility–plasticity frontier; it is not claimed to be universal.

## 9. Maintenance cost

Proposed runtime/stage was 0.184537 s, peak GPU memory 5.57439e+07 bytes, and persistent buffer 155520 bytes in the final benchmark.

## 10. Negative findings

- Proposed lifecycle MSE was worse than Always-FT by 0.000384618 [0.000325426, 0.000442497] (13.9138%).
- Lower harmful transition frequency is partly purchased with lower commit rate and beneficial recall than always-commit baselines.
- Verification-only and severity results may contain local adverse or inconclusive intervals; the detailed reports preserve them.
- Adaptive realignment did not show a clear advantage sufficient for selection.
- The selected configuration is protocol-specific and is not universally optimal.

## 11. Unsupported mechanisms removed

Block-consensus candidate construction: **CONTRADICTED**. Trimmed state-delta aggregation: **CONTRADICTED / unsupported**. Adaptive realignment: **not selected / no clear advantage**.

## 12. Final evidence map by research question

| RQ | Section | Evidence | Boundary |
|---|---|---|---|
| RQ1 | 5.2 | Final confirmatory and six-baseline benchmark | Safety–utility–plasticity tradeoff, not overall best MSE. |
| RQ2 | 5.3 | Frozen alpha .05/.10/.20 severity sweep | Robustness trend only; no post-hoc threshold selection. |
| RQ3 | 5.4 | Confirmatory stationary/gradual/abrupt/recurring streams | Benign-drift plasticity is supported relative to V1, with remaining active-baseline accuracy tradeoffs. |
| RQ4 | 5.5 | Development structural diagnosis and component removals | Supports bounded temporal verification/selective commit; rejects abandoned V1 components. |
| RQ5 | 5.6 | Frozen kappa table and final runtime/memory | Sensitivity and maintenance cost; generality added only after Phase E. |
| RQ6 | 5.7 | Alibaba exact-split external-domain evaluation | External transfer, never fresh external confirmation. |

## 13. Experiments complete

Final V2 confirmatory; six-baseline final benchmark; robustness severity sweep; mechanism/sensitivity consolidation; and Alibaba external evaluation when provenance passed.

## 14. Experiments intentionally not run

No new method, kappa, history-capacity, or baseline search; no CLeaR fresh benchmark; no MER-Reg; no OracleCommit ranking. Phase E is the only authorized architecture/horizon extension.

## 15. Exact remaining experiments

None in the authorized package. The workflow stops for manual scientific review.

## 16. Recommended final Section 5 structure

5.2 Overall safety–utility–plasticity; 5.3 Robustness severity; 5.4 Benign drift; 5.5 Mechanisms; 5.6 Sensitivity and Maintenance Cost; 5.7 External production-trace transfer.

## 17. Recommended claims

Final V2 improves on V1 LegacyFull and sharply reduces harmful transitions/downside relative to active always-commit baselines while retaining nonzero adaptation. Severity and external-domain claims must follow their complete scenario-specific tables.

## 18. Forbidden claims

Do not claim universal lifecycle-loss superiority, risk-free adaptation, universal kappa optimality, fresh Alibaba confirmation, or that abandoned V1 components contribute to Final V2.

## 19. Files, hashes, and commits

- `V2_FINAL_MINIMAL_CONFIRMATORY_REPORT.md`: `1e4787ffc96c5144f8693f103f1e481884e6b13ae4aa4b0a566902927d4435e0`
- `V2_FINAL_BASELINE_BENCHMARK_REPORT.md`: `bf7afa27797bfecf9e867a2f5b656258c1bcf577f032c5414624d818f00fbf91`
- `V2_ROBUSTNESS_SEVERITY_REPORT.md`: `7f224a42dd061c19a270e2147474c34da16486f871403e94a7bd1d2be808ad0d`
- `V2_MECHANISM_AND_SENSITIVITY_REPORT.md`: `dce4ea39040f36b1aff57cfd68e1d148dea13380915a6d5261f00a0474509b53`
- `V2_ALIBABA_EXTERNAL_TRACE_REPORT.md`: `8029bb085276341f4bde73ee25548fac2563887efb492efc2f999892ecb243cf`
- `V2_ARCHITECTURE_HORIZON_GENERALITY_REPORT.md`: `27e05f6098378d5ae9f48d006f01983a8470efeebaf6e0b37cfa39a6815df3ee`
- Repository HEAD at handoff generation: `1b84fbcff8c47fb76dafc313f536f04ba8a9287b`
- Final scientific implementation commit: `7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3`

## 20. Final status

## Architecture and Horizon Generality

Phase E completed 1800/1800 new trajectories and reused 360 GRU-H1 trajectories across MLP/TCN/GRU, H=1/4, 20 fixed centers, 3 seeds, clean/mixed, and Proposed/Always-FT/Frozen. Expected point ordering held in 12/12 cells. Recommended Section 5.6 title: **Sensitivity, Generality, and Maintenance Cost**. Full positive, negative, and inconclusive evidence is in `V2_ARCHITECTURE_HORIZON_GENERALITY_REPORT.md`.

Final state: **V2_FINAL_EXPERIMENT_PACKAGE_WITH_GENERALITY_COMPLETE**. Stop and wait for manual scientific review.
