# Tumor Dynamics Lab

A local research workbench for exploring how tumor populations change during treatment and recovery, forecasting lineage proportions, and comparing predictions with later experimental observations.

## Project status

The local implementation supports prepared-folder imports, an immutable synthetic demonstration, both baseline predictors, saved held-out evaluation, cancellation/interruption/retry, history and evidence ZIP export. The Next.js research workbench includes the inspect → configure → review walkthrough. See [installation and development](docs/development.md), [release verification](docs/release-verification.md) and [evidence bundles](docs/evidence-export.md).

The authoritative first-release specification lives in GitHub Issues; see the specification link below. Verification uses fictional data and establishes software behavior; real-data biological validation remains future work.

## Quick start

Install Node.js 22+, pnpm 11.25.0, Python 3.12+ and uv, then run:

```sh
pnpm install --frozen-lockfile
uv sync --frozen
pnpm demo
pnpm dev
```

Open `http://127.0.0.1:3000`. Dependencies and local assets must be installed before offline execution. The [release guide](docs/release-verification.md) describes production startup, offline checks and Docker persistence. The Docker image, separate-service workflow, persistent storage and evidence downloads have also been verified; the release guide distinguishes native offline isolation from the normal Compose network scope.

## First release

The first workflow imports a prepared experiment through a command-line interface, displays treatment and sampling timelines, and lets a researcher forecast later lineage proportions from an earlier cutoff. Two reference methods—last observed composition and damped trend extrapolation—are compared with held-out observations. Runs persist locally and can be reopened or exported with their configurations and results.

The release includes an explicitly fictional, CPU-only demonstration that operates without network access after installation. Real research datasets are acquired separately. Research value drives the roadmap; reusable engineering evaluation tasks can emerge from normal development.

## Scientific scope

- A lineage identifies shared ancestry; a cell state describes measured biological characteristics. These are separate dimensions.
- Observed proportions describe sampled composition. They do not establish absolute cell growth, and non-detection does not establish extinction.
- Predictions use observations available by the cutoff. Held-out measurements and newly detected lineage identities enter evaluation separately.
- Synthetic demonstrations exercise software behavior; biological validation requires real experiments and an appropriate evaluation protocol.

The longer-term research direction includes temporal cancer datasets such as SUM159PT, Watermelon and TS543. Dataset adapters, gene-expression forecasting and learned models follow the first release. This is a research project; clinical treatment selection is outside its scope.

## Architecture

| Component | Responsibility |
| --- | --- |
| Next.js / TypeScript | Research interface and visual comparisons |
| FastAPI / Python | Validated HTTP API and OpenAPI contract |
| Python scientific package | Dataset validation, eligibility, predictors and evaluation |
| Python worker | Persistent execution independent of the browser |
| SQLite and local files | Metadata, queue, immutable snapshots and results |
| pnpm + uv + Turborepo | Language workspaces and coordinated development commands |

The TypeScript API client is generated from the Python API contract. The scientific package runs independently through the CLI and tests. The supported installation uses one local user and one worker on macOS/Linux.

## Documentation

- [First-release specification and accepted design decisions — issue #1](https://github.com/CostaFernando/tumor-dynamics-lab/issues/1)
- [Domain glossary](GLOSSARY.md)
- [Architecture decisions](docs/adr/)
- [Issue tracker conventions](docs/agents/issue-tracker.md)
- [Triage labels](docs/agents/triage-labels.md)
- [Domain documentation conventions](docs/agents/domain.md)
- [Agent entry point](AGENTS.md)

Specifications and implementation tickets live in GitHub Issues. The repository holds enduring vocabulary, architecture decisions and operational documentation.

## Data and reproducibility

Prepared inputs begin with experiment metadata and lineage counts per sample; full expression matrices are optional. Imports create immutable local snapshots. Each run identifies its input snapshot, method version, cutoff, settings and outcomes.

Local datasets, run artifacts, databases, exports and credentials are excluded from Git. Small synthetic fixtures can be versioned under `fixtures/`. Dataset redistribution permissions are checked separately from the project license.

## License

Original project code and documentation are available under the [MIT license](LICENSE). External datasets and third-party materials retain their own terms.
