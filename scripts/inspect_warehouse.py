"""Print gold results and successful-run count from the default local warehouse."""

import json
from pathlib import Path

import duckdb


def main() -> None:
    database = Path(__file__).resolve().parents[1] / "data/warehouse/analytics.duckdb"
    if not database.exists():
        raise SystemExit("Warehouse missing. Run: uv run --locked de-lab")
    with duckdb.connect(str(database), read_only=True) as connection:
        cursor = connection.execute("SELECT * FROM gold.daily_metrics ORDER BY 1, 2")
        columns = [column[0] for column in cursor.description]
        metrics = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        successful_runs = connection.execute("SELECT count(*) FROM ops.pipeline_runs").fetchone()[0]
    # JSON stays readable on Windows terminals that use a legacy code page.
    print(
        json.dumps(
            {"daily_metrics": metrics, "successful_runs": successful_runs}, default=str, indent=2
        )
    )


if __name__ == "__main__":
    main()
