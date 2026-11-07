"""Command-line entry point. Run from the repository root after `uv sync --locked`."""

import argparse
import json
import logging
import tomllib
from pathlib import Path

import duckdb

from de_lab.pipeline import ContractError, run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the synthetic batch pipeline.")
    parser.add_argument("--config", type=Path, default=Path("config/pipeline.toml"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        config_file = args.config.resolve()
        config = tomllib.loads(config_file.read_text(encoding="utf-8"))
        paths = config["paths"]

        def resolve(name: str) -> Path:
            return (config_file.parent / paths[name]).resolve()

        result = run_pipeline(
            source=resolve("source"),
            contract=resolve("contract"),
            database=resolve("database"),
            raw_directory=resolve("raw_directory"),
        )
    except (ContractError, OSError, ValueError, KeyError, TypeError, duckdb.Error) as exc:
        logging.error(json.dumps({"event": "pipeline_failed", "error": str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
