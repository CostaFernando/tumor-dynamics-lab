# Local development

Use Node.js 22 or newer, pnpm 11.25.0, Python 3.12 or newer, and uv. Install dependencies before working offline:

```sh
pnpm install --frozen-lockfile
uv sync --frozen
```

From the repository root, initialize the fixed fictional experiment and start the API, separate worker and web development servers:

```sh
pnpm demo
pnpm dev
```

Open `http://127.0.0.1:3000`. The API listens on `http://127.0.0.1:8000`; Next.js proxies `/api` to it. `TDL_API_URL` changes that upstream address. The application is local and single-user. It contains no authentication.

`pnpm demo` is idempotent. It outputs a SHA-256 snapshot identity and preserves existing snapshots. SQLite metadata and managed snapshot files live under root `data/` by default. Set an absolute `TDL_DATA_DIR` consistently for demo setup, API and later worker processes to use another storage directory. These files are excluded from Git. Snapshot files are content-addressed and verified when read; edits to source observations do not replace a saved snapshot.

The initial inspection capability displays experiment/culture/scope context, correctly scaled sampling times, treatment exposure and withdrawal, observed proportions, raw counts, sample totals and unknown ancestry. The guided inspection view retains selection when returning to the workbench. Prepared local folders can be imported with `uv run tdl import FOLDER`; see [prepared-input format](prepared-input.md) and its fictional valid/invalid examples. Refresh the browser after import. Experiment, culture and scope selections consistently switch observations, including separately labeled descriptive cell states. Forecast setup selects a culture, comparable scope, observed cutoff and later measured targets. Queued runs are processed by the separate Python worker; closing the browser does not cancel execution. Saved attempts retain their original configuration and results while the editable draft changes.

Inspect saved data independently of HTTP:

```sh
uv run tdl inspect SNAPSHOT_ID
```

## Checks

```sh
pnpm check
pnpm test
pnpm build
```

Turborepo coordinates TypeScript and Python checks. Python source and `uv.lock` are explicit global cache inputs. Research/demo commands run directly, outside Turbo caching. `pnpm test` includes Vitest and pytest; it does not imply a full browser journey.

Regenerate the TypeScript API contract after changing Python API models/routes:

```sh
pnpm api:generate
```

Commit both `packages/api-client/openapi.json` and generated `src/schema.ts`. The client uses openapi-fetch; runtime response validation uses Zod with a compile-time generated-type agreement. Scientific rules and proportion calculations are owned by the Python package.

The UI component foundation is generated from shadcn/ui (`new-york` style); `components.json` records aliases and styling. Standard controls use the generated components; the domain-specific timeline and composition view use backend-computed observations. UI assets and system fonts are local.

Biome editor scanning is limited by root `biome.json` to TypeScript/web source and project configuration. Its scanner excludes dependencies, Git internals, Python environments, build output, caches and local research storage. The scanner-name exclusions retain compatibility with the installed Biome 2.1 editor binary. Set `"biome.requireConfiguration": true` in editor user settings so unconfigured folders also require an explicit scan scope. The release check commands remain those listed above.

## Scientific interpretation

All supplied demo observations are fictional, deterministic and CPU-only. Their sampling times span treatment exposure, withdrawal and recovery; C has a non-detection, D is identified only at later times, and unknown ancestry remains explicit. These observations test software behavior and do not validate tumor biology. Proportions do not establish absolute growth; non-detection does not establish extinction. Real-data acquisition and redistribution permissions require separate assessment.

## Persisted forecasts

`pnpm dev` includes the separate worker. To run it independently against the same storage directory:

```sh
pnpm worker
```

Queue and inspect a forecast without HTTP or Next.js:

```sh
uv run tdl forecast --snapshot SNAPSHOT_ID --culture culture-01 --scope "whole culture" --cutoff 7 --target 14 --target 21
uv run tdl worker --once
uv run tdl run RUN_ID
```

The initial `last_observed` predictor preserves the latest unsmoothed sampled composition and retains previously observed input lineages after non-detection. Unknown ancestry remains in the denominator. Python validates eligibility before queueing and passes only observations through the cutoff into the predictor. Future measurements and identities cannot inform prediction. The API exposes the same eligibility and recorded results; the browser does not implement another predictor.

Each new attempt gets a distinct identity. Configuration, snapshot identity, culture/scope, cutoff/targets, method/software versions and fixed settings are saved in SQLite; completed predictions are stored in managed local run files. Reopening reads these saved artifacts without recomputing. Failures remain explicit in run history. These baseline forecasts ignore treatment changes: crossing withdrawal does not model its biological effect. Composition forecasts do not establish absolute growth or extinction, and synthetic demonstrations do not establish biological validity.

## Held-out evidence

Successful new runs save evaluation separately from their original predictions. Open a run and choose one evidence target time to compare aligned forecast and held-out composition. The exhaustive comparison includes all input lineages, later identified lineages and unknown ancestry; target-only lineages receive zero prediction. Each target has its own total variation distance, observed share of previously unseen identified lineages, raw observed counts/totals and signed forecast-minus-observed differences in percentage points. Table filtering leaves scores, chart proportions and denominators unchanged.

The selected saved run retains its original snapshot, culture/scope, cutoff and targets while the editable draft changes. Its recorded input observations can be expanded independently of draft inspection. The guided walkthrough includes inspect → define forecast → review evidence, using the same selected attempt and evidence target as the workbench. Runs recorded before evaluation was available remain readable and explicitly lack evaluation; reopening never silently computes new results.

## Run lifecycle

The selected saved attempt offers cancellation while queued/running and retry after failure/cancellation. Cancellation and completion use guarded SQLite transitions: whichever terminal outcome commits first is retained. A cancelled attempt never exposes a successful result. Retry creates a distinct identity using the original immutable snapshot and requested configuration; the original remains in history. Actions apply to the selected attempt, independently of edits to the current draft.

One worker owns each storage directory through a local OS file lock (macOS/Linux). A second worker exits with an actionable error instead of recovering the active worker's attempts. After unexpected termination, the next worker acquires ownership and records unfinished running attempts as failed with an interruption explanation; queued jobs and completed results are preserved. Restart `pnpm worker` after a worker crash, then use **Retry as new attempt** for an interrupted run. Closing the browser has no effect on worker execution. Gracefully stopping the worker also records an in-progress attempt as interrupted.

API actions are `POST /runs/{run_id}/cancel` and `POST /runs/{run_id}/retry`; invalid IDs are rejected, missing attempts return 404 and retrying an ineligible status returns 409. Lifecycle integration tests use a completion checkpoint to force both cancellation/completion orderings, and terminate a real worker subprocess before restarting it. They do not depend on a demo job happening to run slowly.

Select **Damped trend extrapolation** in the same forecast form, or add `--method damped_trend` to the CLI command. It requires two distinct input times; an earlier cutoff can make it unavailable, and the selected method is retained until you change it. It uses the last two times, every previously observed input lineage and unknown ancestry. Fixed settings are recorded as `damped-trend-v1`, `alpha: 0.5`, and `damping: 1-exp(-h/delta)`. Centered log composition changes are damped to at most one additional observed interval and converted with stable softmax, following the [agreed method](https://github.com/CostaFernando/tumor-dynamics-lab/issues/1). Pseudocount smoothing means even a very short-horizon result differs from the unsmoothed last-observed composition. These settings are reference-method choices, not fitted biological parameters or treatment effects.
