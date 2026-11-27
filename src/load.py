"""Load step: write the clean table into DuckDB.

Full reload: the table is created from sql/schema.sql if needed, then its
contents are replaced inside one transaction. If the insert fails, the old
data is restored, so the table is never left empty.
"""

import logging
from pathlib import Path

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

SCHEMA_PATH = "sql/schema.sql"
TABLE = "weather_daily"

COLUMNS = [
    "city",
    "date",
    "temp_max_c",
    "temp_min_c",
    "temp_avg_c",
    "precip_mm",
    "wind_max_kmh",
    "loaded_at",
]


def prepare_for_load(df):
    """Make sure column order and types match the table."""
    df = df[COLUMNS].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["loaded_at"] = pd.to_datetime(df["loaded_at"])
    return df


def run_load(df, config):
    """Replace the contents of weather_daily with df. Return the row count."""
    db_path = Path(config["paths"]["database"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    df = prepare_for_load(df)
    schema_sql = Path(SCHEMA_PATH).read_text(encoding="utf-8")

    con = duckdb.connect(str(db_path))
    try:
        con.execute(schema_sql)  # creates the table if it does not exist

        con.execute("BEGIN TRANSACTION")
        try:
            con.execute(f"DELETE FROM {TABLE}")
            con.register("df_to_load", df)
            col_list = ", ".join(COLUMNS)
            con.execute(
                f"INSERT INTO {TABLE} ({col_list}) SELECT {col_list} FROM df_to_load"
            )
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            logger.error("Load failed, transaction rolled back")
            raise

        rows = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
    finally:
        con.close()

    logger.info("Loaded %d rows into %s (%s)", rows, TABLE, db_path)
    if rows != len(df):
        raise RuntimeError(f"Row count mismatch: sent {len(df)}, table has {rows}")
    return rows


if __name__ == "__main__":
    from src.extract import load_config

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config = load_config()
    clean_path = f"{config['paths']['clean']}/weather_clean.csv"
    run_load(pd.read_csv(clean_path), config)