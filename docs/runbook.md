# Local operating runbook

Run commands from the repository root. Install dependencies using `uv sync --locked`.

## Run and inspect

```sh
uv run --locked de-lab --config config/pipeline.toml
uv run --locked python scripts/inspect_warehouse.py
```

Paths in the TOML config resolve relative to that config file. Supply a different config using `--config path/to/pipeline.toml`.

## Failure handling

1. Read the final JSON error on stderr and inspect the source/contract named in the configuration.
2. For invalid input, correct the source upstream. Existing warehouse tables remain unchanged.
3. For a database error, stop overlapping processes, check file permissions and available disk space, and inspect the message. Do not delete a working warehouse to hide a failure.
4. For a raw-snapshot hash mismatch, preserve the suspicious file outside the raw directory for investigation. Rerun only after resolving the corruption.
5. Re-execute the same command. This rebuilds a complete snapshot and adds a successful audit record; it does not append duplicate events.

The previous snapshot is preserved on a failed transaction. Restoring an older accepted input requires a config that points `source` to the corresponding raw CSV. Confirm the config points to the intended warehouse before running it.

## Checks before a change

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

CI additionally runs the bundled sample. A failing workflow blocks confidence in the change; investigate its logs before presenting the repository as working.

## Dependency changes

Edit `pyproject.toml` or use `uv add`, run `uv lock`, and rerun the checks. Commit `uv.lock` with the dependency change. Do not upgrade everything merely to run the project.

## Local data and credentials

Raw snapshots, warehouse files, `.env` files, virtual environments, and caches are ignored. The starter has no external service credentials. Inspect staged changes before pushing; Git ignore rules do not remove files already tracked.
