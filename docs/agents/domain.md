# Domain docs

## Before exploration and design

Read root `GLOSSARY.md` and the relevant decisions in `docs/adr/`. This is one domain context even when the implementation grows into multiple language workspaces. If a referenced document is absent, proceed with available context; create domain documentation when terms or decisions are actually resolved.

## Vocabulary and decisions

Use the glossary's canonical terms in code, tests, issues and explanations. Surface contradictions with existing ADRs explicitly before proposing a change. Use domain-modeling to resolve genuine terminology gaps and maintain the glossary as terms crystallize.

Keep the glossary limited to domain definitions. Record durable architectural trade-offs in sequentially numbered ADRs. Feature requirements and acceptance criteria belong in GitHub Issues; see `issue-tracker.md`.

## Layout

- `GLOSSARY.md`: shared research-domain vocabulary.
- `docs/adr/`: project-wide architectural decisions.

A monorepo alone does not require multiple domain contexts. Introduce `GLOSSARY-MAP.md` only after distinct domain vocabularies emerge and a deliberate decision is made to separate them.
