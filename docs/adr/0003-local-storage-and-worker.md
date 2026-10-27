# Persist local research inputs and execute runs independently of the browser

The initial single-user application uses SQLite for metadata and a persistent run queue, with immutable imported snapshots and result files in managed local storage. A separate Python worker allows runs to survive browser closure without requiring a database server or Redis; interrupted attempts remain explicit and retries create new runs. This design favors a reproducible local research installation over distributed execution, which would require revisiting coordination and storage assumptions.
