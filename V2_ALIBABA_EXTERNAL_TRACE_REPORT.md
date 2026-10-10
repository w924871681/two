# V2 Alibaba External Trace Report

## Material Passport

- Evidence class: post-freeze external-domain evaluation on the exact previously used Alibaba 40-machine heldout split; it is not a fresh external confirmation.
- No Alibaba-specific calibration, threshold, kappa, or machine selection was performed.
- Matrix: 40 machines × 3 seeds × 2 scenarios × 5 methods = 1200 complete trajectories.
- Statistical unit: machine; seeds averaged within machine; paired machine-cluster percentile bootstrap, 4000 replicates, seed 2904.

## Protocol and integrity

Protocol provenance: **PASS**. Integrity: **PASS**. Pairing: **PASS**. Leakage: **PASS**.

## External-domain estimates

| Scenario | Method | Lifecycle MSE (95% CI) | MAE | Harmful rate (95% CI) | Downside (95% CI) | Conditional harmful | Beneficial recall | Commit rate | Runtime/stage (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| clean | Always-FT | 0.00219892 [0.00172838, 0.00271789] | 0.0295592 | 0.341667 [0.316319, 0.366675] | 6.52402e-06 [4.62179e-06, 9.00692e-06] | 0.341667 | 1 | 1 | 0.135196 |
| clean | ER | 0.00221461 [0.0017386, 0.00273925] | 0.0296359 | 0.39375 [0.372917, 0.413889] | 3.44517e-06 [2.69752e-06, 4.30917e-06] | 0.39375 | 1 | 1 | 0.143697 |
| clean | Frozen | 0.00226406 [0.00177001, 0.0028141] | 0.0299259 | 0 [0, 0] | 0 [0, 0] | NA | NA | 0 | 0.00279177 |
| clean | Huber-FT | 0.00223555 [0.00174911, 0.00277539] | 0.0294975 | 0.35625 [0.332986, 0.378828] | 7.61486e-06 [4.64889e-06, 1.1179e-05] | 0.35625 | 1 | 1 | 0.134555 |
| clean | Proposed | 0.00223981 [0.0017551, 0.00277855] | 0.0297378 | 0.00763889 [0.00416667, 0.0118056] | 1.56258e-07 [7.6334e-08, 2.53266e-07] | 0.104902 | 0.0803589 | 0.0611111 | 0.184515 |
| mixed_a010_both | Always-FT | 0.00236695 [0.00188423, 0.0028949] | 0.0313769 | 0.469444 [0.448264, 0.490278] | 8.27518e-05 [7.35327e-05, 9.1734e-05] | 0.469444 | 1 | 1 | 0.134239 |
| mixed_a010_both | ER | 0.00230569 [0.00181977, 0.00283586] | 0.0304588 | 0.503819 [0.477431, 0.530556] | 1.8486e-05 [1.56616e-05, 2.15827e-05] | 0.503819 | 1 | 1 | 0.143702 |
| mixed_a010_both | Frozen | 0.00226406 [0.00177001, 0.0028141] | 0.0299259 | 0 [0, 0] | 0 [0, 0] | NA | NA | 0 | 0.00282178 |
| mixed_a010_both | Huber-FT | 0.00229462 [0.00180151, 0.00283777] | 0.0300505 | 0.480208 [0.463542, 0.495486] | 3.27386e-05 [2.79433e-05, 3.80104e-05] | 0.480208 | 1 | 1 | 0.134485 |
| mixed_a010_both | Proposed | 0.00228428 [0.00179394, 0.00282538] | 0.0300989 | 0.0649306 [0.0552083, 0.0753472] | 3.78829e-06 [2.75904e-06, 4.91565e-06] | 0.437123 | 0.216692 | 0.155208 | 0.183215 |

## Proposed paired differences

Negative values favor Proposed for lifecycle MSE, harmful rate, downside, and runtime. All unfavorable and inconclusive comparisons are retained.

| Scenario | Baseline | Metric | Difference (95% CI) | Relative change |
|---|---|---|---:|---:|
| clean | Always-FT | lifecycle_mse | 4.08891e-05 [2.3152e-05, 6.13857e-05] | 1.85951% |
| clean | Always-FT | harmful_commit_rate | -0.334028 [-0.359375, -0.308681] | -97.7642% |
| clean | Always-FT | average_downside | -6.36776e-06 [-8.82866e-06, -4.4635e-06] | -97.6049% |
| clean | Always-FT | beneficial_commit_recall | -0.919641 [-0.942869, -0.893756] | -91.9641% |
| clean | Always-FT | commit_rate | -0.938889 [-0.955556, -0.919792] | -93.8889% |
| mixed_a010_both | Always-FT | lifecycle_mse | -8.26644e-05 [-0.000106374, -5.8678e-05] | -3.49244% |
| mixed_a010_both | Always-FT | harmful_commit_rate | -0.404514 [-0.427778, -0.381944] | -86.1686% |
| mixed_a010_both | Always-FT | average_downside | -7.89635e-05 [-8.7789e-05, -7.00795e-05] | -95.4221% |
| mixed_a010_both | Always-FT | beneficial_commit_recall | -0.783308 [-0.817152, -0.750966] | -78.3308% |
| mixed_a010_both | Always-FT | commit_rate | -0.844792 [-0.862847, -0.827431] | -84.4792% |
| clean | ER | lifecycle_mse | 2.51969e-05 [1.2943e-05, 4.00482e-05] | 1.13776% |
| clean | ER | harmful_commit_rate | -0.386111 [-0.406597, -0.365278] | -98.06% |
| clean | ER | average_downside | -3.28891e-06 [-4.13652e-06, -2.56745e-06] | -95.4644% |
| clean | ER | beneficial_commit_recall | -0.919641 [-0.942869, -0.893756] | -91.9641% |
| clean | ER | commit_rate | -0.938889 [-0.955556, -0.919792] | -93.8889% |
| mixed_a010_both | ER | lifecycle_mse | -2.14054e-05 [-3.60376e-05, -6.68535e-06] | -0.928373% |
| mixed_a010_both | ER | harmful_commit_rate | -0.438889 [-0.464583, -0.413533] | -87.1123% |
| mixed_a010_both | ER | average_downside | -1.46977e-05 [-1.77377e-05, -1.18838e-05] | -79.5072% |
| mixed_a010_both | ER | beneficial_commit_recall | -0.783308 [-0.817152, -0.750966] | -78.3308% |
| mixed_a010_both | ER | commit_rate | -0.844792 [-0.862847, -0.827431] | -84.4792% |
| clean | Huber-FT | lifecycle_mse | 4.25334e-06 [-4.91763e-06, 1.30827e-05] | 0.190259% |
| clean | Huber-FT | harmful_commit_rate | -0.348611 [-0.370833, -0.32638] | -97.8558% |
| clean | Huber-FT | average_downside | -7.45861e-06 [-1.10204e-05, -4.50107e-06] | -97.948% |
| clean | Huber-FT | beneficial_commit_recall | -0.919641 [-0.942869, -0.893756] | -91.9641% |
| clean | Huber-FT | commit_rate | -0.938889 [-0.955556, -0.919792] | -93.8889% |
| mixed_a010_both | Huber-FT | lifecycle_mse | -1.03349e-05 [-2.53285e-05, 2.79389e-06] | -0.450397% |
| mixed_a010_both | Huber-FT | harmful_commit_rate | -0.415278 [-0.432292, -0.397569] | -86.4787% |
| mixed_a010_both | Huber-FT | average_downside | -2.89503e-05 [-3.42829e-05, -2.41467e-05] | -88.4287% |
| mixed_a010_both | Huber-FT | beneficial_commit_recall | -0.783308 [-0.817152, -0.750966] | -78.3308% |
| mixed_a010_both | Huber-FT | commit_rate | -0.844792 [-0.862847, -0.827431] | -84.4792% |
| clean | Frozen | lifecycle_mse | -2.4258e-05 [-5.03612e-05, -6.34152e-06] | -1.07143% |
| clean | Frozen | harmful_commit_rate | 0.00763889 [0.00416667, 0.0118056] | NA% |
| clean | Frozen | average_downside | 1.56258e-07 [7.6334e-08, 2.53266e-07] | NA% |
| clean | Frozen | beneficial_commit_recall | NA [NA, NA] | NA% |
| clean | Frozen | commit_rate | 0.0611111 [0.0444444, 0.0802083] | NA% |
| mixed_a010_both | Frozen | lifecycle_mse | 2.02204e-05 [-6.76946e-06, 4.20718e-05] | 0.893103% |
| mixed_a010_both | Frozen | harmful_commit_rate | 0.0649306 [0.0552083, 0.0753472] | NA% |
| mixed_a010_both | Frozen | average_downside | 3.78829e-06 [2.75904e-06, 4.91565e-06] | NA% |
| mixed_a010_both | Frozen | beneficial_commit_recall | NA [NA, NA] | NA% |
| mixed_a010_both | Frozen | commit_rate | 0.155208 [0.137153, 0.172569] | NA% |

## Claim boundary

This experiment can support a conditional external-domain transfer claim. It cannot establish fresh confirmation, architecture invariance, or universal superiority. Any clean/mixed tradeoff and every confidence interval crossing zero remain part of the scientific conclusion.

## Output hashes

- `results_v2_alibaba\alibaba_trajectory_index.csv`: `7a17783a01d164acd5bcab23a5d344021c8bc3659aba9559a66a6ed3c9f39f2c`
- `results_v2_alibaba\alibaba_machine_level_summary.csv`: `5850c79d1fac9ade921d27a15d565bade70c637a3e09465d892f4d7f9af5ecbf`
- `results_v2_alibaba\alibaba_scenario_summary.csv`: `8873354feac85e427d9d7cb2366042849cfdeeac13e97dfce9142a7fc3fbe33f`
- `results_v2_alibaba\alibaba_paired_comparisons.csv`: `0f2c9506cb609f8dbe6a9b04fb931ef7ee059d015de28e6342c97c2493e00075`
