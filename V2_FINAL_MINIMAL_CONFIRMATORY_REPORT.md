# V2 Final Minimal Confirmatory Report

Generated: 2026-09-11T09:14:14.447504+00:00

## Material Passport

This is the single frozen analysis of 720 fresh confirmatory trajectories: 30 centers × 3 model seeds × 4 preassigned streams × 2 methods. Every trajectory contains 24 unique lifecycle stages. Statistical inference treats center as the unit and averages model seeds within center; all paired 95% CIs use 4,000 center-cluster bootstrap replicates with seed 2904.

- Final method: `V2_SP_ShortDual`, SinglePath, 50 adaptation steps, history capacity 12, κ_rec=0, κ_hist=0.5.
- Scientific implementation commit: `7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3`.
- Final config SHA-256: `7275a287ee4a1f4602ed0a10a67362a1a61ffa398848d4529669b0584a127d13`.
- Confirmatory manifest SHA-256: `b4428cf870a5bf52aafb5b9b8d74176ea95fb2654f995397f2aa13f8b56430fe`.
- Analysis plan SHA-256: `7cdcafbfbca4e529429a3bc00af3865d23b7f3949a1e5b868d1341c96621ba84`.
- First heldout access: `2026-09-11T08:40:49.736213+00:00`; first materialization: `2026-09-11T08:40:55.443142+00:00`.
- Environment: Python 3.11.15, PyTorch 2.5.1+cu121, CUDA 12.1, NVIDIA GeForce RTX 3060 Laptop GPU.

## Integrity and leakage

Integrity **PASS**: expected/valid=720/720, missing=0, duplicate=0, unexpected=0, partial/invalid=0, stage rows=17280. Decision-order errors=0; state-chain errors=0; data/attack/service hash mismatch groups=0. Leakage audit: **PASS**. Service data remained reachable only after the immutable decision token.

Center-to-regime assignment was frozen as `REGIMES[(center_id-14000) % 4]`: stationary 14000,14004,…; gradual 14001,14005,…; abrupt 14002,14006,…; recurring 14003,14007,… .

## Primary balanced lifecycle MSE

Final V2=0.003150330528, V1 LegacyFull=0.003493148176. Paired Final V2−V1 difference=-0.0003428176484 [-0.0004651098769, -0.0002354862168], relative difference=-9.814%. The primary CI upper bound is below zero.

## Scenario results

All differences are Final V2−V1 paired center-cluster estimates. Harmful/downside, beneficial recall, and commit columns report paired differences and 95% CI.

| Scenario | V2 MSE | V1 MSE | Δ lifecycle MSE [95% CI] | Δ harmful [95% CI] | Δ downside [95% CI] | Δ beneficial recall [95% CI] | Δ commit [95% CI] |
|---|---:|---:|---:|---:|---:|---:|---:|
| stationary | 0.002082197567 | 0.002248780453 | -0.0001665828863 [-0.0002376594883, -9.026151859e-05] | 0.005208333333 [-0.006944444444, 0.015625] | 3.369271124e-07 [6.005004454e-08, 6.47149491e-07] | 0.1290809117 [0.08131760882, 0.181717652] | 0.1111111111 [0.07465277778, 0.1510416667] |
| gradual | 0.002658832262 | 0.00288875699 | -0.0002299247274 [-0.0003965112863, -8.143929153e-05] | 0.01215277778 [0.003472222222, 0.02083333333] | 6.571089115e-07 [4.621708488e-08, 1.327308655e-06] | 0.003313821339 [-0.03453631762, 0.04510147553] | 0.008680555556 [-0.03125, 0.04861111111] |
| abrupt | 0.003847964221 | 0.004334631832 | -0.0004866676113 [-0.0009694415384, -0.0001540070126] | -0.007936507937 [-0.01587301587, 0.001984126984] | -4.804982353e-07 [-2.100815884e-06, 6.89188522e-07] | 0.08259247872 [0.003030392466, 0.1652443256] | 0.07936507937 [0.001984126984, 0.1507936508] |
| recurring | 0.00397368307 | 0.004492392227 | -0.0005187091576 [-0.0008425236307, -0.0002244036064] | 0.007936507937 [-0.007936507937, 0.02777777778] | 2.026553534e-06 [1.832248393e-08, 4.150505109e-06] | 0.03393150178 [-0.04263364847, 0.1032297014] | 0.03571428571 [-0.03571428571, 0.1011904762] |
| mixed_a010_both | 0.003188975521 | 0.00350117938 | -0.0003122038592 [-0.0004635824921, -0.0001864361387] | -0.006944444444 [-0.01990740741, 0.006018518519] | 5.992788593e-08 [-2.185474198e-06, 2.353523546e-06] | 0.07074700426 [0.03743575192, 0.1045039857] | 0.02314814815 [-0.004166666667, 0.05138888889] |
| persistent_a010_verification_only | 0.003139347302 | 0.003457085975 | -0.0003177386736 [-0.0004606734779, -0.0001950908606] | 0.001851851852 [-0.00787037037, 0.01203703704] | 5.633749997e-07 [-1.094158546e-07, 1.320765412e-06] | 0.02191456421 [-0.003430485391, 0.04922663168] | 0.02638888889 [-0.000462962963, 0.05462962963] |
| replay_a010_verification_only | 0.003151325976 | 0.003460222392 | -0.000308896416 [-0.0004512573355, -0.0001889842146] | -0.005555555556 [-0.01157407407, -0.000462962963] | 9.208866956e-08 [-5.842035683e-07, 7.370302962e-07] | 0.05151169438 [0.01466109419, 0.08823493171] | 0.04398148148 [0.01157407407, 0.07592592593] |

The machine-readable scenario table also reports MAE, conditional harmful among commits, and maximum retain streak with center-cluster CIs. Absolute safety passed=true against harmful≤0.05 and downside≤5.60364755325e-05 for mixed, persistent verification-only, and replay verification-only. Relative verification safety passed=true.

## Benign drift and plasticity

Benign lifecycle-MSE regimes with a wholly adverse paired CI: `[]`. Balanced beneficial-recall difference=0.06393314355 [0.03831544839, 0.09056881463]. Fresh excess-loss/recovery uses the pre-access frozen two-method diagnostic: V1 is the contemporaneous reference envelope, so it remains separate from development recovery estimates that used Frozen/Always-FT. Plasticity clear-favorable evidence=true.

Seed-wise balanced MSE differences: `{"7311": -0.00029933839244872067, "7312": -0.00044058232528966024, "7313": -0.0002885322273704353}`. Across 30 centers, median paired difference=-0.0002114014601, range=[-0.001724509083, 4.018728739e-05], favorable fraction=0.967.

## Evidence pools and replay discordance

Development, calibration, and fresh confirmatory evidence remain separate. Development post-calibration GO-5 retained the replay adverse relative-safety signal (verdict `NO-GO`); V2.1 calibration found 14/16 feasible configurations and selected `kr0_kh0.5` with GO-5 PASS. Fresh replay resolution is **C**: A supports the development adverse signal, B supports calibration acceptable safety, and C remains inconclusive under the frozen rule.

Other V1 baselines are prior/development evidence only. No fresh paired superiority claim is made against Always-FT, ER, EWC, Huber-FT, ValidationCommit, Frozen, or CLeaR.

## Negative and inconclusive findings

Any confidence interval crossing zero remains inconclusive and is not described as equivalence. Any adverse regime, relative-safety result, or failed plasticity criterion is retained in the tables and in the verdict audit. This fresh pool will not be used to modify or recalibrate V2.

## Claim boundary and final verdict

Allowed claim: the frozen Final V2 is **CONFIRMED** relative to V1 LegacyFull on this predeclared 30-center minimal fresh confirmatory matrix, under the exact endpoint and safety rules above. Forbidden claims include fresh superiority over baselines not rerun here, pooled inference across development/calibration/heldout, or proof of equivalence from a CI crossing zero.

**Final verdict: CONFIRMED.**
