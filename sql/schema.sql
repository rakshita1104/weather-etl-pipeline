CREATE TABLE IF NOT EXISTS weather_daily (
    city          VARCHAR   NOT NULL,
    date          DATE      NOT NULL,
    temp_max_c    DOUBLE    NOT NULL,
    temp_min_c    DOUBLE    NOT NULL,
    temp_avg_c    DOUBLE    NOT NULL,
    precip_mm     DOUBLE    NOT NULL,
    wind_max_kmh  DOUBLE    NOT NULL,
    loaded_at     TIMESTAMP NOT NULL,
    PRIMARY KEY (city, date)
);