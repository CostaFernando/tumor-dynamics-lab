# Throwaway UX directions

Question: should the first-release retrospective forecasting workflow be organized as a guided study, a spatial workbench, or a run notebook?

**Approved by Fernando on 2026-10-27: B — Research workbench, with A's guided first-run flow.** Keep setup, observations, evidence, and history together for repeated research work; use inspect → configure → review guidance to introduce the forecast boundary. This remains a throwaway prototype, not production implementation.

## Run

From the repository root, with Python 3:

```sh
python3 apps/web/prototype/serve.py
```

Open http://127.0.0.1:4317/?variant=B. No dependencies or network needed. The server binds only to localhost and refuses to run with `NODE_ENV=production`.

There is no existing application route or styling system in the repository. This isolated HTML page sits beside the planned web application and deliberately does not scaffold the production stack.

| Variant | Structure | Decision to explore |
| --- | --- | --- |
| A — Guided study | Three steps: inspect, configure, review | Does a focused path clarify the forecast boundary, or slow down repeat work? |
| B — Research workbench | Setup on the left, observations/evidence in the middle, run history beside them on wide screens | Is keeping context visible worth the increased density? |
| C — Run notebook | Research records sidebar and a sequential context/recipe/evidence document | Does a readable research record justify scrolling between setup and results? |

The default entry opens B. **Start guided walkthrough** opens A; **Return to workbench** returns to B while retaining the draft and runs. C remains an unselected exploration for historical comparison.

Switch with the bottom bar or left/right arrows outside form controls. `?variant=A`, `B`, or `C` survives reload. Drafts and runs survive variant switching but not page reload.

## Suggested comparison

1. Inspect the day-7 input composition, then view raw counts. Lineage C is not detected at day 7; it is not declared extinct.
2. Create the default last-observed forecast for days 14 and 21. Day-14 total variation distance is 0.200 and previously unseen lineage share is 10%.
3. Switch layouts with that result open. Compare how easily you can identify the input boundary, original run configuration, and per-target evidence.
4. Select trend, then move the cutoff to day 0. The method remains selected but unavailable; there is no silent fallback.
5. Select the incompatible scope to inspect the blocking explanation, then return to whole culture.
6. Cancel a new run, then retry. The previous attempt remains and a new identity is created.
7. Open **Inspect prototype state** and select **Worker interruption** before creating a run to explore a failed attempt. Return the scenario to **Succeed** before retrying.
8. Change the draft after a successful run and reopen that result. Its original cutoff and method remain visible.
9. Export a synthetic demo JSON. This is not the production evidence-bundle format.

All relevant state is visible in the state drawer and logged to the console. The drawer also resets in-memory runs.

## Deliberate limits

- One fictional culture and five samples; no real dataset, database, API, worker, CLI import, or durable persistence.
- Worker execution and interruptions are simulated using browser timers. Closing the tab loses state, unlike the planned application.
- Tiny fixture calculations are disposable UI support. Production calculations and eligibility remain owned by Python per ADR 0002; do not migrate this JavaScript into production.
- No cell-state prediction, uncertainty intervals, or biological validation. Unknown ancestry and previously unseen identified lineages are separate.
- No automated tests by design for this throwaway artifact. Manual browser inspection covered the three layouts, a completed baseline comparison, method/scope blocking, cancellation, retry identity, and retained state across switches.

## Capture and follow-up

Primary source: `codex/prototype-ux-directions`, under `apps/web/prototype/`.

Spec: issue #1. Relevant implementation slices: #2–#8. The approved UX decision and its implementation acceptance criteria are authoritative in issue #1 and the affected tickets #2–#9. The scientific constraints in #1 remain unchanged.

The approved direction is B with A's guidance. C's separate notebook navigation is not part of the chosen direction. Keep the full exploration on this branch, outside main, and rewrite the accepted design under production constraints. The comparison switcher, state inspector, simulated worker, and browser-side fixture calculations are prototype tools, not product requirements.

## Variant B motion exploration — 2026-10-27

Added at Fernando's request after selection of B + A guidance:

- Original cell-inspired SVG illustration with a brief, finite nucleus/organelles entrance (decorative, not biological simulation).
- Staggered workbench entrance and short evidence transitions only when the selected run, status or target changes. Ordinary form changes do not replay the workspace entrance.
- Queued pulse, running spinner and completion check, with explicit textual status and a shortcut to the selected attempt/evidence. These are indeterminate indicators, not estimates of progress.
- Subtle button feedback, a motion toggle, and `prefers-reduced-motion` support. Chart geometry, proportions and numerical scores are never animated or interpolated.
- Focus retention for identified form controls/action buttons through the prototype's rerenders.

Reviewed [LottieFiles cell collection](https://lottiefiles.com/free-animations/cell) and [general gallery](https://lottiefiles.com/free-animations/). Chose original inline SVG/CSS for this small motion layer: no downloaded assets, player dependency, CDN or external license requirements. Original assets are covered by the repository's MIT license.

Manual browser verification: variant B renders, a forecast reaches completed evidence, the queued glyph has the expected animation, and turning motion off results in `animation: none` and zero transition duration. OS reduced-motion handling is implemented in CSS and the control label; no OS setting was changed for verification.

This is a prototype refinement for review, not an added production acceptance requirement. The approved B + A structure and mandatory production libraries remain specified in issue #1. Reuse the motion intent only after review; keep the throwaway implementation on this branch.
