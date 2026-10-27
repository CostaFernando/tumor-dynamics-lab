# Issue tracker: GitHub

Issues and specifications live in `CostaFernando/tumor-dynamics-lab` on GitHub. Use the `gh` CLI; infer the repository from the Git remote when working in this clone.

## Operations

- Read: `gh issue view <number> --json number,title,body,labels,comments`.
- List: `gh issue list --state open --json number,title,url,labels`.
- Create: `gh issue create --title "..." --body-file <path>`.
- Update a body: `gh issue edit <number> --body-file <path>`.
- Comment: `gh issue comment <number> --body-file <path>`.
- Label: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`.
- Close: `gh issue close <number> --comment "..."`.

For multiline bodies, write exact text to a temporary file outside the repository and pass `--body-file`. Review the existing issue before changing it. When a skill says to publish to the tracker, create or update a GitHub issue; when it says to fetch a ticket, read that issue and its relevant comments.

## Specifications and related work

Keep specifications authoritative in GitHub Issues and link to them from the README. Repository documentation contains enduring vocabulary, architecture decisions and operational conventions. Avoid retaining a duplicate specification or interview log in the repository.

Use native GitHub sub-issues and dependencies when supported. Otherwise link child work with `Part of #<parent>` and record blockers explicitly. If a workflow needs GitHub API identifiers, resolve the issue's database ID rather than substituting its issue number or node ID.

## Pull requests as a triage surface

**PRs as a request surface: no.**

Issues and PRs share a number space. If a referenced number is ambiguous, resolve its type before editing it. This flag can be changed here later if external PRs should enter the feature-request triage queue.
