"""Export step: write CSV files for Power BI into data/output/.

Files:
  weather_daily.csv        the full daily table
  city_summary.csv         one row per city with overall statistics
  latest_day_summary.csv   one row per city for the latest available day
"""

import logging
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)

QUERIES = {
    "weather_daily.csv": "SELECT * FROM weather_daily ORDER BY city, date",
    "city_summary.csv": """
        SELECT city,
               ROUND(AVG(temp_avg_c), 1)  AS avg_temp_c,
               MAX(temp_max_c)            AS max_temp_c,
               MIN(temp_min_c)            AS min_temp_c,
               ROUND(SUM(precip_mm), 1)   AS total_rain_mm,
               COUNT(*) FILTER (WHERE precip_mm > 1) AS rainy_days,
               MAX(wind_max_kmh)          AS max_wind_kmh
        FROM weather_daily
        GROUP BY city
        ORDER BY city
    """,
    "latest_day_summary.csv": """
        SELECT city, date, temp_max_c, temp_min_c, precip_mm, wind_max_kmh
        FROM weather_daily
        WHERE date = (SELECT MAX(date) FROM weather_daily)
        ORDER BY city
    """,
}


def run_export(config):
    out_dir = Path(config["paths"]["output"])
    out_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(config["paths"]["database"], read_only=True)
    try:
        for file_name, query in QUERIES.items():
            df = con.execute(query).df()
            path = out_dir / file_name
            df.to_csv(path, index=False)
            logger.info("Exported %d rows to %s", len(df), path)
    finally:
        con.close()


if __name__ == "__main__":
    from src.extract import load_config

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_export(load_config())