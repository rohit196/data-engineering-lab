"""Validate a complete input snapshot, then atomically rebuild analytics tables."""

import csv
import hashlib
import io
import json
import logging
import re
import tomllib
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from uuid import uuid4

import duckdb

LOGGER = logging.getLogger(__name__)
COLUMNS = ["event_id", "entity_id", "occurred_at", "category", "amount_cents"]


class ContractError(ValueError):
    """The input violates the documented source contract."""


def validate(payload: bytes, contract: Path) -> list[tuple[str, ...]]:
    spec = tomllib.loads(contract.read_text(encoding="utf-8"))
    supported = {
        "version": 1,
        "columns": COLUMNS,
        "unique_key": "event_id",
        "required_columns": COLUMNS,
        "timestamp_column": "occurred_at",
        "timestamp_requires_timezone": True,
        "nonnegative_integer_column": "amount_cents",
    }
    for key, value in supported.items():
        if spec.get(key) != value:
            raise ContractError(
                f"Unsupported contract setting: {key}. Update the adapter and tests."
            )
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")), strict=True)
        if reader.fieldnames != spec["columns"]:
            raise ContractError(f"Expected CSV header in this order: {spec['columns']}")
        rows = []
        seen = set()
        for line, record in enumerate(reader, start=2):
            if None in record or any(record.get(key) is None for key in COLUMNS):
                raise ContractError(f"Row {line}: wrong number of fields")
            values = {key: record[key].strip() for key in COLUMNS}
            if any(not value for value in values.values()):
                raise ContractError(f"Row {line}: required value is empty")
            if values["event_id"] in seen:
                raise ContractError(f"Row {line}: duplicate event_id")
            seen.add(values["event_id"])
            try:
                timestamp = datetime.fromisoformat(values["occurred_at"])
                if timestamp.utcoffset() is None:
                    raise ValueError("timezone required")
                values["occurred_at"] = timestamp.astimezone(UTC).isoformat()
            except ValueError as exc:
                raise ContractError(
                    f"Row {line}: occurred_at requires an ISO timestamp with timezone"
                ) from exc
            amount = values["amount_cents"]
            if not re.fullmatch(r"[0-9]+", amount) or int(amount) > 2**63 - 1:
                raise ContractError(f"Row {line}: amount_cents requires a nonnegative BIGINT")
            rows.append(tuple(values[key] for key in COLUMNS))
        if not rows:
            raise ContractError("Input is empty; refusing to replace the current snapshot")
        return rows
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ContractError("Input must be a well-formed UTF-8 CSV") from exc


def run_pipeline(
    *, source: Path, contract: Path, database: Path, raw_directory: Path
) -> dict[str, str | int]:
    payload = source.read_bytes()
    rows = validate(payload, contract)
    source_hash = hashlib.sha256(payload).hexdigest()
    run_id = str(uuid4())
    raw_directory.mkdir(parents=True, exist_ok=True)
    snapshot = raw_directory / f"{source_hash}.csv"
    # Exclusive creation keeps an accepted source snapshot immutable across reruns.
    try:
        with snapshot.open("xb") as output:
            output.write(payload)
    except FileExistsError:
        if snapshot.read_bytes() != payload:
            raise ContractError("Raw snapshot does not match its content hash") from None

    database.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.info(json.dumps({"event": "pipeline_started", "run_id": run_id, "rows": len(rows)}))
    with duckdb.connect(str(database)) as connection:
        connection.execute("SET TimeZone='UTC'")
        connection.execute("BEGIN TRANSACTION")
        try:
            sql = files("de_lab").joinpath("sql")
            connection.execute(sql.joinpath("bronze.sql").read_text(encoding="utf-8"))
            connection.executemany("INSERT INTO bronze.events VALUES (?, ?, ?, ?, ?)", rows)
            connection.execute(sql.joinpath("silver.sql").read_text(encoding="utf-8"))
            connection.execute(sql.joinpath("gold.sql").read_text(encoding="utf-8"))
            silver_count = connection.execute("SELECT count(*) FROM silver.events").fetchone()[0]
            gold_count = connection.execute(
                "SELECT coalesce(sum(event_count), 0) FROM gold.daily_metrics"
            ).fetchone()[0]
            if silver_count != len(rows) or gold_count != len(rows):
                raise ContractError("Row-count reconciliation failed")
            # Only successful runs are persisted here; failures are emitted to stderr by the CLI.
            connection.execute("""
                CREATE TABLE IF NOT EXISTS ops.pipeline_runs (
                    run_id VARCHAR PRIMARY KEY, completed_at TIMESTAMPTZ,
                    source_sha256 VARCHAR, row_count BIGINT
                )
            """)
            connection.execute(
                "INSERT INTO ops.pipeline_runs VALUES (?, ?, ?, ?)",
                [run_id, datetime.now(UTC), source_hash, len(rows)],
            )
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    result = {
        "event": "pipeline_completed",
        "run_id": run_id,
        "rows": len(rows),
        "source_sha256": source_hash,
    }
    LOGGER.info(json.dumps(result))
    return result
