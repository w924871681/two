# Submitted reproduction materials

This directory is in 06_Reproducibility_Materials.zip. Extract the complete ZIP before running commands. No original project path, network service or public repository is required for the supplied read-only entries.

From the extraction root:

    python 08_Reproduction/reconstruct_readonly.py
    python 08_Reproduction/public_field/profile_readonly.py --output FIELD_RECOMPUTED
    python 08_Reproduction/field_quant/profile_quant_readonly.py --input 08_Reproduction/field_quant --output QUANT_RECOMPUTED

Use Python with numpy/matplotlib for aggregate reconstruction; the field entries additionally use pandas. See requirements-readonly.txt and each field requirements/readme. These commands reconstruct existing aggregates/descriptive profiles without optimization. The aggregate entry checks the Main result, all330 method/stream rows, E3 machine-paired contrast and E5 sums from supplied CSVs. Field counts and QUANT ppb discrepancies do not calibrate target-DT injection rates/amplitudes/durations.

For supplied executable synthetic lifecycle assets see training_bundle/README.md, REPRODUCE.md, SUBMITTED_CASES.csv and ASSET_MANIFEST.json. Five unchanged frozen synthetic group definitions and their full referenced input/model dependency closure are included. Sixteen historical synthetic PATH_A cases and one specified historical phase-specific PATH_B are represented. Historical nineteen-case acceptance included three measured-domain cases whose input/checkpoint bytes are NOT in this submission subset. Their cited providers, configurations and historical recipes are documented; they are not represented as self-contained paths in this attachment. Recipe source listings are not automatic training commands.

The author's complete unredacted receipts, earlier failures, full research records and large asset index remain in a separate LOCAL ARCHIVE NOT FOR SUBMISSION. They have not been uploaded or made public. The training bundle explains37,843 earlier-protocol steps, separately authorized15,400 historical steps and cumulative53,243 engineering steps. This submission packaging task adds0 steps. No independent external replication or complete matrix rerun is claimed.

Third-party descriptive CSV notices accompany their datasets. Own synthetic checkpoints and inputs do not redistribute Alibaba/UCI/ThermBuild training arrays. SUPPLIED_MATERIALS.json and LICENSES_AND_ACCESS.md define exact inclusion and restrictions. Author final approval is required before any upload.
