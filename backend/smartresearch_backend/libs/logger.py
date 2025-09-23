import logging, sys, os
from logging.handlers import RotatingFileHandler
from pathlib import Path

ROOT_LOGGER_NAME = "smartresearch"
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"   # backend/logs
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Base logger (console)
_base = logging.getLogger(ROOT_LOGGER_NAME)
_base.setLevel(logging.DEBUG)
if not _base.handlers:
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%Y-%m-%d %H:%M:%S")
    ch.setFormatter(fmt)
    _base.addHandler(ch)

# Quiet some chatty deps
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)

def job_logger(job_id: str) -> tuple[logging.Logger, logging.Handler, str]:
    """
    Create/return a child logger and a file handler for this job_id.
    Returns (logger, handler, logfile_path). You MUST remove the handler when done.
    """
    logger = logging.getLogger(f"{ROOT_LOGGER_NAME}.job.{job_id}")
    logger.setLevel(logging.DEBUG)

    logfile = LOG_DIR / f"{job_id}.log"
    fh = RotatingFileHandler(logfile, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)

    # attach once per call; caller must remove when finished
    logger.addHandler(fh)
    logger.propagate = True  # also echo to console via base

    return logger, fh, str(logfile)

def remove_handler(logger: logging.Logger, handler: logging.Handler) -> None:
    try:
        logger.removeHandler(handler)
        handler.close()
    except Exception:
        pass
