# Final Scientific Synthesis

Generated from frozen formal results: 2026-09-10T15:55:55

## Scope, provenance, and interpretation

This report is a scientific synthesis of already completed formal results. It did not run a model, create a trajectory, change a threshold, select a new parameter, or modify any frozen configuration. The only additional calculations are deterministic grouping, relative percentages, and the same preregistered 4,000-replicate center-cluster bootstrap applied to existing formal CSV rows for Q3 regime and Q4 ablation contrasts that were not separately printed in the final tables.

Paired differences are **Proposed − reference**. For MSE, harmful frequency, and downside, a negative value favors Proposed. Reported 95% intervals use centers as the resampling unit and average seeds/stages within center before resampling. Relative percentages are point-estimate ratios; their uncertainty is represented by the accompanying absolute paired CI. OracleCommit is an offline diagnostic and is not treated as a deployable baseline.

| Frozen artifact | Identity |
|---|---|
| Final implementation commit | `0a21cf6f7bdf068ab64b8e5ef0f5e2e8bfb95e2e` |
| Scientific executor commit | `d6d33075cb3afa55a24878e2343f1bc1d1c9368a` |
| Candidate config SHA-256 | `4a9655cf427f41bb321dc5237008fa795f1fb3437c979206fd4784810bca74ea` |
| Commit config SHA-256 | `1da5f249d1a8c41afcc7d49f2bd30d288e2cdabd220b7840cfc0a3903bc9bf3a` |
| Baseline config SHA-256 | `765f58a595a156320caa3c4664657670968d4638e5bf15b7d430444b82581908` |
| Final audit | PASS; 4,000 bootstrap replicates; P15 PASS; P16 PASS |

| Question | Formal execution scale | Stage rows / role |
|---|---|---|
| Q1 | 1,620 trajectories = 3 seeds × 30 centers × 2 conditions × 9 methods | 38,880 |
| Q2 | 7,680 trajectories = 3 seeds × 20 centers × 16 attack cells × 8 deployable methods | 184,320 |
| Q3 | 810 clean trajectories reused deterministically from Q1 = 3 × 30 × 9 | 19,440; no new model execution |
| Q4 | 360 trajectories = 3 seeds × 10 centers × 2 conditions × 6 variants | 8,640 |
| Q5 | 660 sensitivity + 1,800 generality + 400 runtime = 2,860 trajectories | 68,640 |
| Q6 | 2,160 direct-transfer + 480 calibrated diagnostic = 2,640 evaluation trajectories | 63,360; plus 48,600 calibration trajectories |

## Q1 — Overall lifecycle accuracy and update safety

**Experimental question.** Does Proposed improve lifecycle prediction while reducing harmful deployment decisions under clean and mixed operation?

| Condition | Method | Lifecycle MSE [95% CI] | Lifecycle MAE [95% CI] | Harmful | Downside | Worst-10% MSE | CVaR90 center MSE | Beneficial recall | Commit |
|---|---|---|---|---|---|---|---|---|---|
| clean | Proposed | 0.003895 [0.002803, 0.005066] | 0.045653 [0.038497, 0.052951] | 0.017130 | 8.606e-07 | 0.012467 | 0.010635 | 0.245748 | 0.211111 |
| clean | Always-FT | 0.003112 [0.002268, 0.004024] | 0.040857 [0.034706, 0.047163] | 0.237963 | 2.836e-05 | 0.009630 | 0.008227 | 1.000000 | 1.000000 |
| clean | ER | 0.003296 [0.002375, 0.004285] | 0.042175 [0.035684, 0.048802] | 0.162037 | 1.454e-05 | 0.009850 | 0.008647 | 1.000000 | 1.000000 |
| clean | CLeaR-Predictor | 0.003694 [0.002721, 0.004736] | 0.044866 [0.038301, 0.051592] | 0.209722 | 0.000213 | 0.011010 | 0.009661 | 1.000000 | 0.474074 |
| clean | ValidationCommit | 0.005241 [0.003654, 0.006942] | 0.053255 [0.044398, 0.062318] | 0 | 0 | 0.018125 | 0.015082 | 0 | 0 |
| clean | Frozen | 0.005241 [0.003654, 0.006942] | 0.053255 [0.044398, 0.062318] | 0 | 0 | 0.018125 | 0.015082 | NA | 0 |
| mixed | Proposed | 0.003981 [0.002873, 0.005160] | 0.046229 [0.039033, 0.053580] | 0.037500 | 4.006e-06 | 0.012625 | 0.010723 | 0.284483 | 0.205556 |
| mixed | Always-FT | 0.003266 [0.002410, 0.004183] | 0.042149 [0.036073, 0.048318] | 0.423611 | 0.000123 | 0.010019 | 0.008426 | 1.000000 | 1.000000 |
| mixed | ER | 0.003346 [0.002428, 0.004320] | 0.042641 [0.036186, 0.049161] | 0.248611 | 2.699e-05 | 0.009862 | 0.008738 | 1.000000 | 1.000000 |
| mixed | CLeaR-Predictor | 0.004851 [0.003954, 0.005791] | 0.053815 [0.048740, 0.059054] | 0.165741 | 0.000489 | 0.012243 | 0.010187 | 1.000000 | 0.334722 |
| mixed | ValidationCommit | 0.005241 [0.003654, 0.006942] | 0.053255 [0.044398, 0.062318] | 0 | 0 | 0.018125 | 0.015082 | 0 | 0 |
| mixed | Frozen | 0.005241 [0.003654, 0.006942] | 0.053255 [0.044398, 0.062318] | 0 | 0 | 0.018125 | 0.015082 | NA | 0 |

| Condition | Reference | Metric | Paired Δ [95% CI] | Relative Δ |
|---|---|---|---|---|
| clean | Always-FT | MSE | 0.000783 [0.000499, 0.001113] | +25.2% |
| clean | Always-FT | harmful | -0.220833 [-0.250463, -0.190741] | -92.8% |
| clean | Always-FT | downside | -2.750e-05 [-4.684e-05, -1.403e-05] | -97.0% |
| clean | ValidationCommit | MSE | -0.001346 [-0.001983, -0.000752] | -25.7% |
| clean | ValidationCommit | harmful | 0.017130 [0.010185, 0.025000] | undefined (reference = 0) |
| clean | ValidationCommit | downside | 8.606e-07 [4.050e-07, 1.415e-06] | undefined (reference = 0) |
| mixed | Always-FT | MSE | 0.000715 [0.000427, 0.001039] | +21.9% |
| mixed | Always-FT | harmful | -0.386111 [-0.410660, -0.361574] | -91.1% |
| mixed | Always-FT | downside | -0.000119 [-0.000176, -7.560e-05] | -96.7% |
| mixed | ValidationCommit | MSE | -0.001260 [-0.001871, -0.000690] | -24.0% |
| mixed | ValidationCommit | harmful | 0.037500 [0.029167, 0.046296] | undefined (reference = 0) |
| mixed | ValidationCommit | downside | 4.006e-06 [2.536e-06, 5.732e-06] | undefined (reference = 0) |

Proposed reduced harmful frequency relative to Always-FT by 92.8% in clean and 91.1% in mixed operation; downside fell by 97.0% and 96.7%. Those safety gains came with MSE increases of 25.2% and 21.9%, respectively. Worst-10% and CVaR90 were also higher than Always-FT/ER. Commit rate was only 21.1% clean and 20.6% mixed, and beneficial-commit recall was 24.6% and 28.4%.

**Verdict: PARTIALLY_SUPPORTED.** Proposed provides a large, statistically clear safety improvement over always-updating adaptive baselines and materially improves MSE over retain-all Frozen/ValidationCommit. The unqualified lifecycle-loss claim is contradicted by Always-FT, EWC, and ER, while the zero-commit ValidationCommit/Frozen controls remain safer on harmful/downside by construction. The safety result therefore cannot be presented as simultaneous best accuracy and best safety.

## Q2 — Security under corruption

**Experimental question.** Across attack type, corruption fraction, and attack location, does Proposed limit harmful updates and clean-to-attack degradation without sacrificing lifecycle loss?

| Attack | α | Location | P MSE | P clean→attack ΔMSE | Always-FT clean→attack ΔMSE | P−Always-FT MSE [95% CI] | P harmful | P−Always-FT harmful [95% CI] | P downside | P−Always-FT downside [95% CI] | P commit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| burst | 0.05 | both | 0.003858 | 6.192e-05 | 7.944e-05 | 0.000746 [0.000414, 0.001133] | 0.047917 | -0.290972 [-0.322917, -0.261111] | 3.093e-06 | -6.411e-05 [-0.000107, -3.340e-05] | 0.227083 |
| burst | 0.10 | both | 0.003948 | 0.000152 | 0.000225 | 0.000690 [0.000365, 0.001064] | 0.061806 | -0.362500 [-0.395833, -0.331944] | 8.003e-06 | -0.000120 [-0.000186, -7.050e-05] | 0.200000 |
| burst | 0.20 | both | 0.004203 | 0.000407 | 0.000782 | 0.000389 [6.919e-05, 0.000751] | 0.079861 | -0.401389 [-0.425694, -0.379167] | 3.096e-05 | -0.000247 [-0.000370, -0.000153] | 0.197917 |
| persistent_bias | 0.05 | both | 0.003871 | 7.502e-05 | 8.291e-05 | 0.000755 [0.000416, 0.001150] | 0.042361 | -0.313889 [-0.344444, -0.284722] | 2.724e-06 | -6.513e-05 [-0.000106, -3.517e-05] | 0.213889 |
| persistent_bias | 0.10 | both | 0.003950 | 0.000155 | 0.000257 | 0.000661 [0.000323, 0.001047] | 0.069444 | -0.372917 [-0.401389, -0.345139] | 8.233e-06 | -0.000135 [-0.000203, -8.400e-05] | 0.221528 |
| persistent_bias | 0.10 | update_only | 0.003908 | 0.000112 | 0.000257 | 0.000618 [0.000269, 0.001016] | 0.024306 | -0.418056 [-0.447222, -0.390278] | 2.232e-06 | -0.000141 [-0.000209, -9.044e-05] | 0.146528 |
| persistent_bias | 0.10 | verification_only | 0.003838 | 4.241e-05 | 0 | 0.000806 [0.000463, 0.001212] | 0.022917 | -0.205556 [-0.247917, -0.165260] | 7.723e-07 | -2.727e-05 [-5.195e-05, -1.038e-05] | 0.232639 |
| persistent_bias | 0.20 | both | 0.004207 | 0.000411 | 0.000896 | 0.000278 [-4.325e-05, 0.000635] | 0.087500 | -0.409722 [-0.438194, -0.381944] | 3.208e-05 | -0.000309 [-0.000422, -0.000215] | 0.200000 |
| random | 0.05 | both | 0.003808 | 1.241e-05 | 7.137e-06 | 0.000769 [0.000433, 0.001168] | 0.010417 | -0.229861 [-0.272222, -0.186806] | 3.913e-07 | -3.185e-05 [-5.887e-05, -1.338e-05] | 0.182639 |
| random | 0.10 | both | 0.003800 | 3.914e-06 | 7.928e-06 | 0.000759 [0.000431, 0.001140] | 0.018750 | -0.254167 [-0.286111, -0.225000] | 7.719e-07 | -2.971e-05 [-5.179e-05, -1.490e-05] | 0.207639 |
| random | 0.20 | both | 0.003806 | 1.024e-05 | 2.138e-05 | 0.000752 [0.000418, 0.001137] | 0.013194 | -0.290278 [-0.331250, -0.251389] | 4.824e-07 | -4.025e-05 [-6.606e-05, -2.183e-05] | 0.193056 |
| replay | 0.05 | both | 0.003798 | 2.066e-06 | 5.765e-05 | 0.000708 [0.000375, 0.001091] | 0.018056 | -0.257639 [-0.296528, -0.218750] | 5.956e-07 | -3.316e-05 [-5.872e-05, -1.605e-05] | 0.222917 |
| replay | 0.10 | both | 0.003840 | 4.394e-05 | 0.000144 | 0.000663 [0.000309, 0.001072] | 0.058333 | -0.261806 [-0.297222, -0.223611] | 1.317e-06 | -4.373e-05 [-6.579e-05, -2.721e-05] | 0.272222 |
| replay | 0.10 | update_only | 0.003830 | 3.402e-05 | 0.000144 | 0.000653 [0.000292, 0.001069] | 0.013889 | -0.306250 [-0.350017, -0.261111] | 6.252e-07 | -4.442e-05 [-6.649e-05, -2.804e-05] | 0.202083 |
| replay | 0.10 | verification_only | 0.003847 | 5.111e-05 | 0 | 0.000814 [0.000471, 0.001217] | 0.015972 | -0.212500 [-0.254861, -0.171528] | 4.023e-07 | -2.764e-05 [-5.236e-05, -1.087e-05] | 0.168056 |
| replay | 0.20 | both | 0.003929 | 0.000133 | 0.000385 | 0.000511 [0.000125, 0.000938] | 0.090278 | -0.252083 [-0.290972, -0.212500] | 5.745e-06 | -6.527e-05 [-8.811e-05, -4.571e-05] | 0.310417 |

Across all 16 attack cells, harmful frequency fell by 73.6%–95.7% and downside by 88.9%–98.8% relative to Always-FT; all corresponding paired CIs excluded zero. MSE, however, was higher in 15 cells with a positive CI and inconclusive only for persistent bias α=0.20/both (Δ 0.000278 [-4.325e-05, 0.000635]).

**Verification-only corruption.** Persistent-bias verification-only produced MSE 0.003838 and a +0.000806 paired gap to Always-FT [0.000463, 0.001212], while harmful frequency was 0.0229 with a −0.2056 gap [−0.2479, −0.1653]. Replay verification-only produced MSE 0.003847 and +0.000814 [0.000471, 0.001217], while harmful frequency was 0.0160 and −0.2125 [−0.2549, −0.1715]. Downside reductions were also significant. Thus the gate does not collapse when verification data are attacked, but its robust safety is purchased with a clear lifecycle-loss penalty.

**Verdict: PARTIALLY_SUPPORTED.** Security containment is consistent across type, α, and location, including verification-only corruption. Loss superiority is not supported; clean-to-attack degradation stays small for random/replay but Proposed already begins from a worse clean adaptation point than Always-FT.

## Q3 — Benign operating evolution

**Experimental question.** Under attack-free stationary, gradual, abrupt, and recurring evolution, does the robust candidate plus dual-evidence gate retain enough plasticity?

| Regime | P lifecycle MSE [95% CI] | Always-FT MSE | P−Always-FT MSE [95% CI] | Relative | P commit | P beneficial recall | P excess-loss area [95% CI] | Area Δ vs Always-FT [95% CI] | Exploratory recovery |
|---|---|---|---|---|---|---|---|---|---|
| stationary | 0.004564 [0.003240, 0.006112] | 0.003827 | 0.000737 [0.000508, 0.000987] | +19.3% | 0.185764 | 0.197933 | NA | NA | NA |
| gradual | 0.002800 [0.001589, 0.004321] | 0.002293 | 0.000507 [0.000278, 0.000804] | +22.1% | 0.197917 | 0.213572 | 0.009945 [0.005519, 0.015248] | 0.009775 [0.005397, 0.015005] | median 4.0; censored 79.2% (5/24 recovered) |
| abrupt | 0.003791 [0.001473, 0.007033] | 0.003154 | 0.000637 [0.000252, 0.001158] | +20.2% | 0.214286 | 0.247902 | 0.012995 [0.005556, 0.022692] | 0.011933 [0.004907, 0.020611] | median 4.5; censored 81.0% (4/21 recovered) |
| recurring | 0.004487 [0.001844, 0.007538] | 0.003191 | 0.001297 [0.000412, 0.002361] | +40.6% | 0.251984 | 0.298978 | 0.037306 [0.013047, 0.062436] | 0.027982 [0.008723, 0.051049] | median 1.0; censored 66.7% (7/21 recovered) |

Proposed was significantly worse than Always-FT in every benign regime: +19.3% stationary, +22.1% gradual, +20.2% abrupt, and +40.6% recurring. It was significantly better than Frozen in every regime, but that comparison only shows that a low level of selective adaptation is better than no adaptation.

After drift, Proposed's excess-loss area exceeded Always-FT by 0.009775 gradual [0.005397, 0.015005], 0.011933 abrupt [0.004907, 0.020611], and 0.027982 recurring [0.008723, 0.051049]. Recovery was censored in 79.2%, 81.0%, and 66.7% of Proposed trajectories, versus 0% for Always-FT. Recurring drift is the largest loss gap and is consistent with stale historical evidence/retention; abrupt drift also shows long retain-all periods.

**Verdict: CONTRADICTED.** The hypothesis that Proposed preserves benign plasticity without excessive cost is contradicted. The gate avoids Frozen's total rigidity but rejects too many beneficial candidates, producing low recall and slow or censored recovery.

## Q4 — Component analysis

**Experimental question.** Which gains arise from block candidate construction, trimmed aggregation, historical evidence, robust verification, and the commit gate?

| Condition | Variant | Lifecycle MSE | Harmful | Downside | Commit | Beneficial recall |
|---|---|---|---|---|---|---|
| clean | Full | 0.003623 | 0.019444 | 5.063e-07 | 0.240278 | 0.269949 |
| clean | SinglePath + DualEvidence | 0.003227 | 0.012500 | 5.523e-07 | 0.276389 | 0.311987 |
| clean | MeanDelta + DualEvidence | 0.003623 | 0.019444 | 5.063e-07 | 0.240278 | 0.269949 |
| clean | RobustCandidate + RecentOnly | 0.003535 | 0.026389 | 8.959e-07 | 0.279167 | 0.306914 |
| clean | RobustCandidate + MeanVerification | 0.003538 | 0.030556 | 1.051e-06 | 0.329167 | 0.371330 |
| clean | RobustCandidate + AlwaysCommit | 0.003379 | 0.230556 | 8.021e-06 | 1.000000 | 1.000000 |
| mixed | Full | 0.003708 | 0.044444 | 3.896e-06 | 0.211111 | 0.285036 |
| mixed | SinglePath + DualEvidence | 0.003387 | 0.047222 | 5.601e-06 | 0.270833 | 0.376168 |
| mixed | MeanDelta + DualEvidence | 0.003708 | 0.044444 | 3.896e-06 | 0.211111 | 0.285036 |
| mixed | RobustCandidate + RecentOnly | 0.003580 | 0.156944 | 1.864e-05 | 0.422222 | 0.456938 |
| mixed | RobustCandidate + MeanVerification | 0.003646 | 0.062500 | 4.310e-06 | 0.293056 | 0.403893 |
| mixed | RobustCandidate + AlwaysCommit | 0.003465 | 0.418056 | 5.457e-05 | 1.000000 | 1.000000 |

| Condition | Reference ablation | Full−ablation MSE [95% CI] | Full−ablation harmful [95% CI] | Full−ablation downside [95% CI] |
|---|---|---|---|---|
| clean | SinglePath + DualEvidence | 0.000396 [0.000204, 0.000597] | 0.006944 [-0.005556, 0.023611] | -4.594e-08 [-8.577e-07, 5.660e-07] |
| clean | MeanDelta + DualEvidence | 0 [0, 0] | 0 [0, 0] | 0 [0, 0] |
| clean | RobustCandidate + RecentOnly | 8.718e-05 [3.089e-05, 0.000154] | -0.006944 [-0.015278, 0.001389] | -3.895e-07 [-1.005e-06, 3.908e-08] |
| clean | RobustCandidate + MeanVerification | 8.454e-05 [4.725e-05, 0.000121] | -0.011111 [-0.025000, 0.001389] | -5.450e-07 [-1.020e-06, -1.226e-07] |
| clean | RobustCandidate + AlwaysCommit | 0.000244 [0.000142, 0.000346] | -0.211111 [-0.276389, -0.147222] | -7.515e-06 [-1.336e-05, -3.701e-06] |
| mixed | SinglePath + DualEvidence | 0.000321 [0.000108, 0.000556] | -0.002778 [-0.020833, 0.013889] | -1.705e-06 [-3.733e-06, 3.651e-07] |
| mixed | MeanDelta + DualEvidence | 0 [0, 0] | 0 [0, 0] | 0 [0, 0] |
| mixed | RobustCandidate + RecentOnly | 0.000127 [3.642e-05, 0.000233] | -0.112500 [-0.141667, -0.083333] | -1.475e-05 [-1.907e-05, -1.045e-05] |
| mixed | RobustCandidate + MeanVerification | 6.125e-05 [2.495e-05, 0.000102] | -0.018056 [-0.027778, -0.008333] | -4.135e-07 [-9.945e-07, 3.103e-07] |
| mixed | RobustCandidate + AlwaysCommit | 0.000243 [0.000108, 0.000384] | -0.373611 [-0.416667, -0.327778] | -5.067e-05 [-5.931e-05, -4.312e-05] |

- **Block-consensus: CONTRADICTED.** Full had higher MSE than SinglePath by 0.000396 clean [0.000204, 0.000597] and 0.000321 mixed [0.000108, 0.000556], with harmful/downside differences crossing zero. The tested block candidate did not add empirical value over the single path.
- **Trimmed aggregation: CONTRADICTED.** Full and MeanDelta were exactly identical for every reported outcome in both conditions (paired differences and CIs all exactly zero). No contribution is observable under the frozen setting.
- **Historical evidence: PARTIALLY_SUPPORTED.** Relative to RecentOnly, Full increased MSE by 0.000087 clean and 0.000127 mixed, but reduced mixed harmful frequency by 0.1125 [0.0833, 0.1417] and downside by 1.475e-05 [1.045e-05, 1.907e-05]. It improves mixed-condition safety while reducing plasticity.
- **Median/MAD verification: PARTIALLY_SUPPORTED.** Relative to MeanVerification, Full increased MSE in clean and mixed, while lowering mixed harmful frequency by 0.0181 [0.0083, 0.0278]; clean downside also fell significantly, whereas mixed downside CI crossed zero.
- **Commit gate: SUPPORTED for safety, contradicted for loss.** Relative to AlwaysCommit, Full reduced harmful frequency by 0.2111 clean [0.1472, 0.2764] and 0.3736 mixed [0.3278, 0.4167], with significant downside reductions, but MSE increased by about 0.000244 in both conditions.

**Overall Q4 verdict: PARTIALLY_SUPPORTED.** The commit gate and, conditionally, dual/robust evidence contribute to safety. Block-consensus and trimmed aggregation do not support their proposed contribution, and every safety component carries an observed loss/plasticity cost.

## Q5 — Sensitivity, generality, and maintenance cost

**Experimental question.** Is behavior stable across B, β, history capacity, κ, backbone and horizon, and what execution/memory cost does it add?

### Sensitivity

| Variant | Condition | MSE | ΔMSE vs frozen B5/β0.1 [95% CI] | Harmful | Downside | Commit | Beneficial recall |
|---|---|---|---|---|---|---|---|
| B10_beta0.1 | clean | 0.003714 | 9.161e-05 [2.815e-05, 0.000170] | 0.022222 | 4.685e-07 | 0.223611 | 0.249141 |
| B10_beta0.1 | mixed | 0.003780 | 7.252e-05 [1.780e-05, 0.000144] | 0.043056 | 2.714e-06 | 0.226389 | 0.297968 |
| B10_beta0.2 | clean | 0.003721 | 9.852e-05 [3.198e-05, 0.000184] | 0.022222 | 4.796e-07 | 0.219444 | 0.254480 |
| B10_beta0.2 | mixed | 0.003793 | 8.538e-05 [2.257e-05, 0.000163] | 0.044444 | 2.704e-06 | 0.226389 | 0.301149 |
| B5_beta0.1 | clean | 0.003623 | 0 [0, 0] | 0.019444 | 5.063e-07 | 0.240278 | 0.269949 |
| B5_beta0.1 | mixed | 0.003708 | 0 [0, 0] | 0.044444 | 3.896e-06 | 0.211111 | 0.285036 |
| B5_beta0.2 | clean | 0.003616 | -6.505e-06 [-1.761e-05, 4.643e-06] | 0.018056 | 8.075e-07 | 0.241667 | 0.281469 |
| B5_beta0.2 | mixed | 0.003724 | 1.654e-05 [3.832e-06, 3.333e-05] | 0.043056 | 4.102e-06 | 0.215278 | 0.288372 |
| capacity12 | clean | 0.003582 | -4.063e-05 [-9.221e-05, -1.147e-06] | 0.015278 | 5.879e-07 | 0.238889 | 0.267442 |
| capacity12 | mixed | 0.003658 | -4.954e-05 [-0.000124, 9.155e-06] | 0.054167 | 5.203e-06 | 0.234722 | 0.310263 |
| capacity24 | clean | 0.003623 | 0 [0, 0] | 0.019444 | 5.063e-07 | 0.240278 | 0.269949 |
| capacity24 | mixed | 0.003708 | 0 [0, 0] | 0.044444 | 3.896e-06 | 0.211111 | 0.285036 |
| capacity48 | clean | 0.003768 | 0.000145 [3.048e-05, 0.000286] | 0.015278 | 2.180e-07 | 0.211111 | 0.237374 |
| capacity48 | mixed | 0.003820 | 0.000112 [1.414e-05, 0.000231] | 0.031944 | 1.680e-06 | 0.190278 | 0.272076 |
| kappa_hist_-1 | clean | 0.003623 | 0 [0, 0] | 0.019444 | 5.063e-07 | 0.240278 | 0.269949 |
| kappa_hist_-1 | mixed | 0.003708 | 0 [0, 0] | 0.044444 | 3.896e-06 | 0.211111 | 0.285036 |
| kappa_hist_1 | clean | 0.003721 | 9.857e-05 [3.514e-05, 0.000179] | 0.012500 | 2.265e-07 | 0.177778 | 0.199664 |
| kappa_hist_1 | mixed | 0.003823 | 0.000115 [2.848e-05, 0.000230] | 0.020833 | 1.938e-06 | 0.145833 | 0.213777 |
| kappa_rec_-1 | clean | 0.003573 | -4.950e-05 [-8.103e-05, -2.143e-05] | 0.033333 | 9.657e-07 | 0.305556 | 0.336770 |
| kappa_rec_-1 | mixed | 0.003659 | -4.886e-05 [-8.847e-05, -1.785e-05] | 0.059722 | 5.373e-06 | 0.276389 | 0.378641 |
| kappa_rec_1 | clean | 0.003664 | 4.120e-05 [2.289e-05, 5.964e-05] | 0.009722 | 1.761e-07 | 0.183333 | 0.211149 |
| kappa_rec_1 | mixed | 0.003735 | 2.718e-05 [5.642e-06, 5.301e-05] | 0.031944 | 2.667e-06 | 0.165278 | 0.231884 |

B=10 increased MSE relative to frozen B=5 in both conditions by roughly 0.000073–0.000099 with CIs above zero, while harmful/downside differences were mostly inconclusive. Changing β from 0.10 to 0.20 at B=5 had little clean MSE effect but slightly worsened mixed MSE (+1.654e-05 [3.838e-06, 3.313e-05]).

Capacity 12 slightly improved clean MSE and was inconclusive in mixed; capacity 48 significantly worsened MSE (+0.000145 clean, +0.000112 mixed) while lowering mixed harmful frequency. Raising κ_hist to 0.5 and κ_rec to 1.0 made decisions more conservative and generally worsened MSE; lowering κ_rec to 0 improved MSE but significantly increased harmful/downside. Sensitivity therefore follows a coherent safety–plasticity frontier rather than showing parameter invariance.

### Backbone and horizon generality

| Backbone | H | Condition | P MSE | Always-FT MSE | P−Always-FT MSE [95% CI] | Relative | P harmful | Harmful Δ [95% CI] | P commit |
|---|---|---|---|---|---|---|---|---|---|
| GRU | 1 | clean | 0.003623 | 0.002962 | 0.000660 [0.000364, 0.000953] | +22.3% | 0.019444 | -0.181944 [-0.238889, -0.125000] | 0.240278 |
| GRU | 1 | mixed | 0.003708 | 0.003088 | 0.000620 [0.000284, 0.000951] | +20.1% | 0.044444 | -0.393056 [-0.437535, -0.348576] | 0.211111 |
| GRU | 4 | clean | 0.004563 | 0.003696 | 0.000868 [0.000515, 0.001229] | +23.5% | 0.012500 | -0.195833 [-0.263889, -0.133333] | 0.294444 |
| GRU | 4 | mixed | 0.004623 | 0.003816 | 0.000807 [0.000441, 0.001187] | +21.2% | 0.038889 | -0.358333 [-0.394444, -0.311111] | 0.269444 |
| MLP | 1 | clean | 0.005738 | 0.004834 | 0.000904 [0.000583, 0.001243] | +18.7% | 0.016667 | -0.351389 [-0.390278, -0.313889] | 0.269444 |
| MLP | 1 | mixed | 0.005815 | 0.005024 | 0.000791 [0.000444, 0.001179] | +15.7% | 0.038889 | -0.394444 [-0.429167, -0.356944] | 0.263889 |
| MLP | 4 | clean | 0.004667 | 0.003886 | 0.000781 [0.000436, 0.001211] | +20.1% | 0.026389 | -0.297222 [-0.329167, -0.268056] | 0.180556 |
| MLP | 4 | mixed | 0.004765 | 0.004024 | 0.000740 [0.000376, 0.001193] | +18.4% | 0.040278 | -0.369444 [-0.416667, -0.312500] | 0.180556 |
| TCN | 1 | clean | 0.004217 | 0.003673 | 0.000544 [0.000262, 0.000866] | +14.8% | 0.016667 | -0.173611 [-0.212500, -0.134722] | 0.209722 |
| TCN | 1 | mixed | 0.004267 | 0.003800 | 0.000467 [0.000170, 0.000796] | +12.3% | 0.044444 | -0.368056 [-0.412500, -0.322222] | 0.219444 |
| TCN | 4 | clean | 0.005213 | 0.004581 | 0.000632 [0.000369, 0.000918] | +13.8% | 0.016667 | -0.193056 [-0.223611, -0.163889] | 0.291667 |
| TCN | 4 | mixed | 0.005259 | 0.004744 | 0.000514 [0.000241, 0.000808] | +10.8% | 0.038889 | -0.344444 [-0.402778, -0.288889] | 0.313889 |

Across MLP, TCN, and GRU with both H=1 and H=4, the qualitative behavior generalized to all 12 backbone × horizon × condition cells: harmful frequency was significantly lower, while MSE was significantly higher by 10.8%–23.5%. Thus Proposed is not tied to one backbone or horizon for its safety behavior, but no tested architecture recovered a lifecycle-loss advantage over Always-FT.

### Runtime and memory

| Method | Maintenance s/stage [95% CI] | Update s | Verification s | Peak GPU MiB | Persistent KiB |
|---|---|---|---|---|---|
| Always-FT | 0.147609 [0.143576, 0.152635] | 0.145014 | 0.000732 | 53.57 | 0 |
| CLeaR-Predictor | 0.094957 [0.082115, 0.107624] | 0.071115 | 0.000661 | 125.57 | 13456.0 |
| ER | 0.152922 [0.151631, 0.154266] | 0.150293 | 0.000723 | 93.76 | 295.3 |
| EWC | 0.275115 [0.273863, 0.276356] | 0.207600 | 0.000736 | 55.56 | 43.8 |
| Frozen | 0.002911 [0.002819, 0.003010] | 0.000536 | 0.000614 | 24.31 | 0 |
| Huber-FT | 0.144469 [0.143547, 0.145322] | 0.141888 | 0.000727 | 53.57 | 0 |
| Proposed | 0.231071 [0.228432, 0.233485] | 0.149034 | 0.080256 | 53.35 | 303.8 |
| ValidationCommit | 0.146904 [0.144790, 0.148884] | 0.140579 | 0.004473 | 63.28 | 0 |

Proposed required 0.231071 s/stage [0.228432, 0.233485], 56.5% slower than Always-FT. The paired overhead was 0.083462 s [0.076529, 0.089391]. Proposed was 16.0% faster than EWC. Verification consumed 34.7% of Proposed maintenance time. Peak GPU memory was 53.3 MiB, close to Always-FT, and the persistent buffer was 303.8 KiB (similar to ER, far below CLeaR-Predictor's 13.1 MiB).

**Verdict: PARTIALLY_SUPPORTED.** Safety behavior transfers across architectures and horizons, and memory cost is modest. Runtime overhead over ordinary fine-tuning is material, and κ/history sensitivity confirms a nontrivial safety–plasticity tradeoff.

## Q6 — Alibaba external transfer

**Experimental question.** Does the synthetic frozen configuration transfer to an external trace, and does Alibaba-specific calibration materially change the conclusion?

| Mode | Condition | Method | Lifecycle MSE [95% CI] | Harmful | Downside | Commit | Beneficial recall |
|---|---|---|---|---|---|---|---|
| direct_transfer | clean | Proposed | 0.002251 [0.001761, 0.002795] | 0.003819 | 3.743e-08 | 0.037153 | 0.050341 |
| direct_transfer | clean | Always-FT | 0.002199 [0.001728, 0.002718] | 0.341667 | 6.524e-06 | 1.000000 | 1.000000 |
| direct_transfer | clean | ER | 0.002215 [0.001739, 0.002739] | 0.393750 | 3.445e-06 | 1.000000 | 1.000000 |
| direct_transfer | clean | CLeaR-Predictor | 0.002875 [0.002181, 0.003676] | 0.125000 | 0.000120 | 0.232292 | 1.000000 |
| direct_transfer | clean | ValidationCommit | 0.002264 [0.001770, 0.002814] | 0 | 0 | 0 | 0 |
| direct_transfer | clean | Frozen | 0.002264 [0.001770, 0.002814] | 0 | 0 | 0 | NA |
| direct_transfer | mixed | Proposed | 0.002269 [0.001775, 0.002819] | 0.047222 | 1.835e-06 | 0.117708 | 0.151719 |
| direct_transfer | mixed | Always-FT | 0.002367 [0.001884, 0.002895] | 0.469444 | 8.275e-05 | 1.000000 | 1.000000 |
| direct_transfer | mixed | ER | 0.002306 [0.001820, 0.002836] | 0.503819 | 1.849e-05 | 1.000000 | 1.000000 |
| direct_transfer | mixed | CLeaR-Predictor | 0.004497 [0.003802, 0.005235] | 0.150347 | 0.000429 | 0.233681 | 1.000000 |
| direct_transfer | mixed | ValidationCommit | 0.002264 [0.001770, 0.002814] | 0 | 0 | 0 | 0 |
| direct_transfer | mixed | Frozen | 0.002264 [0.001770, 0.002814] | 0 | 0 | 0 | NA |
| domain_calibration_diagnostic | clean | Proposed | 0.002256 [0.001764, 0.002801] | 0.014236 | 7.047e-08 | 0.090278 | 0.115203 |
| domain_calibration_diagnostic | clean | ValidationCommit | 0.002264 [0.001770, 0.002814] | 0 | 0 | 0 | 0 |
| domain_calibration_diagnostic | mixed | Proposed | 0.002266 [0.001771, 0.002815] | 0.051389 | 5.295e-07 | 0.118750 | 0.157980 |
| domain_calibration_diagnostic | mixed | ValidationCommit | 0.002264 [0.001770, 0.002814] | 0 | 0 | 0 | 0 |

| Mode | Condition | Reference | Metric | P−reference [paired 95% CI] |
|---|---|---|---|---|
| direct_transfer | clean | Always-FT | MSE | 5.227e-05 [2.765e-05, 7.986e-05] |
| direct_transfer | clean | Always-FT | harmful | -0.337847 [-0.363203, -0.312839] |
| direct_transfer | clean | Always-FT | downside | -6.487e-06 [-8.969e-06, -4.595e-06] |
| direct_transfer | clean | ValidationCommit | MSE | -1.288e-05 [-2.567e-05, -4.295e-06] |
| direct_transfer | clean | ValidationCommit | harmful | 0.003819 [0.001736, 0.006250] |
| direct_transfer | clean | ValidationCommit | downside | 3.743e-08 [1.184e-08, 6.999e-08] |
| direct_transfer | mixed | Always-FT | MSE | -9.810e-05 [-0.000132, -6.193e-05] |
| direct_transfer | mixed | Always-FT | harmful | -0.422222 [-0.443403, -0.401727] |
| direct_transfer | mixed | Always-FT | downside | -8.092e-05 [-8.963e-05, -7.196e-05] |
| direct_transfer | mixed | ValidationCommit | MSE | 4.788e-06 [-3.301e-06, 1.101e-05] |
| direct_transfer | mixed | ValidationCommit | harmful | 0.047222 [0.038194, 0.056597] |
| direct_transfer | mixed | ValidationCommit | downside | 1.835e-06 [1.222e-06, 2.503e-06] |
| domain_calibration_diagnostic | clean | ValidationCommit | MSE | -8.189e-06 [-1.384e-05, -3.719e-06] |
| domain_calibration_diagnostic | clean | ValidationCommit | harmful | 0.014236 [0.009375, 0.019792] |
| domain_calibration_diagnostic | clean | ValidationCommit | downside | 7.047e-08 [3.863e-08, 1.095e-07] |
| domain_calibration_diagnostic | mixed | ValidationCommit | MSE | 1.721e-06 [-3.706e-06, 6.136e-06] |
| domain_calibration_diagnostic | mixed | ValidationCommit | harmful | 0.051389 [0.042014, 0.061111] |
| domain_calibration_diagnostic | mixed | ValidationCommit | downside | 5.295e-07 [3.811e-07, 7.028e-07] |

Direct transfer was condition-dependent. In clean Alibaba, Proposed was 2.4% worse than Always-FT (paired +5.227e-05 [2.765e-05, 7.986e-05]); in mixed Alibaba it was 4.1% better (−9.810e-05 [−1.321e-04, −6.193e-05]). Harmful frequency fell by 98.9% clean and 89.9% mixed, with significant downside reductions, but commit/beneficial recall were only 3.7%/5.0% clean and 11.8%/15.2% mixed.

Alibaba-specific calibration selected Proposed policy 182. Against retain-all ValidationCommit, calibrated Proposed had a small significant clean MSE improvement (−8.189e-06 [−1.384e-05, −3.719e-06]) and an inconclusive mixed difference (+1.721e-06 [−3.706e-06, 6.136e-06]); harmful/downside were necessarily higher than the zero-commit reference. The calibration diagnostic does not establish broad superiority and does not erase the direct-transfer clean tradeoff.

**Verdict: PARTIALLY_SUPPORTED.** The safety-control behavior transfers, and mixed-corruption loss improves over Always-FT. Clean loss is worse than Always-FT, while calibrated mixed performance is indistinguishable from retain-all. External transfer is conditional, not universal.

## Nine Frozen Scientific Questions

| Question | Verdict | Exact evidence and paired CI | Limitation |
|---|---|---|---|
| 1. Does Proposed reduce lifecycle loss? | CONTRADICTED | Q1 Proposed−Always-FT MSE was +0.000783 [0.000499, 0.001113] clean and +0.000715 [0.000427, 0.001039] mixed; all 12 Q5 architecture/horizon cells were also significantly positive (+10.8% to +23.5%). | It does reduce loss relative to Frozen/retain-all and improves mixed Alibaba relative to Always-FT; the verdict concerns an unqualified loss-reduction claim. |
| 2. Does Proposed reduce harmful frequency/downside? | SUPPORTED | Versus Always-FT in Q1, harmful differences were −0.2208 [−0.2505, −0.1907] clean and −0.3861 [−0.4107, −0.3616] mixed; downside differences were −2.750e-05 [−4.684e-05, −1.403e-05] and −1.185e-04 [−1.763e-04, −7.560e-05]. All Q2 attack cells had significant reductions. | Frozen/ValidationCommit commit nothing and therefore have exactly zero harmful updates/downside; safety superiority applies to adaptive baselines. |
| 3. Is the safety gain only a consequence of low commit rate? | CONTRADICTED (the word ‘only’) | Q1 commit rates were 0.211 clean and 0.206 mixed, but conditional harmful rate among accepted commits was also lower than Always-FT: 0.081 vs 0.238 clean and 0.182 vs 0.424 mixed. Q4 Full−AlwaysCommit harmful differences were −0.2111 [−0.2764, −0.1472] and −0.3736 [−0.4167, −0.3278]. | Low commit rate is still a major source of the aggregate safety gain, and beneficial recall is only 0.246–0.284 in Q1. |
| 4. Does block-consensus make a real contribution? | CONTRADICTED | Full−SinglePath MSE was +0.000396 [0.000204, 0.000597] clean and +0.000321 [0.000108, 0.000556] mixed; harmful/downside CIs crossed zero. Full−MeanDelta was exactly 0 with [0, 0] for every reported metric. | This verdict is confined to the frozen 10-center diagnostic slice and tested block/trim settings. |
| 5. Is dual evidence more reliable? | PARTIALLY_SUPPORTED | Against RecentOnly, Full reduced mixed harmful by 0.1125 [0.0833, 0.1417] and downside by 1.475e-05 [1.045e-05, 1.907e-05], but increased MSE by 0.000127 [0.000036, 0.000233]. Robust median/MAD similarly lowered some safety metrics while increasing MSE. | Clean harmful/downside contrasts are partly inconclusive; reliability is supported for mixed safety, not overall accuracy. |
| 6. Is there benefit when verification data are corrupted? | PARTIALLY_SUPPORTED | For verification-only persistent bias/replay, harmful differences versus Always-FT were −0.2056 [−0.2479, −0.1653] and −0.2125 [−0.2549, −0.1715], with significant downside reductions. | MSE was significantly worse by +0.000806 and +0.000814; robustness means containment, not loss superiority. |
| 7. Does benign drift lose too much plasticity? | SUPPORTED (yes, excessive loss is observed) | Proposed−Always-FT benign MSE was significantly positive in stationary/gradual/abrupt/recurring (+19.3%, +22.1%, +20.2%, +40.6%). Post-drift area differences were +0.009775, +0.011933, and +0.027982 with all CIs above zero; 66.7%–81.0% of Proposed recovery observations were censored. | Proposed remains better than Frozen, so it is selectively adaptive rather than fully static. |
| 8. Does the external trace transfer? | PARTIALLY_SUPPORTED | Direct-transfer mixed Alibaba MSE improved over Always-FT by −9.810e-05 [−1.321e-04, −6.193e-05] with a −0.4222 harmful gap [−0.4434, −0.4017]. | Clean MSE was worse by +5.227e-05 [2.765e-05, 7.986e-05]; calibrated mixed MSE versus retain-all was inconclusive. |
| 9. What are the runtime and memory costs? | SUPPORTED (quantified) | Proposed maintenance was 0.2311 s/stage [0.2284, 0.2335], +0.08346 s [0.07653, 0.08939] or +56.5% versus Always-FT; peak GPU was 53.3 MiB and persistent state 303.8 KiB. It was 16.0% faster than EWC. | Timing is specific to the RTX 3060 Laptop GPU, frozen implementation, 10-center runtime slice, and current software stack. |

## Final Contribution Assessment

| Method contribution | Verdict | Assessment |
|---|---|---|
| Block-consensus candidate plus trimmed aggregation | CONTRADICTED | Full is significantly worse than SinglePath on MSE and exactly identical to MeanDelta; no measurable safety gain offsets this in Q4. |
| Dual recent/historical evidence with robust median/MAD verification | PARTIALLY_SUPPORTED | It improves harmful/downside under mixed corruption and survives verification-only attacks, but worsens MSE and benign plasticity; several clean contrasts are inconclusive. |
| Selective commit gate | SUPPORTED | It sharply reduces harmful commits and downside versus AlwaysCommit and always-updating baselines. The supported contribution is safety control; it has low commit/beneficial recall and a clear lifecycle-loss cost. |

These verdicts do not redefine the contribution after seeing heldout results. The defensible paper contribution is a conservative safety gate with conditional dual-evidence robustness, accompanied by an explicit accuracy/plasticity tradeoff. The data do not support claiming that block consensus or trimmed aggregation improves outcomes under the frozen experiment.

## Publication Claim Boundary Table

| Claim | Supported evidence | Counter-evidence | Allowed manuscript wording | Forbidden overclaim |
|---|---|---|---|---|
| Proposed reduces harmful updates versus adaptive baselines | Q1/Q2/Q5/Q6 harmful paired CIs consistently below zero | Frozen/ValidationCommit have zero harmful updates by never committing | Allowed: ‘reduced harmful-update frequency relative to always-updating adaptive baselines.’ | Forbidden: ‘safest of all methods’ or ‘eliminates harmful updates.’ |
| Proposed reduces downside | Q1 and every Q2 attack-cell paired CI versus Always-FT below zero | Non-committing controls have zero downside; CLeaR can have larger downside despite fewer commits | Allowed: ‘substantially reduced mean downside versus adaptive baselines.’ | Forbidden: ‘zero downside’ or ‘dominates every baseline.’ |
| Proposed improves lifecycle accuracy | Better than Frozen/ValidationCommit; mixed Alibaba better than Always-FT | Worse than Always-FT in Q1, all benign regimes, 15/16 Q2 cells, and all 12 generality cells | Allowed: ‘trades lifecycle accuracy for safer selective updates; beats retain-all in synthetic tests.’ | Forbidden: ‘lower lifecycle loss overall’ or ‘best predictive performance.’ |
| Safety is more than a low commit rate | Conditional harmful rate among accepted commits is lower than Always-FT | Commit rate and beneficial recall are very low | Allowed: ‘both fewer commits and better accepted-commit quality contribute.’ | Forbidden: ‘safety is cost-free’ or ‘retains full plasticity.’ |
| Block-consensus/trimmed aggregation adds value | No positive Q4 evidence | Full worse than SinglePath; Full exactly equals MeanDelta | Allowed: ‘the preregistered ablation found no benefit.’ | Forbidden: ‘block consensus is empirically superior’ or ‘trimmed aggregation drives gains.’ |
| Dual/robust evidence improves reliability | Lower mixed harmful/downside versus RecentOnly/MeanVerification; verification-only attacks contained | MSE worsens and several clean safety CIs cross zero | Allowed: ‘improved mixed-corruption safety in the tested slice.’ | Forbidden: ‘uniformly more reliable’ or ‘improves both safety and accuracy.’ |
| Benign drift adaptation is preserved | Better than Frozen in all regimes | Worse than Always-FT in all regimes; high censored recovery, especially recurring/abrupt | Allowed: ‘retains some adaptation but is over-conservative.’ | Forbidden: ‘no plasticity cost’ or ‘rapid recovery.’ |
| External transfer succeeds | Mixed Alibaba improves over Always-FT with large safety reductions | Clean Alibaba MSE worsens; calibrated mixed vs retain-all is inconclusive | Allowed: ‘conditional transfer under mixed corruption.’ | Forbidden: ‘universal cross-domain superiority.’ |
| Maintenance cost is acceptable | 53.3 MiB peak GPU, 303.8 KiB persistent state; faster than EWC | 56.5% slower than Always-FT; acceptability depends on deployment budget | Allowed: ‘modest memory with measurable runtime overhead.’ | Forbidden: ‘negligible overhead’ or ‘free safety.’ |
| ValidationCommit comparison proves adaptive safety | Provides retain-all reference with zero harmful/downside | Its calibration used the preregistered retain-all fallback and commit rate is zero | Allowed: ‘retain-all safety/accuracy boundary.’ | Forbidden: ‘Proposed is safer than ValidationCommit.’ |

## Audit trail

- `results/tables/all_summaries.csv`: 279 frozen summary cells with marginal center-cluster CIs.
- `results/tables/all_paired_comparisons.csv`: 249 paired comparisons, each with 4,000 center-cluster replicates.
- `results/figure_data/q2_security_attack_increases.csv`: clean-to-attack degradation.
- `results/figure_data/q3_drift_adaptation.csv`: excess-loss area and exploratory recovery/censoring.
- `results/figure_data/q5_runtime.csv`: runtime, GPU memory, and persistent state.
- `audits/final_reproducibility_audit.json`: P16 PASS and exact formal counts.
- `audits/p15_figure_manifest.json`: P15 PASS and publication artifact hashes.
- `audits/Q4_parallel_execution.json`, `Q5_*_parallel_execution.json`, and `Q6_Alibaba_*_parallel_execution.json`: zero missing/invalid/temp formal trajectories.
