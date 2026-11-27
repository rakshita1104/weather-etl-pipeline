"""Quality step: validate the clean table before it is loaded.

Every check returns (passed, detail). All checks run and are logged,
then the step raises DataQualityError if any of them failed.
"""

import logging
from datetime import date

import pandas as pd

from src.extract import get_date_range

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "city",
    "date",
    "temp_max_c",
    "temp_min_c",
    "precip_mm",
    "wind_max_kmh",
]


class DataQualityError(Exception):
    """Raised when one or more quality checks fail."""


def check_not_empty(df):
    passed = len(df) > 0
    return passed, f"{len(df)} rows"


def check_row_count(df, config):
    start, end = get_date_range(config)
    days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    expected = len(config["cities"]) * days
    passed = len(df) == expected
    return passed, f"expected {expected} rows ({len(config['cities'])} cities x {days} days), got {len(df)}"


def check_no_nulls(df):
    null_counts = df[REQUIRED_COLUMNS].isna().sum()
    bad = null_counts[null_counts > 0]
    if bad.empty:
        return True, "no nulls in required columns"
    return False, "nulls found: " + ", ".join(f"{col}={n}" for col, n in bad.items())


def check_no_duplicates(df):
    dupes = int(df.duplicated(subset=["city", "date"]).sum())
    return dupes == 0, f"{dupes} duplicate (city, date) rows"


def check_max_not_below_min(df):
    bad = int((df["temp_max_c"] < df["temp_min_c"]).sum())
    return bad == 0, f"{bad} rows where temp_max_c < temp_min_c"


def check_value_ranges(df):
    problems = []

    bad_temp = int(
        (
            (df["temp_max_c"].notna() & ~df["temp_max_c"].between(-10, 55))
            | (df["temp_min_c"].notna() & ~df["temp_min_c"].between(-10, 55))
        ).sum()
    )
    if bad_temp:
        problems.append(f"{bad_temp} temperature values outside -10 to 55")

    bad_rain = int((df["precip_mm"] < 0).sum())
    if bad_rain:
        problems.append(f"{bad_rain} negative rainfall values")

    bad_wind = int((df["wind_max_kmh"] < 0).sum())
    if bad_wind:
        problems.append(f"{bad_wind} negative wind values")

    if problems:
        return False, "; ".join(problems)
    return True, "all values within expected ranges"


def run_quality(df, config):
    """Run all checks, log each result, raise DataQualityError if any failed."""
    checks = [
        ("not_empty", check_not_empty(df)),
        ("row_count", check_row_count(df, config)),
        ("no_nulls", check_no_nulls(df)),
        ("no_duplicates", check_no_duplicates(df)),
        ("max_not_below_min", check_max_not_below_min(df)),
        ("value_ranges", check_value_ranges(df)),
    ]

    failed = []
    for name, (passed, detail) in checks:
        if passed:
            logger.info("PASS %-18s %s", name, detail)
        else:
            logger.error("FAIL %-18s %s", name, detail)
            failed.append(name)

    if failed:
        raise DataQualityError(f"{len(failed)} quality check(s) failed: {', '.join(failed)}")

    logger.info("All %d quality checks passed", len(checks))
    return True


if __name__ == "__main__":
    from src.extract import load_config

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config = load_config()
    clean_path = f"{config['paths']['clean']}/weather_clean.csv"
    run_quality(pd.read_csv(clean_path), config)