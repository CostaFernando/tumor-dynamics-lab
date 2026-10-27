# Local development

Use Node.js 22 or newer, pnpm 11.25.0, Python 3.12 or newer, and uv. Install dependencies before working offline:

```sh
pnpm install --frozen-lockfile
uv sync --frozen
```

From the repository root, initialize the fixed fictional experiment and start the API and web development servers:

```sh
pnpm demo
pnpm dev
```

Open `http://127.0.0.1:3000`. The API listens on `http://127.0.0.1:8000`; Next.js proxies `/api` to it. `TDL_API_URL` changes that upstream address. The application is local and single-user. It contains no authentication.

`pnpm demo` is idempotent. It outputs a SHA-256 snapshot identity and preserves existing snapshots. SQLite metadata and managed snapshot files live under root `data/` by default. Set an absolute `TDL_DATA_DIR` consistently for demo setup, API and later worker processes to use another storage directory. These files are excluded from Git. Snapshot files are content-addressed and verified when read; edits to source observations do not replace a saved snapshot.

The initial inspection capability displays experiment/culture/scope context, correctly scaled sampling times, treatment exposure and withdrawal, observed proportions, raw counts, sample totals and unknown ancestry. The guided inspection view retains selection when returning to the workbench. Forecast configuration is added in subsequent implementation slices.

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

## Scientific interpretation

All supplied demo observations are fictional, deterministic and CPU-only. Their sampling times span treatment exposure, withdrawal and recovery; C has a non-detection, D is identified only at later times, and unknown ancestry remains explicit. These observations test software behavior and do not validate tumor biology. Proportions do not establish absolute growth; non-detection does not establish extinction. Real-data acquisition and redistribution permissions require separate assessment.
