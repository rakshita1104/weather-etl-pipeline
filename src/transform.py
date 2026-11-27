"""Transform step: turn raw Open-Meteo JSON files into one clean table.

Input : data/raw/<city>_<date>.json  (parallel lists inside a 'daily' block)
Output: data/clean/weather_clean.csv (one row per city per day)

This step does NOT drop or fill missing values. Nulls are caught by the
quality step, so bad data fails loudly instead of being hidden.
"""

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

COLUMN_MAP = {
    "time": "date",
    "temperature_2m_max": "temp_max_c",
    "temperature_2m_min": "temp_min_c",
    "precipitation_sum": "precip_mm",
    "wind_speed_10m_max": "wind_max_kmh",
}

NUMERIC_COLUMNS = ["temp_max_c", "temp_min_c", "precip_mm", "wind_max_kmh"]

FINAL_COLUMNS = [
    "city",
    "date",
    "temp_max_c",
    "temp_min_c",
    "temp_avg_c",
    "precip_mm",
    "wind_max_kmh",
    "loaded_at",
]


def get_latest_raw_files(raw_dir):
    """Return {city_name: latest_file_path} from the raw folder.

    File names look like mumbai_2026-11-27.json. The date in the name is
    ISO format, so sorting by name also sorts by date; the last file wins.
    """
    latest = {}
    for file_path in sorted(Path(raw_dir).glob("*.json")):
        city = file_path.stem.rsplit("_", 1)[0]
        latest[city] = file_path
    return latest


def raw_to_dataframe(file_path, city_name):
    """Read one raw JSON file and return its daily block as a table."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data["daily"])  # parallel lists -> rows
    df["city"] = city_name.title()
    return df


def clean(df):
    """Rename columns, fix types, remove duplicates, add derived columns."""
    df = df.rename(columns=COLUMN_MAP)

    df["date"] = pd.to_datetime(df["date"]).dt.date
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.drop_duplicates(subset=["city", "date"])

    df["temp_avg_c"] = ((df["temp_max_c"] + df["temp_min_c"]) / 2).round(2)
    df["loaded_at"] = pd.Timestamp.now().floor("s")

    df = df[FINAL_COLUMNS].sort_values(["city", "date"]).reset_index(drop=True)
    return df


def run_transform(config):
    """Transform all cities and save one clean CSV. Return the clean table."""
    raw_files = get_latest_raw_files(config["paths"]["raw"])
    if not raw_files:
        raise FileNotFoundError(
            f"No raw files found in {config['paths']['raw']}. Run extract first."
        )

    frames = []
    for city, file_path in raw_files.items():
        df = raw_to_dataframe(file_path, city)
        logger.info("%s: %d rows read from %s", city.title(), len(df), file_path.name)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    rows_in = len(combined)

    clean_df = clean(combined)
    logger.info("Rows in: %d, rows out: %d", rows_in, len(clean_df))

    clean_dir = Path(config["paths"]["clean"])
    clean_dir.mkdir(parents=True, exist_ok=True)
    out_path = clean_dir / "weather_clean.csv"
    clean_df.to_csv(out_path, index=False)
    logger.info("Clean data saved to %s", out_path)

    return clean_df


if __name__ == "__main__":
    from src.extract import load_config

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    run_transform(load_config())