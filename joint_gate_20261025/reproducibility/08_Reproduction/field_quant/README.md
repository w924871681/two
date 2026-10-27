# Public paired-reference field follow-up (R2.4)

This attachment is descriptive external measurement evidence, not a new RAVM training experiment or target-site calibration. DOI https://doi.org/10.5281/zenodo.10775692 (v1), paper https://doi.org/10.1038/s41597-024-03767-2. Credit Sebastian Diez, Stuart Lacy, Pete Edwards, Katie Read and Josefina Urquiza as identified in the provider metadata. The dataset-level metadata states CC BY 4.0; its description identifies sensor/reference source information under Open Government Licence v3.0. Preserve both acknowledgements and original provider terms; see ZENODO_10775692_METADATA.json. No third-party data are represented as newly collected by these authors.

All released NO2 systems and all product versions were selected before profiling. NO2 is in ppb. Ratified references are paired on the exact released city/hour; duplicate keys cause failure. Nonfinite values are not imputed. Five system/product strata have no finite reference pair and remain in the CSV. Existing nonempty manufacturer flags are retained, not silently dropped. These are descriptive discrepancies, not classified sensor faults or independent trials. Product versions can share sensors, hours and reference instruments.

Install requirements.txt in a reader's environment, then run entirely within this extracted directory:

    python profile_quant_readonly.py --input . --output ./recomputed

It checks input hashes and recomputes every system/product metric and product summary from the supplied CSVs. No network, source project path, model checkpoint or training is used. Full provider files are not required for this entry. To regenerate the derivative CSVs, obtain the two original hourly sensor/reference files at the exact URLs/checksums in DOWNLOAD_RECEIPT.json, then run --raw ORIGINAL_DIRECTORY --output NEW_DIRECTORY. The unused duplicate-reference download is retained in the acquisition receipt as provenance, not used as a substitute target. Provider row numbers refer to nonblank data records, excluding the header.

Missing-run lengths use hourly first/last observed bounds, not verified deployment dates. Long gaps may represent maintenance, replacement or relocation; they are not fault-duration ground truth. Hourly sampling cannot establish one-hour fault incidence or sub-hour duration. Error ranges across strata must not be treated as field-calibrated temperature/utilization perturbations. No 5/10/20-percent fault-rate threshold was fitted, no learned calibration was performed, and no Main/E0-E5 results were changed.
