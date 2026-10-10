# V2 Mechanism and Sensitivity Report

## Material Passport

- Evidence type: consolidation of completed development, calibration, and final benchmark artifacts. Phase C generated no scientific trajectories.
- Structural selection: `V2_SP_ShortDual`; final calibrated gate: kappa_rec=0.0, kappa_hist=0.5.
- Development, calibration, and final-test estimates remain separate; they are not pooled.

## 1. Evidence provenance

- `results_v2_dev\development\development_summary.csv` SHA-256: `3820279a72f532ce659fcdf820cd10f00d3147718cc9b49267a8467a936ca319`
- `results_v2_dev\v2_1_security_calibration\security_pareto_table.csv` SHA-256: `3725847aed1933ce314708d555b672501f50349687ddf603c234fcdaacfcd414`
- `results_v2_final_baselines\final_main_table.csv` SHA-256: `873f610f5d5e4825ecbd065a40ff86428e2266f89cdbd9970ad28f76534b02aa`
- `audits_v2_dev\v2_structural_selection.json` SHA-256: `d1da9f88c425330ca29465474b2eae19d9ce2515ee3b6af5bbfaa1607114fdce`
- `audits_v2_dev\v2_1_security_aware_calibration.json` SHA-256: `86b667efe0fa2f8ca84fb7f23ed5c6e30d76576107d11efb404fcf822d8a4c4f`

## 2–4. RecentOnly, long-history dual evidence, and short-history Final V2

Development estimates below diagnose structure under the frozen development protocol. V1_SP_StaticDual is the long-history SinglePath reference; V2_SP_ShortDual bounds history at 12; D0 removes historical evidence.

| Structure | Scenario | MSE (95% CI) | Harmful (95% CI) | Downside (95% CI) | Beneficial recall | Commit rate | Max retain streak |
|---|---|---:|---:|---:|---:|---:|---:|
| D0_SP_RecentOnly | stationary | 0.00269886 [0.00135238, 0.00419662] | 0.0444444 [0.0111111, 0.0777778] | 2.55836e-06 [3.83693e-07, 4.73303e-06] | 0.228849 | 0.216667 | 10.8 |
| D0_SP_RecentOnly | gradual | 0.00345601 [0.0014651, 0.00580023] | 0.0166667 [0.00277778, 0.0361111] | 1.65781e-06 [4.66457e-08, 3.55183e-06] | 0.383916 | 0.358333 | 6.73333 |
| D0_SP_RecentOnly | abrupt | 0.00339693 [0.00113622, 0.00568363] | 0.0416667 [0.0138889, 0.0694444] | 2.34743e-06 [4.89836e-07, 4.20502e-06] | 0.349276 | 0.322222 | 7.2 |
| D0_SP_RecentOnly | recurring | 0.00350224 [0.00249586, 0.00487566] | 0.0166667 [0.00555556, 0.0305556] | 5.81331e-07 [9.87461e-08, 1.06392e-06] | 0.466775 | 0.386111 | 5.6 |
| D0_SP_RecentOnly | mixed_a010_both | 0.00333523 [0.00244345, 0.00427845] | 0.125694 [0.100694, 0.152083] | 2.11867e-05 [1.66725e-05, 2.56557e-05] | 0.469006 | 0.41875 | 5.45 |
| D0_SP_RecentOnly | persistent_a010_verification_only | 0.00326946 [0.00236715, 0.00422702] | 0.0409722 [0.0263889, 0.0569444] | 3.14555e-06 [1.46311e-06, 5.08985e-06] | 0.40831 | 0.369444 | 6.05 |
| D0_SP_RecentOnly | replay_a010_verification_only | 0.00327044 [0.00237665, 0.0042243] | 0.0277778 [0.0173611, 0.0388889] | 1.73048e-06 [7.62248e-07, 3.01297e-06] | 0.333816 | 0.3 | 8.21667 |
| V1_SP_StaticDual | stationary | 0.00272183 [0.00135933, 0.00424571] | 0.0222222 [0.00277778, 0.0416667] | 8.251e-07 [7.24362e-09, 1.64958e-06] | 0.175379 | 0.152778 | 12.8 |
| V1_SP_StaticDual | gradual | 0.00367252 [0.00157565, 0.00604442] | 0.0111111 [0.00277778, 0.0194444] | 9.93825e-07 [4.66457e-08, 2.22885e-06] | 0.263281 | 0.247222 | 8.53333 |
| V1_SP_StaticDual | abrupt | 0.00369229 [0.00119432, 0.00619027] | 0.0277778 [0.00555556, 0.05] | 2.0741e-06 [4.04966e-07, 3.74324e-06] | 0.277845 | 0.258333 | 8.13333 |
| V1_SP_StaticDual | recurring | 0.00424442 [0.00288277, 0.00643388] | 0.00277778 [0, 0.00833333] | 1.46366e-07 [0, 4.39099e-07] | 0.344515 | 0.283333 | 6.73333 |
| V1_SP_StaticDual | mixed_a010_both | 0.0036572 [0.00262324, 0.00472339] | 0.0458333 [0.0319444, 0.0618056] | 5.89993e-06 [3.27724e-06, 8.95616e-06] | 0.305512 | 0.246528 | 7.91667 |
| V1_SP_StaticDual | persistent_a010_verification_only | 0.00363435 [0.00258493, 0.00472338] | 0.0173611 [0.00833333, 0.0277778] | 1.52188e-06 [4.98846e-07, 2.73257e-06] | 0.271544 | 0.244444 | 8.58333 |
| V1_SP_StaticDual | replay_a010_verification_only | 0.0036215 [0.00259167, 0.00470133] | 0.0159722 [0.00763889, 0.0256944] | 7.92051e-07 [2.65964e-07, 1.42143e-06] | 0.238572 | 0.215972 | 9.58333 |
| V2_SP_ShortDual | stationary | 0.00271835 [0.0013628, 0.00422679] | 0.0166667 [0.00277778, 0.0361111] | 7.72727e-07 [7.24362e-09, 1.56564e-06] | 0.179352 | 0.15 | 13.8667 |
| V2_SP_ShortDual | gradual | 0.0035648 [0.00149661, 0.00594728] | 0.00833333 [0.00277778, 0.0138889] | 1.00347e-06 [4.66457e-08, 2.23849e-06] | 0.296498 | 0.275 | 8 |
| V2_SP_ShortDual | abrupt | 0.00351721 [0.00114144, 0.00589299] | 0.0277778 [0.00555556, 0.05] | 1.45469e-06 [1.5338e-07, 3.14186e-06] | 0.297576 | 0.272222 | 8 |
| V2_SP_ShortDual | recurring | 0.00384042 [0.00260081, 0.00566104] | 0 [0, 0] | 0 [0, 0] | 0.368052 | 0.3 | 7.2 |
| V2_SP_ShortDual | mixed_a010_both | 0.00348565 [0.00252776, 0.00450268] | 0.0444444 [0.0305556, 0.0590278] | 5.50574e-06 [3.08183e-06, 8.43094e-06] | 0.326068 | 0.251389 | 8.3 |
| V2_SP_ShortDual | persistent_a010_verification_only | 0.00340551 [0.00246531, 0.00439191] | 0.0173611 [0.00902778, 0.0277778] | 2.25771e-06 [7.08623e-07, 4.12801e-06] | 0.290038 | 0.258333 | 8.18333 |
| V2_SP_ShortDual | replay_a010_verification_only | 0.00344554 [0.00247654, 0.00447445] | 0.0159722 [0.00763889, 0.0256944] | 1.43647e-06 [4.16018e-07, 2.86923e-06] | 0.262247 | 0.234722 | 9.23333 |

RecentOnly is insufficient because removing historical evidence raises transition risk under mixed corruption even when it improves utility/plasticity. Long unbounded history can retain stale pre-drift evidence and prolong retain streaks. The selected bounded 12-block history preserves a historical check while reducing that lockout. These are mechanism interpretations of the frozen comparisons, not new causal components fitted after final testing.

## 5. ValidationCommit

ValidationCommit committed 0 of stages, had MSE 0.00481787, harmful rate 0, and beneficial recall 0. Final Proposed committed 0.236728, had MSE 0.0031489, harmful rate 0.0215538, and beneficial recall 0.268184. Thus a retain-all validation anchor provides safety but no useful transition behavior; selective temporal verification is required to retain nonzero adaptation.

## 6. Adaptive variants

- `V3_SP_AdaptiveDual`: 8 frozen structural settings; scenario MSE range 0.0027215–0.00418398, harmful range 0.00277778–0.0527778. It was not selected because the constrained frozen selection found no clear advantage over the simpler bounded static dual-evidence structure.
- `V4_SP_AdaptiveDual_NoRealign`: 8 frozen structural settings; scenario MSE range 0.0027215–0.00418426, harmful range 0.00277778–0.0527778. It was not selected because the constrained frozen selection found no clear advantage over the simpler bounded static dual-evidence structure.

## 7. Removed unsupported components

| Component | Final assessment | Evidence consequence |
|---|---|---|
| Block-consensus candidate construction | CONTRADICTED | The V1 diagnosis did not support retaining the multi-path candidate mechanism; Final V2 uses SinglePath. |
| Trimmed state-delta aggregation | CONTRADICTED / unsupported | It did not provide the claimed benefit and was removed. |
| Adaptive realignment | Not selected / no clear advantage | V3/V4 did not justify extra mechanism complexity under the frozen constrained rule. |
| Selective commit | SUPPORTED for transition safety | Final benchmark shows much lower harmful frequency/downside than active always-commit baselines while keeping nonzero commits. |
| Bounded temporal verification | SUPPORTED as final mechanism | Short history was selected, calibrated, and confirmed without reopening method design. |

## 8. Kappa sensitivity

The complete frozen 16-configuration table is reproduced without rerunning or reselecting the grid.

| Config | kappa_rec | kappa_hist | Balanced MSE | Mixed harmful | Mixed downside | Persistent harmful | Replay harmful | Beneficial recall | Commit rate | Feasible | Pareto | Selected |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| kr0_kh0 | 0 | 0 | 0.00316193 | 0.08125 | 1.0248e-05 | 0.0243056 | 0.025 | 0.369355 | 0.320556 | False | True | False |
| kr0_kh0.5 | 0 | 0.5 | 0.00326789 | 0.0354167 | 4.16249e-06 | 0.0125 | 0.0152778 | 0.284808 | 0.23625 | True | True | True |
| kr0_kh1 | 0 | 1 | 0.00337742 | 0.0166667 | 1.1055e-06 | 0.00902778 | 0.00625 | 0.200228 | 0.170833 | True | True | False |
| kr0_kh1.5 | 0 | 1.5 | 0.00354604 | 0.00763889 | 5.18643e-07 | 0.00486111 | 0.00277778 | 0.148715 | 0.123889 | True | True | False |
| kr0.5_kh0 | 0.5 | 0 | 0.00320921 | 0.0534722 | 6.04223e-06 | 0.0152778 | 0.0159722 | 0.290963 | 0.249861 | False | True | False |
| kr0.5_kh0.5 | 0.5 | 0.5 | 0.00330991 | 0.03125 | 2.54774e-06 | 0.00694444 | 0.00902778 | 0.238571 | 0.198056 | True | True | False |
| kr0.5_kh1 | 0.5 | 1 | 0.00340918 | 0.0131944 | 1.10715e-06 | 0.00416667 | 0.00555556 | 0.180477 | 0.150278 | True | True | False |
| kr0.5_kh1.5 | 0.5 | 1.5 | 0.00356613 | 0.00555556 | 3.13162e-07 | 0.00277778 | 0.00277778 | 0.13083 | 0.108472 | True | True | False |
| kr1_kh0 | 1 | 0 | 0.00327183 | 0.0430556 | 4.57772e-06 | 0.0118056 | 0.00833333 | 0.22774 | 0.19375 | True | True | False |
| kr1_kh0.5 | 1 | 0.5 | 0.00337134 | 0.0243056 | 2.14755e-06 | 0.00486111 | 0.00555556 | 0.194103 | 0.161806 | True | True | False |
| kr1_kh1 | 1 | 1 | 0.00346519 | 0.00972222 | 7.66445e-07 | 0.00347222 | 0.00347222 | 0.146839 | 0.122083 | True | True | False |
| kr1_kh1.5 | 1 | 1.5 | 0.00362465 | 0.00416667 | 2.97555e-07 | 0.00208333 | 0.000694444 | 0.108264 | 0.0901389 | True | True | False |
| kr1.5_kh0 | 1.5 | 0 | 0.00334495 | 0.0340278 | 3.2443e-06 | 0.00555556 | 0.00555556 | 0.171207 | 0.147222 | True | True | False |
| kr1.5_kh0.5 | 1.5 | 0.5 | 0.00343521 | 0.01875 | 1.59181e-06 | 0.00208333 | 0.00347222 | 0.156389 | 0.132222 | True | True | False |
| kr1.5_kh1 | 1.5 | 1 | 0.0035118 | 0.00763889 | 4.8405e-07 | 0.00277778 | 0.00208333 | 0.122676 | 0.103056 | True | True | False |
| kr1.5_kh1.5 | 1.5 | 1.5 | 0.00365403 | 0.00138889 | 6.37438e-08 | 0.000694444 | 0 | 0.0929902 | 0.0763889 | True | True | False |

## 9. Safety–utility–plasticity frontier

Lower kappa values open more transitions and improve plasticity but can violate the frozen risk rule; larger historical penalties reduce harmful transitions while reducing beneficial recall and commit rate. The selected `(0, 0.5)` point is the frozen constrained choice for this protocol, not a universally optimal configuration.

## 10. Runtime / memory

| Method | Runtime/stage (s) | Peak GPU bytes | Persistent buffer bytes |
|---|---:|---:|---:|
| Proposed | 0.184537 | 5.57439e+07 | 155520 |
| Always-FT | 0.249596 | 5.55996e+07 | 0 |
| ER | 0.262024 | 9.83173e+07 | 302400 |
| EWC | 0.504161 | 5.82605e+07 | 44808 |
| Huber-FT | 0.250123 | 5.55996e+07 | 0 |
| ValidationCommit | 0.251534 | 6.77274e+07 | 0 |
| Frozen | 0.004404 | 2.54961e+07 | 0 |

Final Proposed has a persistent evidence buffer of 155,520 bytes in the primary benchmark. It is faster per stage than Always-FT, ER, EWC, Huber-FT, and ValidationCommit in the recorded two-worker run, while Frozen remains the trivial lowest-cost anchor.

## 11. Mechanism conclusions

Bounded historical evidence plus selective commit is the supported final mechanism. Recent-only evidence leaves excess safety risk; unbounded historical evidence can become stale; adaptive realignment did not demonstrate enough added value; block-consensus and trimmed aggregation are not retained contributions.

## 12. Claim boundary

Allowed: Final V2 uses a simpler SinglePath candidate with bounded temporal verification to trade some active-adaptation accuracy for substantially safer state transitions and nonzero plasticity. Forbidden: every original V1 component contributes; adaptive realignment is necessary; the selected kappa is universal; ValidationCommit alone proves useful adaptation.
