# V2 Post-Calibration GO-5 Completion Audit

Generated: 2026-09-11T02:04:05.870895+00:00

## Scope and provenance

This audit completes the verification-only evidence for the already frozen decision-calibration winner. It is **not parameter tuning or a new grid search**. Before any of these trajectories ran, the configuration was fixed as `V2_SP_ShortDual`, history capacity 12, `kappa_rec=0`, `kappa_hist=0.5`, `delta_imp=2.80182377662436e-05`, and `delta_ret=0`. Its exact SHA-256 is `68e06d381ced23ed105694b97e221b37ea5302fb389789f9ec310c8bbe74d3f4`.

The run contains exactly 20 existing development centers × 3 model seeds × 2 existing verification-only scenarios = **120 complete 24-stage trajectories**. It used scientific implementation commit `7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3` without changing the scientific core. The original frozen NO-GO report and decision audit remain intact.

## Integrity

- Result integrity: **PASS**; expected=120, valid=120, missing=0, duplicate=0, unexpected=0, partial/invalid=0.
- Frozen V0 reference: **PASS**; 120/120 reference artifacts valid, development aggregate SHA-256 `032239b87875b4a7f2a3f583a9a8e932fb681306a8f9d0f00ee56eb5f4aa9b34`.
- V0 alignment: attack mask, update data, verification data, and service data hashes have zero mismatches across all 2,880 paired stages.
- Runtime: Python 3.11.15, PyTorch 2.5.1+cu121, CUDA 12.1, GPU NVIDIA GeForce RTX 3060 Laptop GPU.
- Fresh confirmatory heldout access/materialized: **false / false**.

## Center-cluster paired results

All intervals use paired center-cluster bootstrap with 4,000 replicates and center as the resampling unit. Differences are `FinalCalibratedShortDual - V0_LegacyFull`.

| Scenario | Metric | Final calibrated ShortDual [95% CI] | V0 Legacy Full [95% CI] | Paired difference [95% CI] |
|---|---|---:|---:|---:|
| persistent_a010_verification_only | Lifecycle MSE | 0.003501507135 [0.002510338334, 0.004543246901] | 0.003821184471 [0.002709882573, 0.004980559532] | -0.0003196773354 [-0.0004839355635, -0.0001707023969] |
| persistent_a010_verification_only | Harmful commit rate | 0.01180555556 [0.004166666667, 0.02083333333] | 0.01875 [0.01180555556, 0.02638888889] | -0.006944444444 [-0.01458333333, +0.0006944444444] |
| persistent_a010_verification_only | Average downside | 1.729455673e-06 [3.391227882e-07, 3.505370502e-06] | 1.147383106e-06 [4.333485514e-07, 1.997424414e-06] | +5.820725669e-07 [-4.426024498e-07, +1.790947523e-06] |
| persistent_a010_verification_only | Conditional harmful among commits | 0.04504689755 [0.01568181818, 0.08073773449] | 0.1069336219 [0.05226217532, 0.1760347523] | -0.03688672439 [-0.07612340669, -0.003537578163] |
| persistent_a010_verification_only | Beneficial recall | 0.2679126414 [0.2160085932, 0.3185436291] | 0.2564506126 [0.1871566529, 0.3234996658] | +0.01146202879 [-0.02812694736, +0.05166367091] |
| persistent_a010_verification_only | Commit rate | 0.2381944444 [0.1944270833, 0.2798611111] | 0.2291666667 [0.1701215278, 0.2881944444] | +0.009027777778 [-0.02779513889, +0.04444444444] |
| replay_a010_verification_only | Lifecycle MSE | 0.003536115098 [0.002545356589, 0.004580964919] | 0.003840705294 [0.002743748487, 0.004996035796] | -0.0003045901961 [-0.0004517537694, -0.0001681133836] |
| replay_a010_verification_only | Harmful commit rate | 0.01736111111 [0.009027777778, 0.02638888889] | 0.008333333333 [0.002777777778, 0.01527777778] | +0.009027777778 [+0.0006944444444, +0.01805555556] |
| replay_a010_verification_only | Average downside | 1.51220245e-06 [6.110093333e-07, 2.646448184e-06] | 2.726359121e-07 [2.641936589e-08, 6.751673502e-07] | +1.239566538e-06 [+2.21335339e-07, +2.360198021e-06] |
| replay_a010_verification_only | Conditional harmful among commits | 0.1056746032 [0.05075396825, 0.1709563492] | 0.1048772215 [0.02089930132, 0.2322802198] | -0.0256003256 [-0.1338185965, +0.06000440917] |
| replay_a010_verification_only | Beneficial recall | 0.2509352014 [0.1937729837, 0.3083465632] | 0.2016156093 [0.1361773706, 0.2687155954] | +0.04931959213 [+0.003507105002, +0.09679077099] |
| replay_a010_verification_only | Commit rate | 0.2263888889 [0.1784722222, 0.2736111111] | 0.1791666667 [0.1242881944, 0.2368055556] | +0.04722222222 [+0.009722222222, +0.08541666667] |

## Frozen GO-5 decision

**GO-5: FAIL.** Absolute harmful rates are 0.01180556 and 0.01736111, both below rho=0.05; both downside estimates are below epsilon=5.60364755325e-05. The replay scenario nevertheless has a wholly adverse harmful-rate paired CI and a wholly adverse downside paired CI. Under the original frozen GO-5 rule, either one is sufficient for failure. The rule has not been redefined.

Failure evidence:

- replay_a010_verification_only: harmful-rate paired CI wholly adverse
- replay_a010_verification_only: downside paired CI wholly adverse

GO-1, GO-2, GO-3, GO-4, and GO-6 mechanically remain PASS. Resulting overall verdict: **NO-GO**.

No final V2 freeze/tag was created, no fresh confirmatory center was materialized or accessed, and no confirmatory experiment was started. State: `WAITING_FOR_MANUAL_V2_METHOD_REVIEW`.
