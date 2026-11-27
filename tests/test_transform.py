import json

import pandas as pd

from src.transform import FINAL_COLUMNS, clean, raw_to_dataframe


def make_raw_file(tmp_path):
    data = {
        "daily": {
            "time": ["2026-01-01", "2026-01-02"],
            "temperature_2m_max": [30.0, 32.0],
            "temperature_2m_min": [20.0, 22.0],
            "precipitation_sum": [0.0, 5.0],
            "wind_speed_10m_max": [10.0, 12.0],
        }
    }
    path = tmp_path / "mumbai_2026-01-10.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_raw_to_dataframe_makes_one_row_per_day(tmp_path):
    df = raw_to_dataframe(make_raw_file(tmp_path), "mumbai")
    assert len(df) == 2
    assert set(df["city"]) == {"Mumbai"}


def test_clean_renames_columns_and_adds_average(tmp_path):
    df = clean(raw_to_dataframe(make_raw_file(tmp_path), "mumbai"))
    assert list(df.columns) == FINAL_COLUMNS
    assert df.loc[0, "temp_avg_c"] == 25.0


def test_clean_removes_duplicate_city_date_rows(tmp_path):
    raw = raw_to_dataframe(make_raw_file(tmp_path), "mumbai")
    doubled = pd.concat([raw, raw], ignore_index=True)
    assert len(clean(doubled)) == 2


def test_clean_keeps_nulls_for_quality_step(tmp_path):
    raw = raw_to_dataframe(make_raw_file(tmp_path), "mumbai")
    raw.loc[0, "temperature_2m_max"] = None
    df = clean(raw)
    assert df["temp_max_c"].isna().sum() == 1