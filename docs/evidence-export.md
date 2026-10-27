# Saved evidence bundles, format 1

Select a successful saved run and choose **Download evidence bundle** in the workbench or guided evidence review. The selected run's original configuration determines the export even if the editable draft has changed. An incomplete, failed or cancelled attempt cannot be exported; a successful legacy attempt without recorded evaluation explains that a new forecast is required.

The API provides the same download at `GET /runs/RUN_ID/export`, returning `application/zip` with an attachment filename. Invalid run identifiers return 422, unknown runs 404 and unavailable exports 409 with an actionable explanation. Export reads saved results without rerunning prediction or evaluation. Repeated downloads of an unchanged saved run are byte-identical.

| File | Contents |
| --- | --- |
| `manifest.json` | Bundle version, run identity/time, immutable snapshot identity/relative locator, experiment, culture/scope/time units, cutoff/targets, method/software versions, fixed settings, deterministic flag, synthetic status, limitations and SHA-256 hashes for the other files. |
| `configuration.json` | Original recorded forecast configuration. |
| `predictions.json` | Exact saved per-target prediction dictionaries, without adding target-only lineages. |
| `evaluations.json` | Saved exhaustive comparisons and scores per target. |
| `comparisons.csv` | Per-target category, predicted/observed proportions, observed counts/totals, forecast-minus-observed differences in percentage points, and previously unseen flags. |
| `scores.csv` | Total variation distance and previously unseen identified lineage share for each target. |
| `README.txt` | Reproduction requirements and interpretation conventions. |

Both initial predictors are deterministic, so `random_seeds` is `null`; no random seed is applicable. Unknown ancestry remains a distinct category and is included in sample totals. Previously unseen identified lineages retain zero predicted proportion in evaluation and contribute to error. Scores do not pool counts across targets or cultures.

The source dataset and input observation tables are not implicitly bundled. The comparison counts are outcome evidence. Reproducing the calculation requires access to the input snapshot named by `manifest.input_snapshot.id`; resolve `managed_relative_path` beneath the installation's `TDL_DATA_DIR` and verify the SHA-256 digest. Original mutable source paths are not used as snapshot identities. Preserve that managed snapshot separately when moving evidence between installations.

The bundle carries the fictional/synthetic label from the snapshot and the scientific limitations: observed proportions do not establish absolute growth, non-detection does not establish extinction, these baselines ignore biological effects of treatment changes, and synthetic performance does not establish biological validity. Dataset permissions remain separate from the application's code license.
