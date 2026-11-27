"""Run the whole weather ETL pipeline: extract -> transform -> quality -> load -> export.

Usage: python run_pipeline.py
Logs go to the console and to logs/pipeline.log.
"""

import logging
import sys
import time
from pathlib import Path

from src.export import run_export
from src.extract import load_config, run_extract
from src.load import run_load
from src.quality import run_quality
from src.transform import run_transform

logger = logging.getLogger("pipeline")


def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
        ],
    )


def timed(step_name, func, *args):
    """Run one step, log its duration, and return its result."""
    logger.info("--- %s: start", step_name)
    started = time.time()
    result = func(*args)
    logger.info("--- %s: done in %.1fs", step_name, time.time() - started)
    return result


def main():
    setup_logging()
    logger.info("Pipeline started")
    try:
        config = load_config()
        timed("extract", run_extract, config)
        clean_df = timed("transform", run_transform, config)
        timed("quality", run_quality, clean_df, config)
        timed("load", run_load, clean_df, config)
        timed("export", run_export, config)
    except Exception:
        logger.exception("Pipeline FAILED")
        sys.exit(1)
    logger.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()