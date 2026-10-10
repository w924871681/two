# V2 Final Baseline Benchmark Report

Generated: 2026-09-11T14:43:16.455064+00:00

## Material Passport and provenance

This post-freeze benchmark completion uses the already opened final test pool (centers 14000–14029) after Final V2 was permanently frozen and confirmed. It is not method development, calibration, tuning, or a new fresh-heldout selection. The benchmark adds exactly six frozen baselines: Always-FT, ER, EWC, Huber-FT, ValidationCommit, and Frozen. Final V2 was reused from its 360 hash-valid trajectories and was not rerun. V1 LegacyFull is excluded from the main table.

Frozen baseline engine SHA-256: `b143046aac84e62ab098c5cb5f1666dafe4fe24419ea8b164acdf2c8cbee23a6`. Frozen manifest SHA-256: `8ebbe73c40683c882c56cd5407cb546b24847aa78dbb8716fdf93e1aa656dfb7`. Runtime: Python 3.11.15, PyTorch 2.5.1+cu121, CUDA 12.1, GPU NVIDIA GeForce RTX 3060 Laptop GPU. The clean regime assignment exactly reuses `REGIMES[(center_id-14000)%4]` from the Final V2 manifest.

## Integrity, pairing, and leakage

Execution integrity **PASS**: expected/valid=2160/2160, missing=0, duplicate=0, unexpected=0, partial-invalid=0, stage rows=51840. Pairing **PASS** with mismatch rows `{"update_data_hash": 0, "verification_data_hash": 0, "service_data_hash": 0, "attack_mask_hash": 0, "initial_state_hash": 0}`. Leakage **PASS**; decision-order errors=0, state-chain errors=0.

## Main overall table

Balanced values give equal weight to stationary, gradual, abrupt, recurring, mixed, persistent verification-only, and replay verification-only. Runtime is mean maintenance seconds per stage.

| Method | MSE | MAE | Harmful | Downside | Conditional harmful | Beneficial recall | Commit rate | Runtime/stage s | Peak GPU bytes | Buffer bytes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Proposed | 0.0031489037 | 0.041762668 | 0.02155376 | 2.0005908e-06 | 0.088566491 | 0.26818429 | 0.23672761 | 0.18453692 | 55743869 | 155520 |
| Always-FT | 0.0027642857 | 0.03896533 | 0.2676422 | 4.0449086e-05 | 0.2676422 | 1 | 1 | 0.24959596 | 55599616 | 0 |
| ER | 0.0029276678 | 0.040130118 | 0.15805461 | 1.499247e-05 | 0.15805461 | 1 | 1 | 0.26202433 | 98317312 | 302400 |
| EWC | 0.0027643361 | 0.038966392 | 0.2672312 | 3.9690857e-05 | 0.2672312 | 1 | 1 | 0.50416061 | 58260480 | 44808 |
| Huber-FT | 0.0029351535 | 0.040117291 | 0.24966459 | 2.6791737e-05 | 0.24966459 | 1 | 1 | 0.25012263 | 55599616 | 0 |
| ValidationCommit | 0.0048178665 | 0.051608838 | 0 | 0 | NA | 0 | 0 | 0.25153411 | 67727360 | 0 |
| Frozen | 0.0048178665 | 0.051608838 | 0 | 0 | NA | NA | 0 | 0.0044040046 | 25496064 | 0 |

## Scenario results

No unfavorable scenario is omitted. Intervals shown for MSE are center-cluster bootstrap 95% CIs; the machine-readable scenario table contains CIs for every reported metric.

| Scenario | Method | Lifecycle MSE [95% CI] | MAE | Harmful | Downside | Conditional harmful | Beneficial recall | Commit rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| stationary | Proposed | 0.0020821976 [0.0013733515, 0.0027484708] | 0.035169167 | 0.013888889 | 5.1212803e-07 | 0.080257937 | 0.18367278 | 0.16493056 |
| stationary | Always-FT | 0.0018156814 [0.0011966969, 0.0023843875] | 0.03273555 | 0.26388889 | 1.341072e-05 | 0.26388889 | 1 | 1 |
| stationary | ER | 0.0018149493 [0.001203603, 0.0023820838] | 0.032787209 | 0.16145833 | 2.9241688e-06 | 0.16145833 | 1 | 1 |
| stationary | EWC | 0.0018158121 [0.0011967522, 0.0023844504] | 0.03273684 | 0.26215278 | 1.3304123e-05 | 0.26215278 | 1 | 1 |
| stationary | Huber-FT | 0.0019414547 [0.0012746309, 0.0025610188] | 0.033880667 | 0.265625 | 1.3272048e-05 | 0.265625 | 1 | 1 |
| stationary | ValidationCommit | 0.0022805433 [0.0014855765, 0.0030147737] | 0.036763591 | 0 | 0 | NA | 0 | 0 |
| stationary | Frozen | 0.0022805433 [0.0014855765, 0.0030147737] | 0.036763591 | 0 | 0 | NA | NA | 0 |
| gradual | Proposed | 0.0026588323 [0.00116598, 0.0041343545] | 0.037068244 | 0.022569444 | 1.3925902e-06 | 0.094345238 | 0.23833386 | 0.22569444 |
| gradual | Always-FT | 0.0023958425 [0.0010134228, 0.0037488117] | 0.034804034 | 0.21006944 | 1.597699e-05 | 0.21006944 | 1 | 1 |
| gradual | ER | 0.0025980272 [0.0011033823, 0.0040504933] | 0.036496389 | 0.098958333 | 2.8673737e-06 | 0.098958333 | 1 | 1 |
| gradual | EWC | 0.0023963674 [0.0010136085, 0.0037502883] | 0.034807665 | 0.20833333 | 1.5644982e-05 | 0.20833333 | 1 | 1 |
| gradual | Huber-FT | 0.0025155389 [0.0010669234, 0.0039410326] | 0.035701668 | 0.19618056 | 1.0579609e-05 | 0.19618056 | 1 | 1 |
| gradual | ValidationCommit | 0.0042015159 [0.0018935064, 0.0064881254] | 0.047626733 | 0 | 0 | NA | 0 | 0 |
| gradual | Frozen | 0.0042015159 [0.0018935064, 0.0064881254] | 0.047626733 | 0 | 0 | NA | NA | 0 |
| abrupt | Proposed | 0.0038479642 [0.0023270885, 0.0053138998] | 0.047037255 | 0.0099206349 | 4.7481883e-07 | 0.023039923 | 0.32560902 | 0.29365079 |
| abrupt | Always-FT | 0.0034262225 [0.0020823628, 0.004715785] | 0.044379601 | 0.23214286 | 2.1586059e-05 | 0.23214286 | 1 | 1 |
| abrupt | ER | 0.0036623658 [0.0021993872, 0.0050826793] | 0.046021538 | 0.11507937 | 1.3305056e-05 | 0.11507937 | 1 | 1 |
| abrupt | EWC | 0.0034275878 [0.0020825464, 0.0047182061] | 0.044388258 | 0.23412698 | 2.1139254e-05 | 0.23412698 | 1 | 1 |
| abrupt | Huber-FT | 0.0037487583 [0.0022372394, 0.0052000205] | 0.04632853 | 0.22222222 | 1.9254338e-05 | 0.22222222 | 1 | 1 |
| abrupt | ValidationCommit | 0.0072210703 [0.0039341123, 0.01080511] | 0.065600675 | 0 | 0 | NA | 0 | 0 |
| abrupt | Frozen | 0.0072210703 [0.0039341123, 0.01080511] | 0.065600675 | 0 | 0 | NA | NA | 0 |
| recurring | Proposed | 0.0039736831 [0.0021895858, 0.0058810087] | 0.047462039 | 0.025793651 | 3.3430441e-06 | 0.067046842 | 0.35039617 | 0.30753968 |
| recurring | Always-FT | 0.0034125781 [0.0018652098, 0.0050713879] | 0.043768853 | 0.26785714 | 6.6992953e-05 | 0.26785714 | 1 | 1 |
| recurring | ER | 0.0036884543 [0.001900103, 0.005614257] | 0.045581826 | 0.19246032 | 3.6034835e-05 | 0.19246032 | 1 | 1 |
| recurring | EWC | 0.0034118326 [0.0018647562, 0.0050703516] | 0.043768122 | 0.26785714 | 6.5855206e-05 | 0.26785714 | 1 | 1 |
| recurring | Huber-FT | 0.0035778354 [0.0019393793, 0.0053503351] | 0.044848548 | 0.24603175 | 5.0041629e-05 | 0.24603175 | 1 | 1 |
| recurring | ValidationCommit | 0.0057538465 [0.0029791634, 0.0087404961] | 0.057551844 | 0 | 0 | NA | 0 | 0 |
| recurring | Frozen | 0.0057538465 [0.0029791634, 0.0087404961] | 0.057551844 | 0 | 0 | NA | NA | 0 |
| mixed_a010_both | Proposed | 0.0031889755 [0.0024252947, 0.0039956785] | 0.042088895 | 0.047222222 | 5.8855881e-06 | 0.21092753 | 0.31144164 | 0.23425926 |
| mixed_a010_both | Always-FT | 0.0028620889 [0.0021902081, 0.0035697595] | 0.039912214 | 0.41342593 | 0.00010816656 | 0.41342593 | 1 | 1 |
| mixed_a010_both | ER | 0.002945908 [0.002209695, 0.0037356609] | 0.040324378 | 0.25601852 | 2.3701755e-05 | 0.25601852 | 1 | 1 |
| mixed_a010_both | EWC | 0.0028605278 [0.0021884825, 0.0035678546] | 0.039900478 | 0.41296296 | 0.00010585549 | 0.41296296 | 1 | 1 |
| mixed_a010_both | Huber-FT | 0.0029663473 [0.0022474503, 0.0037322028] | 0.040401743 | 0.35277778 | 4.9335532e-05 | 0.35277778 | 1 | 1 |
| mixed_a010_both | ValidationCommit | 0.0047560297 [0.0034149595, 0.0062151081] | 0.051239674 | 0 | 0 | NA | 0 | 0 |
| mixed_a010_both | Frozen | 0.0047560297 [0.0034149595, 0.0062151081] | 0.051239674 | 0 | 0 | NA | NA | 0 |
| persistent_a010_verification_only | Proposed | 0.0031393473 [0.0023831576, 0.0039381981] | 0.041693524 | 0.02037037 | 1.2168555e-06 | 0.097058805 | 0.2360114 | 0.2212963 |
| persistent_a010_verification_only | Always-FT | 0.0027187932 [0.0020568399, 0.0034140637] | 0.038578528 | 0.24305556 | 2.8505159e-05 | 0.24305556 | 1 | 1 |
| persistent_a010_verification_only | ER | 0.0028919851 [0.0021621131, 0.0036735009] | 0.039849745 | 0.1412037 | 1.3057052e-05 | 0.1412037 | 1 | 1 |
| persistent_a010_verification_only | EWC | 0.0027191126 [0.0020571239, 0.0034146069] | 0.03858169 | 0.24259259 | 2.8018469e-05 | 0.24259259 | 1 | 1 |
| persistent_a010_verification_only | Huber-FT | 0.0028980701 [0.0021869974, 0.0036513117] | 0.039829941 | 0.23240741 | 2.2529501e-05 | 0.23240741 | 1 | 1 |
| persistent_a010_verification_only | ValidationCommit | 0.0047560297 [0.0034149595, 0.0062151081] | 0.051239674 | 0 | 0 | NA | 0 | 0 |
| persistent_a010_verification_only | Frozen | 0.0047560297 [0.0034149595, 0.0062151081] | 0.051239674 | 0 | 0 | NA | NA | 0 |
| replay_a010_verification_only | Proposed | 0.003151326 [0.0023930199, 0.0039582235] | 0.041819554 | 0.011111111 | 1.1791107e-06 | 0.047289161 | 0.23182517 | 0.20972222 |
| replay_a010_verification_only | Always-FT | 0.0027187932 [0.0020568399, 0.0034140637] | 0.038578528 | 0.24305556 | 2.8505159e-05 | 0.24305556 | 1 | 1 |
| replay_a010_verification_only | ER | 0.0028919851 [0.0021621131, 0.0036735009] | 0.039849745 | 0.1412037 | 1.3057052e-05 | 0.1412037 | 1 | 1 |
| replay_a010_verification_only | EWC | 0.0027191126 [0.0020571239, 0.0034146069] | 0.03858169 | 0.24259259 | 2.8018469e-05 | 0.24259259 | 1 | 1 |
| replay_a010_verification_only | Huber-FT | 0.0028980701 [0.0021869974, 0.0036513117] | 0.039829941 | 0.23240741 | 2.2529501e-05 | 0.23240741 | 1 | 1 |
| replay_a010_verification_only | ValidationCommit | 0.0047560297 [0.0034149595, 0.0062151081] | 0.051239674 | 0 | 0 | NA | 0 | 0 |
| replay_a010_verification_only | Frozen | 0.0047560297 [0.0034149595, 0.0062151081] | 0.051239674 | 0 | 0 | NA | NA | 0 |

## Proposed versus each baseline

All rows are Proposed−baseline on identical center, seed, and scenario realizations. CIs crossing zero are inconclusive and are not evidence of equivalence.

| Baseline | Metric | Proposed | Baseline | Difference [95% CI] | Relative difference |
|---|---|---:|---:|---:|---:|
| Always-FT | lifecycle_mse | 0.0031489037 | 0.0027642857 | 0.00038461802 [0.00032542615, 0.0004424974] | 13.91383% |
| Always-FT | lifecycle_mae | 0.041762668 | 0.03896533 | 0.0027973385 [0.0025246141, 0.0030527345] | 7.1790449% |
| Always-FT | harmful_commit_rate | 0.02155376 | 0.2676422 | -0.24608844 [-0.26240564, -0.22967043] | -91.9468% |
| Always-FT | average_downside | 2.0005908e-06 | 4.0449086e-05 | -3.8448495e-05 [-4.7756111e-05, -3.0311888e-05] | -95.054052% |
| Always-FT | beneficial_commit_recall | 0.26818429 | 1 | -0.73181571 [-0.76032346, -0.70486563] | -73.181571% |
| Always-FT | commit_rate | 0.23672761 | 1 | -0.76327239 [-0.78908618, -0.73884785] | -76.327239% |
| ER | lifecycle_mse | 0.0031489037 | 0.0029276678 | 0.00022123589 [0.00017662462, 0.00026501638] | 7.5567279% |
| ER | lifecycle_mae | 0.041762668 | 0.040130118 | 0.0016325497 [0.0013030312, 0.0019351606] | 4.0681409% |
| ER | harmful_commit_rate | 0.02155376 | 0.15805461 | -0.13650085 [-0.15047052, -0.12399093] | -86.363093% |
| ER | average_downside | 2.0005908e-06 | 1.499247e-05 | -1.299188e-05 [-1.8198077e-05, -8.618229e-06] | -86.65603% |
| ER | beneficial_commit_recall | 0.26818429 | 1 | -0.73181571 [-0.76032346, -0.70486563] | -73.181571% |
| ER | commit_rate | 0.23672761 | 1 | -0.76327239 [-0.78908618, -0.73884785] | -76.327239% |
| EWC | lifecycle_mse | 0.0031489037 | 0.0027643361 | 0.00038456756 [0.00032543179, 0.00044241938] | 13.911751% |
| EWC | lifecycle_mae | 0.041762668 | 0.038966392 | 0.0027962763 [0.0025239169, 0.0030511617] | 7.1761233% |
| EWC | harmful_commit_rate | 0.02155376 | 0.2672312 | -0.24567744 [-0.26184837, -0.22951123] | -91.934415% |
| EWC | average_downside | 2.0005908e-06 | 3.9690857e-05 | -3.7690266e-05 [-4.6719441e-05, -2.9777658e-05] | -94.959568% |
| EWC | beneficial_commit_recall | 0.26818429 | 1 | -0.73181571 [-0.76032346, -0.70486563] | -73.181571% |
| EWC | commit_rate | 0.23672761 | 1 | -0.76327239 [-0.78908618, -0.73884785] | -76.327239% |
| Huber-FT | lifecycle_mse | 0.0031489037 | 0.0029351535 | 0.00021375016 [0.00017498747, 0.00025227595] | 7.2824184% |
| Huber-FT | lifecycle_mae | 0.041762668 | 0.040117291 | 0.0016453772 [0.0014349915, 0.0018497832] | 4.1014164% |
| Huber-FT | harmful_commit_rate | 0.02155376 | 0.24966459 | -0.22811083 [-0.2451559, -0.21153723] | -91.366913% |
| Huber-FT | average_downside | 2.0005908e-06 | 2.6791737e-05 | -2.4791146e-05 [-3.1147328e-05, -1.9331439e-05] | -92.532807% |
| Huber-FT | beneficial_commit_recall | 0.26818429 | 1 | -0.73181571 [-0.76032346, -0.70486563] | -73.181571% |
| Huber-FT | commit_rate | 0.23672761 | 1 | -0.76327239 [-0.78908618, -0.73884785] | -76.327239% |
| ValidationCommit | lifecycle_mse | 0.0031489037 | 0.0048178665 | -0.0016689628 [-0.0020799197, -0.0012795484] | -34.641117% |
| ValidationCommit | lifecycle_mae | 0.041762668 | 0.051608838 | -0.0098461697 [-0.011546587, -0.0081808109] | -19.078457% |
| ValidationCommit | harmful_commit_rate | 0.02155376 | 0 | 0.02155376 [0.016869331, 0.026597045] | NA% |
| ValidationCommit | average_downside | 2.0005908e-06 | 0 | 2.0005908e-06 [1.3960496e-06, 2.7101718e-06] | NA% |
| ValidationCommit | beneficial_commit_recall | 0.26818429 | 0 | 0.26818429 [0.23967654, 0.29513437] | NA% |
| ValidationCommit | commit_rate | 0.23672761 | 0 | 0.23672761 [0.21091382, 0.26115215] | NA% |
| Frozen | lifecycle_mse | 0.0031489037 | 0.0048178665 | -0.0016689628 [-0.0020799197, -0.0012795484] | -34.641117% |
| Frozen | lifecycle_mae | 0.041762668 | 0.051608838 | -0.0098461697 [-0.011546587, -0.0081808109] | -19.078457% |
| Frozen | harmful_commit_rate | 0.02155376 | 0 | 0.02155376 [0.016869331, 0.026597045] | NA% |
| Frozen | average_downside | 2.0005908e-06 | 0 | 2.0005908e-06 [1.3960496e-06, 2.7101718e-06] | NA% |
| Frozen | beneficial_commit_recall | 0.26818429 | NA | NA [NA, NA] | NA% |
| Frozen | commit_rate | 0.23672761 | 0 | 0.23672761 [0.21091382, 0.26115215] | NA% |

## Runtime, recovery, and trade-off interpretation

Runtime, peak GPU memory, and persistent-buffer costs are reported without hiding maintenance overhead. Recovery and post-drift excess-loss use the pre-execution frozen stagewise minimum of Frozen and Always-FT as the common reference. Detailed paired recovery rows are in `proposed_vs_baseline_paired.csv`.

The scientific interpretation is the observed safety–utility–plasticity trade-off rather than a claim that Proposed must minimize every metric. Always-FT may improve adaptation while accepting harmful transitions; Frozen may minimize transition harm while sacrificing adaptation; Huber-FT may help under corruption without explicit transition control; strong ValidationCommit results remain visible. Negative and inconclusive paired results are retained in full.

## Claim boundary and conclusion

Allowed wording: “On the common final test pool, the frozen Proposed method was compared with six representative baselines under identical center/seed/scenario realizations.” This report does not claim superiority over CLeaR, MER-Reg, every continual-learning method, universal robustness, or universal optimality. V1 remains separate method-evolution evidence.

The benchmark is complete and auditable. Scientific claims must follow the direction and confidence intervals in the tables; no baseline result may be used to modify Final V2.
