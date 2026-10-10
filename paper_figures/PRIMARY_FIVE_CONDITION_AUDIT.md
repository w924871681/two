# Primary Five-Condition Audit

## Status

**PASS** — deterministic re-aggregation only; no model training or scientific trajectory execution occurred.

## Frozen statistical protocol

- Conditions: stationary, gradual, abrupt, recurring, mixed_a010_both
- Statistical unit: computing center.
- Seeds are averaged within center before resampling.
- Center-cluster percentile bootstrap: 4000 replicates, seed 2904.
- Every replicate recomputes the equal-weight five-condition aggregate.
- Persistent-bias and replay verification-only conditions are excluded from this aggregate.

## Authoritative identity checks

- V2_FINAL_MINIMAL_CONFIRMATORY_REPORT.md: 1e4787ffc96c5144f8693f103f1e481884e6b13ae4aa4b0a566902927d4435e0
- V2_FINAL_BASELINE_BENCHMARK_REPORT.md: bf7afa27797bfecf9e867a2f5b656258c1bcf577f032c5414624d818f00fbf91
- V2_ROBUSTNESS_SEVERITY_REPORT.md: 7f224a42dd061c19a270e2147474c34da16486f871403e94a7bd1d2be808ad0d
- V2_MECHANISM_AND_SENSITIVITY_REPORT.md: dce4ea39040f36b1aff57cfd68e1d148dea13380915a6d5261f00a0474509b53
- V2_ALIBABA_EXTERNAL_TRACE_REPORT.md: 8029bb085276341f4bde73ee25548fac2563887efb492efc2f999892ecb243cf
- V2_ARCHITECTURE_HORIZON_GENERALITY_REPORT.md: 27e05f6098378d5ae9f48d006f01983a8470efeebaf6e0b37cfa39a6815df3ee
- audits_v2_final_baselines/final_baseline_output_hash_manifest.json: PASS (5 result files)
- audits_v2_severity/severity_output_hash_manifest.json: PASS (4 result files)
- audits_v2_alibaba/alibaba_output_hash_manifest.json: PASS (4 result files)
- audits_v2_generality/generality_output_hash_manifest.json: PASS (5 result files)

## Five-condition estimates

| Method | Metric | Estimate | 95% CI |
|---|---|---:|---:|
| RAVM-DT | lifecycle_mse | 0.00315033053 | [0.00255703836, 0.00376157917] |
| RAVM-DT | lifecycle_mae | 0.0417651199 | [0.0371912438, 0.0462713963] |
| RAVM-DT | harmful_commit_rate | 0.0238789683 | [0.0176188823, 0.0306052414] |
| RAVM-DT | average_downside | 2.32163383e-06 | [1.51771835e-06, 3.26598708e-06] |
| RAVM-DT | conditional_harmful_rate | 0.0951234938 | [0.072087511, 0.12025052] |
| RAVM-DT | beneficial_commit_recall | 0.281890694 | [0.244508594, 0.317788882] |
| RAVM-DT | commit_rate | 0.245214947 | [0.211024884, 0.277816386] |
| Always-FT | lifecycle_mse | 0.00278248268 | [0.00225767522, 0.00333079316] |
| Always-FT | lifecycle_mae | 0.0391200503 | [0.0348632244, 0.0433990423] |
| Always-FT | harmful_commit_rate | 0.277476852 | [0.253541419, 0.300003886] |
| Always-FT | average_downside | 4.52266565e-05 | [3.41668087e-05, 5.81547542e-05] |
| Always-FT | conditional_harmful_rate | 0.277476852 | [0.253541419, 0.300003886] |
| Always-FT | beneficial_commit_recall | 1 | [1, 1] |
| Always-FT | commit_rate | 1 | [1, 1] |
| ER | lifecycle_mse | 0.0029419409 | [0.00236234895, 0.0035466942] |
| ER | lifecycle_mae | 0.040242268 | [0.0356634287, 0.044858429] |
| ER | harmful_commit_rate | 0.164794974 | [0.148646908, 0.182315476] |
| ER | average_downside | 1.57666377e-05 | [9.64102809e-06, 2.34280845e-05] |
| ER | conditional_harmful_rate | 0.164794974 | [0.148646908, 0.182315476] |
| ER | beneficial_commit_recall | 1 | [1, 1] |
| ER | commit_rate | 1 | [1, 1] |
| EWC | lifecycle_mse | 0.00278242555 | [0.00225762759, 0.0033306122] |
| EWC | lifecycle_mae | 0.0391202727 | [0.0348625725, 0.0434029814] |
| EWC | harmful_commit_rate | 0.27708664 | [0.253450562, 0.299253307] |
| EWC | average_downside | 4.4359812e-05 | [3.35045991e-05, 5.70134627e-05] |
| EWC | conditional_harmful_rate | 0.27708664 | [0.253450562, 0.299253307] |
| EWC | beneficial_commit_recall | 1 | [1, 1] |
| EWC | commit_rate | 1 | [1, 1] |
| Huber-FT | lifecycle_mse | 0.0029499869 | [0.00238308904, 0.00353651561] |
| Huber-FT | lifecycle_mae | 0.0402322311 | [0.0357312504, 0.0446836973] |
| Huber-FT | harmful_commit_rate | 0.25656746 | [0.233722966, 0.279199983] |
| Huber-FT | average_downside | 2.8496631e-05 | [2.08978389e-05, 3.77597897e-05] |
| Huber-FT | conditional_harmful_rate | 0.25656746 | [0.233722966, 0.279199983] |
| Huber-FT | beneficial_commit_recall | 1 | [1, 1] |
| Huber-FT | commit_rate | 1 | [1, 1] |
| ValidationCommit | lifecycle_mse | 0.00484260117 | [0.0037800916, 0.00592599594] |
| ValidationCommit | lifecycle_mae | 0.0517565034 | [0.0456120244, 0.0579890748] |
| ValidationCommit | harmful_commit_rate | 0 | [0, 0] |
| ValidationCommit | average_downside | 0 | [0, 0] |
| ValidationCommit | conditional_harmful_rate | nan | [nan, nan] |
| ValidationCommit | beneficial_commit_recall | 0 | [0, 0] |
| ValidationCommit | commit_rate | 0 | [0, 0] |
| Frozen | lifecycle_mse | 0.00484260117 | [0.0037800916, 0.00592599594] |
| Frozen | lifecycle_mae | 0.0517565034 | [0.0456120244, 0.0579890748] |
| Frozen | harmful_commit_rate | 0 | [0, 0] |
| Frozen | average_downside | 0 | [0, 0] |
| Frozen | conditional_harmful_rate | nan | [nan, nan] |
| Frozen | beneficial_commit_recall | nan | [nan, nan] |
| Frozen | commit_rate | 0 | [0, 0] |

## Five-condition paired comparisons

Differences are RAVM-DT minus baseline; all adverse and inconclusive intervals are retained.

| Baseline | Metric | Difference | 95% CI | Relative change |
|---|---|---:|---:|---:|
| Always-FT | lifecycle_mse | 0.000367847843 | [0.00029145723, 0.000443510549] | 13.220% |
| Always-FT | lifecycle_mae | 0.00264506962 | [0.00229163863, 0.00298806658] | 6.761% |
| Always-FT | harmful_commit_rate | -0.253597884 | [-0.27493163, -0.231230159] | -91.394% |
| Always-FT | average_downside | -4.29050226e-05 | [-5.52955051e-05, -3.22556324e-05] | -94.867% |
| Always-FT | conditional_harmful_rate | -0.182179747 | [-0.207723096, -0.156332832] | -65.718% |
| Always-FT | beneficial_commit_recall | -0.718109306 | [-0.755491406, -0.682211118] | -71.811% |
| Always-FT | commit_rate | -0.754785053 | [-0.788975116, -0.722183614] | -75.479% |
| ER | lifecycle_mse | 0.000208389624 | [0.000149903354, 0.000266136271] | 7.083% |
| ER | lifecycle_mae | 0.00152285186 | [0.00110029875, 0.0019182375] | 3.784% |
| ER | harmful_commit_rate | -0.140916005 | [-0.159213046, -0.124249256] | -85.510% |
| ER | average_downside | -1.34450038e-05 | [-2.04738376e-05, -7.77487174e-06] | -85.275% |
| ER | conditional_harmful_rate | -0.0696714798 | [-0.097535585, -0.0416268113] | -42.278% |
| ER | beneficial_commit_recall | -0.718109306 | [-0.755491406, -0.682211118] | -71.811% |
| ER | commit_rate | -0.754785053 | [-0.788975116, -0.722183614] | -75.479% |
| EWC | lifecycle_mse | 0.00036790498 | [0.000291599801, 0.000443457864] | 13.222% |
| EWC | lifecycle_mae | 0.00264484723 | [0.0022924493, 0.00298831207] | 6.761% |
| EWC | harmful_commit_rate | -0.253207672 | [-0.274207507, -0.231332424] | -91.382% |
| EWC | average_downside | -4.20381781e-05 | [-5.41317587e-05, -3.16642899e-05] | -94.766% |
| EWC | conditional_harmful_rate | -0.181789535 | [-0.207250077, -0.155453951] | -65.670% |
| EWC | beneficial_commit_recall | -0.718109306 | [-0.755491406, -0.682211118] | -71.811% |
| EWC | commit_rate | -0.754785053 | [-0.788975116, -0.722183614] | -75.479% |
| Huber-FT | lifecycle_mse | 0.000200343624 | [0.00015153473, 0.000251212953] | 6.791% |
| Huber-FT | lifecycle_mae | 0.00153288877 | [0.00127049282, 0.00178798355] | 3.810% |
| Huber-FT | harmful_commit_rate | -0.232688492 | [-0.255274884, -0.21004828] | -90.693% |
| Huber-FT | average_downside | -2.61749972e-05 | [-3.46476834e-05, -1.9033278e-05] | -91.853% |
| Huber-FT | conditional_harmful_rate | -0.160749522 | [-0.187660556, -0.133481219] | -62.925% |
| Huber-FT | beneficial_commit_recall | -0.718109306 | [-0.755491406, -0.682211118] | -71.811% |
| Huber-FT | commit_rate | -0.754785053 | [-0.788975116, -0.722183614] | -75.479% |
| ValidationCommit | lifecycle_mse | -0.00169227064 | [-0.00223593836, -0.00117887092] | -34.945% |
| ValidationCommit | lifecycle_mae | -0.00999138354 | [-0.0121972623, -0.00781458052] | -19.305% |
| ValidationCommit | harmful_commit_rate | 0.0238789683 | [0.0176188823, 0.0306052414] | NA |
| ValidationCommit | average_downside | 2.32163383e-06 | [1.51771835e-06, 3.26598708e-06] | NA |
| ValidationCommit | conditional_harmful_rate | nan | [nan, nan] | NA |
| ValidationCommit | beneficial_commit_recall | 0.281890694 | [0.244508594, 0.317788882] | NA |
| ValidationCommit | commit_rate | 0.245214947 | [0.211024884, 0.277816386] | NA |
| Frozen | lifecycle_mse | -0.00169227064 | [-0.00223593836, -0.00117887092] | -34.945% |
| Frozen | lifecycle_mae | -0.00999138354 | [-0.0121972623, -0.00781458052] | -19.305% |
| Frozen | harmful_commit_rate | 0.0238789683 | [0.0176188823, 0.0306052414] | NA |
| Frozen | average_downside | 2.32163383e-06 | [1.51771835e-06, 3.26598708e-06] | NA |
| Frozen | conditional_harmful_rate | nan | [nan, nan] | NA |
| Frozen | beneficial_commit_recall | nan | [nan, nan] | NA |
| Frozen | commit_rate | 0.245214947 | [0.211024884, 0.277816386] | NA |

## Five-condition versus published seven-condition aggregate

| Method | Metric | Five-condition | Seven-condition | Difference |
|---|---|---:|---:|---:|
| RAVM-DT | lifecycle_mse | 0.00315033053 | 0.0031489037 | 1.42682551e-06 |
| RAVM-DT | lifecycle_mae | 0.0417651199 | 0.0417626682 | 2.45167424e-06 |
| RAVM-DT | harmful_commit_rate | 0.0238789683 | 0.0215537604 | 0.00232520786 |
| RAVM-DT | average_downside | 2.32163383e-06 | 2.00059076e-06 | 3.21043068e-07 |
| RAVM-DT | conditional_harmful_rate | 0.0951234938 | 0.0885664908 | 0.00655700296 |
| RAVM-DT | beneficial_commit_recall | 0.281890694 | 0.268184292 | 0.0137064025 |
| RAVM-DT | commit_rate | 0.245214947 | 0.236727608 | 0.00848733938 |
| Always-FT | lifecycle_mse | 0.00278248268 | 0.00276428568 | 1.81970021e-05 |
| Always-FT | lifecycle_mae | 0.0391200503 | 0.0389653297 | 0.000154720579 |
| Always-FT | harmful_commit_rate | 0.277476852 | 0.267642196 | 0.00983465608 |
| Always-FT | average_downside | 4.52266565e-05 | 4.04490857e-05 | 4.77757074e-06 |
| Always-FT | conditional_harmful_rate | 0.277476852 | 0.267642196 | 0.00983465608 |
| Always-FT | beneficial_commit_recall | 1 | 1 | 0 |
| Always-FT | commit_rate | 1 | 1 | 0 |
| ER | lifecycle_mse | 0.0029419409 | 0.00292766781 | 1.42730917e-05 |
| ER | lifecycle_mae | 0.040242268 | 0.0401301185 | 0.000112149567 |
| ER | harmful_commit_rate | 0.164794974 | 0.158054611 | 0.00674036281 |
| ER | average_downside | 1.57666377e-05 | 1.49924704e-05 | 7.7416721e-07 |
| ER | conditional_harmful_rate | 0.164794974 | 0.158054611 | 0.00674036281 |
| ER | beneficial_commit_recall | 1 | 1 | 0 |
| ER | commit_rate | 1 | 1 | 0 |
| EWC | lifecycle_mse | 0.00278242555 | 0.00276433615 | 1.80894027e-05 |
| EWC | lifecycle_mae | 0.0391202727 | 0.0389663919 | 0.00015388076 |
| EWC | harmful_commit_rate | 0.27708664 | 0.267231198 | 0.00985544218 |
| EWC | average_downside | 4.4359812e-05 | 3.96908568e-05 | 4.66895519e-06 |
| EWC | conditional_harmful_rate | 0.27708664 | 0.267231198 | 0.00985544218 |
| EWC | beneficial_commit_recall | 1 | 1 | 0 |
| EWC | commit_rate | 1 | 1 | 0 |
| Huber-FT | lifecycle_mse | 0.0029499869 | 0.00293515354 | 1.48333622e-05 |
| Huber-FT | lifecycle_mae | 0.0402322311 | 0.040117291 | 0.000114940077 |
| Huber-FT | harmful_commit_rate | 0.25656746 | 0.249664588 | 0.00690287226 |
| Huber-FT | average_downside | 2.8496631e-05 | 2.67917367e-05 | 1.70489438e-06 |
| Huber-FT | conditional_harmful_rate | 0.25656746 | 0.249664588 | 0.00690287226 |
| Huber-FT | beneficial_commit_recall | 1 | 1 | 0 |
| Huber-FT | commit_rate | 1 | 1 | 0 |
| ValidationCommit | lifecycle_mse | 0.00484260117 | 0.00481786647 | 2.47346956e-05 |
| ValidationCommit | lifecycle_mae | 0.0517565034 | 0.0516088379 | 0.000147665505 |
| ValidationCommit | harmful_commit_rate | 0 | 0 | 0 |
| ValidationCommit | average_downside | 0 | 0 | 0 |
| ValidationCommit | conditional_harmful_rate | nan | nan | nan |
| ValidationCommit | beneficial_commit_recall | 0 | 0 | 0 |
| ValidationCommit | commit_rate | 0 | 0 | 0 |
| Frozen | lifecycle_mse | 0.00484260117 | 0.00481786647 | 2.47346956e-05 |
| Frozen | lifecycle_mae | 0.0517565034 | 0.0516088379 | 0.000147665505 |
| Frozen | harmful_commit_rate | 0 | 0 | 0 |
| Frozen | average_downside | 0 | 0 | 0 |
| Frozen | conditional_harmful_rate | nan | nan | nan |
| Frozen | beneficial_commit_recall | nan | nan | nan |
| Frozen | commit_rate | 0 | 0 | 0 |

The recomputed five-condition point estimates exactly match the frozen `*_utility_balanced_5` values. Recomputed paired estimates and confidence limits match the frozen helper output within 2e-15 absolute tolerance. These values were not used for method or parameter selection.
