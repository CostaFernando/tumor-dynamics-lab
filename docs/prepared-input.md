# Prepared input format, version 1

Import a local folder containing `experiment.json` from the repository root:

```sh
uv run tdl import fixtures/prepared-example
uv run tdl inspect SNAPSHOT_ID
```

Use the returned SHA-256 identity in `inspect`, or refresh the browser and select the new experiment snapshot. Importing the same content returns the same identity. A changed input creates another snapshot; it never updates a previous one. Imports are a CLI workflow; the browser has no upload control.

The bundled [valid example](../fixtures/prepared-example/experiment.json) is fictional. It demonstrates metadata, two separate cultures, exposure/withdrawal, two whole-culture times, a selected fraction, raw lineage counts, explicit unknown ancestry and optional descriptive cell-state information. The [invalid example](../fixtures/invalid-negative-count/experiment.json) has a negative count and exits unsuccessfully:

```sh
uv run tdl import fixtures/invalid-negative-count
# Error: samples.0.counts.A ... Input should be greater than or equal to 0
```

## File structure

The top-level JSON object has these fields. Unknown fields are rejected.

| Field | Meaning |
| --- | --- |
| `format_version` | Required literal string `"1"`; future versions are not inferred. |
| `id`, `name` | Nonempty experiment identifier and display name. |
| `synthetic` | JSON boolean; label all fictional inputs `true`. |
| `time_unit` | Exactly `"hours"` or `"days"`, applying to all sample and treatment times. Convert other units explicitly during preparation. |
| `description` | Optional text describing the experiment and sampling context. |
| `acquisition` | Optional provenance text. For real data, record accession/source URL, acquisition date, preparation method and relevant source version. |
| `redistribution` | Optional permissions text. For real data, record license/access restrictions and whether redistribution is allowed. Empty text does not grant permission. |
| `cultures` | Nonempty array of culture metadata. |
| `samples` | Nonempty array of sample/count records. |

Each culture has a unique `id`, a `name`, and optional `treatments` (default `[]`). Each treatment has a `name`, finite numeric `start` and `end` with `end > start`, and optional `dose` text. `end` marks withdrawal of that exposure; an empty treatment list means no supplied schedule. Cultures remain separate and are not presumed biologically independent. A culture with no samples can be recorded, and the browser explains its empty observation state.

Each sample has a unique `id`, a resolved `culture_id`, a nonempty `scope`, a finite numeric `time`, and a `counts` object. `scope` names the comparable sampling population, such as `whole culture` or `selected fraction`. Choose honest, consistent scope labels during preparation. Different scopes remain separate even at the same time. Multiple samples at the same culture/scope/time are rejected; combining technical replicates is an explicit upstream preparation decision.

`counts` maps experiment-local lineage identifiers to nonnegative JSON integer counts. The reserved key `__unknown__` is required for every sample, including when its count is zero. It denotes observed cells with unresolved ancestry, not a biological lineage. Sample totals include it. The total must be greater than zero. Omitted identified lineages have no observed cells in that sample; this is non-detection and does not establish extinction. Identical lineage labels in unrelated experiments do not identify shared ancestry. JSON objects act as count tables keyed by lineage; duplicate keys are rejected rather than silently taking the last value.

`cell_state_summary` is optional descriptive text (or `null`) on a sample. It is displayed separately from lineage identity. Full expression matrices and study-specific adapters are not required by this format. Other files in the folder are not imported or represented in the snapshot; retain expression matrices and other source assets separately with their own provenance.

## Rejections and immutable storage

Validation reuses strict Pydantic models from the scientific package. Counts such as `-1`, `1.5`, `true` or `"4"` are rejected, rather than coerced or rounded. Missing unknown-ancestry counts, zero-total samples, unresolved cultures, duplicate cultures/sample IDs/count keys, repeated culture/scope/time tuples, nonfinite times, unsupported versions and ambiguous units are rejected. Duplicate JSON metadata keys are also rejected. CLI errors identify the file or model field to repair; a rejected import creates no usable snapshot. Do not silently repair identifiers, pool fractions or remove unknown ancestry during preparation.

Accepted model content is copied to managed `snapshots/SHA256.json`, with metadata in SQLite under `TDL_DATA_DIR` (default root `data/`). Identity is computed from canonical validated JSON, independent of original path, whitespace and object-key order. The snapshot retains the accepted observations and metadata, and is verified against its digest when read. Subsequent source-folder edits do not change it. Browser/API inspection always resolves that managed snapshot, preserving observed counts, totals and proportions.

External dataset permissions are separate from the code license. Download real inputs separately, record acquisition/redistribution information and keep restricted materials out of Git. The bundled examples and demo are original fictional data; no real dataset is distributed here.
