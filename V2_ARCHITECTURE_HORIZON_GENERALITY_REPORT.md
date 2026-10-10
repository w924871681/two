# V2 Architecture and Horizon Generality Report

## Material Passport

- Evidence class: post-freeze generality evaluation; no architecture, horizon, method, or decision-parameter selection was performed.
- Settings: MLP-H1/H4, TCN-H1/H4, GRU-H1/H4. Methods: Proposed, Always-FT, Frozen. Scenarios: clean and mixed alpha=0.10 both.
- Centers: fixed first 20 already opened final-test centers (14000–14019); seeds 7311–7313; statistical unit center.
- New execution: 1800 trajectories / 43200 stage rows. Reused GRU-H1: 360 trajectories. Bootstrap: 4000 center-cluster replicates, seed 2904.

## Integrity

Architecture provenance: **PASS**. Checkpoints: **PASS**. New execution: **PASS**. Pairing: **PASS**. Leakage: **PASS**. GRU-H1 reuse: **PASS**.

## Main generality table

| Architecture | H | Scenario | Proposed MSE | Always-FT MSE | Frozen MSE | Proposed harmful | Always-FT harmful | Proposed downside | Always-FT downside | Beneficial recall | Commit rate | Runtime/stage | Ordering |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GRU | 1 | clean | 0.00312368 | 0.00273766 | 0.00488513 | 0.0138889 | 0.241667 | 7.76578e-07 | 2.55519e-05 | 0.272224 | 0.244444 | 0.184511 | holds |
| GRU | 1 | mixed_a010_both | 0.00322681 | 0.00287748 | 0.00488513 | 0.0409722 | 0.411806 | 5.33076e-06 | 0.000101253 | 0.335034 | 0.240972 | 0.18383 | holds |
| GRU | 4 | clean | 0.00420107 | 0.00356884 | 0.00689486 | 0.0152778 | 0.235417 | 2.36906e-06 | 4.25959e-05 | 0.254541 | 0.233333 | 0.205132 | holds |
| GRU | 4 | mixed_a010_both | 0.0042891 | 0.00371623 | 0.00689486 | 0.0402778 | 0.418056 | 7.63611e-06 | 0.000118115 | 0.288808 | 0.228472 | 0.202442 | holds |
| MLP | 1 | clean | 0.0054505 | 0.00500162 | 0.0103709 | 0.0256944 | 0.378472 | 3.15542e-06 | 0.000161006 | 0.333402 | 0.220833 | 0.100588 | holds |
| MLP | 1 | mixed_a010_both | 0.00554846 | 0.00514071 | 0.0103709 | 0.0347222 | 0.434722 | 7.33664e-06 | 0.000277767 | 0.303078 | 0.197222 | 0.0986878 | holds |
| MLP | 4 | clean | 0.00453271 | 0.00396444 | 0.00670251 | 0.0173611 | 0.322917 | 1.3224e-06 | 5.65267e-05 | 0.250301 | 0.213194 | 0.097973 | holds |
| MLP | 4 | mixed_a010_both | 0.00458037 | 0.0040899 | 0.00670251 | 0.0465278 | 0.413194 | 7.7949e-06 | 0.000131136 | 0.285388 | 0.23125 | 0.0974231 | holds |
| TCN | 1 | clean | 0.00401565 | 0.00363229 | 0.00565881 | 0.00972222 | 0.213194 | 5.14512e-07 | 3.11562e-05 | 0.315415 | 0.281944 | 2.97527 | holds |
| TCN | 1 | mixed_a010_both | 0.00413075 | 0.00375749 | 0.00565881 | 0.0444444 | 0.418056 | 7.00988e-06 | 0.000106488 | 0.329693 | 0.254167 | 2.97574 | holds |
| TCN | 4 | clean | 0.00541973 | 0.00474856 | 0.00865467 | 0.00416667 | 0.220139 | 1.19337e-07 | 3.68792e-05 | 0.284929 | 0.25 | 3.22015 | holds |
| TCN | 4 | mixed_a010_both | 0.00562711 | 0.00489194 | 0.00865467 | 0.04375 | 0.404861 | 7.4567e-06 | 0.000128298 | 0.268783 | 0.220833 | 3.22111 | holds |

## Paired evidence

Negative paired differences favor Proposed for MSE, harmful rate, downside, and runtime. No architectures are pooled into a larger inferential sample.

| Architecture | H | Scenario | Baseline | Metric | Difference (95% CI) |
|---|---:|---|---|---|---:|
| MLP | 1 | clean | Always-FT | lifecycle_mse | 0.000448885 [0.000223951, 0.000667399] |
| MLP | 1 | clean | Always-FT | harmful_commit_rate | -0.352778 [-0.380556, -0.325] |
| MLP | 1 | clean | Always-FT | average_downside | -0.000157851 [-0.000195388, -0.000120242] |
| MLP | 1 | mixed_a010_both | Always-FT | lifecycle_mse | 0.000407753 [0.000191681, 0.000633923] |
| MLP | 1 | mixed_a010_both | Always-FT | harmful_commit_rate | -0.4 [-0.423611, -0.375] |
| MLP | 1 | mixed_a010_both | Always-FT | average_downside | -0.00027043 [-0.000330324, -0.000211928] |
| MLP | 4 | clean | Always-FT | lifecycle_mse | 0.000568267 [0.000369254, 0.000765248] |
| MLP | 4 | clean | Always-FT | harmful_commit_rate | -0.305556 [-0.331944, -0.277778] |
| MLP | 4 | clean | Always-FT | average_downside | -5.52043e-05 [-7.27463e-05, -3.85656e-05] |
| MLP | 4 | mixed_a010_both | Always-FT | lifecycle_mse | 0.000490469 [0.000291724, 0.000695651] |
| MLP | 4 | mixed_a010_both | Always-FT | harmful_commit_rate | -0.366667 [-0.404861, -0.328455] |
| MLP | 4 | mixed_a010_both | Always-FT | average_downside | -0.000123341 [-0.000153951, -9.84153e-05] |
| TCN | 1 | clean | Always-FT | lifecycle_mse | 0.000383358 [0.00024529, 0.00052459] |
| TCN | 1 | clean | Always-FT | harmful_commit_rate | -0.203472 [-0.236111, -0.169444] |
| TCN | 1 | clean | Always-FT | average_downside | -3.06416e-05 [-5.2278e-05, -1.38951e-05] |
| TCN | 1 | mixed_a010_both | Always-FT | lifecycle_mse | 0.000373257 [0.000215801, 0.000543637] |
| TCN | 1 | mixed_a010_both | Always-FT | harmful_commit_rate | -0.373611 [-0.402083, -0.345139] |
| TCN | 1 | mixed_a010_both | Always-FT | average_downside | -9.94785e-05 [-0.000122724, -7.91379e-05] |
| TCN | 4 | clean | Always-FT | lifecycle_mse | 0.000671173 [0.000455962, 0.000882931] |
| TCN | 4 | clean | Always-FT | harmful_commit_rate | -0.215972 [-0.250694, -0.182639] |
| TCN | 4 | clean | Always-FT | average_downside | -3.67599e-05 [-6.13505e-05, -1.79505e-05] |
| TCN | 4 | mixed_a010_both | Always-FT | lifecycle_mse | 0.00073517 [0.000456061, 0.00103207] |
| TCN | 4 | mixed_a010_both | Always-FT | harmful_commit_rate | -0.361111 [-0.395156, -0.327083] |
| TCN | 4 | mixed_a010_both | Always-FT | average_downside | -0.000120842 [-0.000154399, -9.2667e-05] |
| GRU | 1 | clean | Always-FT | lifecycle_mse | 0.000386019 [0.000264865, 0.000513417] |
| GRU | 1 | clean | Always-FT | harmful_commit_rate | -0.227778 [-0.255556, -0.197222] |
| GRU | 1 | clean | Always-FT | average_downside | -2.47754e-05 [-3.84836e-05, -1.37711e-05] |
| GRU | 1 | mixed_a010_both | Always-FT | lifecycle_mse | 0.000349325 [0.00020961, 0.000501343] |
| GRU | 1 | mixed_a010_both | Always-FT | harmful_commit_rate | -0.370833 [-0.405556, -0.338177] |
| GRU | 1 | mixed_a010_both | Always-FT | average_downside | -9.59224e-05 [-0.0001168, -7.74636e-05] |
| GRU | 4 | clean | Always-FT | lifecycle_mse | 0.000632233 [0.00042677, 0.000848891] |
| GRU | 4 | clean | Always-FT | harmful_commit_rate | -0.220139 [-0.261806, -0.179861] |
| GRU | 4 | clean | Always-FT | average_downside | -4.02268e-05 [-6.58001e-05, -2.17945e-05] |
| GRU | 4 | mixed_a010_both | Always-FT | lifecycle_mse | 0.000572873 [0.00039692, 0.000745471] |
| GRU | 4 | mixed_a010_both | Always-FT | harmful_commit_rate | -0.377778 [-0.409045, -0.346528] |
| GRU | 4 | mixed_a010_both | Always-FT | average_downside | -0.000110479 [-0.00013511, -8.6802e-05] |
| MLP | 1 | clean | Frozen | lifecycle_mse | -0.00492038 [-0.00658634, -0.00333454] |
| MLP | 1 | clean | Frozen | harmful_commit_rate | 0.0256944 [0.0173611, 0.0347222] |
| MLP | 1 | clean | Frozen | average_downside | 3.15542e-06 [2.07211e-06, 4.37613e-06] |
| MLP | 1 | mixed_a010_both | Frozen | lifecycle_mse | -0.00482242 [-0.0064817, -0.00324484] |
| MLP | 1 | mixed_a010_both | Frozen | harmful_commit_rate | 0.0347222 [0.0222222, 0.0479167] |
| MLP | 1 | mixed_a010_both | Frozen | average_downside | 7.33664e-06 [3.8693e-06, 1.13876e-05] |
| MLP | 4 | clean | Frozen | lifecycle_mse | -0.0021698 [-0.00359435, -0.00117824] |
| MLP | 4 | clean | Frozen | harmful_commit_rate | 0.0173611 [0.0111111, 0.0236111] |
| MLP | 4 | clean | Frozen | average_downside | 1.3224e-06 [7.10038e-07, 2.04827e-06] |
| MLP | 4 | mixed_a010_both | Frozen | lifecycle_mse | -0.00212214 [-0.00353913, -0.00113575] |
| MLP | 4 | mixed_a010_both | Frozen | harmful_commit_rate | 0.0465278 [0.0340278, 0.0590278] |
| MLP | 4 | mixed_a010_both | Frozen | average_downside | 7.7949e-06 [5.32064e-06, 1.04177e-05] |
| TCN | 1 | clean | Frozen | lifecycle_mse | -0.00164316 [-0.00280348, -0.000840382] |
| TCN | 1 | clean | Frozen | harmful_commit_rate | 0.00972222 [0.00486111, 0.0152778] |
| TCN | 1 | clean | Frozen | average_downside | 5.14512e-07 [1.11585e-07, 1.14205e-06] |
| TCN | 1 | mixed_a010_both | Frozen | lifecycle_mse | -0.00152806 [-0.00261743, -0.000766814] |
| TCN | 1 | mixed_a010_both | Frozen | harmful_commit_rate | 0.0444444 [0.0354167, 0.0548611] |
| TCN | 1 | mixed_a010_both | Frozen | average_downside | 7.00988e-06 [4.38948e-06, 9.80559e-06] |
| TCN | 4 | clean | Frozen | lifecycle_mse | -0.00323494 [-0.00511451, -0.00182804] |
| TCN | 4 | clean | Frozen | harmful_commit_rate | 0.00416667 [0.00138889, 0.00763889] |
| TCN | 4 | clean | Frozen | average_downside | 1.19337e-07 [2.84724e-09, 3.42723e-07] |
| TCN | 4 | mixed_a010_both | Frozen | lifecycle_mse | -0.00302756 [-0.00476781, -0.00170566] |
| TCN | 4 | mixed_a010_both | Frozen | harmful_commit_rate | 0.04375 [0.0305556, 0.0576389] |
| TCN | 4 | mixed_a010_both | Frozen | average_downside | 7.4567e-06 [3.87845e-06, 1.13568e-05] |
| GRU | 1 | clean | Frozen | lifecycle_mse | -0.00176145 [-0.00285848, -0.00087898] |
| GRU | 1 | clean | Frozen | harmful_commit_rate | 0.0138889 [0.00763889, 0.0208333] |
| GRU | 1 | clean | Frozen | average_downside | 7.76578e-07 [2.00317e-07, 1.69235e-06] |
| GRU | 1 | mixed_a010_both | Frozen | lifecycle_mse | -0.00165832 [-0.00270236, -0.000807636] |
| GRU | 1 | mixed_a010_both | Frozen | harmful_commit_rate | 0.0409722 [0.0284722, 0.0541667] |
| GRU | 1 | mixed_a010_both | Frozen | average_downside | 5.33076e-06 [3.30503e-06, 7.54881e-06] |
| GRU | 4 | clean | Frozen | lifecycle_mse | -0.00269378 [-0.00408076, -0.00153132] |
| GRU | 4 | clean | Frozen | harmful_commit_rate | 0.0152778 [0.00972222, 0.0215278] |
| GRU | 4 | clean | Frozen | average_downside | 2.36906e-06 [1.06389e-06, 3.8168e-06] |
| GRU | 4 | mixed_a010_both | Frozen | lifecycle_mse | -0.00260576 [-0.00395972, -0.00145193] |
| GRU | 4 | mixed_a010_both | Frozen | harmful_commit_rate | 0.0402778 [0.0298611, 0.0506944] |
| GRU | 4 | mixed_a010_both | Frozen | average_downside | 7.63611e-06 [4.76171e-06, 1.07549e-05] |

## Interpretation and claim boundary

The full point-estimate safety–utility ordering holds in **12/12 architecture/horizon/scenario cells**. Every weak or inconsistent cell is shown above and in the machine-readable tables.
Recommended Section 5.6 title: **Sensitivity, Generality, and Maintenance Cost**.
Allowed wording, only if supported by the complete table: the verification-guided mechanism shows consistent safety–utility behavior across the tested three architectures and two horizons. Forbidden wording: architecture invariance, universal generality, or architecture-independent optimality.

## Output hashes

- `results_v2_generality\generality_trajectory_index.csv`: `8bf5632577380a25a11f9b6f052221c488e6f61677695afc680200be552357f8`
- `results_v2_generality\generality_center_summary.csv`: `e4d8e278eafb3b1a61e2e581bea1ebfef7baad30fd6927e353f0d7c63e6759ed`
- `results_v2_generality\generality_setting_summary.csv`: `fb67aeed27d84edfaa563152c9c96cbf283abb44dfac996ff8cc8af6ea60437e`
- `results_v2_generality\generality_paired_comparisons.csv`: `f46fed7e9b4e420c9137423be909acea9f2a98e23d45667e67753a9b6163221d`
- `results_v2_generality\generality_main_table.csv`: `e2ff68fe0e75b39a50b4ffbcf937e24c3e5a277e6b52075c24c0d9052e3ce426`
