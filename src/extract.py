"""Extract step: fetch daily weather data from Open-Meteo and save it as raw JSON.

No cleaning happens here. The API response is stored exactly as received,
so the transform step can be re-run later without calling the API again.
"""

import json
import logging
from datetime import date, timedelta
from pathlib import Path

import requests
import yaml

logger = logging.getLogger(__name__)

API_URL = "https://archive-api.open-meteo.com/v1/archive"


def load_config(path="config/config.yaml"):
    """Read the YAML config file and return it as a dict."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_date_range(config):
    """Return (start, end) as 'YYYY-MM-DD' strings.

    start comes from config; end is today minus end_lag_days,
    because the archive API lags a few days behind.
    """
    start = str(config["start_date"])
    end = (date.today() - timedelta(days=config["end_lag_days"])).isoformat()
    return start, end


def fetch_city(city, start, end, config):
    """Call the API for one city and return the parsed JSON."""
    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "start_date": start,
        "end_date": end,
        "daily": ",".join(config["daily_variables"]),
        "timezone": config["timezone"],
    }
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()  # stops with a clear error on 4xx / 5xx
    return response.json()


def save_raw(data, city_name, raw_dir):
    """Save the untouched API response to data/raw/ and return the file path."""
    folder = Path(raw_dir)
    folder.mkdir(parents=True, exist_ok=True)
    file_path = folder / f"{city_name.lower()}_{date.today()}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return file_path


def run_extract(config):
    """Fetch and save raw data for every city. Return the list of saved files."""
    start, end = get_date_range(config)
    logger.info("Extracting %s to %s for %d cities", start, end, len(config["cities"]))

    saved_files = []
    for city in config["cities"]:
        data = fetch_city(city, start, end, config)
        file_path = save_raw(data, city["name"], config["paths"]["raw"])
        days = len(data["daily"]["time"])
        logger.info("%s: %d days saved to %s", city["name"], days, file_path)
        saved_files.append(file_path)

    logger.info("Extract finished: %d files", len(saved_files))
    return saved_files


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    run_extract(load_config())