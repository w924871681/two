# Accepted paths, environments and historical effort accounting

Run from this extracted training_bundle directory. Use an output directory outside it, e.g. ../READER_OUTPUT. No commands run automatically. verify and preflight perform zero optimization; train/source_training/train_from_source are explicit reader commands for future reproduction, not commands executed during submission packaging.

## PATH_A: supplied frozen checkpoints

    python run.py verify
    python run.py preflight --output ../READER_OUTPUT/preflight
    python run.py train --group Main --center 63000 --seed 7311 --stream mixed --arm JOINT__l3__m0 --output ../READER_OUTPUT/main_joint

The five groups in SUBMITTED_CASES.csv retain their original complete frozen configurations and dependencies. RUN_MATRIX.csv lists supported commands, not new experiments. Sixteen earlier synthetic lifecycles form the attached asset coverage. The historical nineteen-case audit additionally included three measured-domain cases whose raw inputs/checkpoints are not in this submitted bundle.

## PATH_B: final accepted phase-specific route

Choose two local interpreters with the recorded environments in ENVIRONMENT_LOCK.json: source fitting Python 3.11.15/PyTorch 2.5.1+cu121/NumPy 2.4.6; target warm-up and lifecycle Python 3.13.5/PyTorch 2.13.0+cu126. The exercised host was Windows with RTX 3060 Laptop GPU. HISTORICAL_ENVIRONMENT_REPRODUCE.md supplies the exact explicit reader command sequence. Source fitting completes the original 50 epochs/14,150 updates; fresh warm-up uses 50 and the 24-stage lifecycle uses 1,200. Source/M0/all72 stage states/all24 actions matched, maximum MSE difference zero and original audit PASS. This specified route is the final accepted PATH_B. Do not use --max-optimizer-steps 2 as a completed source fit.

## Earlier attempt and budget ledger (retained, not relabelled)

The earlier one-environment source fit completed execution/audit but failed strict numerical identity: max MSE difference9.229406714439392e-7 exceeded the locked1e-7 tolerance. That is a separate prior attempt, not the final accepted phase-specific route. Original failure and success receipts are preserved without edits in the author's local archive, and their hash-bound scientific acceptance fields are supplied in ACCEPTANCE_EVIDENCE.json.

37,843 steps were charged to the earlier protocol (including its initial acceptance, retained failure charge and earlier full PATH_B), within its50,000 ceiling. The subsequently separately authorized historical-environment protocol used15,400 steps. Cumulative engineering attempt charge was53,243; it is not37,843 and it is not a retrospective increase to the earlier ceiling. Submission packaging adds0 steps. No new seeds/parameters, no attempt selection to change the paper's scientific results, and no full-matrix rerun are claimed.

## Materials scope

The parent README, SUPPLIED_MATERIALS.json and LICENSES_AND_ACCESS.md distinguish submitted derivatives from provider-only inputs. Aggregates and licensed public descriptive-field CSVs are supplied for read-only reconstruction. Alibaba/UCI/ThermBuild input/checkpoint arrays are not in this submitted training subset; use their original providers and the accompanying frozen recipe descriptions. No public deposit or author-approved access-on-request promise is invented.
