# Progress log

## Step 1: Repo setup
- Created folder structure, venv, config.yaml, .gitignore and pushed to GitHub.
- Learned: config holds cities, dates and paths so code never needs editing for changes.

## Step 2: Extract
- Calls the Open-Meteo archive API per city and saves the untouched JSON to data/raw/.
- Learned: raw layer lets me re-run transform without calling the API again.
- Broke: (write what went wrong, for example the skeleton had only TODO bodies, so nothing ran).

## Step 3: Transform
- Reshaped parallel lists into one row per city per day; renamed columns, fixed types, added temp_avg_c.
- Learned: transform does not drop nulls; quality checks catch them so bad data fails loudly.

## Step 4: Quality checks
- Six checks (not empty, row count, no nulls, no duplicates, max >= min, value ranges) stop the pipeline on failure.
- Broke: (write what happened, for example nulls in the newest days, fixed by raising end_lag_days).
- Learned: all checks run before failing, so I see every problem at once.