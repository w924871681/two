# V2 Robustness Severity Report

## Material Passport

- Evidence class: frozen Final V2 final-test severity extension plus exact reuse of prior alpha=0.10 final-test trajectories.
- Final-test centers 14000–14029 were already opened on 2026-09-11; this report makes no fresh/unseen claim.
- Frozen Final V2 config SHA-256: `7275a287ee4a1f4602ed0a10a67362a1a61ffa398848d4529669b0584a127d13`.
- New execution: 2160 complete trajectories / 51840 stage rows. Reused alpha=0.10: 1080 trajectories. Combined: 3240 trajectories.
- Statistical unit: center; seeds averaged within center; paired center-cluster percentile bootstrap, 4000 replicates, seed 2904.

## Integrity and provenance

Execution integrity: **PASS**. Pairing: **PASS**. Leakage: **PASS**. Alpha=0.10 reuse: **PASS**.
No alpha=0.10 trajectory was rerun. No severity result was used for parameter selection or to modify Final V2.

## Scenario estimates

| Attack | Alpha | Method | Lifecycle MSE (95% CI) | Harmful rate (95% CI) | Downside (95% CI) | Conditional harmful | Beneficial recall | Commit rate | Absolute safety |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| mixed | 0.05 | Always-FT | 0.0027734 [0.00210684, 0.00347447] | 0.352315 [0.326389, 0.378241] | 5.29027e-05 [3.53886e-05, 7.67175e-05] | 0.352315 | 1 | 1 | FAIL |
| mixed | 0.05 | ER | 0.00292349 [0.00219118, 0.00370975] | 0.210185 [0.180093, 0.239352] | 1.83974e-05 [9.54018e-06, 3.09912e-05] | 0.210185 | 1 | 1 | FAIL |
| mixed | 0.05 | Huber-FT | 0.00292729 [0.0022127, 0.003685] | 0.297685 [0.272685, 0.323611] | 2.97642e-05 [1.79609e-05, 4.58475e-05] | 0.297685 | 1 | 1 | FAIL |
| mixed | 0.05 | Proposed | 0.00313581 [0.00239016, 0.00393458] | 0.0425926 [0.0324074, 0.0541667] | 3.33737e-06 [2.22302e-06, 4.67487e-06] | 0.193863 | 0.292694 | 0.255093 | PASS |
| mixed | 0.10 | Always-FT | 0.00286209 [0.00219021, 0.00356976] | 0.413426 [0.389352, 0.438426] | 0.000108167 [8.30113e-05, 0.000142523] | 0.413426 | 1 | 1 | FAIL |
| mixed | 0.10 | ER | 0.00294591 [0.00220969, 0.00373566] | 0.256019 [0.224537, 0.288889] | 2.37018e-05 [1.62863e-05, 3.3554e-05] | 0.256019 | 1 | 1 | FAIL |
| mixed | 0.10 | Huber-FT | 0.00296635 [0.00224745, 0.0037322] | 0.352778 [0.326389, 0.37963] | 4.93355e-05 [3.44844e-05, 7.17219e-05] | 0.352778 | 1 | 1 | FAIL |
| mixed | 0.10 | Proposed | 0.00318898 [0.00242529, 0.00399568] | 0.0472222 [0.0375, 0.0574074] | 5.88559e-06 [4.31706e-06, 7.72988e-06] | 0.210928 | 0.311442 | 0.234259 | PASS |
| mixed | 0.20 | Always-FT | 0.00315829 [0.00246294, 0.00387783] | 0.454167 [0.434722, 0.475] | 0.000306867 [0.000256873, 0.000372606] | 0.454167 | 1 | 1 | FAIL |
| mixed | 0.20 | ER | 0.00298844 [0.00225124, 0.00378104] | 0.340278 [0.303704, 0.377778] | 4.91616e-05 [3.87479e-05, 6.32742e-05] | 0.340278 | 1 | 1 | FAIL |
| mixed | 0.20 | Huber-FT | 0.00312393 [0.00238107, 0.00390002] | 0.434722 [0.411111, 0.456956] | 0.000156388 [0.000125578, 0.000200611] | 0.434722 | 1 | 1 | FAIL |
| mixed | 0.20 | Proposed | 0.00339905 [0.00259313, 0.00424318] | 0.0439815 [0.0324074, 0.0560185] | 1.646e-05 [1.13768e-05, 2.2144e-05] | 0.25272 | 0.29462 | 0.190741 | PASS |
| persistent_bias | 0.05 | Always-FT | 0.00271879 [0.00205684, 0.00341406] | 0.243056 [0.212037, 0.272222] | 2.85052e-05 [1.58239e-05, 4.50886e-05] | 0.243056 | 1 | 1 | FAIL |
| persistent_bias | 0.05 | ER | 0.00289199 [0.00216211, 0.0036735] | 0.141204 [0.119444, 0.164815] | 1.30571e-05 [5.42954e-06, 2.37507e-05] | 0.141204 | 1 | 1 | FAIL |
| persistent_bias | 0.05 | Huber-FT | 0.00289807 [0.002187, 0.00365131] | 0.232407 [0.202315, 0.261111] | 2.25295e-05 [1.34193e-05, 3.43572e-05] | 0.232407 | 1 | 1 | FAIL |
| persistent_bias | 0.05 | Proposed | 0.00310712 [0.00236218, 0.00390056] | 0.0180556 [0.0115741, 0.025463] | 1.40647e-06 [5.78605e-07, 2.44662e-06] | 0.0825277 | 0.257292 | 0.236574 | PASS |
| persistent_bias | 0.10 | Always-FT | 0.00271879 [0.00205684, 0.00341406] | 0.243056 [0.212037, 0.272222] | 2.85052e-05 [1.58239e-05, 4.50886e-05] | 0.243056 | 1 | 1 | FAIL |
| persistent_bias | 0.10 | ER | 0.00289199 [0.00216211, 0.0036735] | 0.141204 [0.119444, 0.164815] | 1.30571e-05 [5.42954e-06, 2.37507e-05] | 0.141204 | 1 | 1 | FAIL |
| persistent_bias | 0.10 | Huber-FT | 0.00289807 [0.002187, 0.00365131] | 0.232407 [0.202315, 0.261111] | 2.25295e-05 [1.34193e-05, 3.43572e-05] | 0.232407 | 1 | 1 | FAIL |
| persistent_bias | 0.10 | Proposed | 0.00313935 [0.00238316, 0.0039382] | 0.0203704 [0.012963, 0.0282407] | 1.21686e-06 [5.61873e-07, 1.97636e-06] | 0.0970588 | 0.236011 | 0.221296 | PASS |
| persistent_bias | 0.20 | Always-FT | 0.00271879 [0.00205684, 0.00341406] | 0.243056 [0.212037, 0.272222] | 2.85052e-05 [1.58239e-05, 4.50886e-05] | 0.243056 | 1 | 1 | FAIL |
| persistent_bias | 0.20 | ER | 0.00289199 [0.00216211, 0.0036735] | 0.141204 [0.119444, 0.164815] | 1.30571e-05 [5.42954e-06, 2.37507e-05] | 0.141204 | 1 | 1 | FAIL |
| persistent_bias | 0.20 | Huber-FT | 0.00289807 [0.002187, 0.00365131] | 0.232407 [0.202315, 0.261111] | 2.25295e-05 [1.34193e-05, 3.43572e-05] | 0.232407 | 1 | 1 | FAIL |
| persistent_bias | 0.20 | Proposed | 0.00320081 [0.00244142, 0.00399934] | 0.0171296 [0.0111111, 0.0240741] | 9.98695e-07 [4.62474e-07, 1.60947e-06] | 0.0865657 | 0.213573 | 0.199074 | PASS |
| replay | 0.05 | Always-FT | 0.00271879 [0.00205684, 0.00341406] | 0.243056 [0.212037, 0.272222] | 2.85052e-05 [1.58239e-05, 4.50886e-05] | 0.243056 | 1 | 1 | FAIL |
| replay | 0.05 | ER | 0.00289199 [0.00216211, 0.0036735] | 0.141204 [0.119444, 0.164815] | 1.30571e-05 [5.42954e-06, 2.37507e-05] | 0.141204 | 1 | 1 | FAIL |
| replay | 0.05 | Huber-FT | 0.00289807 [0.002187, 0.00365131] | 0.232407 [0.202315, 0.261111] | 2.25295e-05 [1.34193e-05, 3.43572e-05] | 0.232407 | 1 | 1 | FAIL |
| replay | 0.05 | Proposed | 0.00311044 [0.00236193, 0.00390527] | 0.0148148 [0.0087963, 0.0212963] | 1.29977e-06 [4.31273e-07, 2.3555e-06] | 0.0590809 | 0.25233 | 0.22963 | PASS |
| replay | 0.10 | Always-FT | 0.00271879 [0.00205684, 0.00341406] | 0.243056 [0.212037, 0.272222] | 2.85052e-05 [1.58239e-05, 4.50886e-05] | 0.243056 | 1 | 1 | FAIL |
| replay | 0.10 | ER | 0.00289199 [0.00216211, 0.0036735] | 0.141204 [0.119444, 0.164815] | 1.30571e-05 [5.42954e-06, 2.37507e-05] | 0.141204 | 1 | 1 | FAIL |
| replay | 0.10 | Huber-FT | 0.00289807 [0.002187, 0.00365131] | 0.232407 [0.202315, 0.261111] | 2.25295e-05 [1.34193e-05, 3.43572e-05] | 0.232407 | 1 | 1 | FAIL |
| replay | 0.10 | Proposed | 0.00315133 [0.00239302, 0.00395822] | 0.0111111 [0.00601852, 0.0171296] | 1.17911e-06 [3.61344e-07, 2.1993e-06] | 0.0472892 | 0.231825 | 0.209722 | PASS |
| replay | 0.20 | Always-FT | 0.00271879 [0.00205684, 0.00341406] | 0.243056 [0.212037, 0.272222] | 2.85052e-05 [1.58239e-05, 4.50886e-05] | 0.243056 | 1 | 1 | FAIL |
| replay | 0.20 | ER | 0.00289199 [0.00216211, 0.0036735] | 0.141204 [0.119444, 0.164815] | 1.30571e-05 [5.42954e-06, 2.37507e-05] | 0.141204 | 1 | 1 | FAIL |
| replay | 0.20 | Huber-FT | 0.00289807 [0.002187, 0.00365131] | 0.232407 [0.202315, 0.261111] | 2.25295e-05 [1.34193e-05, 3.43572e-05] | 0.232407 | 1 | 1 | FAIL |
| replay | 0.20 | Proposed | 0.00318761 [0.00242833, 0.00398679] | 0.0166667 [0.0106481, 0.0231481] | 1.52822e-06 [6.28384e-07, 2.61233e-06] | 0.0756089 | 0.206736 | 0.19537 | PASS |

## Proposed paired differences

Negative differences favor Proposed for lifecycle MSE, harmful rate, and downside. All estimates below preserve favorable, adverse, and inconclusive findings.

| Attack | Alpha | Baseline | Metric | Difference (95% CI) | Relative change |
|---|---:|---|---|---:|---:|
| mixed | 0.05 | Always-FT | lifecycle_mse | 0.000362411 [0.000266818, 0.000469646] | 13.0674% |
| mixed | 0.05 | Always-FT | harmful_commit_rate | -0.309722 [-0.335185, -0.285174] | -87.9106% |
| mixed | 0.05 | Always-FT | average_downside | -4.95654e-05 [-7.26524e-05, -3.26345e-05] | -93.6915% |
| mixed | 0.05 | Always-FT | beneficial_commit_recall | -0.707306 [-0.755884, -0.658191] | -70.7306% |
| mixed | 0.05 | Always-FT | commit_rate | -0.744907 [-0.780093, -0.709722] | -74.4907% |
| mixed | 0.10 | Always-FT | lifecycle_mse | 0.000326887 [0.000222638, 0.000445427] | 11.4213% |
| mixed | 0.10 | Always-FT | harmful_commit_rate | -0.366204 [-0.391667, -0.341667] | -88.5778% |
| mixed | 0.10 | Always-FT | average_downside | -0.000102281 [-0.00013636, -7.70454e-05] | -94.5588% |
| mixed | 0.10 | Always-FT | beneficial_commit_recall | -0.688558 [-0.729833, -0.647449] | -68.8558% |
| mixed | 0.10 | Always-FT | commit_rate | -0.765741 [-0.794907, -0.737037] | -76.5741% |
| mixed | 0.20 | Always-FT | lifecycle_mse | 0.000240759 [9.89018e-05, 0.000402282] | 7.62308% |
| mixed | 0.20 | Always-FT | harmful_commit_rate | -0.410185 [-0.43287, -0.38934] | -90.316% |
| mixed | 0.20 | Always-FT | average_downside | -0.000290407 [-0.000356988, -0.000239811] | -94.6361% |
| mixed | 0.20 | Always-FT | beneficial_commit_recall | -0.70538 [-0.749691, -0.661609] | -70.538% |
| mixed | 0.20 | Always-FT | commit_rate | -0.809259 [-0.835185, -0.783333] | -80.9259% |
| persistent_bias | 0.05 | Always-FT | lifecycle_mse | 0.000388323 [0.00029304, 0.000492346] | 14.2829% |
| persistent_bias | 0.05 | Always-FT | harmful_commit_rate | -0.225 [-0.252778, -0.196285] | -92.5714% |
| persistent_bias | 0.05 | Always-FT | average_downside | -2.70987e-05 [-4.2789e-05, -1.5022e-05] | -95.0659% |
| persistent_bias | 0.05 | Always-FT | beneficial_commit_recall | -0.742708 [-0.791964, -0.693025] | -74.2708% |
| persistent_bias | 0.05 | Always-FT | commit_rate | -0.763426 [-0.808333, -0.718056] | -76.3426% |
| persistent_bias | 0.10 | Always-FT | lifecycle_mse | 0.000420554 [0.000315395, 0.000532932] | 15.4684% |
| persistent_bias | 0.10 | Always-FT | harmful_commit_rate | -0.222685 [-0.25, -0.193981] | -91.619% |
| persistent_bias | 0.10 | Always-FT | average_downside | -2.72883e-05 [-4.3521e-05, -1.4885e-05] | -95.7311% |
| persistent_bias | 0.10 | Always-FT | beneficial_commit_recall | -0.763989 [-0.809091, -0.715805] | -76.3989% |
| persistent_bias | 0.10 | Always-FT | commit_rate | -0.778704 [-0.818981, -0.736574] | -77.8704% |
| persistent_bias | 0.20 | Always-FT | lifecycle_mse | 0.000482021 [0.000362143, 0.000613565] | 17.7292% |
| persistent_bias | 0.20 | Always-FT | harmful_commit_rate | -0.225926 [-0.253241, -0.197222] | -92.9524% |
| persistent_bias | 0.20 | Always-FT | average_downside | -2.75065e-05 [-4.40093e-05, -1.49866e-05] | -96.4964% |
| persistent_bias | 0.20 | Always-FT | beneficial_commit_recall | -0.786427 [-0.824864, -0.746797] | -78.6427% |
| persistent_bias | 0.20 | Always-FT | commit_rate | -0.800926 [-0.834722, -0.766655] | -80.0926% |
| replay | 0.05 | Always-FT | lifecycle_mse | 0.000391646 [0.000295539, 0.000498556] | 14.4052% |
| replay | 0.05 | Always-FT | harmful_commit_rate | -0.228241 [-0.255556, -0.199537] | -93.9048% |
| replay | 0.05 | Always-FT | average_downside | -2.72054e-05 [-4.28671e-05, -1.52202e-05] | -95.4402% |
| replay | 0.05 | Always-FT | beneficial_commit_recall | -0.74767 [-0.794771, -0.699792] | -74.767% |
| replay | 0.05 | Always-FT | commit_rate | -0.77037 [-0.8139, -0.725463] | -77.037% |
| replay | 0.10 | Always-FT | lifecycle_mse | 0.000432533 [0.000324159, 0.000555717] | 15.909% |
| replay | 0.10 | Always-FT | harmful_commit_rate | -0.231944 [-0.260185, -0.202315] | -95.4286% |
| replay | 0.10 | Always-FT | average_downside | -2.7326e-05 [-4.3173e-05, -1.51141e-05] | -95.8635% |
| replay | 0.10 | Always-FT | beneficial_commit_recall | -0.768175 [-0.817066, -0.716152] | -76.8175% |
| replay | 0.10 | Always-FT | commit_rate | -0.790278 [-0.834722, -0.743056] | -79.0278% |
| replay | 0.20 | Always-FT | lifecycle_mse | 0.00046882 [0.000358797, 0.000592044] | 17.2437% |
| replay | 0.20 | Always-FT | harmful_commit_rate | -0.226389 [-0.254167, -0.197685] | -93.1429% |
| replay | 0.20 | Always-FT | average_downside | -2.69769e-05 [-4.26406e-05, -1.50744e-05] | -94.6388% |
| replay | 0.20 | Always-FT | beneficial_commit_recall | -0.793264 [-0.844929, -0.7393] | -79.3264% |
| replay | 0.20 | Always-FT | commit_rate | -0.80463 [-0.852326, -0.75463] | -80.463% |
| mixed | 0.05 | ER | lifecycle_mse | 0.000212319 [0.000146156, 0.000286042] | 7.26253% |
| mixed | 0.05 | ER | harmful_commit_rate | -0.167593 [-0.194444, -0.138889] | -79.7357% |
| mixed | 0.05 | ER | average_downside | -1.50601e-05 [-2.68083e-05, -6.87321e-06] | -81.8596% |
| mixed | 0.05 | ER | beneficial_commit_recall | -0.707306 [-0.755884, -0.658191] | -70.7306% |
| mixed | 0.05 | ER | commit_rate | -0.744907 [-0.780093, -0.709722] | -74.4907% |
| mixed | 0.10 | ER | lifecycle_mse | 0.000243068 [0.000164425, 0.000330752] | 8.25102% |
| mixed | 0.10 | ER | harmful_commit_rate | -0.208796 [-0.242593, -0.175] | -81.5552% |
| mixed | 0.10 | ER | average_downside | -1.78162e-05 [-2.78608e-05, -9.90936e-06] | -75.1681% |
| mixed | 0.10 | ER | beneficial_commit_recall | -0.688558 [-0.729833, -0.647449] | -68.8558% |
| mixed | 0.10 | ER | commit_rate | -0.765741 [-0.794907, -0.737037] | -76.5741% |
| mixed | 0.20 | ER | lifecycle_mse | 0.000410608 [0.000300003, 0.000545828] | 13.7399% |
| mixed | 0.20 | ER | harmful_commit_rate | -0.296296 [-0.333796, -0.258796] | -87.0748% |
| mixed | 0.20 | ER | average_downside | -3.27016e-05 [-4.78893e-05, -2.06442e-05] | -66.5186% |
| mixed | 0.20 | ER | beneficial_commit_recall | -0.70538 [-0.749691, -0.661609] | -70.538% |
| mixed | 0.20 | ER | commit_rate | -0.809259 [-0.835185, -0.783333] | -80.9259% |
| persistent_bias | 0.05 | ER | lifecycle_mse | 0.000215131 [0.000149691, 0.000287617] | 7.43887% |
| persistent_bias | 0.05 | ER | harmful_commit_rate | -0.123148 [-0.147234, -0.100463] | -87.2131% |
| persistent_bias | 0.05 | ER | average_downside | -1.16506e-05 [-2.15073e-05, -4.55316e-06] | -89.2282% |
| persistent_bias | 0.05 | ER | beneficial_commit_recall | -0.742708 [-0.791964, -0.693025] | -74.2708% |
| persistent_bias | 0.05 | ER | commit_rate | -0.763426 [-0.808333, -0.718056] | -76.3426% |
| persistent_bias | 0.10 | ER | lifecycle_mse | 0.000247362 [0.000171526, 0.000330112] | 8.55337% |
| persistent_bias | 0.10 | ER | harmful_commit_rate | -0.120833 [-0.143519, -0.0986111] | -85.5738% |
| persistent_bias | 0.10 | ER | average_downside | -1.18402e-05 [-2.21536e-05, -4.35744e-06] | -90.6805% |
| persistent_bias | 0.10 | ER | beneficial_commit_recall | -0.763989 [-0.809091, -0.715805] | -76.3989% |
| persistent_bias | 0.10 | ER | commit_rate | -0.778704 [-0.818981, -0.736574] | -77.8704% |
| persistent_bias | 0.20 | ER | lifecycle_mse | 0.000308829 [0.000221699, 0.000408144] | 10.6788% |
| persistent_bias | 0.20 | ER | harmful_commit_rate | -0.124074 [-0.147685, -0.102315] | -87.8689% |
| persistent_bias | 0.20 | ER | average_downside | -1.20584e-05 [-2.27456e-05, -4.55954e-06] | -92.3513% |
| persistent_bias | 0.20 | ER | beneficial_commit_recall | -0.786427 [-0.824864, -0.746797] | -78.6427% |
| persistent_bias | 0.20 | ER | commit_rate | -0.800926 [-0.834722, -0.766655] | -80.0926% |
| replay | 0.05 | ER | lifecycle_mse | 0.000218454 [0.000149899, 0.000295687] | 7.55379% |
| replay | 0.05 | ER | harmful_commit_rate | -0.126389 [-0.149537, -0.10463] | -89.5082% |
| replay | 0.05 | ER | average_downside | -1.17573e-05 [-2.16541e-05, -4.61378e-06] | -90.0455% |
| replay | 0.05 | ER | beneficial_commit_recall | -0.74767 [-0.794771, -0.699792] | -74.767% |
| replay | 0.05 | ER | commit_rate | -0.77037 [-0.8139, -0.725463] | -77.037% |
| replay | 0.10 | ER | lifecycle_mse | 0.000259341 [0.00017469, 0.000350029] | 8.96757% |
| replay | 0.10 | ER | harmful_commit_rate | -0.130093 [-0.154167, -0.106944] | -92.1311% |
| replay | 0.10 | ER | average_downside | -1.18779e-05 [-2.17812e-05, -4.61543e-06] | -90.9695% |
| replay | 0.10 | ER | beneficial_commit_recall | -0.768175 [-0.817066, -0.716152] | -76.8175% |
| replay | 0.10 | ER | commit_rate | -0.790278 [-0.834722, -0.743056] | -79.0278% |
| replay | 0.20 | ER | lifecycle_mse | 0.000295628 [0.000202885, 0.000395923] | 10.2223% |
| replay | 0.20 | ER | harmful_commit_rate | -0.124537 [-0.148611, -0.102315] | -88.1967% |
| replay | 0.20 | ER | average_downside | -1.15288e-05 [-2.13741e-05, -4.50963e-06] | -88.2958% |
| replay | 0.20 | ER | beneficial_commit_recall | -0.793264 [-0.844929, -0.7393] | -79.3264% |
| replay | 0.20 | ER | commit_rate | -0.80463 [-0.852326, -0.75463] | -80.463% |
| mixed | 0.05 | Huber-FT | lifecycle_mse | 0.000208519 [0.000138162, 0.000281834] | 7.12329% |
| mixed | 0.05 | Huber-FT | harmful_commit_rate | -0.255093 [-0.281481, -0.230544] | -85.6921% |
| mixed | 0.05 | Huber-FT | average_downside | -2.64268e-05 [-4.14372e-05, -1.5143e-05] | -88.7873% |
| mixed | 0.05 | Huber-FT | beneficial_commit_recall | -0.707306 [-0.755884, -0.658191] | -70.7306% |
| mixed | 0.05 | Huber-FT | commit_rate | -0.744907 [-0.780093, -0.709722] | -74.4907% |
| mixed | 0.10 | Huber-FT | lifecycle_mse | 0.000222628 [0.000162556, 0.000290207] | 7.50513% |
| mixed | 0.10 | Huber-FT | harmful_commit_rate | -0.305556 [-0.333796, -0.278241] | -86.6142% |
| mixed | 0.10 | Huber-FT | average_downside | -4.34499e-05 [-6.57783e-05, -2.83884e-05] | -88.0703% |
| mixed | 0.10 | Huber-FT | beneficial_commit_recall | -0.688558 [-0.729833, -0.647449] | -68.8558% |
| mixed | 0.10 | Huber-FT | commit_rate | -0.765741 [-0.794907, -0.737037] | -76.5741% |
| mixed | 0.20 | Huber-FT | lifecycle_mse | 0.000275119 [0.000181767, 0.000379157] | 8.80682% |
| mixed | 0.20 | Huber-FT | harmful_commit_rate | -0.390741 [-0.4125, -0.36713] | -89.8829% |
| mixed | 0.20 | Huber-FT | average_downside | -0.000139928 [-0.000184082, -0.000108065] | -89.4749% |
| mixed | 0.20 | Huber-FT | beneficial_commit_recall | -0.70538 [-0.749691, -0.661609] | -70.538% |
| mixed | 0.20 | Huber-FT | commit_rate | -0.809259 [-0.835185, -0.783333] | -80.9259% |
| persistent_bias | 0.05 | Huber-FT | lifecycle_mse | 0.000209046 [0.000140469, 0.000279655] | 7.21328% |
| persistent_bias | 0.05 | Huber-FT | harmful_commit_rate | -0.214352 [-0.243056, -0.185185] | -92.2311% |
| persistent_bias | 0.05 | Huber-FT | average_downside | -2.1123e-05 [-3.22325e-05, -1.26107e-05] | -93.7572% |
| persistent_bias | 0.05 | Huber-FT | beneficial_commit_recall | -0.742708 [-0.791964, -0.693025] | -74.2708% |
| persistent_bias | 0.05 | Huber-FT | commit_rate | -0.763426 [-0.808333, -0.718056] | -76.3426% |
| persistent_bias | 0.10 | Huber-FT | lifecycle_mse | 0.000241277 [0.000167754, 0.000320666] | 8.32544% |
| persistent_bias | 0.10 | Huber-FT | harmful_commit_rate | -0.212037 [-0.239815, -0.183796] | -91.2351% |
| persistent_bias | 0.10 | Huber-FT | average_downside | -2.13126e-05 [-3.28407e-05, -1.24288e-05] | -94.5988% |
| persistent_bias | 0.10 | Huber-FT | beneficial_commit_recall | -0.763989 [-0.809091, -0.715805] | -76.3989% |
| persistent_bias | 0.10 | Huber-FT | commit_rate | -0.778704 [-0.818981, -0.736574] | -77.8704% |
| persistent_bias | 0.20 | Huber-FT | lifecycle_mse | 0.000302744 [0.000210388, 0.000411499] | 10.4464% |
| persistent_bias | 0.20 | Huber-FT | harmful_commit_rate | -0.215278 [-0.242593, -0.186574] | -92.6295% |
| persistent_bias | 0.20 | Huber-FT | average_downside | -2.15308e-05 [-3.33364e-05, -1.2547e-05] | -95.5672% |
| persistent_bias | 0.20 | Huber-FT | beneficial_commit_recall | -0.786427 [-0.824864, -0.746797] | -78.6427% |
| persistent_bias | 0.20 | Huber-FT | commit_rate | -0.800926 [-0.834722, -0.766655] | -80.0926% |
| replay | 0.05 | Huber-FT | lifecycle_mse | 0.000212369 [0.000148198, 0.000283212] | 7.32796% |
| replay | 0.05 | Huber-FT | harmful_commit_rate | -0.217593 [-0.245833, -0.188426] | -93.6255% |
| replay | 0.05 | Huber-FT | average_downside | -2.12297e-05 [-3.23532e-05, -1.26853e-05] | -94.2308% |
| replay | 0.05 | Huber-FT | beneficial_commit_recall | -0.74767 [-0.794771, -0.699792] | -74.767% |
| replay | 0.05 | Huber-FT | commit_rate | -0.77037 [-0.8139, -0.725463] | -77.037% |
| replay | 0.10 | Huber-FT | lifecycle_mse | 0.000253256 [0.000186489, 0.000333147] | 8.73878% |
| replay | 0.10 | Huber-FT | harmful_commit_rate | -0.221296 [-0.249537, -0.19213] | -95.2191% |
| replay | 0.10 | Huber-FT | average_downside | -2.13504e-05 [-3.25528e-05, -1.27446e-05] | -94.7664% |
| replay | 0.10 | Huber-FT | beneficial_commit_recall | -0.768175 [-0.817066, -0.716152] | -76.8175% |
| replay | 0.10 | Huber-FT | commit_rate | -0.790278 [-0.834722, -0.743056] | -79.0278% |
| replay | 0.20 | Huber-FT | lifecycle_mse | 0.000289543 [0.00022062, 0.000363559] | 9.99088% |
| replay | 0.20 | Huber-FT | harmful_commit_rate | -0.215741 [-0.243519, -0.1875] | -92.8287% |
| replay | 0.20 | Huber-FT | average_downside | -2.10013e-05 [-3.21202e-05, -1.2521e-05] | -93.2168% |
| replay | 0.20 | Huber-FT | beneficial_commit_recall | -0.793264 [-0.844929, -0.7393] | -79.3264% |
| replay | 0.20 | Huber-FT | commit_rate | -0.80463 [-0.852326, -0.75463] | -80.463% |

## Severity interpretation boundary

The alpha sequence is a predeclared descriptive robustness sweep. It does not fit or select a new threshold. A confidence interval crossing zero is recorded as inconclusive rather than treated as equivalence. Any absolute safety failure or wholly adverse paired interval remains visible in the tables and is not removed from the report.

## Output hashes

- `results_v2_severity\severity_trajectory_index.csv`: `1cae04f9edfd7c4774aae9f430aae70d446e7366a4db00e12406c3765afc04b8`
- `results_v2_severity\severity_scenario_summary.csv`: `5a4034fcabd419634ca9dc60210757d2d3abb154ac8adca0b3d66b26fb0d5678`
- `results_v2_severity\severity_paired_comparisons.csv`: `04fea93cecbc3ab76f6ede458f8d9af6808cee9d5e021f101c0960cf145030db`
- `results_v2_severity\severity_trend_table.csv`: `8207b54c19ec78e7912fd51e92be9021b0051b4c4216392f98fca4e62dad4d61`
