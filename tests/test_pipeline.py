import json
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

from de_lab.pipeline import ContractError, run_pipeline

ROOT = Path(__file__).resolve().parents[1]
HEADER = "event_id,entity_id,occurred_at,category,amount_cents\n"
GOOD = "e1,c1,2026-01-02T00:30:00+01:00,Sample_A,1200\n"


def run(tmp_path, text=HEADER + GOOD):
    source = tmp_path / "input.csv"
    source.write_text(text, encoding="utf-8")
    return run_pipeline(
        source=source,
        contract=ROOT / "contracts/events.toml",
        database=tmp_path / "analytics.duckdb",
        raw_directory=tmp_path / "raw",
    )


def query(tmp_path, sql):
    with duckdb.connect(str(tmp_path / "analytics.duckdb"), read_only=True) as connection:
        return connection.execute(sql).fetchall()


def test_demo_reconciles_expected_utc_totals(tmp_path):
    run(tmp_path, (ROOT / "data/sample/events.csv").read_text(encoding="utf-8"))
    rows = query(tmp_path, "SELECT * FROM gold.daily_metrics ORDER BY 1, 2")
    assert [
        (str(day), category, count, entities, cents)
        for day, category, count, entities, cents in rows
    ] == [
        ("2026-01-01", "sample_a", 2, 2, 2000),
        ("2026-01-01", "sample_b", 2, 2, 750),
        ("2026-01-02", "sample_a", 1, 1, 2000),
        ("2026-01-02", "sample_b", 1, 1, 750),
    ]


def test_rerun_keeps_analytics_idempotent_and_audits_each_success(tmp_path):
    first = run(tmp_path)
    second = run(tmp_path)
    assert first["source_sha256"] == second["source_sha256"]
    assert first["run_id"] != second["run_id"]
    assert query(tmp_path, "SELECT count(*) FROM silver.events") == [(1,)]
    assert query(tmp_path, "SELECT count(*) FROM ops.pipeline_runs") == [(2,)]
    assert len(list((tmp_path / "raw").glob("*.csv"))) == 1
    assert (
        next((tmp_path / "raw").glob("*.csv")).read_bytes() == (tmp_path / "input.csv").read_bytes()
    )


@pytest.mark.parametrize(
    "bad",
    [
        HEADER,
        HEADER + GOOD + GOOD,
        HEADER + GOOD.replace("1200", "-1"),
        HEADER + GOOD.replace("1200", "1.5"),
        HEADER + GOOD.replace("1200", str(2**63)),
        HEADER + GOOD.replace("+01:00", ""),
        HEADER + GOOD.replace("2026-01-02", "2026-13-02"),
        HEADER + GOOD.replace("c1", " "),
        HEADER + GOOD.rstrip() + ",extra\n",
        HEADER + "e1,c1\n",
        HEADER.replace("event_id", "renamed_id") + GOOD,
    ],
)
def test_invalid_input_keeps_previous_snapshot(tmp_path, bad):
    run(tmp_path)
    before = query(tmp_path, "SELECT * FROM gold.daily_metrics")
    with pytest.raises(ContractError):
        run(tmp_path, bad)
    assert query(tmp_path, "SELECT * FROM gold.daily_metrics") == before
    assert query(tmp_path, "SELECT count(*) FROM ops.pipeline_runs") == [(1,)]


def test_replacement_is_a_full_snapshot_not_an_append(tmp_path):
    run(tmp_path)
    run(tmp_path, HEADER + GOOD.replace("e1", "e2").replace("1200", "500"))
    assert query(tmp_path, "SELECT event_id, amount_cents FROM silver.events") == [("e2", 500)]


def test_database_failure_rolls_back_replaced_tables(tmp_path):
    run(tmp_path)
    before = query(tmp_path, "SELECT * FROM silver.events")
    # Force a real database failure late in the transaction by breaking the audit schema.
    with duckdb.connect(str(tmp_path / "analytics.duckdb")) as connection:
        connection.execute("ALTER TABLE ops.pipeline_runs RENAME COLUMN row_count TO incompatible")
        connection.execute("ALTER TABLE ops.pipeline_runs ADD COLUMN extra VARCHAR")
    with pytest.raises(duckdb.Error):
        run(tmp_path, HEADER + GOOD.replace("1200", "500"))
    assert query(tmp_path, "SELECT * FROM silver.events") == before


def test_tampered_raw_snapshot_is_rejected(tmp_path):
    run(tmp_path)
    next((tmp_path / "raw").glob("*.csv")).write_bytes(b"tampered")
    with pytest.raises(ContractError, match="content hash"):
        run(tmp_path)


def test_cli_reports_failure_without_traceback(tmp_path):
    config = tmp_path / "pipeline.toml"
    config.write_text(
        '[paths]\nsource="missing.csv"\ncontract="missing.toml"\n'
        'database="db.duckdb"\nraw_directory="raw"\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "de_lab.cli", "--config", str(config)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert json.loads(result.stderr)["event"] == "pipeline_failed"


def test_cli_config_paths_resolve_from_config_directory(tmp_path):
    (tmp_path / "events.csv").write_text(HEADER + GOOD, encoding="utf-8")
    (tmp_path / "events.toml").write_bytes((ROOT / "contracts/events.toml").read_bytes())
    config = tmp_path / "pipeline.toml"
    config.write_text(
        '[paths]\nsource="events.csv"\ncontract="events.toml"\n'
        'database="out/db.duckdb"\nraw_directory="raw"\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "de_lab.cli", "--config", str(config)],
        cwd=tmp_path.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["rows"] == 1
    assert (tmp_path / "out/db.duckdb").exists()
