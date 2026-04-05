import logging
import os


LOG_LEVEL_ENV = "FRETBOARD_LOG_LEVEL"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def normalize_log_level(value: str | None) -> int:
    if not value:
        return logging.INFO

    level_name = value.upper()
    if level_name not in logging._nameToLevel:
        raise ValueError(f"Unsupported log level: {value}")
    return logging._nameToLevel[level_name]


def configure_logging(level: str | None = None) -> int:
    resolved_level = normalize_log_level(level or os.environ.get(LOG_LEVEL_ENV))
    logging.basicConfig(level=resolved_level, format=LOG_FORMAT, force=True)
    return resolved_level


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
