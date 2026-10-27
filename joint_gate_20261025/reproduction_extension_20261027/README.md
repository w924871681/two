# Joint Gate frozen reproduction inputs: 2026-10-27 extension

This additive extension complements the [2026-10-25 publication](../README.md) and its original `reproducibility/08_Reproduction/training_bundle`. The original bundle and its checksums are unchanged. Eleven additional group definitions and 667 frozen inputs, source checkpoints and initial states cover **16 groups in total**: Main, E1, six E2 groups, five E4 groups and three E5 cost groups. See `EXTENSION_MANIFEST.json` for exact hashes and roles. Existing paper PDFs, results and figure scripts are in the 2026-10-25 publication.

## Assemble and verify

With a recent Python (3.11 or later), run from the repository root, using a **new** output directory outside the repository and the base bundle:

```bash
python joint_gate_20261025/reproduction_extension_20261027/assemble.py --output /path/to/new_training_bundle
python /path/to/new_training_bundle/run.py verify
python /path/to/new_training_bundle/run.py preflight --output /path/to/new_preflight_output
```

On Windows, replace the example paths with suitable new Windows paths. Assembly checks the original manifest and every included dependency by SHA-256, copies them to the new directory, and never modifies the base. Consult the assembled bundle's `REPRODUCE.md` and `run.py --help` for environment requirements and execution options. Training is not invoked by these three commands. Do not confuse the original five-group guide with this extension's 16-group coverage.

The 16-group bundle passed local input, import, role, fault-sampling and forward preflight, including 660 source/initial model loads, in a CPU-only Python 3.13.5 / PyTorch 2.13.0+cu126 environment. This is not an independent full-lifecycle rerun or proof of numerical equivalence on other hardware. Upstream source fitting and development selection were not independently rerun; the scope starts from supplied frozen source and initial model states and preprocessed Final inputs. Existing limited-path training acceptance is documented in the base bundle; this extension does not increase that accepted training coverage. No optimizer steps were performed to prepare this extension.

## E3 Alibaba assets and access boundary

The E3 group definition and `E3_UNDISTRIBUTED_ASSET_INDEX.json` are supplied, but the 284 missing E3 assets (including trace-derived inputs and model states) are **not** distributed here because rights to redistribute those derivatives publicly have not been established. The [Alibaba clusterdata project](https://github.com/alibaba/clusterdata) describes access to its research traces; obtaining raw data does not by itself establish permission to redistribute processed derivatives. Readers require authorized access to the exact frozen files identified by the index (or an independently established procedure that produces the same bytes); we do not claim a complete public reconstruction pipeline for them.

If those exact files are available under an authorized local `assets/` directory, include them without modifying the published base:

```bash
python joint_gate_20261025/reproduction_extension_20261027/assemble.py --alibaba-assets /path/to/authorized_directory --output /path/to/new_17_group_bundle
```

The assembler validates each listed file by size and SHA-256 before using it. A locally supplied E3 bundle passed the same bounded preflight, including 123 model loads and zero optimizer steps; the assets used for that check are not included in the public repository. This does not establish independent access or a full training rerun.

## Data terms and checksums

Read [ATTRIBUTION_AND_LICENSE.md](ATTRIBUTION_AND_LICENSE.md) for UCI CC BY 4.0 and ThermBuild CC BY-SA 4.0 attribution, modifications and distribution conditions. Other original notices remain applicable. `SHA256SUMS.txt` records the extension's published files; `PREFLIGHT_VERIFICATION.json` summarizes the bounded checks without local paths. E3 availability and full independent training remain open limitations.
