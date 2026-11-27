"""Run every query in sql/analysis.sql and print the results.

Each query starts with a comment line like: -- Q1: some title
"""

import logging
from pathlib import Path

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

ANALYSIS_PATH = "sql/analysis.sql"


def split_queries(sql_text):
    """Return a list of (title, query) from the analysis file."""
    queries = []
    for block in sql_text.split(";"):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        title = lines[0].lstrip("- ").strip() if lines[0].startswith("--") else "Query"
        queries.append((title, block))
    return queries


def run_analysis(config):
    sql_text = Path(ANALYSIS_PATH).read_text(encoding="utf-8")
    con = duckdb.connect(config["paths"]["database"], read_only=True)
    try:
        for title, query in split_queries(sql_text):
            df = con.execute(query).df()
            print(f"\n=== {title} ===")
            print(df.to_string(index=False))
    finally:
        con.close()


if __name__ == "__main__":
    from src.extract import load_config

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    pd.set_option("display.width", 200)
    run_analysis(load_config())