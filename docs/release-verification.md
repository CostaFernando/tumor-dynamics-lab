# Local release and verification

The supported release is a CPU-only, single-user research installation on macOS/Linux. All demo observations are original fictional data. Its baseline comparisons establish software behavior, rather than biological validity. Neural training, expression prediction, study-specific real-data adapters, browser uploads, hypothetical treatment simulation and public deployment remain deferred.

## Install and run

Install Node.js 22+, pnpm 11.25.0, Python 3.12+ and uv. From the repository root, while installation network access is available:

```sh
pnpm install --frozen-lockfile
uv sync --frozen
pnpm check
pnpm test
pnpm build
pnpm demo
```

`pnpm demo` is the single demo-setup command. Repetition preserves the existing content-addressed snapshot. Development startup is `pnpm dev`, which starts Next.js, FastAPI and the separate worker. For the built production interface, use these three commands in separate terminals, from the root:

```sh
uv run --offline --no-sync uvicorn tumor_api.app:app --host 127.0.0.1 --port 8000
uv run --offline --no-sync tdl worker
pnpm --filter @tdl/web start
```

Open `http://127.0.0.1:3000`. Set the same absolute `TDL_DATA_DIR` for demo/import, API and worker to relocate storage. The default is root `data/`, excluded from Git. Stop each process with Ctrl-C. The worker's ownership lock and interrupted-attempt recovery apply to production and development alike. The frontend contains local assets and system fonts; it fetches the local API through `/api`.

To use another API address, set `TDL_API_URL` consistently during frontend build and startup. Rebuild after changing that address: the generated Next.js rewrite configuration belongs to the built artifact. The default native address is `http://127.0.0.1:8000`; the Docker image builds against `http://api:8000`.

Prepared-folder imports use `uv run --offline --no-sync tdl import FOLDER`. See [format, examples and validation](prepared-input.md). Refresh the browser after importing. The bundled `fixtures/prepared-example` demonstrates the format; the five-timepoint demo supplies enough history and later targets to exercise both predictors.

## Integrated checks and offline execution

```sh
pnpm verify:release
pnpm benchmark:demo
```

`verify:release` creates temporary prepared demo input, imports it through the installed CLI, launches a real localhost API and executes each baseline with a separate CLI worker. It verifies source-folder mutation cannot alter the snapshot, saved held-out evaluation, stable reopen/ZIP download, and cancellation/retry preserving the original identity. All temporary services/storage are cleaned up. The ordinary Python suite includes this command as a release seam, plus the feature-owned deterministic worker termination/restart and cancellation/completion race checks. Vitest remains the TypeScript runner. The real browser journey is recorded separately below.

These commands run outside Turbo caching. Normal coordinated checks include explicit global inputs for Python sources, both Python package manifests, root `pyproject.toml`, `uv.lock` and verification scripts; package lockfiles and package-local sources remain task inputs. Research runs are never Turbo tasks.

Offline means installation/build has already finished. Setting package managers to offline mode alone does not enforce network isolation. On macOS, this supplied OS profile permits localhost and denies other outbound connections:

```sh
sandbox-exec -f scripts/offline-local.sb .venv/bin/python scripts/verify_release.py
sandbox-exec -f scripts/offline-local.sb .venv/bin/python scripts/benchmark_demo.py
```

For a whole application check, launch the API, worker, built frontend and a fresh browser test process under outbound-denying OS isolation while retaining required local communication. Existing browser processes do not inherit a newly applied profile. Browser "offline" emulation also blocks localhost, so it is unsuitable for this application journey. Normal use simply needs the installed dependencies and local assets.

## Docker path

The image installs locked dependencies and builds the frontend before execution. Compose separates demo initialization, API, worker and web processes and mounts persistent `research` storage. API and worker attach only to the internal `research` network. Web also attaches to an ordinary `ingress` bridge so Docker can publish its port on localhost. The web container therefore has egress capability: normal Compose startup is a local execution path, not a claim of full network isolation. Only the web port is published, bound to localhost.

```sh
docker compose build api
docker compose up -d --no-build
# Open http://127.0.0.1:3000
docker compose logs worker
docker compose down
```

`docker compose down` preserves the research volume. To use another local web port, prefix startup with `TDL_WEB_PORT=3300`. Import a prepared folder through a read-only bind mount:

```sh
docker compose run --rm --no-deps -v /ABSOLUTE/PREPARED/FOLDER:/input:ro api tdl import /input
```

Build the image before disabling installation network access. `docker compose config --quiet` validates the definition. Once built, the standalone integrated command can also run with all container networking disabled:

```sh
docker run --rm --network none tumor-dynamics-lab:local python scripts/verify_release.py
```

That command's API and worker communicate over container loopback, and its two-method import/forecast/evaluation/reopen/export/cancel/retry workflow passed with `--network none`. The normal Compose browser path uses internal research communication plus the web ingress bridge described above. Full browser/application outbound-denied verification was performed natively under OS isolation, as recorded below. The supplied development container path is separate from any future DataAnnotation packaging adapter or environment restrictions.

**Docker verification:** The image built successfully on Linux arm64 with Python 3.12.12. The installed release command and all 62 Python tests passed with `--network none`. Normal Compose startup on localhost port 3300 completed both predictors through the web API proxy and separate worker. A fresh browser reopened both saved methods and downloaded ZIPs matching the saved export hashes. Compose down/up retained the same snapshot, run records and export bytes in its named volume. API and worker external TCP probes were rejected with network-unreachable errors. After the reviewed UI/scientific preparation changes at `c67f104`, the image was rebuilt and both-method network-disabled release and normal proxy workflows passed again; the final browser evidence rendered with zero console errors or warnings. The web ingress bridge retains the egress capability stated above. Verification containers were stopped afterward; the named research volume was preserved.

## Recorded verification — 2026-10-27

- `pnpm check`, `pnpm test` and `pnpm build` passed: 62 Python tests and 17 Vitest tests. Standard controls use shadcn/ui, browser boundaries use Zod, shared Python models use Pydantic, and API types are generated from OpenAPI.
- `sandbox-exec -f scripts/offline-local.sb .venv/bin/python scripts/verify_release.py` passed with both baseline methods, two evidence bundles, source snapshot immutability, saved results and distinct retry identity. The fixed snapshot is `9034c7b15e08740295c68cd16ddcdff472a4c64daabbf887c47038e829a9a7e9`.
- Feature integration tests terminate a real worker subprocess and force both cancellation/completion orderings with deterministic checkpoints. Queued and completed attempts survive restart.
- The production browser journey passed with a prepared fixed-demo folder imported through the CLI. API, worker, built Next.js and a fresh Chrome process ran under OS outbound-denying isolation permitting localhost and local Unix IPC; an external `1.1.1.1:443` probe raised `PermissionError`. All recorded page resource origins were `http://127.0.0.1:3000`.
- Guided inspect → define → create → review, target switching and return to the workbench preserved the selected run and draft. Editing draft cutoff to 0 retained the saved cutoff of 7 and its export. Last-observed day-14 TVD was 0.200 and previously unseen share was 10%. Trend remained selected and blocked with a reason at cutoff 0; restoring cutoff 7 allowed a direct workbench forecast. Closing/reopening the browser preserved the completed trend in history. Both methods downloaded ZIPs whose snapshot, method, run identity, unknown ancestry and unseen-lineage comparisons were checked.
- A 390-pixel viewport had a 390-pixel document width, with usable evidence and controls. The ephemeral browser test profile required browser sandbox flags inside the separate OS sandbox; application configuration and normal browser startup were unchanged.

## Fixed-demo measurements

Measured on macOS 27.0.1 arm64, Python 3.13.2, using the snapshot above, cutoff 7 days and targets 14/21 days. The predictors are deterministic. `pnpm benchmark:demo` measures both predictors and each two-target evaluation per sample, including scientific preparation, without HTTP or browser work. Five observed samples under outbound-denying OS isolation were 0.149, 0.071, 0.062, 0.065 and 0.060 milliseconds; median **0.065 ms**. Overall scientific-process maximum RSS was **38.52 MiB**, including imports, fixture and preparation.

A separate `/usr/bin/time -l .venv/bin/python scripts/verify_release.py` observation took **0.83 seconds** elapsed for the complete temporary CLI/API/worker/export verification command. Parent-process maximum RSS was **64.23 MiB**; it is not aggregate peak memory of its API/worker children, and it excludes frontend/browser/Docker VM memory. For Linux `/usr/bin/time -v`, maximum RSS units are KiB; macOS `time -l` and `ru_maxrss` use bytes. The benchmark normalizes platform units explicitly.

These observations establish a measurement procedure and an initial reference. No performance acceptance threshold has been imposed, and the small fictional workload does not establish real-data scalability.
