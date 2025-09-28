import logging
import sys
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Main global logger
logger = logging.getLogger("smartresearch")
logger.setLevel(logging.DEBUG)

# Console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    "%Y-%m-%d %H:%M:%S"
)
ch.setFormatter(formatter)

# Add handler if not already added
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    logger.addHandler(ch)

# Per-job loggers
def job_logger(job_id: str) -> logging.Logger:
    job_log = logging.getLogger(f"smartresearch.job.{job_id}")
    if not job_log.handlers:
        fh = logging.FileHandler(LOG_DIR / f"{job_id}.log", encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        job_log.addHandler(fh)
    job_log.setLevel(logging.INFO)
    return job_log

def remove_handler(job_id: str):
    job_log = logging.getLogger(f"smartresearch.job.{job_id}")
    for h in job_log.handlers[:]:
        job_log.removeHandler(h)
        h.close()

__all__ = ["logger", "job_logger", "remove_handler"]
