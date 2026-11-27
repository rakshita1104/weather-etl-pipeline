-- Q1: Average max temperature per city (hottest city first)
SELECT city,
       ROUND(AVG(temp_max_c), 1) AS avg_max_temp_c
FROM weather_daily
GROUP BY city
ORDER BY avg_max_temp_c DESC;

-- Q2: Hottest day per city
SELECT city, date, temp_max_c
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY city ORDER BY temp_max_c DESC) AS rn
    FROM weather_daily
)
WHERE rn = 1
ORDER BY temp_max_c DESC;

-- Q3: Coldest night per city
SELECT city, date, temp_min_c
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY city ORDER BY temp_min_c ASC) AS rn
    FROM weather_daily
)
WHERE rn = 1
ORDER BY temp_min_c ASC;

-- Q4: Number of rainy days per city (more than 1 mm of rain)
SELECT city,
       COUNT(*) FILTER (WHERE precip_mm > 1) AS rainy_days,
       COUNT(*) AS total_days
FROM weather_daily
GROUP BY city
ORDER BY rainy_days DESC;

-- Q5: Monthly average temperature per city
SELECT city,
       DATE_TRUNC('month', date) AS month,
       ROUND(AVG(temp_avg_c), 1) AS avg_temp_c
FROM weather_daily
GROUP BY city, month
ORDER BY city, month;

-- Q6: Cities ranked by total rainfall
SELECT city,
       ROUND(SUM(precip_mm), 1) AS total_rain_mm,
       RANK() OVER (ORDER BY SUM(precip_mm) DESC) AS rain_rank
FROM weather_daily
GROUP BY city
ORDER BY rain_rank;

-- Q7: Top 10 windiest days
SELECT city, date, wind_max_kmh
FROM weather_daily
ORDER BY wind_max_kmh DESC
LIMIT 10;

-- Q8: Biggest day-to-day temperature jumps (uses LAG)
SELECT city, date, temp_avg_c, change_c
FROM (
    SELECT city, date, temp_avg_c,
           ROUND(temp_avg_c - LAG(temp_avg_c) OVER (PARTITION BY city ORDER BY date), 2) AS change_c
    FROM weather_daily
)
WHERE change_c IS NOT NULL
ORDER BY ABS(change_c) DESC
LIMIT 10;

-- Q9: Summary of the latest available day across all cities
SELECT date,
       ROUND(AVG(temp_max_c), 1) AS avg_max_temp_c,
       MAX_BY(city, temp_max_c)  AS hottest_city,
       MIN_BY(city, temp_min_c)  AS coldest_city,
       ROUND(SUM(precip_mm), 1)  AS total_rain_mm,
       MAX_BY(city, wind_max_kmh) AS windiest_city
FROM weather_daily
WHERE date = (SELECT MAX(date) FROM weather_daily)
GROUP BY date;