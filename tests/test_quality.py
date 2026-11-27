import pandas as pd

from src.quality import (
    check_max_not_below_min,
    check_no_duplicates,
    check_no_nulls,
    check_not_empty,
    check_value_ranges,
)


def good_df():
    return pd.DataFrame(
        {
            "city": ["Mumbai", "Mumbai"],
            "date": ["2026-01-01", "2026-01-02"],
            "temp_max_c": [30.0, 31.0],
            "temp_min_c": [20.0, 21.0],
            "precip_mm": [0.0, 2.0],
            "wind_max_kmh": [10.0, 12.0],
        }
    )


def test_good_data_passes_every_check():
    df = good_df()
    assert check_not_empty(df)[0]
    assert check_no_nulls(df)[0]
    assert check_no_duplicates(df)[0]
    assert check_max_not_below_min(df)[0]
    assert check_value_ranges(df)[0]


def test_empty_table_fails():
    assert not check_not_empty(good_df().iloc[0:0])[0]


def test_null_value_fails():
    df = good_df()
    df.loc[0, "temp_max_c"] = None
    assert not check_no_nulls(df)[0]


def test_duplicate_city_date_fails():
    df = pd.concat([good_df(), good_df().iloc[[0]]], ignore_index=True)
    assert not check_no_duplicates(df)[0]


def test_max_below_min_fails():
    df = good_df()
    df.loc[0, "temp_max_c"] = 10.0
    assert not check_max_not_below_min(df)[0]


def test_negative_rain_fails():
    df = good_df()
    df.loc[0, "precip_mm"] = -1.0
    assert not check_value_ranges(df)[0]


def test_impossible_temperature_fails():
    df = good_df()
    df.loc[0, "temp_max_c"] = 90.0
    assert not check_value_ranges(df)[0]